import argparse
import importlib
import json

import cv2
import numpy as np

from plate import PlateVisionSystem
from plate.well_plates import Plates
from arm_control.inverse_kinematics import inverse_kinematics as ik


PLATE_TYPES = ["96well", "24well", "12well", "6well"]

# ChArUco calibration values (March 16, 2026)
DEFAULT_CAMERA_MATRIX = np.array([
    [2.43991893e03, 0.0, 9.41578101e02],
    [0.0, 2.43832968e03, 5.28765084e02],
    [0.0, 0.0, 1.0],
], dtype=np.float64)
DEFAULT_DIST_COEFFS = np.array([
    1.13331347e-01,
    1.53496279e00,
    -6.97631297e-03,
    1.60303967e-03,
    -1.00315130e01,
], dtype=np.float64)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Raspberry Pi headless ArUco plate + arm detection"
    )
    parser.add_argument("--plate-type", required=True, choices=PLATE_TYPES,
                        help="Target plate type to detect")
    parser.add_argument("--image", type=str,
                        help="Optional input image path (recommended for Node-RED snapshots)")
    parser.add_argument("--camera-index", type=int, default=0,
                        help="OpenCV camera index fallback (default: 0)")
    parser.add_argument("--width", type=int, default=1280, help="Capture width")
    parser.add_argument("--height", type=int, default=720, help="Capture height")
    parser.add_argument("--fps", type=int, default=30, help="Capture frame rate")
    parser.add_argument("--warmup-frames", type=int, default=4,
                        help="Frames to discard before capture when using camera")
    parser.add_argument("--no-use-picamera2", action="store_true",
                        help="Disable Picamera2 and force OpenCV camera capture")
    parser.add_argument("--preview", action="store_true",
                        help="Show preview window for laptop debugging")
    parser.add_argument("--lock-exposure", action="store_true",
                        help="Disable auto exposure when camera backend supports it")
    parser.add_argument("--exposure-us", type=int,
                        help="Manual exposure time in microseconds (Picamera2)")
    parser.add_argument("--analogue-gain", type=float,
                        help="Manual analog gain (Picamera2)")
    parser.add_argument("--no-undistort", action="store_true",
                        help="Skip applying camera undistortion")
    parser.add_argument("--pretty-json", action="store_true",
                        help="Pretty-print JSON instead of single-line output")
    return parser.parse_args()


def _open_picamera2(width, height, fps, lock_exposure=False, exposure_us=None, analogue_gain=None):
    try:
        picamera2_module = importlib.import_module("picamera2")
        Picamera2 = picamera2_module.Picamera2
    except ImportError:
        return None, None

    picam2 = Picamera2()
    controls = {"FrameDurationLimits": (int(1e6 / fps), int(1e6 / fps))}
    if lock_exposure:
        controls["AeEnable"] = False
        if exposure_us is not None:
            controls["ExposureTime"] = int(exposure_us)
        if analogue_gain is not None:
            controls["AnalogueGain"] = float(analogue_gain)

    config = picam2.create_preview_configuration(main={"size": (width, height), "format": "RGB888"}, controls=controls)
    picam2.configure(config)
    picam2.start()
    return "picamera2", picam2


def _open_opencv_camera(index, width, height, fps, lock_exposure=False):
    cap = cv2.VideoCapture(index)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    cap.set(cv2.CAP_PROP_FPS, fps)

    if lock_exposure:
        # Backend-specific: these values are best-effort and may vary by driver.
        cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1)

    if not cap.isOpened():
        return None, None
    return "opencv", cap


def open_camera(args):
    if not args.no_use_picamera2:
        mode, camera = _open_picamera2(
            args.width,
            args.height,
            args.fps,
            lock_exposure=args.lock_exposure,
            exposure_us=args.exposure_us,
            analogue_gain=args.analogue_gain,
        )
        if mode is not None:
            return mode, camera

    mode, camera = _open_opencv_camera(
        args.camera_index,
        args.width,
        args.height,
        args.fps,
        lock_exposure=args.lock_exposure,
    )
    if mode is None:
        raise RuntimeError("Unable to open camera via Picamera2 or OpenCV")
    return mode, camera


def read_frame(camera_mode, camera):
    if camera_mode == "picamera2":
        frame = camera.capture_array()
        if frame is None:
            return False, None
        # Picamera2 RGB -> OpenCV BGR for consistent processing paths.
        return True, cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

    ret, frame = camera.read()
    return ret, frame


