# Debug Session Prompt

Debug context
- This is a diagnosis-first session.
- Prioritize identifying root causes and proving them with logs, intermediate values, and frame-consistency checks.

What to debug
1. Marker detection stability and corner ordering.
2. Coordinate-frame consistency from image frame to robot frame.
3. Relative angle computation and sign conventions.
4. Scale conversion consistency for plate marker and arm marker.
5. Height mismatch effects and depth approximation behavior.
6. IK reachability and shoulder-limit filtering.

Expected outputs
- Root-cause findings ordered by severity.
- Exact file and line references for each issue.
- Minimal fixes with clear risk assessment.
- Validation results before and after fixes.

Debug checks to run
- Print arm and plate pose values before and after coordinate transforms.
- Print raw and effective scales:
  - plate_scale_px_per_mm
  - arm_scale_px_per_mm
  - arm_scale_projected_to_plate_px_per_mm
  - depth_ratio_arm_to_plate
- Print first-row target coordinates in mm and their back-projected image pixels.
- Print IK acceptance summary:
  - valid count
  - invalid count
  - first few invalid reasons

Node-RED compatibility checks
- Confirm stdout is valid JSON only for machine parsing.
- Confirm contract fields are stable across success and failure paths.
- Confirm timeout and retry behavior for controller handshakes.

Inputs for this debug run
- Plate type: <fill here>
- Image path optional: <fill here>
- Camera-to-plate distance mm optional: <fill here>
- Arm-above-plate distance mm optional: <fill here>
- Any known bad case image: <fill here>

Definition of done
- At least one failing case and one passing case are explained.
- Recommended fix list is prioritized and testable.
- Residual risks and calibration needs are clearly listed.
