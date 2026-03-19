# Build Request Prompt

Project context
- You are working on my robotic cell seeding stack with computer vision, inverse kinematics, and Node-RED orchestration.
- Assume I want production-ready behavior, not a demo-only script.

What I want built
1. Accept user selections for plate type, pipette mode, and run mode.
2. Run CV plus coordinate pipeline.
3. Return structured JSON with targets, IK results, and diagnostics.
4. Drive movement commands to the controller.
5. Coordinate pipette actions and done or ready handshakes.
6. Handle retry, timeout, and safe-stop behavior.

Requirements
- Keep image display in normal camera orientation.
- Use robot coordinate conversion only for math and annotation values.
- Keep angle conventions consistent across detection, transforms, and IK.
- Handle marker scale robustly with optional depth approximation inputs.
- If depth approximation inputs are provided, apply projection of arm scale to plate plane.
- If depth approximation inputs are missing, fall back gracefully and report this in output.
- Ensure output is machine-parseable JSON with no non-JSON lines on stdout.
- Include status flags for:
  - plate_detected
  - arm_detected
  - success
  - failure_reason
  - invalid_targets

Node-RED integration requirements
- Define exact input payload contract expected from Node-RED.
- Define exact output payload contract returned to Node-RED.
- Include deterministic state transitions:
  - idle
  - vision_running
  - move_pending
  - pipette_pending
  - done
  - error
- Add timeout handling and retry policy for controller acknowledgements.

Validation I need
- Run at least one image-based test and one camera or live test path.
- Print concise test summary with:
  - detected markers
  - relative angle
  - scale values
  - number of valid IK targets
  - final success status
- Highlight assumptions that still need physical calibration.

Coding constraints
- Do not break existing working behavior.
- Keep changes minimal and explain each one.
- Add focused debug fields only where they improve diagnosis.
- Include a short summary of what changed and why.

Inputs for this run
- Plate type: <fill here>
- Pipette mode: <fill here>
- Camera-to-plate distance mm: <fill here or none>
- Arm-above-plate distance mm: <fill here or none>
- Test image path optional: <fill here>
- Live camera mode optional: <fill here>

Success criteria
- I can trigger the flow from Node-RED and receive parseable JSON.
- Target generation and IK are consistent with expected physical orientation.
- Failure modes are explicit and actionable, not silent.
