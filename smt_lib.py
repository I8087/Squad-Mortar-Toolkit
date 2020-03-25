"""A collection of functions and algorithms for calculating mortar data."""

import math

__version__ = "1.0"

__all__ = [
    "aimpoint_offset",
    "calc_data",
    "correction_offset",
    "InvalidAzimuthError",
    "InvalidCorrectionError",
    "InvalidGridError",
    "get_az",
    "get_el",
    "get_rn",
    "get_tof",
    "grid_to_vec",
    "OutOfRangeError",
    "SMTLIB_Error",
    "valid_grid",
    "vec_to_grid"
    ]

################################
# LIBRARY VARIABLES
################################

# Squad mortar range card.
# (range, elevation, TOF)
# NOTE: TOF is based on the average time of flight for three HE rounds.
#       Any zeros means that no test have been conducted for that range.
range_card = ((50, 1579, 22.6),
              (100, 1558, 22.7),
              (150, 1538, 22.7),
              (200, 1517, 22.6),
              (250, 1496, 22.6),
              (300, 1475, 22.6),
              (350, 1453, 22.5),
              (400, 1431, 22.5),
              (450, 1409, 22.4),
              (500, 1387, 0),
              (550, 1364, 0),
              (600, 1341, 0),
              (650, 1317, 0),
              (700, 1292, 0),
              (750, 1267, 0),
              (800, 1240, 0),
              (850, 1212, 0),
              (900, 1183, 0),
              (950, 1152, 0),
              (1000, 1118, 0),
              (1050, 1081, 0),
              (1100, 1039, 0),
              (1150, 988, 0),
              (1200, 918, 17.9),
              (1250, 800, 16.2)
              )

# The minimum and maximum range for mortars in Squad.
min_range = 50
max_range = 1250

################################
# LIBRARY EXCEPTIONS
################################

class SMTLIB_Error(Exception):
    """Base class for exceptions in this library."""

    pass

class InvalidAzimuthError(SMTLIB_Error):
    """Exception for an invalid azimuth."""

    def __init__(self, az):
        self.az = az

    def __str__(self):
        return "Invalid azimuth given: {}".format(self.az)

class InvalidCorrectionError(SMTLIB_Error):
    """Exception for an invalid correction format."""

    def __init__(self, corr):
        self.corr = corr

    def __str__(self):
        return "Invalid correction format: \"{}\"".format(self.corr)

class InvalidGridError(SMTLIB_Error):
    """Exception for an invalid grid format."""

    def __init__(self, grid):
        self.grid = grid

    def __str__(self):
        return "Invalid grid format: \"{}\"".format(self.grid)

class OutOfRangeError(SMTLIB_Error):
    """Exception for being out of range."""

    def __init__(self, rn):
        self.rn = rn

    def __str__(self):
        return "Out of range for mortar: {}m".format(self.rn)

################################
# GRID FUNCTIONS
################################

def valid_grid(grid):
    """Checks to see if a valid grid was passed."""

    # Make sure something was passed.
    if not grid:
        return False

    # Make sure the grid is long enough.
    if len(grid) < 2:
        return False

    # Split the grid up.
    grid = grid.split("-")

    # Make sure we have an easting.
    if not grid[0][0].isalpha():
        return False

    # Make sure we have a southing.
    if not grid[0][1:].isdigit():
        return False

    del grid[0]

    # Check for numbers between the dashes.
    while grid:
        if len(grid[0]) == 1 and grid[0].isdigit():
            del grid[0]
        else:
            return False

    return True

def grid_to_vec(grid):
    """Converts a Squad grid into a vector point."""

    x = 0
    y = 0

    # Make sure the grid is valid!
    if not valid_grid(grid):
        raise InvalidGridError(grid)

    grid = grid.split("-")

    # Distance adjuster in meters.
    # Gets smaller as the grid gets more precise.
    d = 300

    for i in range(len(grid)):

        # Grid zone designators.
        if i == 0:
            x = (ord(grid[0][0].upper())-ord("A"))*d
            y = (int(grid[0][1:])-1)*-d
            continue

        d /= 3

        if grid[i] in ("4", "5", "6"):
            y -= d

        if grid[i] in ("1", "2", "3"):
            y -= 2*d

        if grid[i] in ("2", "5", "8"):
            x += d

        if grid[i] in ("3", "6", "9"):
            x += 2*d

    return (x, y)

