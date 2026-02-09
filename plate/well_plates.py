class Plates:        
    def __init__(self, plate_pos = None):
        self.plate_pos = plate_pos        

    def identify_plate(self, marker_id):
        id_plate = {
            10 : '96well',
            15 : '24well',
            20 : '12well',
            25 : '6well'      
        }

        return id_plate.get(marker_id, 'Unknown Plate Type') #.get() returns 'unknown' if no ID found
    
class well96(Plates):
    def __init__(self, plate_pos):
        super().__init__(plate_pos)

class well24(Plates):
    def __init__(self, plate_pos):
        super().__init__(plate_pos)

class well12(Plates):
    def __init__(self, plate_pos):
        super().__init__(plate_pos)

class well6(Plates):
    def __init__(self, plate_pos):
        super().__init__(plate_pos)

def main():
    print('ooga!')
    pass

if __name__ == "__main__":
    main()