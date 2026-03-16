# Camera calibration using a ChArUco board.
# Board parameters must match those used to generate the board in charuco.py.
# Reference: https://docs.opencv.org/4.x/da/d13/tutorial_aruco_calibration.html

####USED COPILOT FOR CODING THIS####

#
# Usage:
#   USB / dev webcam:       python camera_callibration.py
#   RPi (with display):     python camera_callibration.py --rpi
#   RPi (headless / SSH):   python camera_callibration.py --rpi --headless
#   From saved images:      python camera_callibration.py --images path/to/folder
#
# RPi setup (run once on the Pi):
#   sudo apt install -y python3-picamera2
#
# Headless mode: auto-captures a frame every --interval seconds whenever the
# board is detected. Move the board to a new angle between beeps (terminal
# prints). Stops automatically once MIN_FRAMES good frames are collected.
#
# Controls (live/display mode only):
#   s  — save current frame for calibration
#   q  — quit capture and run calibration

import argparse
import sys
from pathlib import Path

import cv2
import cv2.aruco as aruco
import numpy as np

# ── Board parameters — keep in sync with charuco.py ────────────────────────────
SQUARES_X       = 5
SQUARES_Y       = 7
SQUARE_LENGTH   = 0.030   # metres
MARKER_LENGTH   = 0.022   # metres
DICT_ID         = aruco.DICT_4X4_50
MIN_FRAMES      = 20      # minimum frames needed for a reliable calibration
OUTPUT_FILE     = Path(__file__).resolve().parent.parent / "camera_calibration.npz"
# ───────────────────────────────────────────────────────────────────────────────


def _make_board():
    dictionary = aruco.getPredefinedDictionary(DICT_ID)
    board = aruco.CharucoBoard(
        (SQUARES_X, SQUARES_Y),
        SQUARE_LENGTH,
        MARKER_LENGTH,
        dictionary,
    )
    return board, dictionary


MIN_CORNERS_PER_FRAME = 6  # need >=6 for a stable homography in Zhang's method


def _detect(frame, detector):
    """Return (charuco_corners, charuco_ids) or (None, None) if too few detected."""
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    charuco_corners, charuco_ids, _, _ = detector.detectBoard(gray)
    if charuco_ids is not None and len(charuco_ids) >= MIN_CORNERS_PER_FRAME:
        return charuco_corners, charuco_ids
    return None, None


def calibrate(all_corners, all_ids, image_size, board):
    """Run cv2.aruco calibration from accumulated detections."""
    # Drop any frame that has fewer than MIN_CORNERS_PER_FRAME corners
    # (can happen if detection quality degraded between capture and calibration).
    filtered = [(c, i) for c, i in zip(all_corners, all_ids)
                if len(i) >= MIN_CORNERS_PER_FRAME]
    if len(filtered) < MIN_FRAMES:
        sys.exit(
            f"Only {len(filtered)} frames have enough corners after filtering "
            f"(need {MIN_FRAMES}). Re-run and ensure the full board is clearly visible."
        )
    all_corners, all_ids = zip(*filtered)
    print(f"\nCalibrating with {len(all_corners)} frames ({len(filtered)} passed filter)...")
    ret, camera_matrix, dist_coeffs, rvecs, tvecs = aruco.calibrateCameraCharuco(
        list(all_corners), list(all_ids), board, image_size, None, None
    )
    print(f"Reprojection error: {ret:.4f} px")
    print(f"Camera matrix:\n{camera_matrix}")
    print(f"Distortion coefficients: {dist_coeffs.ravel()}")

    np.savez(
        OUTPUT_FILE,
        camera_matrix=camera_matrix,
        dist_coeffs=dist_coeffs,
        reprojection_error=ret,
    )
    print(f"\nSaved calibration to: {OUTPUT_FILE}")
    return camera_matrix, dist_coeffs, ret


def from_images(folder):
    board, _ = _make_board()
    detector = aruco.CharucoDetector(board)
    all_corners, all_ids = [], []
    image_size = None

    paths = sorted(Path(folder).glob("*.png")) + sorted(Path(folder).glob("*.jpg"))
    if not paths:
        sys.exit(f"No PNG/JPG images found in {folder}")

    for p in paths:
        frame = cv2.imread(str(p))
        if frame is None:
            print(f"  Skipped (unreadable): {p.name}")
            continue
        if image_size is None:
            image_size = (frame.shape[1], frame.shape[0])
        corners, ids = _detect(frame, detector)
        if corners is not None:
            all_corners.append(corners)
            all_ids.append(ids)
            print(f"  OK  {p.name}  ({len(ids)} corners)")
        else:
            print(f"  --  {p.name}  (not enough corners)")

    if len(all_corners) < MIN_FRAMES:
        sys.exit(
            f"Only {len(all_corners)} usable frames (need {MIN_FRAMES}). "
            "Capture more images from different angles and distances."
        )
    calibrate(all_corners, all_ids, image_size, board)


# ── Camera backends ────────────────────────────────────────────────────────────

class _UsbCamera:
    """Thin wrapper around cv2.VideoCapture for USB / V4L2 cameras."""
    def __init__(self, index=0):
        self._cap = cv2.VideoCapture(index)
        if not self._cap.isOpened():
            sys.exit(f"Cannot open camera index {index}")

    def read(self):
        ret, frame = self._cap.read()
        return frame if ret else None

    def release(self):
        self._cap.release()


