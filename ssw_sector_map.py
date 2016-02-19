#!/usr/bin/python

'''
Utilities to deal with a SSW sector map
Including a parser for the HTML file
'''

# Copyright 2008 Squiffle

# TODO: Assume that missing links are bi-directional (they always have been so far).
# TODO: Change to allow debugging to be enabled at run-time

import HTMLParser, htmlentitydefs, operator, datetime, unittest
import ssw_missing_links, ssw_societies

'''Set this to True to log debugging information'''
debug = False
'''Where the debug information ends up'''
debug_filename = '/tmp/ssw_sector_map.log'

'''
datetimes for the start of each cycle
Indexed by the actual cycle number (i.e. starting from 1, not 0).
From munk's email where possible, else guessed from war end dates.
Note that there's usually a break between one war's end and the start of the next cycle.
'''
cycle_start = [None,
               datetime.datetime(3007, 12, 1, 0, 10), # guess
               datetime.datetime(3008, 1, 14, 0, 10), # guess
               datetime.datetime(3008, 4, 14, 0, 10), # guess
               datetime.datetime(3008, 6, 9, 0, 10),
               datetime.datetime(3008, 9, 3, 0, 10),
               datetime.datetime(3008, 10, 1, 0, 10), # guess
               datetime.datetime(3009, 1, 19, 0, 9),
               datetime.datetime(3009, 5, 16, 0, 11),
               datetime.datetime(3009, 6, 19, 11, 45),
               datetime.datetime(3009, 8, 8, 0, 11),
               datetime.datetime(3010, 2, 4, 0, 45),
               datetime.datetime(3010, 3, 19, 11, 10),
               datetime.datetime(3010, 4, 23, 11, 8),
               datetime.datetime(3010, 5, 30, 23, 13),
               datetime.datetime(3010, 10, 27, 23, 22),
               datetime.datetime(3010, 12, 19, 23, 8),
               datetime.datetime(3011, 7, 9, 23, 41)]

'''
datetimes for the end of each war
Indexed by the actual war number (i.e. starting from 1, not 0).
'''
war_end = [None,
           datetime.datetime(3008, 1, 7, 23, 59),
           datetime.datetime(3008, 4, 7, 23, 59),
           datetime.datetime(3008, 6, 3, 23, 59),
           datetime.datetime(3008, 8, 20, 23, 59),
           datetime.datetime(3008, 9, 23, 23, 59),
           datetime.datetime(3008, 12, 12, 23, 59),
           datetime.datetime(3009, 5, 8, 23, 59),
           datetime.datetime(3009, 6, 15, 23, 59),
           datetime.datetime(3009, 8, 5, 23, 59),
           datetime.datetime(3010, 1, 24, 23, 59),
           datetime.datetime(3010, 3, 14, 23, 59),
           datetime.datetime(3010, 4, 19, 23, 59),
           datetime.datetime(3010, 5, 22, 23, 59),
           datetime.datetime(3010, 10, 22, 23, 59),
           datetime.datetime(3010, 12, 11, 23, 59),
           datetime.datetime(3011, 6, 17, 23, 59)]

'''
Flambe was a later addition
'''
flambe_added_datetime = datetime.datetime(3010, 5, 30, 13, 22)

'''
There was a major change to the map at this point.
'''
planets_moved_datetime = datetime.datetime(3011, 6, 21, 16, 26)

'''
Leroy Tong's was a later addition
'''
new_store_datetime = datetime.datetime(3009, 1, 19, 0, 0)

'''
Dates when Mars appears, as (month, day) tuples
'''
mars_dates = [(3, 17), # Little Green Man Day
              (5, 5),  # Inca De Maya
              (7, 4),  # Imperial Drinking Holiday
              (9, 19)] # Space Pirate Day

'''
This is the longest route that the code will bother looking for.
The higher this number, the more time it will take, but the greater the
likelihood of actually finding a route.
'''
max_route_length = 15

'''All the known ores'''
all_ores = ['Afaikite',
            'Bofhozonite',
            'Esabatmite',
            'Fwiwzium',
            'Imhozium',
            'Lmaozium',
            'Lolnium',
            'Nimbyite',
            'Omgonite',
            'Pebkacium',
            'Rofolzium',
            'Tanstaaflite']

# What do we expect to find ?
'''
Planets that appear occasionally. List of (name, sector) tuples.
Sector is None if the planet has no fixed abode.
'''
temporary_planets = [('Mars', 4),
                     ('Planet X', None),
                     ('The <3 Boat', None)]
mars = temporary_planets[0]
love_boat = temporary_planets[1]
planet_x = temporary_planets[2]

def cycle(map_datetime):
    """
    Identifies the cycle that was happening at the specified SSW time.
    Returns 0 for dates before the first cycle.
    """
    for cycle in range(len(cycle_start)-1):
        if (map_datetime < cycle_start[cycle+1]):
            return cycle
    return len(cycle_start)-1

def war_ongoing(map_datetime):
    """
    Returns True if the war hadn't yet ended.
    """
    try:
        return map_datetime < war_end[cycle(map_datetime)]
    except IndexError:
        # Must be the current war, which is still ongoing
        return True

'''For cycle 13, diagonal moves were disallowed'''
def can_move_diagonally(map_datetime):
    """
    Returns True if diagonal moves were possible, False otherwise.
    """
    return not (13 == cycle(map_datetime))

'''Mars appears on a regular schedule'''
def mars_present(map_datetime):
    """
    Returns a boolean indicating whether Mars appears on the specified date.
    """
    return ((map_datetime.month, map_datetime.day) in mars_dates)

'''Where was The <3 Boat ?'''
def love_boat_sector(year):
    """
    Returns the sector where The <3 Boat appeared in the specified year, if known
    """
    # TODO Add <3 Boat locations for 3008, 3010, and 3011
    if (year == 3009):
        return 157
    return None

'''Where was Planet X ?'''
def planet_x_sector(year):
    """
    Returns the sector where Planet X appeared in the specified year, if known
    """
    # TODO Add Planet X locations for 3007, 3008 and 3009
    if (year == 3010):
        return 516
    return None

'''The <3 Boat appears on a regular schedule'''
def love_boat_present(map_datetime):
    """
    Returns a boolean indicating whether The <3 Boat appears on the specified date.
    """
    # Just Valentine's Day
    return ((map_datetime.month, map_datetime.day) == (2, 14))

'''Planet X appears on a regular schedule'''
def planet_x_present(map_datetime):
    """
    Returns a boolean indicating whether Planet X appears on the specified date.
    """
    # Christmastime
    return ((map_datetime.month == 12) and (map_datetime.day >= 25))

