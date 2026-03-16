import argparse
import sys

import cv2
import cv2.aruco as aruco
import numpy as np

class PlateVisionSystem:
    def __init__(self, marker_dict=aruco.DICT_4X4_50):
        # Initialize ArUco settings
        self.dictionary = aruco.getPredefinedDictionary(marker_dict)
        self.parameters = aruco.DetectorParameters()
        self.detector = aruco.ArucoDetector(self.dictionary, self.parameters)

    def get_plate_pose(self, frame):
        """Returns (x, y) center, angle, marker corners, and marker ID of detected plate"""
<<<<<<< Updated upstream:plate/aruco_well_locator.py
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        corners, ids, rejected = self.detector.detectMarkers(gray)
=======
        if frame is None:
            return None, None, None, None, None

        if len(frame.shape) == 2:
            gray = frame
        else:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) # converts to grayscale
        corners, ids, rejected = self.detector.detectMarkers(gray) # detect markers
>>>>>>> Stashed changes:plate/aruco_plate_locator.py
        
        # Debug: Show detection status
        # if ids is None:
        #     print(f"No markers detected. Rejected: {len(rejected) if rejected is not None else 0}")
        # else:
        #     print(f"Detected {len(ids)} marker(s)")
        
        if ids is not None and len(ids) > 0:
            # Get first detected plate
            c = corners[0][0]
            center_x = np.mean(c[:, 0])
            center_y = np.mean(c[:, 1])
            marker_id = ids[0][0]  # Extract marker ID
            
            # Calculate angle for axis rotation
            angle = np.arctan2(c[1][1] - c[0][1], c[1][0] - c[0][0])
            
            return (center_x, center_y), angle, corners[0:1], c, marker_id
        return None, None, None, None, None
    
<<<<<<< Updated upstream:plate/aruco_well_locator.py
    def draw_position_info(self, frame, center, angle_rad, marker_corners):
=======
    def arm_coord(self, frame):
        arm_coords = self.get_plate_pose(frame, 4)
        return arm_coords[0] #returns just the centre of the marker

    def setScale(self, corner, markerDimension = 35): #35mm
        return (corner[1][0] - corner[0][0]) / markerDimension

    def identify_plate(self, marker_id): #use this with config for well_plates class
        return self.ID_TO_TYPE.get(marker_id, "Unknown Plate Type")
    
    def draw_position_info(self, frame, center, angle_rad, marker_corners): # I didn't write
>>>>>>> Stashed changes:plate/aruco_plate_locator.py
        """Draw position and axes at top left corner of ArUco marker"""
        if center is None or marker_corners is None:
            return
        
        # Get top left corner of the marker (index 0 in ArUco corner order)
        origin_x = int(marker_corners[0][0])
        origin_y = int(marker_corners[0][1])
        
        # Draw axes at marker's top left
        axis_length = 30
        
        # X-axis (red)
        x_end_x = int(origin_x + axis_length * np.cos(angle_rad))
        x_end_y = int(origin_y + axis_length * np.sin(angle_rad))
        cv2.arrowedLine(frame, (origin_x, origin_y), (x_end_x, x_end_y),
                       (0, 0, 255), 2, tipLength=0.2)
        cv2.putText(frame, 'X', (x_end_x + 3, x_end_y - 3),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1)
        
        # Y-axis (green)
        y_angle = angle_rad + np.pi / 2
        y_end_x = int(origin_x + axis_length * np.cos(y_angle))
        y_end_y = int(origin_y + axis_length * np.sin(y_angle))
        cv2.arrowedLine(frame, (origin_x, origin_y), (y_end_x, y_end_y),
                       (0, 255, 0), 2, tipLength=0.2)
        cv2.putText(frame, 'Y', (y_end_x + 3, y_end_y - 3),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)
        
        # Display coordinates of top left corner
        cv2.putText(frame, f"TL X: {marker_corners[0][0]:.1f}", (origin_x + 5, origin_y - 15),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)
        cv2.putText(frame, f"TL Y: {marker_corners[0][1]:.1f}", (origin_x + 5, origin_y),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 255, 0), 1)
<<<<<<< Updated upstream:plate/aruco_well_locator.py
    
    def draw_grid(self, frame, grid_spacing=50):
        """Draw a grid overlay on the frame"""
        h, w = frame.shape[:2]
        color = (100, 100, 100)  # Dark gray
        thickness = 1
        
        # Vertical lines
        for x in range(0, w, grid_spacing):
            cv2.line(frame, (x, 0), (x, h), color, thickness)
        
        # Horizontal lines
        for y in range(0, h, grid_spacing):
            cv2.line(frame, (0, y), (w, y), color, thickness)
=======


class RpiCamera:
    def __init__(self, width=1280, height=720):
        try:
            from picamera2 import Picamera2
        except ImportError:
            sys.exit(
                "picamera2 not found. Install it on the Pi with: "
                "sudo apt install -y python3-picamera2"
            )

        self.camera = Picamera2()
        config = self.camera.create_preview_configuration(
            main={"format": "RGB888", "size": (width, height)}
        )
        self.camera.configure(config)
        self.camera.start()

    def read(self):
        frame_rgb = self.camera.capture_array()
        frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
        return True, frame_bgr

    def release(self):
        self.camera.stop()
        self.camera.close()
>>>>>>> Stashed changes:plate/aruco_plate_locator.py

# --- Main Test Loop ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ArUco plate detection")
    parser.add_argument("--rpi", action="store_true", help="Use the RPi Camera Module via picamera2")
    parser.add_argument("--headless", action="store_true", help="Print detections instead of opening a window")
    args = parser.parse_args()

    vision = PlateVisionSystem()
<<<<<<< Updated upstream:plate/aruco_well_locator.py
    cap = cv2.VideoCapture(0)
=======
    cap = RpiCamera() if args.rpi else cv2.VideoCapture(0)
    target_marker_id = None
>>>>>>> Stashed changes:plate/aruco_plate_locator.py

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to read frame")
            break
        
        center, angle, corners, marker_corners, marker_id = vision.get_plate_pose(frame)
        
        # Draw marker and position info
        if corners is not None:
            if args.headless:
                print(
                    f"marker_id={marker_id}, center=({center[0]:.1f}, {center[1]:.1f}), "
                    f"angle_rad={angle:.3f}"
                )
            else:
                aruco.drawDetectedMarkers(frame, corners)
                vision.draw_position_info(frame, center, angle, marker_corners)

        if args.headless:
            continue

        cv2.imshow("Plate Detection", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    print(vision.arm_coord(frame))
    cap.release()
    if not args.headless:
        cv2.destroyAllWindows()