import cv2
from plate import PlateVisionSystem, Plates

def main():
    vision = PlateVisionSystem()
    plate = Plates()
    cap = cv2.VideoCapture(0)
    print("Choose '1' for 96-well, '2' for 24-well, '3' for 12-well, '4' for 6-well, '0' for any marker")
    target_marker_id = int(input("Enter target marker ID (1-4) or '0': "))
    if target_marker_id == 0:
        target_marker_id = None  # accept any
    else:
        target_marker_id -= 1  # Adjust for 0-based indexing

    # Create window and bring it to front
    cv2.namedWindow("Plate Detection", cv2.WINDOW_NORMAL)
    cv2.setWindowProperty("Plate Detection", cv2.WND_PROP_TOPMOST, 1)

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to read frame")
            break

        center, angle, corners, marker_corners, marker_id = vision.get_plate_pose(
            frame, target_marker_id=target_marker_id
        )
        
        # Display frame
        cv2.imshow("Plate Detection", frame)
        
        # Press 'q' to exit
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        # elif key == ord('1'):
        #     target_marker_id = 0  # 96-well
        # elif key == ord('2'):
        #     target_marker_id = 1  # 24-well
        # elif key == ord('3'):
        #     target_marker_id = 2  # 12-well
        # elif key == ord('4'):
        #     target_marker_id = 3  # 6-well
        # elif key == ord('0'):
        #     target_marker_id = None  # accept any

    print(f"Marker ID: {marker_id}")
    print(f"Angle: {angle}")
    print(f"Plate Type: {vision.identify_plate(marker_id)}")
    print(f"Plate Center: {center}\n, Corners: {corners}\n, Marker Corners: {marker_corners}")
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()