'''Planets we expect to always find. List of (name, sector) tuples.'''
def expected_planets(map_datetime):
    """
    Where planets should appear.
    Returns a list of tuples with (name, sector).
    """
    '''Planets we expect to always find. List of (name, sector) tuples.'''
    retval = [('Earth', 1),
              ('Solaris', 15),
              ('Yeranus', 30),
              ('Boria', 33),
              ('Eroticon 69', 69),
              ('Phallorus', 123),
              ('Deep Six Fauna', 142),
              ('Trinoc', 202),
              ('Nortonia', 365),
              ('Barnimus', 457),
              ('Ahlnuldia', 471),
              ('Laxloo', 493),
              ('Xiao MeiMei', 612),
              ('Tranquility', 899)]
    # Three planets moved when the map was re-worked
    moved_planets_before = [('Lucky Spaceman Distilleries', 49),
                            ('New Ceylon', 92),
                            ('Pharma', 102)]
    moved_planets_after = [('Lucky Spaceman Distilleries', 631),
                           ('New Ceylon', 227),
                           ('Pharma', 721)]
    # Flambe was a later addition
    flambe = ('Flambe', 1070)
    # Pinon Sol and Hedrok appeared when the map was re-worked
    new_planets = [('Pinon Sol', 707),
                   ('Hedrok', 888)]

    if (map_datetime > planets_moved_datetime):
        retval += moved_planets_after
        retval += new_planets
    else:
        retval += moved_planets_before
    if (map_datetime > flambe_added_datetime):
        retval.append(flambe)
    if (mars_present(map_datetime)):
        retval.append(mars)
    if (love_boat_present(map_datetime)):
        sector = love_boat_sector(map_datetime.year)
        if (sector):
            retval.append((love_boat[0],sector))
    if (planet_x_present(map_datetime)):
        sector = planet_x_sector(map_datetime.year)
        if (sector):
            retval.append((planet_x[0],sector))
    return retval

'''Sectors that we expect to have missing links'''
def expected_missing_links(map_datetime):
    """
    Which sectors should have missing links.
    Constant up to cycle 13, then space got mazified.
    dict, indexed by sector, of list of neighbouring sectors that you can't move to.
    """
    maze_free_sectors = {501: [467, 468, 469, 533, 534, 535],
                         502: [468, 469, 470, 501, 503, 534, 535, 536]}
    cycle_13_map_change_datetime = datetime.datetime(3010, 5, 22, 23, 59)
    cycle_16_map_change_datetime = datetime.datetime(3011, 7, 3, 23, 59)

    if (cycle(map_datetime) < 13):
        return maze_free_sectors
    elif (cycle(map_datetime) == 13):
        if (map_datetime < cycle_13_map_change_datetime):
            return ssw_missing_links.cycle_13_war_links
        else:
            return ssw_missing_links.cycle_13_late_links
    elif (cycle(map_datetime) == 14):
        return ssw_missing_links.cycle_14_links
    elif (cycle(map_datetime) == 15):
        return ssw_missing_links.cycle_15_links
    elif (cycle(map_datetime) == 16):
        if (map_datetime < cycle_13_map_change_datetime):
            return ssw_missing_links.cycle_16_war_links
        else:
            return ssw_missing_links.cycle_16_late_links
    elif (cycle(map_datetime) == 17):
        return ssw_missing_links.cycle_17_links
    else:
        # If we get here, we need to add missing links for this cycle
        return {}

'''Number of asteroids we expect to find'''
def expected_asteroids(map_datetime):
    """
    How many asteroids should be present in a sector map.
    """
    # TODO: I've got a cycle 4 map, which has 9 of each asteroid, plus an extra Tanst
    # Cycle 7 had just 3 of each asteroid
    if (cycle(map_datetime) == 7):
        expected_asteroids_per_ore = 3
    # Cycles 11 and later have fewer asteroids - 6 of each
    elif (cycle(map_datetime) > 10):
        expected_asteroids_per_ore = 6
    else:
        # Before that, 9 was the standard number
        expected_asteroids_per_ore = 9
    return expected_asteroids_per_ore * len(all_ores)

'''List of sectors where we expect to find black holes'''
expected_black_holes = [2, 54, 99, 112, 205, 292, 355, 370, 409, 446, 500, 502, 521, 641, 696, 737, 755, 777, 869, 928, 951, 1040, 1059, 1089]

'''NPC stores we expect to always find.'''
def expected_npc_stores(map_datetime):
    """
    What NPC stores exist, and where.
    Returns a list of (name, sector) tuples.
    """
    retval = [('Salty Bob`s Waterin` Hole', 1),
              ('Syawillim', 502),
              ('Captain Jork`s Last Chance Saloon', 1075)]
    # LSD Store moved when the map was re-worked
    lsd_store_before = ('Lucky Spaceman Liquor Store', 49)
    lsd_store_after = ('Lucky Spaceman Liquor Store', 631)
    # New store added 19Jan2009
    new_store = ('Leroy Tong`s Trancendental Soul Food', 923)

    if (map_datetime > planets_moved_datetime):
        retval.append(lsd_store_after)
    else:
        retval.append(lsd_store_before)
    if ((map_datetime > new_store_datetime)):
        retval.append(new_store)
    return retval

'''Number of space jellyfish we expect to find'''
expected_jellyfish = 100

'''Number of trading ports we expect to find'''
expected_trading_ports = 250

'''Number of ipt beacons we expect to find'''
expected_ipts = 100

'''Number of luvsats we expect to find'''
expected_luvsats = 5

if debug:
   flog = open(debug_filename, "w", buffering=1)
else:
   flog = open("/dev/null", "w")

# List of month numbers and names
months = dict([(datetime.date(2008,x,01).strftime('%b'),x) for x in range(1,13)])

'''List of all valid sector numbers'''
all_sectors = range(1,1090)

'''Number of sectors in each row(and column)'''
sectors_per_row = 33

'''List of valid coordinate (row or column) numbers'''
coord_range = range(0,sectors_per_row)

def sector_to_coords(sector_number):
    '''
    Convert a sector number to a (col,row) coordinate tuple
    Sector numbers start from 1, but we number rows and cols from 0
    '''
    # Sector numbers start from 1, but we'll number rows and cols from 0
    row = (sector_number-1)/sectors_per_row
    col = (sector_number-1)%sectors_per_row
    return (col,row)

def coords_to_sector(column, row):
    '''
    Convert a row and column to a sector number
    Sector numbers start from 1, but we number rows and cols from 0
    '''
    return (row*sectors_per_row)+column+1

def adj_sectors_towards(from_sector, to_sector, can_move_diagonally):
    '''
    Returns the list of sectors adjacent to from_sector
    in the direction of to_sector
    Note that you can't necessarily get to all of them
    TODO: Support can_move_diagonally = False
    '''
    retval = []
    if to_sector == from_sector:
       return retval
    assert can_move_diagonally, "function not updated for mazey space"
    col1,row1 = sector_to_coords(from_sector)
    col2,row2 = sector_to_coords(to_sector)
    # On same row or column - return 3 sectors
    # On a diagonal - return 1 sector
    # Otherwise, return 2 sectors
    if row1 == row2:
        if col1 > col2:
            c = col1-1
        else:
            c = col1+1
        for r in range(row1-1,row1+2):
            if (c in coord_range) and (r in coord_range):
                retval.append(coords_to_sector(c,r))
        return retval
    if col1 == col2:
        if row1 > row2:
            r = row1-1
        else:
            r = row1+1
        for c in range(col1-1,col1+2):
            if (c in coord_range) and (r in coord_range):
                retval.append(coords_to_sector(c,r))
        return retval
    if (row1 < row2) and (col1 < col2):
        r = row1+1
        c = col1+1
    if (row1 > row2) and (col1 < col2):
        r = row1-1
        c = col1+1
    if (row1 < row2) and (col1 > col2):
        r = row1+1
        c = col1-1
    if (row1 > row2) and (col1 > col2):
        r = row1-1
        c = col1-1
    if (c in coord_range) and (r in coord_range):
        retval.append(coords_to_sector(c,r))
    if abs(row1-row2) == abs(col1-col2):
        # We're on the diagonal, so that one is enough
        return retval
    # Now we just need to add the other sector of interest
    if ((abs(row1 - row2) > abs(col1 - col2)) and
        ((row1 - row2) > (col1 - col2))):
        r = row1-1
        c = col1
    if ((abs(row1 - row2) > abs(col1 - col2)) and
        ((row1 - row2) < (col1 - col2))):
        r = row1+1
        c = col1
    if ((abs(row1 - row2) < abs(col1 - col2)) and
        ((row1 - row2) > (col1 - col2))):
        r = row1
        c = col1+1
    if ((abs(row1 - row2) < abs(col1 - col2)) and
        ((row1 - row2) < (col1 - col2))):
        r = row1
        c = col1-1
    if (c in coord_range) and (r in coord_range):
        retval.append(coords_to_sector(c,r))
    retval.sort()
    return retval