def close_camera(camera_mode, camera):
    if camera_mode == "picamera2":
        camera.stop()
        camera.close()
        return
    camera.release()


def preprocess_frame(frame, undistort=True):
    if not undistort:
        return frame
    h, w = frame.shape[:2]
    new_mtx, _ = cv2.getOptimalNewCameraMatrix(DEFAULT_CAMERA_MATRIX, DEFAULT_DIST_COEFFS, (w, h), 1, (w, h))
    return cv2.undistort(frame, DEFAULT_CAMERA_MATRIX, DEFAULT_DIST_COEFFS, None, new_mtx)


def capture_single_frame(args):
    if args.image:
        frame = cv2.imread(args.image)
        if frame is None:
            raise FileNotFoundError(f"Could not read image path: {args.image}")
        return "image", frame

    camera_mode, camera = open_camera(args)
    try:
        for _ in range(max(args.warmup_frames, 0)):
            read_frame(camera_mode, camera)

        ret, frame = read_frame(camera_mode, camera)
        if not ret or frame is None:
            raise RuntimeError("Failed to capture frame from camera")
        return camera_mode, frame
    finally:
        close_camera(camera_mode, camera)


def main():
    args = parse_args()
    vision = PlateVisionSystem()
    # type_to_marker_id = {v: k for k, v in vision.ID_TO_TYPE.items()} #
    # target_marker_id = type_to_marker_id[args.plate_type]

    #target marker to be given by UDP form node-red, for now try 96-well marker
    target_marker_id = 0
    plate = Plates(vision.ID_TO_TYPE.get(target_marker_id))
    camera_mode, raw_frame = capture_single_frame(args)
    frame = preprocess_frame(raw_frame, undistort=not args.no_undistort)
    cv2.imwrite("/home/aspamtech/robotic-cell-seeding/debug/capture.jpg", frame)

      #return (br_x, br_y), angle, [corners[selected_index]], marker_id

    arm_center = vision.arm_coord(frame)
    br, angle, plate_corners, marker_id = vision.get_plate_pose(frame, target_marker_id=target_marker_id)
    if plate_corners is not None:
            scale = vision.setScale(plate_corners, vision.PLATE_MARKER_DIMENSION_MM) 
            br = (br[0]/scale, br[1]/scale) #convert from pixels to mm using scale
            arm_center = (arm_center[0]/scale, arm_center[1]/scale) 
    else: 
        scale = None


    plate_topLeft = plate.marker_to_well(angle, br)
    translation_vector = plate.top_left_to_arm(plate_topLeft, arm_center) # in mm (arm_center converted to mm)
    grid_points = plate.well_coordinate(plate_topLeft, translation_vector)
    rotated_grid = plate.rotate_grid(grid_points, angle, plate_topLeft)
    first_row = rotated_grid[:plate.config["cols"]]
    
    #inverse kinematics block now
    target_pos = []
    invalid_targets = []
    for coord in first_row:
        try:
            ik(coord)
        except ValueError as exc:
            invalid_targets.append({"coord": coord.tolist() if hasattr(coord, "tolist") else coord, "error": str(exc)})
            continue
        target_pos.append(coord)

    if args.preview:
        preview = frame.copy()
        if plate_corners is not None:
            cv2.aruco.drawDetectedMarkers(preview, plate_corners)
            vision.draw_position_info(preview, angle, br)
        cv2.imshow("Plate Detection", preview)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    output = {
        "plate_type_requested": args.plate_type,
        "plate_detected": br is not None,
        "angle": np.rad2deg(angle),
        "target_coordinates": target_pos,
        "invalid_targets": invalid_targets,

        # "detected_marker_ids": [
        #     marker_id for marker_id in [
        #         int(plate_pose[4]) if plate_pose[4] is not None else None,
        #         vision.ARM_MARKER_ID if arm_center is not None else None,
        #     ]
        #     if marker_id is not None
        # ],
        "success": bool(br[0] is not None and arm_center is not None and len(invalid_targets) == 0),
    }

    json_text = json.dumps(
        output,
        default=lambda x: x.tolist() if hasattr(x, "tolist") else x,
        indent=2 if args.pretty_json else None,
    )
    print(json_text)


if __name__ == "__main__":
    main()