class _RpiCamera:
    """Wrapper around picamera2 for the RPi Camera Module (CSI).

    Requires: sudo apt install -y python3-picamera2
    Works with Camera Module v1 (OV5647) on RPi 3B+ via libcamera.
    """
    def __init__(self, width=1920, height=1080):
        try:
            from picamera2 import Picamera2  # noqa: PLC0415
        except ImportError:
            sys.exit(
                "picamera2 not found.\n"
                "Install it on the Pi with: sudo apt install -y python3-picamera2"
            )
        self._picam = Picamera2()
        cfg = self._picam.create_preview_configuration(
            main={"format": "RGB888", "size": (width, height)}
        )
        self._picam.configure(cfg)
        self._picam.start()
        print(f"RPi Camera opened at {width}x{height}")

    def read(self):
        # picamera2 returns RGB — convert to BGR for OpenCV
        frame_rgb = self._picam.capture_array()
        return cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)

    def release(self):
        self._picam.stop()
        self._picam.close()

# ───────────────────────────────────────────────────────────────────────────────


def _run_capture_loop(camera, board, detector):
    """Interactive capture loop (requires a display). Returns (all_corners, all_ids, image_size)."""
    all_corners, all_ids = [], []
    image_size = None
    print("Press 's' to save frame, 'q' to finish & calibrate.")

    while True:
        frame = camera.read()
        if frame is None:
            print("Camera read failed.")
            break
        if image_size is None:
            image_size = (frame.shape[1], frame.shape[0])

        display = frame.copy()
        corners, ids = _detect(frame, detector)
        if corners is not None:
            cv2.aruco.drawDetectedCornersCharuco(display, corners, ids)
            cv2.putText(display, f"Detected: {len(ids)} pts", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

        cv2.putText(display, f"Saved frames: {len(all_corners)}/{MIN_FRAMES}",
                    (10, 65), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
        cv2.putText(display, "s=save  q=calibrate", (10, display.shape[0] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
        cv2.imshow("ChArUco Calibration", display)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('s') and corners is not None:
            all_corners.append(corners)
            all_ids.append(ids)
            print(f"  Saved frame {len(all_corners)}")
        elif key == ord('q'):
            break

    cv2.destroyAllWindows()
    return all_corners, all_ids, image_size


def _run_headless_loop(camera, board, detector, interval=3.0):
    """Headless capture loop — no display required.

    Auto-captures a frame every `interval` seconds when the board is detected.
    Move the board to a new position/angle between captures.
    Returns (all_corners, all_ids, image_size).
    """
    import time
    all_corners, all_ids = [], []
    image_size = None
    last_capture = 0.0

    print(f"Headless mode: auto-capturing every {interval}s when board is visible.")
    print(f"Move the board to a new angle between captures. Need {MIN_FRAMES} frames.")
    print("Press Ctrl+C to abort.")

    try:
        while len(all_corners) < MIN_FRAMES:
            frame = camera.read()
            if frame is None:
                print("Camera read failed.")
                break
            if image_size is None:
                image_size = (frame.shape[1], frame.shape[0])

            corners, ids = _detect(frame, detector)
            now = time.monotonic()

            if corners is not None and (now - last_capture) >= interval:
                all_corners.append(corners)
                all_ids.append(ids)
                last_capture = now
                print(f"  Captured frame {len(all_corners)}/{MIN_FRAMES}  ({len(ids)} corners)")
            elif corners is None:
                print("  Board not visible — reposition and hold steady...", end="\r")

    except KeyboardInterrupt:
        print("\nAborted by user.")

    return all_corners, all_ids, image_size


def live_capture(camera_index=0, use_rpi=False, headless=False, interval=3.0):
    board, _ = _make_board()
    detector = aruco.CharucoDetector(board)

    camera = _RpiCamera() if use_rpi else _UsbCamera(camera_index)
    try:
        if headless:
            all_corners, all_ids, image_size = _run_headless_loop(
                camera, board, detector, interval=interval
            )
        else:
            all_corners, all_ids, image_size = _run_capture_loop(camera, board, detector)
    finally:
        camera.release()

    if len(all_corners) < MIN_FRAMES:
        sys.exit(
            f"Only {len(all_corners)} frames captured (need {MIN_FRAMES}). "
            "Re-run and move the board to more varied angles."
        )
    calibrate(all_corners, all_ids, image_size, board)

    if not headless:
        # Quick visual check — only possible when a display is available
        print("\nShowing undistorted feed. Press any key to exit.")
        camera2 = _RpiCamera() if use_rpi else _UsbCamera(camera_index)
        camera_matrix = np.load(OUTPUT_FILE)["camera_matrix"]
        dist_coeffs   = np.load(OUTPUT_FILE)["dist_coeffs"]
        try:
            while True:
                frame = camera2.read()
                if frame is None:
                    break
                undistorted = cv2.undistort(frame, camera_matrix, dist_coeffs)
                cv2.imshow("Undistorted (verification)", undistorted)
                if cv2.waitKey(1) & 0xFF != 255:
                    break
        finally:
            camera2.release()
        cv2.destroyAllWindows()


def main():
    parser = argparse.ArgumentParser(description="ChArUco camera calibration")
    parser.add_argument(
        "--images",
        metavar="FOLDER",
        help="Calibrate from a folder of images instead of live capture",
    )
    parser.add_argument(
        "--camera",
        type=int,
        default=0,
        metavar="INDEX",
        help="Camera index for USB/V4L2 live capture (default: 0)",
    )
    parser.add_argument(
        "--rpi",
        action="store_true",
        help="Use RPi Camera Module (picamera2) instead of a USB camera",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="No display/GUI: auto-capture frames on a timer (use when running over SSH)",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=3.0,
        metavar="SECONDS",
        help="Seconds between auto-captures in headless mode (default: 3)",
    )
    args = parser.parse_args()

    if args.images:
        from_images(args.images)
    else:
        live_capture(camera_index=args.camera, use_rpi=args.rpi,
                     headless=args.headless, interval=args.interval)


if __name__ == "__main__":
    main()