def adjacent_sectors(to_sector, can_move_diagonally):
    '''
    Returns the list of adjacent sectors
    Note that you can't necessarily get to all of them
    '''
    retval = []
    col,row = sector_to_coords(to_sector)
    if can_move_diagonally:
        for r in range(row-1,row+2):
            for c in range(col-1,col+2):
                if (c in coord_range) and (r in coord_range):
                    retval.append(coords_to_sector(c,r))
        retval.remove(to_sector)
    else:
        if (col-1 in coord_range):
            retval.append(coords_to_sector(col-1,row))
        if (row-1 in coord_range):
            retval.append(coords_to_sector(col,row-1))
        if (col+1 in coord_range):
            retval.append(coords_to_sector(col+1,row))
        if (row+1 in coord_range):
            retval.append(coords_to_sector(col,row+1))
    return retval

def can_move(from_sector, to_sector, missing_links={}, avoiding_sectors=[]):
    '''
    Checks whether you can move from from_sector to adjacent to_sector
    It will lie if the two sectors aren't adjacent
    '''
    try:
        if to_sector in missing_links[from_sector]:
            return False
    except:
        pass
    if to_sector in avoiding_sectors:
        return False
    return True

def direct_distance(from_sector, to_sector):
    '''
    Figure out how many turns it would take to fly from one sector to another
    If you could get from any sector to its neighbour
    '''
    from_row, from_col = sector_to_coords(from_sector)
    to_row, to_col = sector_to_coords(to_sector)
    return max(abs(from_row - to_row), abs(from_col - to_col))

def routes_of_length(length, from_sector, to_sector, can_move_diagonally, missing_links={}, avoiding_sectors=[]):
    '''
    Find all routes between two sectors of the specified length
    This will take a long time if length is more than about 7
    '''
    # TODO Could do with a more efficient algorithm for this
    #      It's ok for routes up to about 7 length, but rapidly slows down
    #      Probably mostly because of the number of routes :
    #      Distance Max routes
    #      1        1
    #      1        3
    #      3        7
    #      4        19
    #      5        51
    #      6        141
    #      7        393
    #      8        1107
    #      9        3139
    #      10       8953
    #      11       25653
    #      12       73789
    #      13       212941
    #      14       616227
    if (length == 0) and (from_sector == to_sector):
       # We just need to stay in from_sector
       return [[]]
    retval = []
    length -= 1
    for s in adjacent_sectors(from_sector, can_move_diagonally):
        # Figure out whether s is 1 closer to to_sector
        if can_move(from_sector,s,missing_links,avoiding_sectors) and (direct_distance(s,to_sector) <= length) :
            # It is
            retval.append([s])
    # Here's the recursive bit - termination condition is that we've got there
    if length > 0:
        # No idea whether new_retval is strictly necesary, but better to be safe
        new_retval = []
        for route in retval:
            # Find routes from the end of route to to_sector
            temp = routes_of_length(length,route[-1],to_sector,can_move_diagonally,missing_links,avoiding_sectors+route)
            for s in temp:
                new_retval.append(route+s)
        retval = new_retval
    return retval
 
def a_route_of_length(length, from_sector, to_sector, can_move_diagonally, missing_links={}, avoiding_sectors=[]):
    '''
    Find any one route of the specified length between the two sectors
    '''
    print >>flog
    print >>flog, "a_route_of_length(%d, %d, %d, %s, ..., %s)" % (length, from_sector, to_sector, str(can_move_diagonally), str(avoiding_sectors))
    if (length == 0) and (from_sector == to_sector):
        # We just need to stay in from_sector
        print >>flog," Returning []"
        return []
    elif (length == 1) and to_sector in adjacent_sectors(from_sector, can_move_diagonally):
        if can_move(from_sector,to_sector,missing_links,avoiding_sectors):
            print >>flog," Returning [%d]" % to_sector
            return [to_sector]
        else:
            # There is no route
            print >>flog," Returning None (1)"
            return None
    length -= 1
    for s in adjacent_sectors(from_sector, can_move_diagonally):
        print >>flog," Trying via %d" % s
        # Figure out whether s is 1 closer to to_sector
        if can_move(from_sector,s,missing_links,avoiding_sectors) and (direct_distance(s,to_sector) <= length) :
            print >>flog," Recursing"
            temp = a_route_of_length(length,s,to_sector, can_move_diagonally,missing_links,avoiding_sectors+[from_sector,s])
            if temp != None:
                print >>flog," Returning [%d] + %s" % (s, str(temp))
                return [s] + temp
    # If we get here, there are no routes of the specified length
    print >>flog," Returning None (2)"
    return None
 
def routes(from_sector, to_sector, can_move_diagonally, missing_links={}, avoiding_sectors=[], max_length=max_route_length):
    '''
    Find routes from one sector to another
    Returns a list of ordered lists of intermediate sectors
    Will only include shortest-distance routes
    (all routes returned will be the same length)
    '''
    if (from_sector in avoiding_sectors) or (to_sector in avoiding_sectors):
        # No route is possible
        return []
    retval = []
    route_length = direct_distance(from_sector, to_sector)
    # Find all shortest-distance routes first
    # If there aren't any, find routes that are 1 longer, etc.
    while (len(retval) == 0) and (route_length < max_length):
        retval = routes_of_length(route_length, from_sector, to_sector, can_move_diagonally, missing_links, avoiding_sectors)
        route_length += 1
    return retval

def a_route(from_sector, to_sector, can_move_diagonally, missing_links={}, avoiding_sectors=[], max_length=max_route_length):
    '''
    Find a route from one sector to another
    Returns an ordered list of intermediate sectors
    Will return one shortest-distance route
    '''
#    print "Looking for a route from %d to %d" % (from_sector, to_sector)
    if (from_sector in avoiding_sectors) or (to_sector in avoiding_sectors):
        # No route is possible
        return None
    route_length = direct_distance(from_sector, to_sector)
    # Here's another optimisation - if all the sectors adjacent to either
    # the source or destination are impassable, drop out early
    # But only if we actually need to move
    if route_length > 0:
        if len(set(adjacent_sectors(from_sector, can_move_diagonally)) - set(avoiding_sectors)) == 0:
            return None
        if len(set(adjacent_sectors(to_sector, can_move_diagonally)) - set(avoiding_sectors)) == 0:
            return None
    retval = None
    # Find a shortest-distance route first
    # If there aren't any, find routes that are 1 longer, etc.
    while (retval == None) and (route_length < max_length):
        #print "In a_route(%d,%d,...,%s) - looking for route of length %d" % (from_sector, to_sector, str(avoiding_sectors), route_length)
        retval = a_route_of_length(route_length, from_sector, to_sector, can_move_diagonally, missing_links, avoiding_sectors)
        route_length += 1
    return retval

