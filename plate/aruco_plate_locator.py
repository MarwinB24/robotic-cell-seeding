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
    ARM_MARKER_ID = 4
    PLATE_MARKER_IDS = {0, 1, 2, 3}
    PLATE_MARKER_DIMENSION_MM = 32 #35
    
    def __init__(self, marker_dict=aruco.DICT_ARUCO_ORIGINAL): #DICT_4X4_50
        # Initialize ArUco settings
        self.dictionary = aruco.getPredefinedDictionary(marker_dict)
        self.parameters = aruco.DetectorParameters()
        self.detector = aruco.ArucoDetector(self.dictionary, self.parameters)

    def _detect_markers(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        return self.detector.detectMarkers(gray) #returns corners, ids, rejected

    def _select_marker_index(self, ids, target_marker_id=None): #uses result from _detect_markers
        if ids is None or len(ids) == 0: 
            return None

        flat_ids = ids.flatten() # 

        if target_marker_id is not None:
            for i, mid in enumerate(flat_ids):
                if int(mid) == int(target_marker_id):
                    return i 
            return None

        # Prefer plate markers when auto-selecting a marker for plate pose.
        for i, mid in enumerate(flat_ids):
            if int(mid) in self.PLATE_MARKER_IDS:
                return i

        return 0

    def _br_from_detection(self, corners, ids, selected_index): #uses result from _detect_markers and index from _select_marker_index
        c = corners[selected_index][0] 
        br_x, br_y = c[2] #this is shortcut for c[2][:]
        marker_id = ids[selected_index][0]
        angle = np.arctan2(c[1][1] - c[0][1], c[1][0] - c[0][0])
        return (br_x, br_y), angle, c, marker_id


    def get_plate_pose(self, frame, target_marker_id=None): # I didn't write
        """Returns (x, y) center, angle, marker corners, and marker ID of detected plate"""
        corners, ids, rejected = self._detect_markers(frame)
        
        if ids is not None and len(ids) > 0:
            selected_index = self._select_marker_index(ids, target_marker_id=target_marker_id)
            if selected_index is None:
                return None, None, None, None
            return self._br_from_detection(corners, ids, selected_index)

        return None, None, None, None
    
    def arm_coord(self, frame):
        arm = self.get_plate_pose(frame, self.ARM_MARKER_ID)
        arm_coords = arm[2] #corners of arm marker
        angle = arm[1]
        center_x = np.mean(arm_coords[:, 0])
        center_y = np.mean(arm_coords[:, 1])
        center = (center_x, center_y)        
        return center, angle #returns just the centre of the marker

    def preprocess_frame(self, frame, camera_matrix, dist_coeffs, undistort=True):
        if not undistort:
            return frame, camera_matrix, dist_coeffs
        h, w = frame.shape[:2]
        new_mtx, _ = cv2.getOptimalNewCameraMatrix(camera_matrix, dist_coeffs, (w, h), 1, (w, h))
        undistorted = cv2.undistort(frame, camera_matrix, dist_coeffs, None, new_mtx)
        # Distortion has already been removed in undistorted image space.
        return undistorted, new_mtx, np.zeros_like(dist_coeffs)

    @staticmethod
    def to_robot_point(pt, frame_height):
        if pt is None:
            return None
        return (pt[0], frame_height - pt[1])

    @staticmethod
    def to_robot_corners(marker_corners, frame_height):
        if marker_corners is None:
            return None
        marker_corners = np.array(marker_corners, dtype=np.float32)
        marker_corners[:, 1] = frame_height - marker_corners[:, 1]
        return marker_corners

    @staticmethod
    def estimate_marker_z_mm(marker_corners, marker_size_mm, camera_matrix, dist_coeffs):
        """Estimate marker depth (camera Z, mm) using solvePnP on ArUco corners."""
        if marker_corners is None:
            return None

        img_pts = np.array(marker_corners, dtype=np.float32).reshape(4, 2)
        half = float(marker_size_mm) / 2.0
        # ArUco corner order: top-left, top-right, bottom-right, bottom-left.
        obj_pts = np.array([
            [-half, half, 0.0],
            [half, half, 0.0],
            [half, -half, 0.0],
            [-half, -half, 0.0],
        ], dtype=np.float32)

        pnp_flag = getattr(cv2, "SOLVEPNP_IPPE_SQUARE", cv2.SOLVEPNP_ITERATIVE)
        ok, _rvec, tvec = cv2.solvePnP(obj_pts, img_pts, camera_matrix, dist_coeffs, flags=pnp_flag)
        if not ok:
            return None
        return float(tvec[2][0])

    def setScale(self, corner, markerDimension): #pixel distance device by scale gives mm
        c = corner.astype(np.float32)  # shape (4,2)
        d01 = np.linalg.norm(c[1] - c[0]) #linalg.norm calculates Euclidean distance between 2 points
        d12 = np.linalg.norm(c[2] - c[1])
        d23 = np.linalg.norm(c[3] - c[2])
        d30 = np.linalg.norm(c[0] - c[3])

        mean_side_px = np.mean([d01, d12, d23, d30])
        px_per_mm = mean_side_px / markerDimension
        print(px_per_mm)
        return px_per_mm

    def identify_plate(self, marker_id): #use this with config for well_plates class
        if marker_id is None:
            return "Unknown Plate Type"
        return self.ID_TO_TYPE.get(int(marker_id), "Unknown Plate Type")

    # def identify_plate_and_arm(self, frame, plate_type=None):
    #     """
    #     Detect selected plate type and arm centre in a single frame.

    #     Returns a dictionary with:
    #     - plate_pose: tuple in the same structure as get_plate_pose
    #     - plate_type: identified plate type string or None
    #     - plate_marker_id: marker id for selected plate or None
    #     - arm_center: (x, y) tuple or None
    #     - detected_marker_ids: list[int]
    #     """
    #     corners, ids, _ = self._detect_markers(frame)
    #     if ids is None or len(ids) == 0:
    #         return {
    #             "plate_pose": (None, None, None, None, None),
    #             "plate_type": None,
    #             "plate_marker_id": None,
    #             "arm_center": None,
    #             "detected_marker_ids": [],
    #         }

    #     flat_ids = [int(mid) for mid in ids.flatten()]

    #     plate_marker_id = None
    #     if plate_type is not None:
    #         normalized = str(plate_type).strip().lower()
    #         marker_to_type = {v.lower(): k for k, v in self.ID_TO_TYPE.items() if k in self.PLATE_MARKER_IDS}
    #         plate_marker_id = marker_to_type.get(normalized)
    #         if plate_marker_id is None:
    #             valid_types = ", ".join(sorted(marker_to_type.keys()))
    #             raise ValueError(f"Unknown plate type '{plate_type}'. Expected one of: {valid_types}")

    #     selected_plate_index = self._select_marker_index(ids, target_marker_id=plate_marker_id)
    #     plate_pose = (
    #         self._pose_from_detection(corners, ids, selected_plate_index)
    #         if selected_plate_index is not None
    #         else (None, None, None, None, None)
    #     )

    #     arm_index = self._select_marker_index(ids, target_marker_id=self.ARM_MARKER_ID)
    #     arm_center = None
    #     if arm_index is not None:
    #         arm_center = self._pose_from_detection(corners, ids, arm_index)[0]

    #     plate_marker = plate_pose[4]
    #     plate_type_name = self.identify_plate(int(plate_marker)) if plate_marker is not None else None

    #     return {
    #         "plate_pose": plate_pose,
    #         "plate_type": plate_type_name,
    #         "plate_marker_id": int(plate_marker) if plate_marker is not None else None,
    #         "arm_center": arm_center,
    #         "detected_marker_ids": flat_ids,
    #     }
    
    def draw_position_info(self, frame, angle_rad, br): # I didn't write
        """Draw position and axes at bottom right corner of ArUco marker"""
        if br is None: 
            return
        
        # Get bottom right corner of the marker (index 2 in ArUco corner order)
        origin_x = int(br[0])
        origin_y = int(br[1])
        
        # Draw axes at marker's bottom_right
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
        
        # Display coordinates of bottom right corner
        cv2.putText(frame, f"BR X: {br[0]:.1f}", (origin_x + 5, origin_y - 15),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)
        cv2.putText(frame, f"BR Y: {br[1]:.1f}", (origin_x + 5, origin_y),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 255, 0), 1)
    

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
        
        # Draw marker and position info
        # if corners is not None:
        #     aruco.drawDetectedMarkers(frame, corners)
        #     vision.draw_position_info(frame, center, angle, marker_corners)
        #     # Display marker ID
        #     # cv2.putText(frame, f"Marker ID: {marker_id}", (10, 30),
        #     #            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)

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