def vec_to_grid(self, cords):
    """Takes a vector point and converts it into a Squad grid."""

    grid = ""

    # For a more accurate conversion, round to the thousands place.
    x = round(cords[0], 3)
    y = abs(round(cords[1], 3))

    d = 300

    grid += chr(65+int(x//d))
    x -= (x//d)*d

    grid += "{:.0f}".format(y//d+1)
    y -= (y//d)*d

    while x > 1 or y > 1:
        d /= 3
        g = 55

        while x >= d:
                x -= d
                g += 1

        while y >= d:
                y -= d
                g -= 3


        grid += "-{}".format(chr(g))

    return grid

################################
# OFFSET FUNCTIONS
################################

def aimpoint_offset(grid, di, rn):
    """Calculates a new location based on grid, direction, and distance."""

    # Turn the grid into a vector point.
    cords = grid_to_vec(grid)

    # Make sure the direction is correct.
    if not 0 <= di <= 360:
        raise InvalidAzimuthError(di)

    # Find the quadrant we're working in.
    if 0 <= di <= 90:
        x_neg = False
        y_neg = False
        x = (di/45)
        y = 2 - x
    elif 91 <= di <= 179:
        di -= 90
        x_neg = False
        y_neg = True
        y = (di/45)
        x = 2 - y
    elif 180 <= di <= 270:
        di -= 180
        x_neg = True
        y_neg = True
        x = (di/45)
        y = 2 - x
    elif 271 <= di <= 360:
        di -= 270
        x_neg = True
        y_neg = False
        y = (di/45)
        x = 2 - y

    # Find the correction lengths of x and y.
    x, y = math.sqrt(rn**2/2*x), math.sqrt(rn**2/2*y)

    if x_neg:
        x *= -1

    if y_neg:
        y *= -1

    # Return the new location as a grid.
    return self.vec_to_grid((cords[0]+x, cords[1]+y))

def correction_offset(self, grid, di, dev_cor="0", rn_cor="0"):
    """Adjusts a grid based on the observer's azimuth and corrections."""

    # Try to do a deviation correction.
    if dev_cor != "0":
        temp_di = di
        if dev_cor[0] == "R":
            temp_di += 90
        elif dev_cor[0] == "L":
            temp_di += 270
        else:
            raise InvalidCorrectionError(dev_cor)

        # Make sure we stay within an actual azimuth.
        if temp_di >= 360:
                temp_di -= 360

        grid = self.aimpoint_offset(grid, temp_di, int(dev_cor[1:]))

    # Try to do a range correction.
    if rn_cor != "0":
        temp_di = di
        if rn_cor[0] == "+":
            pass
        elif rn_cor[0] == "-":
            temp_di += 180
        else:
            raise InvalidCorrectionError(rn_cor)

        # Make sure we stay within an actual azimuth.
        if temp_di >= 360:
                temp_di -= 360

        grid = self.aimpoint_offset(grid, temp_di, int(rn_cor[1:]))

    return grid

################################
# MORTAR FUNCTIONS
################################

def get_rn(grid1, grid2):
    """Returns the range between two grids."""

    # Lose of precision due to rounding, might remove later.
    return round(math.dist(grid_to_vec(grid1),
                           grid_to_vec(grid2)))

def get_az(grid1, grid2):
    """Returns the azimuth between two grids."""

    # Turn both grids into vector points.
    g = grid_to_vec(grid1)
    t = grid_to_vec(grid2)

    # Get the angle of the tangent in radians.
    az = math.atan2(t[0]-g[0], t[1]-g[1])

    # And then turn it into caridnal degrees.
    az = math.degrees(az)

    # Lose of precision due to rounding, might remove later.
    az = round(az)

    # Turn a negative angle into a positive one.
    if az < 0:
        az += 360

    # 360 degrees is the same direction as 0 degrees.
    if az == 360:
        az = 0

    return az

def get_el(gun, tgt):
    """Gets the elevation of the gun based on the gun and target grids."""

    # Get the range between the gun and target.
    # Range is needed for determining elevation.
    rn = get_rn(gun, tgt)
    rn50 = rn//50-1

    # Make sure the target is within range.
    if min_range <= rn <= max_range:

        # Try and find the exact elevation.
        if rn % 50 == 0:
            return range_card[rn50][1]

        # Interpolate if the range isn't exact.
        e = (range_card[rn50+1][1] - range_card[rn50][1])/50
        r = abs(range_card[rn50][0] - rn)
        return round(range_card[rn50][1]+e*r)

    # At this point we were unable to calculate for elevation.
    raise OutOfRangeError(rn)

def get_tof(gun, tgt):
    """Gets the time of flight of the round based on the gun and target grids."""

    # Get the range between the gun and target.
    # Range is needed for determining time of flight.
    rn = get_rn(gun, tgt)
    rn50 = rn//50-1

    # Make sure the target is within range.
    if min_range <= rn <= max_range:

        # Try and find the exact time of flight.
        if rn % 50 == 0:
            return range_card[rn50][2]

        # Interpolate if the range isn't exact.
        t = (range_card[rn50+1][2] - range_card[rn50][2])/50
        r = abs(range_card[rn50][0] - rn)
        return round(range_card[rn50][2]+t*r)

    # At this point we were unable to calculate for time of flight.
    raise OutOfRangeError(rn)

def calc_data(gun, tgt):
    """Takes two grids, a gun and target, and returns a tuple of firing data.
       (range, azimuth, elevation, time of flight)
    """

    # Calculate the firing data.
    rn = get_rn(gun, tgt)
    az = get_az(gun, tgt)
    el = get_el(gun, tgt)
    tof = get_tof(gun, tgt)

    return (rn, az, el, tof)
