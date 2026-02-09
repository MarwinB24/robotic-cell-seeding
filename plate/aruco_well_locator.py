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
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        corners, ids, rejected = self.detector.detectMarkers(gray)
        
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
    
    def draw_position_info(self, frame, center, angle_rad, marker_corners):
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

# --- Main Test Loop ---
if __name__ == "__main__":
    vision = PlateVisionSystem()
    cap = cv2.VideoCapture(0)

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to read frame")
            break
        
        center, angle, corners, marker_corners, marker_id = vision.get_plate_pose(frame)
        
        # Draw grid on frame (AFTER detection to not interfere)
        vision.draw_grid(frame, grid_spacing=50)
        
        # Draw marker and position info
        if corners is not None:
            aruco.drawDetectedMarkers(frame, corners)
            vision.draw_position_info(frame, center, angle, marker_corners)
            # Display marker ID
            # cv2.putText(frame, f"Marker ID: {marker_id}", (10, 30),
            #            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)

        cv2.imshow("Plate Detection", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()