def drones_en_route(route, drones):
    '''
    What drones will be met on a route ?
    Returns a list of the drone societies such that len(retval) is the number
    of sectors with drones in them
    '''
    # Figure out what drones will be met en route
    drone_sectors = set([sector for society,sector in drones])
    drone_dict = dict([(sector,society) for society,sector in drones])
    # Which sectors are on the route and have drones ?
    drone_sectors = drone_sectors.intersection(set(route))
    retval = [drone_dict[sector] for sector in drone_sectors]
    return retval

def accessible_sectors(from_sector, can_move_diagonally, missing_links={}, avoiding_sectors=[], drones=[], max=max_route_length):
    '''
    Figure out which sectors can be reached from the specified start sector.
    Returns a list of sectors.
    '''
    # TODO Should retval be a set rather than a list ? No real ordering...
    # Is start_sector accessible ?
    if start_sector in avoiding_sectors:
        return []
    retval = [start_sector]
    # TODO Now keep adding adjacent accessible sectors that aren't already in the list
    # until there are no more sectors to check
    # TODO Need some sort of loop here...
    new_retval = retval
    for sector in retval:
        for adj in adjacent_sectors(sector, can_move_diagonally):
            if adj not in avoiding_sectors and adj not in retval:
                new_retval.append(adj)
    retval = new_retval
    return retval

def fly_distance(from_sector, to_sector, can_move_diagonally, missing_links={}, avoiding_sectors=[], drones=[], max=max_route_length):
    '''
    Figure out how many turns it takes to fly from one sector to another
    Returns a tuple with (distance,list of drones en route) if it finds a route
    Returns (None,[]) if there is no route
    '''
    # With a simple map, there's no need to actually find a route
    if (len(missing_links) == 0) and (len(avoiding_sectors) == 0) and (len(drones) == 0):
        temp = direct_distance(from_sector, to_sector)
        if (temp <= max):
            return (temp,[])
        else:
            return (None,[])
    temp = a_route(from_sector, to_sector, can_move_diagonally, missing_links, avoiding_sectors, max)
    if temp != None:
        return (len(temp),drones_en_route(temp,drones))
    # If we get here, it's not possible to fly between those sectors
    return (None,[])

class TradingPort:
    '''
    Class to store everything about one trading port
    '''
    def __init__(self, name, sector, good, order, buy_prices, sell_prices):
        self.name = name
        self.sector = sector
        self.good = good
        self.order = order
        self.buy_prices = buy_prices
        self.sell_prices = sell_prices

    def full_name(self):
        '''Returns the full name of the trading port'''
        return "Trader %s Trading Port #%d" % (self.name, self.sector)

    def alignment_str(self):
        '''Returns the alignment string (GE and OC numbers)'''
        return "GE: %d OC: %d" % (self.good, self.order)

    def society_initial(self):
        '''Returns the initial of the society with which the port is aligned'''
        return ssw_societies.initial(self.good, self.order)

    def __str__(self):
        return "[%s, %s (%s), buys %s, sells %s]" % (self.full_name(), self.alignment_str(), self.society_initial(), self.buy_prices, self.sell_prices)

class SectorMapParser(HTMLParser.HTMLParser):
    '''
    Class to parse the sector map
    '''
    entitydefs = htmlentitydefs.entitydefs

    def __init__(self):
        HTMLParser.HTMLParser.__init__(self)
        # TODO Doing this here will likely cause problems if the user calls
        # feed() more than once for some reason
        self.ores_bought = {}
        self.ores_sold = {}
        self.missing_links = {}
        self.drones = []
        self.your_drones = []
        self.planets = []
        self.asteroids = []
        self.black_holes = []
        self.npc_stores = []
        self.jellyfish = []
        self.trading_ports = []
        self.ipts = []
        self.luvsats = []
        self.known_sectors = 0
        self.unknown_sectors = []
        self.forgotten_sectors = []
        self.expected_totals = {}
        self.in_totals = False
        self.current_sector = 0
        self.last_density = {}

    def expected_planets(self):
        '''
        Which planets should be present in this map ?
        Returns a list of (name, sector) tuples.
        '''
        return expected_planets(self.datetime)

    def expected_asteroids(self):
        '''
        How many asteroids should be present in this map ?
        '''
        return expected_asteroids(self.datetime)

    def expected_npc_stores(self):
        '''
        Which NPC stores should be present in this map ?
        '''
        return expected_npc_stores(self.datetime)

    def expected_missing_links(self):
        '''
        Which missing links should be present in this map ?
        '''
        return expected_missing_links(self.datetime)

    def can_move_diagonally(self):
        '''
        Are diagonal moves possible on this map ?
        '''
        return can_move_diagonally(self.datetime)

    def cycle(self):
        '''
        What cycle does this map belong to ?
        '''
        return cycle(self.datetime)

    def war_ongoing(self):
        '''
        Was the war ongoing at the time of this map ?
        '''
        return war_ongoing(self.datetime)

    def war_ended(self):
        '''
        Had the war ended at the time of this map ?
        '''
        return not self.war_ongoing()

    def parse_sector_number(self, text):
        '''
        Internal - Extracts the sector number
        '''
        temp = text.find('CAPTION')
        assert temp > -1,text
        words = text[temp:].split()
        self.current_sector = int(words[1][1:])
#        print "Sector %d" % self.current_sector

    def parse_density(self, text):
        '''
        Internal - Extracts the sector density
        '''
        # This distinguishes a "visited" from an unknown sector
        temp = text.find('Last Recorded Density:')
        if temp > -1:
            words = text[temp:].split('<')
#            print "*** Density %s" % words[0][23:],
            # This is an assumption because we haven't yet parsed the colour
            self.sector_known = True
            self.known_sectors += 1
            self.last_density[self.current_sector] = int(words[0][23:])
        else:
            self.unknown_sectors.append(self.current_sector)

    def parse_drones(self, text):
        '''
        Internal - Extracts the number of drones, including your drones
        '''
        temp = text.find('Drones:')
        if temp > -1:
            words = text[temp:].split('<')
#            print "*** Drones %s" % words[1][4:]
            self.drones.append((words[1][4:],self.current_sector))
        temp = text.find('Your Drones:')
        if temp > -1:
            words = text[temp:].split('<')
#            print "*** Your Drones %s" % words[1][4:]
            self.your_drones.append((int(words[1][4:]),self.current_sector))

    def parse_planet(self, text):
        '''
        Internal - Extracts the name of any planet
        '''
        temp = text.find('Planet:')
        if temp > -1:
            words = text[temp:].split('<')
#            print "*** Planet %s" % words[1][4:]
            self.planets.append((words[1][4:],self.current_sector))

    def parse_asteroid(self, text):
        '''
        Internal - Extracts the type of any asteroid
        '''
        temp = text.find('There is an asteroid in this sector:')
        if temp > -1:
            words = text[temp:].split()
            words2 = words[6].split('>')
#            print "*** %s Asteroid" % words2[-1]
            self.asteroids.append((words2[-1],self.current_sector))

    def parse_black_hole(self, text):
        '''
        Internal - Extracts the presence of a black hole
        '''
        if text.find('Black Hole in sector') > -1:
#            print "*** Black Hole"
            self.black_holes.append(self.current_sector)

    def parse_npc_store(self, text):
        '''
        Internal - Extracts the name of any NPC store
        '''
        temp = text.find('NPC Store:')
        if temp > -1:
            words = text[temp:].split('<')
