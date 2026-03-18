#using big printer, printer 8, printer 11, printer 10
#marker to A1 (96-well) 1.4 vertically, 1.7cm horizontally

#raspberry pi, user: aspamtech, pw: aspamBTV2026

import numpy as np

class Plates:
    PLATE_CONFIGS = {
        "96well": {"rows": 8, "cols": 12, "pitch_mmX": 10.5, "pitch_mmY": 10.5, "xApart": 16, "yApart": 15.5},
        "24well": {"rows": 4, "cols": 6, "pitch_mmX": 19.0, "pitch_mmY": 19.0, "xApart": 39, "yApart": 39},
        "12well": {"rows": 3, "cols": 4, "pitch_mmX": 26.0, "pitch_mmY": 26.0, "xApart": 52, "yApart": 52},
        "6well": {"rows": 2, "cols": 3, "pitch_mmX": 39.0, "pitch_mmY": 39.0, "xApart": 78, "yApart": 78},
    }

    def __init__(self, plate_type=None):
        self.plate_type = plate_type
        if plate_type:
            self.config = self.PLATE_CONFIGS.get(plate_type)

    def marker_to_well(self, angle, markerBotLeft):
        # Offset from marker corner to well-plate A1 in the marker's local frame.
        # xApart is along the marker's local X axis, yApart is along its local -Y axis.
        offset = np.array([self.config["xApart"], -self.config["yApart"]])

        # Rotate into the camera/pixel frame using the marker's detected angle.
        R = np.array([[np.cos(angle), -np.sin(angle)],
                      [np.sin(angle),  np.cos(angle)]])
        rotated_offset = R @ offset

        topLeft = (markerBotLeft[0] + rotated_offset[0],
                   markerBotLeft[1] + rotated_offset[1])
        return topLeft
    
    #arm coordinates found using aruco_plate_locator func 'arm_coord'
    def top_left_to_arm(self, topLeft, arm_center_pos): #need to setscale, pixel to mm
        # Translates grid relative to the arm pos (using offset from top_left to arm center)
        # Basically redefining the origin (coordinate system), arm is centre instead of top_left
        # This is what is sent to the inverse kinematics
        # It doesn't matter if it is pixels or mm (relative calcs) but prefer mm since arm joints is measure in mm
        translation_vector = np.array(topLeft) - np.array(arm_center_pos)

        return translation_vector
    
    def well_coordinate(self, translation_vector): #topLeft array (x,y)
        x_coords = [translation_vector[0] + (i * self.config["pitch_mmX"]) for i in range(self.config["cols"])]
        y_coords = [translation_vector[1] - (i * self.config["pitch_mmY"]) for i in range(self.config["rows"])]

        # 2. Create the 2D grid (Matrix)
        X, Y = np.meshgrid(x_coords, y_coords)

        # 3. Combine them into (x, y) pairs if needed
        grid_points = np.vstack([X.ravel(), Y.ravel()]).T
        return grid_points
    
    def rotate_grid(self, grid_points, angle_rad, topLeft): #set origin has topLEft
        rotation_matrix = np.array([[np.cos(angle_rad), -np.sin(angle_rad)],
                                    [np.sin(angle_rad),  np.cos(angle_rad)]])
        centered_points = grid_points - topLeft
        rotated_points = centered_points @ rotation_matrix.T
        return rotated_points + topLeft

def main():
    print('ooga!')
    plate1 = Plates("96well")
    topLeft = plate1.marker_to_well(0, (0,0))
    print(topLeft)
    grid = plate1.well_coordinate(topLeft)
    print(grid)
    rotated_grid = plate1.rotate_grid(grid, np.radians(np.pi / 2))
    print(rotated_grid)
    #print(type(grid[0]))
    #print(type(grid[0][0]))
    print()
    pass

if __name__ == "__main__":
    main()