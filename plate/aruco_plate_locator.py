import cv2
import cv2.aruco as aruco
import numpy as np

#add scaling from pixels to mm (measure known distance and distance on camera percieved to get ratio)
#take corner of aruco and subtract, we know this distance

class PlateVisionSystem:
    ID_TO_TYPE = {
        0: "96well",
        1: "24well",
        2: "12well",
        3: "6well",
        4: "Scara_Arm_Centre",
        5: "Tip_Box",
        6: "Waste_Bin",
    }
    
    def __init__(self, marker_dict=aruco.DICT_4X4_50):
        # Initialize ArUco settings
        self.dictionary = aruco.getPredefinedDictionary(marker_dict)
        self.parameters = aruco.DetectorParameters()
        self.detector = aruco.ArucoDetector(self.dictionary, self.parameters)

    def get_plate_pose(self, frame, target_marker_id=None): # I didn't write
        """Returns (x, y) center, angle, marker corners, and marker ID of detected plate"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) # converts to grayscale
        corners, ids, rejected = self.detector.detectMarkers(gray) # detect markers
        
        # Debug: Show detection status
        # if ids is None:
        #     print(f"No markers detected. Rejected: {len(rejected) if rejected is not None else 0}")
        # else:
        #     print(f"Detected {len(ids)} marker(s)")
        
        if ids is not None and len(ids) > 0:
            # Select marker by desired ID when provided
            selected_index = 0
            if target_marker_id is not None:
                for i, mid in enumerate(ids.flatten()):
                    if int(mid) == int(target_marker_id):
                        selected_index = i
                        break

            # Use selected marker
            c = corners[selected_index][0]
            center_x = np.mean(c[:, 0]) #x corners, [0][0] is top left then clockwise, [1][0] [2][0] [3][0]
            center_y = np.mean(c[:, 1]) #y corners, same pattern as above but [y][1]
            marker_id = ids[selected_index][0]  # Extract marker ID
            
            # Calculate angle for axis rotation
            angle = np.arctan2(c[1][1] - c[0][1], c[1][0] - c[0][0]) # y coord, x coord
            
            return (center_x, center_y), angle, [corners[selected_index]], c, marker_id
        return None, None, None, None, None
    
    def arm_coord(self):
        arm_coords = self.get_plate_pose(frame, 4)
        return arm_coords[0] #returns just the centre of the marker

    def setScale(self, corner, markerDimension):
        return (corner[1][0] - corner[0][0]) / markerDimension

    def identify_plate(self, marker_id): #use this with config for well_plates class
        return self.ID_TO_TYPE.get(marker_id, "Unknown Plate Type")
    
    def draw_position_info(self, frame, center, angle_rad, marker_corners): # I didn't write
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
    
    def draw_grid(self, frame, grid_spacing=50): #I didn't write
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
    target_marker_id = None

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to read frame")
            break

        center, angle, corners, marker_corners, marker_id = vision.get_plate_pose(
            frame, target_marker_id=target_marker_id
        )
        
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
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('1'):
            target_marker_id = 0  # 96-well
        elif key == ord('2'):
            target_marker_id = 1  # 24-well
        elif key == ord('3'):
            target_marker_id = 2  # 12-well
        elif key == ord('4'):
            target_marker_id = 3  # 6-well
        elif key == ord('0'):
            target_marker_id = None  # accept any

    cap.release()
    cv2.destroyAllWindows()