#            print "*** NPC Store %s" % words[1][4:]
            self.npc_stores.append((words[1][4:],self.current_sector))

    def parse_jellyfish(self, text):
        '''
        Internal - Extracts the presence of jellyfish
        '''
        if text.find('Space Jellyfish in sector') > -1:
#            print "*** Jellyfish"
            self.jellyfish.append(self.current_sector)

    def parse_trading_port(self, text):
        '''
        Internal - Extracts the buy and sell prices of any trading port
        '''
        temp = text.find('Trader')
        if temp > -1:
            good = 0
            order = 0
            ore_buys = []
            ore_sells = []
            words = text[temp:].split()
            name = words[1]
#            print "*** Trading Port"
            align_idx = len(words)
            ge_idx = len(words)
            oc_idx = len(words)
            buy_idx = len(words)
            sell_idx = len(words)
            end_idx = len(words)
            for i in range(4,sell_idx):
                if words[i].find("Alignment:") > -1:
                    align_idx = i
#                    print "is aligned"
                if words[i].find("GE:") > -1:
                    ge_idx = i
#                    print "has GE"
                if words[i].find("OC:") > -1:
                    oc_idx = i
#                    print "has OC"
                if words[i].find("Buying:") > -1:
                    buy_idx = i
#                    print "is buying"
                if words[i].find("Selling:") > -1:
#                    print "is selling"
                    sell_idx = i
                if words[i].find("Links") > -1:
                    if end_idx == len(words):
                        end_idx = i
                if words[i].find("Emergency") > -1:
                    end_idx = i
                # Sector 502 has no links, but has text after the "sell" list
                if words[i].find("</p><i>This") > -1:
                    if end_idx == len(words):
                        end_idx = i
            ores_bought = words[buy_idx+1:sell_idx:4]
            buy_prices = words[buy_idx+3:sell_idx:4]
            for ore,price in zip(ores_bought,buy_prices):
                if ore not in self.ores_bought:
                    self.ores_bought[ore] = []
                sb = int(price[1:])
                self.ores_bought[ore].append((sb,self.current_sector))
                ore_buys.append((ore, sb))
            ores_sold = words[sell_idx+1:end_idx:4]
            sell_prices = words[sell_idx+3:end_idx:4]
            for ore,price in zip(ores_sold,sell_prices):
                if ore not in self.ores_sold:
                    self.ores_sold[ore] = []
                sb = int(price[1:])
                self.ores_sold[ore].append((sb,self.current_sector))
                ore_sells.append((ore, sb))
            if align_idx < len(words):
#                print "Found trading port alignment"
#                print words[align_idx+1:ge_idx+1]
                good = int(words[ge_idx+1:oc_idx][0])
                order = int(words[oc_idx+1:buy_idx+1][0].split('<')[0])
#                print "GE: "+str(good)+" OC: "+str(order)
            self.trading_ports.append(TradingPort(name, self.current_sector, good, order, ore_buys, ore_sells))
#        print

    def parse_ipt(self, text):
        '''
        Internal - Extracts the destination of any IPT
        '''
        temp = text.find('Emergency IPT')
        if temp > -1:
            words = text[temp:].split('>')
#            print "*** IPT to %s" % words[1][4:-3]
            self.ipts.append((words[1][4:-3],self.current_sector))

    def parse_luvsat(self, text):
        '''
        Internal - Extracts the presence of any luvsat
        '''
        if text.find('LuvSat in sector') > -1:
#            print "*** LuvSat"
            self.luvsats.append(self.current_sector)

    def parse_links(self, text):
        '''
        Internal - If the sector isn't linked to all neighbours,
                   stores that info in self.missing_links.
        '''
        # We only get links for "known" sectors
        # So we'll assume the rest link to all neighbours
        if self.sector_known:
            temp = text.find('Links To:')
            if temp > -1:
                words = text[temp:].split("'")
                words2 = words[0].split(",")
                links = [int(x[x.rindex(' '):]) for x in words2]
            else:
                links = []
