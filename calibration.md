Fix hardware first
Mount camera rigidly, lock focus/exposure, and keep working distance constant.

Print a ChArUco board with known square size
Example: 10 mm squares. Measure printed squares with calipers/ruler.

Capture calibration images (20–40)
Different tilts/positions, include image edges/corners, same final camera settings.

Run intrinsic calibration
Use OpenCV aruco.detectMarkers + interpolateCornersCharuco + calibrateCameraCharuco to get K and distortion coefficients.

Check quality
Verify mean reprojection error (target ~`<0.5 px), then save params (camera_matrix, dist_coeffs`).

Build plane mapping for cm conversion
Put a known planar reference on your work surface (board/ruler), undistort image, compute homography (findHomography) from image points to real-world cm points.

Convert pixels to cm in runtime
For each detected point: undistort → apply homography (perspectiveTransform) → output (x_cm, y_cm).

Validate accuracy
Measure 5–10 known distances across the field; compute error. If error is high at edges, recapture calibration images.

(If driving robot motion) add hand-eye calibration
This gives camera-to-robot transform so cm coordinates map to robot coordinates reliably.