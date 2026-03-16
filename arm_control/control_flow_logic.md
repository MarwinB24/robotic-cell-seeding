3 Factors to actuation:
User selection
Location determination
Pipette mode + communication

1) User selects mode + plate type
2) Camera identifies location of plate 
3) Sends signal to pipette to actuate when ready, pause all other motions while this occurs (bundle the done message for move + pipette)
4) When pipette is done, sends signal back to logic
5) logic moves to next location

Stage,Action,Responsibility
1. Config,User selects Mode/Plate.,Node-RED / Pi
2. Vision,"Identify Plate X,Y and ""Z-top"".",OpenCV / Pi
3. IK Solve,"Convert X,Y,Z to Stepper Angles.",Pi (Python/Node-RED)
4. Move-To,Move arm to Safe Height over Target.,Arduino (Stepper)
5. Actuate,"Lower Pipette, Aspiration/Dispense.",Arduino (Servo/Linear)
6. Feedback,Send READY; or DONE; string.,Arduino → Pi

TODO:
Organize communication between microcontrollers
Inverse kinematics