#            print "*** Links to %s" % str(links)
            for s in adjacent_sectors(self.current_sector, self.can_move_diagonally()):
                if s not in links:
                    if not self.current_sector in self.missing_links:
                        self.missing_links[self.current_sector] = []
                    self.missing_links[self.current_sector].append(s)

    def parse_sector_description(self, text):
        '''
        Internal - Calls each of the other parse_ functions in turn
        '''
        # Note that ordering matters for some of these
        self.sector_known = False
        # parse_sector_number sets current_sector
        self.parse_sector_number(text)
        # parse_density sets sector_known
        self.parse_density(text)
        self.parse_drones(text)
        self.parse_planet(text)
        self.parse_asteroid(text)
        self.parse_black_hole(text)
        self.parse_npc_store(text)
        self.parse_jellyfish(text)
        self.parse_trading_port(text)
        self.parse_ipt(text)
        self.parse_luvsat(text)
        self.parse_links(text)

    def enhance_map(self):
        '''
        Adds known info to a partially-populated map.
        Can include missing links, black holes, NPC stores and planets,
        because they all stay put.
        Asteroids and trading ports move at reset.
        IPTs, jellyfish and luvsats move daily.
        '''
        if len(self.planets) < len(self.expected_planets()):
            unknown_planets = [planet for planet in self.expected_planets() if planet not in self.planets]
            self.planets += unknown_planets
            print "Added %d planet(s) - %s" % (len(unknown_planets), str(unknown_planets))

        if len(self.black_holes) < len(expected_black_holes):
            unknown_black_holes = [black_hole for black_hole in expected_black_holes if black_hole not in self.black_holes]
            self.black_holes += unknown_black_holes
            print "Added %d black hole(s)" % len(unknown_black_holes)

        if len(self.npc_stores) < len(self.expected_npc_stores()):
            unknown_npc_stores = [npc_store for npc_store in self.expected_npc_stores() if npc_store not in self.npc_stores]
            self.npc_stores += unknown_npc_stores
            print "Added %d NPC store(s) - %s" % (len(unknown_npc_stores), str(unknown_npc_stores))

        if len(self.missing_links) < len(self.expected_missing_links()):
            unknown_missing_links = [(sector,links) for sector,links in self.expected_missing_links().iteritems() if sector not in self.missing_links]
            for sector, links in unknown_missing_links:
                self.missing_links[sector] = links
            print "Added %d missing link(s)" % len(unknown_missing_links)

    def valid(self, quiet=False):
        '''
        Checks that the HTML file that was parsed was a valid SSW sector map
        Returns a tuple of (boolean validity, error message).
        Setting quiet to True inhibits printing any problems found
        '''
        # A Valid map should have the right number of sectors
        if (self.known_sectors + len(self.unknown_sectors) + len(self.forgotten_sectors)) != len(all_sectors):
            return False,'Known plus unknown plus forgotten sectors is %d, not %d' % (self.known_sectors + len(self.unknown_sectors) + len(self.forgotten_sectors), len(all_sectors))

        # A Valid map should have the numbers of things that it says it has
        for key,value in self.expected_totals.iteritems():
            if key == 'planets':
                if len(self.planets) != value:
                    return False,'Expected %d planets, found %d' % (value, len(self.planets))
            elif key == 'asteroid':
                if len(self.asteroids) != value:
                    return False,'Expected %d asteroids, found %d' % (value, len(self.asteroids))
            elif key == 'black hole':
                if len(self.black_holes) != value:
                    return False,'Expected %d black holes, found %d' % (value, len(self.black_holes))
            elif key == 'npc store':
                if len(self.npc_stores) != value:
                    return False,'Expected %d npc stores, found %d' % (value, len(self.npc_stores))
            elif key == 'space jellyfish':
                if len(self.jellyfish) != value:
                    return False,'Expected %d jellyfish, found %d' % (value, len(self.jellyfish))
            elif key == 'trading port':
                if len(self.trading_ports) != value:
                    return False,'Expected %d trading ports, found %d' % (value, len(self.trading_ports))
            elif key == 'ipt beacon':
                if len(self.ipts) != value:
                    return False,'Expected %d IPT beacons, found %d' % (value, len(self.ipt_beacons))
            elif key == 'luvsat':
                if len(self.luvsats) != value:
                    return False,'Expected %d luvsats, found %d' % (value, len(self.luvsats))

        if not quiet:
            # These are more tests of this code than tests of the map file itself,
            # but this is the one place we know will be called once after parsing
            for sector in set(self.expected_missing_links()) - set(self.missing_links):
                if sector not in self.unknown_sectors + self.forgotten_sectors:
                    print "WARNING Didn't find expected missing links from sector %d" % (sector)
            for sector in set(self.missing_links) - set(self.expected_missing_links()):
                print "WARNING Didn't expect to find missing links in sector %d" % (sector)
            for planet, sector in set(self.expected_planets()) - set(self.planets):
                if sector not in self.unknown_sectors + self.forgotten_sectors:
                    print "WARNING Planet %s is missing from sector %d" % (planet, sector)
            for planet, sector in set(self.planets) - set(self.expected_planets()):
                if ((planet, sector) not in temporary_planets) and ((planet, None) not in temporary_planets):
                    print "WARNING Didn't expect to find planet %s in sector %d" % (planet, sector)
            if self.expected_asteroids() < len(self.asteroids):
                print "WARNING: code expects fewer asteroids"
            elif self.expected_asteroids() > len(self.asteroids) + len(self.unknown_sectors) + len(self.forgotten_sectors):
                print "WARNING: code expects more asteroids"
            for sector in set(expected_black_holes) - set(self.black_holes):
                if sector not in self.unknown_sectors + self.forgotten_sectors:
                    print "WARNING Black hole is missing from sector %d" % (sector)
            for sector in set(self.black_holes) - set(expected_black_holes):
                print "WARNING Didn't expect to find black hole in sector %d" % (sector)
            for store, sector in set(self.expected_npc_stores()) - set(self.npc_stores):
                if sector not in self.unknown_sectors + self.forgotten_sectors:
                    print "WARNING NPC store %s is missing from sector %d" % (store, sector)
            for store, sector in set(self.npc_stores) - set(self.expected_npc_stores()):
                print "WARNING Didn't expect to find NPC store %s in sector %d" % (store, sector)
            if expected_jellyfish < len(self.jellyfish):
                print "WARNING: code expects fewer jellyfish"
            elif expected_jellyfish > len(self.jellyfish) + len(self.unknown_sectors) + len(self.forgotten_sectors):
                print "WARNING: code expects more jellyfish"
            if expected_trading_ports < len(self.trading_ports):
                print "WARNING: code expects fewer trading ports"
            elif expected_trading_ports > len(self.trading_ports) + len(self.unknown_sectors) + len(self.forgotten_sectors):
                print "WARNING: code expects more trading ports"
            if expected_ipts < len(self.ipts):
                print "WARNING: code expects fewer IPT beacons"
            elif expected_ipts > len(self.ipts) + len(self.unknown_sectors) + len(self.forgotten_sectors):
                print "WARNING: code expects more IPT beacons"
            if expected_luvsats < len(self.luvsats):
                print "WARNING: code expects fewer luvsats"
            elif expected_luvsats > len(self.luvsats) + len(self.unknown_sectors) + len(self.forgotten_sectors):
                print "WARNING: code expects more luvsats"

        # If we get here, all is good
        return True,''

    def extract_date(self, text):
        '''
        Internal - Extracts the date of the map
        '''
        text = text.replace('\xa0', ' ')
        text = text.replace('&nbsp;', ' ')
        temp = text.find('UTC:')
        assert temp > -1,text
        words = text[temp:].split()
        self.datetime = datetime.datetime(int(words[4].split('<')[0]),int(months[words[2]]),int(words[3][:-1]),int(words[1][:-3]),int(words[1][3:]))
