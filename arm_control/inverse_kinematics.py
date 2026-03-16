from math import acos, atan2, cos, sin, pi
from numpy import rad2deg
import serial
#import waypoints

#arduino = serial.Serial(port = 'COM5', baudrate = 115200)

ARM_SEGMENT_ONE = 160
ARM_SEGMENT_TWO = 200


def inverse_kinematics(target_pos):
    #invert = False
    
    L1 = ARM_SEGMENT_ONE
    L2 = ARM_SEGMENT_TWO
    x = target_pos[0]   
    y = target_pos[1]

    theta2 = acos((x**2 + y**2 - L1**2 - L2**2)/(2*L1*L2)) #extrapolated l1 segment, angle between this and l2
    hyp = atan2(y,x)
    above_below = atan2((L2*sin(theta2)),(L1 + (L2*cos(theta2)))) #from x to joint1
    if theta2 > 0:
        above_below = -above_below

    theta1 = hyp + above_below
    theta1 = rad2deg(theta1)

    #NEED TO ADJUST theta2 logic based on where 'home' is set
    #lets assume 180 rotation and 'home' is perpendicular to joint1 on the right
    #the angle logic all depends on if joint2 only has 180 degrees, if more need to rethink

    if theta2 >  0:
        theta2 = theta2 + pi/2
    else:
        theta2 = pi/2 + theta2

    theta2 = rad2deg(theta2)

    return (round(theta1.item(0),1), round(theta2.item(),1))

# def export_waypoints(path, filename):
#     with open(filename, "w") as f:   
#         for point in path:
#             point.write(f)

# def load_waypoints(filename):
#     with open(filename, "r") as f:
#         return waypoints.parse_file(f.readlines())

def main():
    print(inverse_kinematics((100,40)))


if __name__ == "__main__":
    main()
