import cv2
from plate import PlateVisionSystem, Plates

def main():
    vision = PlateVisionSystem()
    plate = Plates()
    cap = cv2.VideoCapture(0)
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to read frame")
            break

        center, angle, corners, marker_corners, marker_id = vision.get_plate_pose(frame)
        
        # Display frame
        cv2.imshow("Plate Detection", frame)
        
        # Press 'q' to exit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    print(f"Marker ID: {marker_id}")
    print(f"Angle: {angle}")
    print(f"Plate Type: {plate.identify_plate(marker_id)}")
    print(f"Plate Center: {center}\n, Corners: {corners}\n, Marker Corners: {marker_corners}")
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()