#        print "Map for " + str(self.datetime)

    def extract_explored(self, text):
        '''
        Internal - Figures out from the sector colour whether it has been explored,
                   never visited, or forgotten
        '''
        temp = text.find('rgb')
        if temp > -1:
            words = text[temp:].split(')')
            colour = words[0][4:]
        else:
            temp = text.find('background:#')
            words = text[temp:].split(':')
            colour = words[1]
        if (colour == "0, 255, 0") or (colour == "#00ff00;"):
            self.sector_colour = 'green'
        elif (colour == "255, 255, 255") or (colour == "#ffffff;"):
            # Nardo's script uses this colour to flag sectors with your drones
            self.sector_colour = 'green'
        elif (colour == "204, 204, 204") or (colour == "#cccccc;"):
            # Forgotten sector
            self.sector_colour = 'light grey'
            assert self.sector_known
            self.known_sectors -= 1
            self.forgotten_sectors.append(self.current_sector)
            self.sector_known = False
            # That means that we no longer know about missing links
            del self.missing_links[self.current_sector]
        elif (colour == "153, 153, 153") or (colour == "#999999;"):
            # Never explored
            self.sector_colour = 'dark grey'
            assert not self.sector_known
        elif (colour == "255, 204, 0") or (colour == "#ffcc00;"):
            self.sector_colour = 'yellow'
        # We want to be able to parse HTML files that aren't SSW maps,
        # but we also want to notice when secotr colours change...
        elif self.current_sector != 0:
            assert 0, 'Unrecognised sector colour ' + colour + ' in sector ' + str(self.current_sector)
        # This is the last thing we do for a sector
        self.current_sector = 0

    def extract_totals(self, text):
        '''
        Internal - Extracts the total number of each item of interest from the header
        '''
        temp = text.find('(')
        assert temp > -1,text
        key = text[:temp-1].lower()
        try:
            value = int(text[temp+1:-1])
            self.expected_totals[key] = value
        except ValueError:
            pass

    def enemy_drones(self, for_society, unexplored_sector_society=None):
        '''
        Return list of sectors with enemy drones
        for_society is a string : "Illuminati", "Oddfellowish", "Eastern Star", etc
        unexplored sectors will be assumed to belong to unexplored_sector_society
        '''
        if for_society == None:
            return []
        retval = [sector for society,sector in self.drones if society != for_society]
        if (unexplored_sector_society != None) and (society != unexplored_sector_society):
            # Add all unexplored sectors to retval
            retval += self.unknown_sectors
        return retval

    def trading_port(self, in_sector):
        '''
        Returns the trading port (if any) in the specified sector
        '''
        for port in self.trading_ports:
            if port.sector == in_sector:
                return port
        return None

    def nearest(self, to_sector, planets_or_ipts, max_length, for_society=None, unexplored_sector_society=None):
        '''
        Internal - Where's the nearest planet/IPT to a sector ?
        Returns a tuple of (name, sector, distance, drones en route)
        This is really just the code common to nearest_planet() and nearest_ipt()
        Check for it returning None for the sector to see whether it found one.
        Note that we assume that direction doesn't matter
        '''
        closest_name = ""
        closest_sector = None
        closest_distance = max_length
        closest_drones = []
        # fly distance can't be less than direct_distance,
        # so use direct distance as a first approximation
        temp = [(name, sector, direct_distance(to_sector, sector)) for (name, sector) in planets_or_ipts]
        # start with the one that is physically closest
        for (name, sector, dist) in sorted(temp, key=operator.itemgetter(2)):
            if dist < closest_distance:
                # Here, we go from the planet or IPT to the sector of interest
                # This helps pick up embargoed planets much quicker
                (fly_dist, drones) = fly_distance(sector, to_sector, self.can_move_diagonally(), self.missing_links, self.enemy_drones(for_society, unexplored_sector_society), self.drones, closest_distance)
                if (fly_dist != None) and (fly_dist < closest_distance):
                    closest_name = name
                    closest_sector = sector
                    closest_distance = fly_dist
                    closest_drones = drones
            else:
                # No point in going further through the list
                break
        return (closest_name, closest_sector, closest_distance, closest_drones)

    def nearest_planet(self, to_sector, max_length=max_route_length, for_society=None, unexplored_sector_society=None):
        '''
        Where's the nearest planet to a sector ?
        Returns a tuple of (planet name, sector, distance, drones en route)
        '''
        (name, sector, distance, drones) = self.nearest(to_sector, self.planets, max_length, for_society, unexplored_sector_society)
        # For nearest planet, we want to go from the planet to the sector,
        # but "nearest" does the opposite, so we need to allow for drones
        # at the sector of interest, too
        return (name, sector, distance, drones + drones_en_route([to_sector], self.drones))
 
    def nearest_ipt(self, to_sector, max_length=max_route_length, for_society=None, unexplored_sector_society=None):
        '''
        Where's the nearest IPT to a sector ?
        Returns a tuple of (IPT destination, sector, distance, drones en route)
        '''
        temp = self.nearest(to_sector, self.ipts, max_length, for_society, unexplored_sector_society)
        return temp

    def nearest_planet_or_ipt(self, to_sector, max_length=max_route_length, for_society=None, unexplored_sector_society=None):
        '''
        Where's the nearest planet or IPT to a sector ?
        Returns a tuple of (IPT dest or planet name, sector, distance, drones en route)
        '''
        (ipt_dest, ipt_sector, ipt_dist, ipt_drones) = self.nearest_ipt(to_sector, max_length, for_society, unexplored_sector_society)
        (planet_name, planet_sector, planet_dist, planet_drones) = self.nearest_planet(to_sector, max_length, for_society, unexplored_sector_society)
        if ipt_dist < planet_dist:
            return (ipt_dest, ipt_sector, ipt_dist, ipt_drones)
        else:
            return (planet_name, planet_sector, planet_dist, planet_drones)

    def shortest_distance(self, from_sector, to_sector, for_society=None, unexplored_sector_society=None, max_length=max_route_length):
        '''
        How long to get between the two sectors by the shortest route ?
        Returns a tuple with (the distance, None or a tuple of via sectors,
        list of drones en route)
        Distance will be None if there's no route between the two
        '''
        # Short-circuiting at this point saves an awful lot of effort when there are lots of drones around
        # Otherwise, we can get hung up trying to find a route between a planet or IPT and a drone-free sector
        if (for_society != None):
            if (from_sector in self.enemy_drones(for_society, unexplored_sector_society)) or (to_sector in self.enemy_drones(for_society, unexplored_sector_society)):
                return (None, None, None)
        # Could go via a planet
        (dest_name, dest_sector, dest_dist, dest_drones) = self.nearest_planet(to_sector, max_length, for_society, unexplored_sector_society)
        # If we can't get to the destination from a planet,
        # there's no point looking for a route from the source to a planet or IPT
        if (dest_sector == None):
            (via_dest, via_sector, via_dist, via_drones) = ('', None, sectors_per_row, [])
        else:
            (via_dest, via_sector, via_dist, via_drones) = self.nearest_planet_or_ipt(from_sector, max_length, for_society, unexplored_sector_society)
        # Flying distance can't be less than direct distance
        if (via_dist + dest_dist) < direct_distance(from_sector, to_sector):
            return (via_dist + dest_dist, (via_sector, dest_sector), via_drones + dest_drones)
        # or, could just fly between the two
        (fly_dist, fly_drones) = fly_distance(from_sector, to_sector, self.can_move_diagonally(), self.missing_links, self.enemy_drones(for_society, unexplored_sector_society), self.drones, via_dist+dest_dist)
        if (dest_sector == None) or (via_sector == None):
            # There's no route between the two via a planet
            # fly_dist is either None or the quickest route
            return (fly_dist, None, fly_drones)
        if (fly_dist == None) or ((via_dist + dest_dist) < fly_dist):
            # Going via a planet is quickest (or the only possible way)
            return (via_dist + dest_dist, (via_sector, dest_sector), via_drones + dest_drones)
        # Going direct is quickest
        return (fly_dist, None, fly_drones)

    def shortest_route(self, from_sector, to_sector, for_society=None, unexplored_sector_society=None, max_length=max_route_length):
        '''
        Returns a tuple with (distance, route description string, list of
        drones en route) for the shortest route
        You can set to_sector == from_sector if you only have one sector of interest
        '''
        if for_society == None:
            soc_str = ""
        else:
            soc_str = " avoiding enemy drones"
        if from_sector == to_sector:
            fail_str = "No route shorter than %d moves to %d%s" % (max_length, from_sector, soc_str)
        else:
            fail_str = "No route shorter than %d moves from %d to %d%s" % (max_length, from_sector, to_sector, soc_str)

        # Short-circuiting at this point saves an awful lot of effort when there are lots of drones around
        # Otherwise, we can get hung up trying to find a route between a planet or IPT and a drone-free sector
        if for_society != None:
            if (from_sector in self.enemy_drones(for_society, unexplored_sector_society)) or (to_sector in self.enemy_drones(for_society, unexplored_sector_society)):
                return (sectors_per_row, fail_str, [])

        (start_planet, start_sector, start_dist, start_drones) = self.nearest_planet(from_sector, max_length, for_society, unexplored_sector_society)
        # If we can't get to from_sector from a planet,
        # there's no point looking for the rest of the route
        if (start_sector == None):
            (end_name, end_sector, end_dist, end_drones) = ('', None, sectors_per_row, [])
        else:
            (end_name, end_sector, end_dist, end_drones) = self.nearest_planet_or_ipt(to_sector, max_length, for_society, unexplored_sector_society)
        # Similarly, if we can't get back from to_sector,
        # there's no point looking for a route to to_sector
        if (end_sector == None):
           (dist, route, drones) = (None, [], [])
        else:
           (dist, route, drones) = self.shortest_distance(from_sector, to_sector, for_society, unexplored_sector_society, max_length)
        if dist == None:
            return (sectors_per_row, fail_str, [])
        if start_sector == None:
            return (sectors_per_row, "No route to %d%s" % (to_sector, soc_str), [])
        if end_sector == None:
            return (sectors_per_row, "No route out of %d%s" % (from_sector, soc_str), [])
        if route:
            planet_name = [name for (name, sector) in self.planets if sector == route[1]]
            route_str = "via %d and %s (%d)" % (route[0], planet_name[0], route[1])
        else:
            route_str = "direct"
        moves = start_dist+dist+end_dist
        if moves == 1:
            move_str = "move"
        else:
            move_str = "moves"
        if from_sector == to_sector:
            return (moves, "%d %s - %s (%d), to %d, to %d (%s)" % (moves, move_str, start_planet, start_sector, from_sector, end_sector, end_name), start_drones + drones + end_drones)
        return (moves, "%d %s - %s (%d), to %d, %s to %d, to %d (%s)" % (moves, move_str, start_planet, start_sector, from_sector, route_str, to_sector, end_sector, end_name), start_drones + drones + end_drones)

    def handle_starttag(self, tag, atts):
        '''
        Internal - deal with the start of the HTML entity
        '''
        if tag == "div":
            for (key,val) in atts:
                if not key.find('onmouseover'):
                    self.parse_sector_description(val)
        elif tag == 'span':
            for (key,val) in atts:
                if not key.find('onmouseover'):
                    self.extract_date(val)
        elif tag == 'td':
            if (len(atts) == 1) and (atts[0][0] == 'style'):
                if ('vertical-align: middle' in atts[0][1]) and ('font-size: 10px' in atts[0][1]):
                    self.in_totals = True
                    self.text = []
        elif tag == 'a':
            keys = [key for key,value in atts]
            if 'title' in keys:
                pass
            elif 'target' in keys:
                pass
            elif 'name' in keys:
                pass
            else:
                for (key,val) in atts:
                    if not key.find('style'):
                        self.extract_explored(val)

