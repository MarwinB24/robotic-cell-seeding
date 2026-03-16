#Description

Automated robotic cell seeding device
-------------------------------------
Features:
- Computer vision to identify and locate well positions
- Microfluidic control and mixing for pipetting mechanism
- Scara arm with inverse kinematic control
- Embedded system design

## Raspberry Pi 3B+ Headless Detection

Use the main script to identify both:
- a chosen plate type marker (`96well`, `24well`, `12well`, `6well`)
- the SCARA arm center marker (`ID 4`)

Default behavior is Raspberry Pi headless single-shot processing.

Node-RED / snapshot image example:

```bash
python main.py --plate-type 96well --image /path/to/field.jpg
```

Pi camera capture example (Picamera2 preferred automatically):

```bash
python main.py --plate-type 24well --lock-exposure --exposure-us 12000 --analogue-gain 1.5
```

Laptop/debug preview example:

```bash
python main.py --plate-type 24well --preview --pretty-json
```

OpenCV camera fallback (disable Picamera2):

```bash
python main.py --plate-type 24well --no-use-picamera2 --camera-index 0
```

The script prints JSON including `plate_pose` (same return structure as `get_plate_pose`), `arm_center`, calibration metadata, and `success`.