#    def handle_entityref(self, name):
#        if self.indiv:
#            self.handle_data(self.entitydefs.get(name, "?"))

    def handle_data(self, data):
        '''
        Internal - Deal with the content of the HTML entity
        '''
#        print self.in_totals
#        print data
        if self.in_totals:
            self.text.append(data)

    def handle_endtag(self, tag):
        '''
        Internal - deal with the end of the HTML entity
        '''
        if (tag == "td") and self.in_totals:
            self.in_totals = False
            if self.text:
                self.extract_totals("".join(self.text))

# TODO Add lots more unit tests

class CoordsKnownValues(unittest.TestCase):
    known_values = [(1, (0, 0)),
                    (2, (1, 0)),
                    (33, (32, 0)),
                    (34, (0, 1)),
                    (1057, (0, 32)),
                    (1089, (32, 32))]

    def testToCoords(self):
        '''sector_to_coords should give the expected result for known input'''
        for sector, coords in self.known_values:
            result = sector_to_coords(sector)
            self.assertEqual(result, coords)

    def testToSector(self):
        '''coords_to_sector should give the expected result for known input'''
        for sector, (col, row) in self.known_values:
            result = coords_to_sector(col, row)
            self.assertEqual(result, sector)

class CoordsSanityCheck(unittest.TestCase):
    def testSanity(self):
        '''coords_to_sector(sector_to_coords(n)) == n for all n'''
        for input in all_sectors:
            coords = sector_to_coords(input)
            result = coords_to_sector(coords[0], coords[1])
            self.assertEqual(result, input)

class AdjacentKnownValues(unittest.TestCase):
    known_values = [(1, [2, 34, 35]),
                    (2, [1, 3, 34, 35, 36]),
                    (33, [32, 65, 66]),
                    (102, [68, 69, 70, 101, 103, 134, 135, 136]),
                    (1057, [1024, 1025, 1058]),
                    (1089, [1055, 1056, 1088])]

    def testAdjacentKnownValues(self):
        '''adjacent_sectors should give expected result for known input'''
        for sector, adj in self.known_values:
            result = adjacent_sectors(sector, True)
            self.assertEqual(result, adj)

class AdjTowardsKnownValues(unittest.TestCase):
    known_values = [(1, 4, [2, 35]),
                    (2, 70, [36]),
                    (33, 98, [65, 66]),
                    (102, 168, [134, 135, 136]),
                    (1057, 959, [1024, 1025]),
                    (1089, 1083, [1055, 1088])]

    def testAdjacentKnownValues(self):
        '''adj_sectors_towards should give expected result for known input'''
        for start, end, adj in self.known_values:
            result = adj_sectors_towards(start, end, True)
            self.assertEqual(result, adj)

class AdjacentSectors(unittest.TestCase):
    def testAdjacentCount(self):
        '''adjacent_sectors should always return 3, 5 or 8 sectors'''
        for sector in all_sectors:
            result = adjacent_sectors(sector, True)
            length = len(result)
            self.assert_(length in [3, 5, 8])

    def testAdjTowardsCount(self):
        '''adj_sectors_towards should always return 1, 2 or 3 sectors'''
        for sector in all_sectors:
            result = adj_sectors_towards(sector, 600, True)
            length = len(result)
            if sector == 600:
                self.assertEqual(length, 0)
            else:
                self.assert_(length in [1, 2, 3])

    def testSubset(self):
        '''adj_sectors_towards should always return a subset of adjacent_sectors'''
        for sector in all_sectors:
            all_adj = adjacent_sectors(sector, True)
            subset = adj_sectors_towards(sector, 500, True)
            self.assert_(set(subset).issubset((all_adj)))

class CanMove(unittest.TestCase):
    def testEmptyLists(self):
        '''can_move should return True if both missing_links and avoiding_sectors are empty'''
        for sector in all_sectors:
            result = can_move(sector, 100)
            self.assertEqual(result, True)

    def testMissingLinks(self):
        '''can_move should return False if there's no link to the destination from the start'''
        for sector in all_sectors:
            result = can_move(sector, 100, {sector: [50, 100]})
            self.assertEqual(result, False)

    def testNotInMissingLinks(self):
        '''can_move should return True if there is a link to the destination from the start'''
        for sector in all_sectors:
            result = can_move(sector, 150, {sector: [50, 100]})
            self.assertEqual(result, True)

    def testSourceNotInMissingLinks(self):
        '''can_move should return True if there is a link to the destination from the start'''
        for sector in all_sectors:
            result = can_move(sector, 100, {300: [50, 100]})
            if sector == 300:
                self.assertEqual(result, False)
            else:
                self.assertEqual(result, True)

    def testAvoidingSector(self):
        '''can_move should return False if the destination is in avoiding_sector'''
        for sector in all_sectors:
            result = can_move(sector, 100, [], [50, 100])
            self.assertEqual(result, False)

    def testAvoidingOtherSector(self):
        '''can_move should return True if the destination is not in avoiding_sector'''
        for sector in all_sectors:
            result = can_move(sector, 150, [], [50, 100])
            self.assertEqual(result, True)

class DirectDistance(unittest.TestCase):
    def testSelf(self):
        '''distance to the same sector is always zero'''
        for sector in all_sectors:
            result = direct_distance(sector, sector)
            self.assertEqual(result, 0)

    def testAdjacent(self):
        '''distance to adjacent sectors is always one'''
        for sector in all_sectors:
            for end in adjacent_sectors(sector, True):
                result = direct_distance(sector, end)
                self.assertEqual(result, 1)

# This one takes several seconds
#    def testLimits(self):
#        '''distance to any sector ranges from 0 to 32'''
#        for sector in all_sectors:
#            for end in all_sectors:
#                result = direct_distance(sector, end)
#                self.assert_(result in range(0,33))

class DirectDistanceKnownValues(unittest.TestCase):
    # TODO Add to this list
    known_values = [(1, 3, 2),
                    (3, 1, 2),
                    (1, 4, 3),
                    (1, 33, 32),
                    (1, 1057, 32),
                    (1057, 1, 32),
                    (1, 1089, 32)]

    def testdirectdistanceKnownValues(self):
        '''direct_distance should give expected result for known input'''
        for start, end, distance in self.known_values:
            result = direct_distance(start, end)
            self.assertEqual(result, distance)

if __name__ == "__main__":
    unittest.main()

