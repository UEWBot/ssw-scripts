#!/usr/bin/python

'''
Utilities to deal with a SSW sector map
Including a parser for the HTML file.
This is a copy of ssw_sector_map, reworked to use BeautifulSoup.
'''

# Copyright 2008-2016 Squiffle

# TODO: Assume that missing links are bi-directional (they always have been so far).
# TODO: Change to allow debugging to be enabled at run-time

from __future__ import absolute_import
from __future__ import print_function
import operator, datetime, unittest, re
from bs4 import BeautifulSoup
import ssw_missing_links, ssw_societies, ssw_utils
from ssw_trading_port import TradingPort
import ssw_get_asteroids, ssw_get_planets, ssw_get_stores, ssw_get_trading_ports
import six
from six.moves import range

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
               datetime.datetime(3011, 7, 9, 23, 41),
               datetime.datetime(3011, 10, 12, 23, 40),
               datetime.datetime(3016, 1, 4, 0, 34), # no reset
               datetime.datetime(3016, 5, 1, 0, 2),
               datetime.datetime(3017, 4, 30, 0, 18)]

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
           datetime.datetime(3011, 6, 17, 23, 59),
           datetime.datetime(3011, 10, 1, 23, 59),
           datetime.datetime(3011, 12, 5, 23, 59),
           datetime.datetime(3016, 4, 8, 11, 20),
           datetime.datetime(3017, 1, 5, 23, 59),
          ]

'''
Before this date, movement between adjacent sectors was almost unrestricted
'''
space_mazified_datetime = datetime.datetime(3010, 5, 22, 23, 59)

'''
Flambe was a later addition
'''
flambe_added_datetime = datetime.datetime(3010, 5, 30, 13, 22)

'''
There was a major change to the map at this point.
'''
planets_moved_datetime = datetime.datetime(3011, 6, 21, 16, 26)

'''
SSW came back from the dead.
'''
shutdown_datetime = datetime.datetime(3012, 0o2, 12)
reboot_datetime = datetime.datetime(3015, 11, 17, 18, 12)

'''
Hedrok vanished, then reappeared
'''
hedrok_removed_datetime = datetime.datetime(3016, 1, 21, 23, 0o7)
hedrok_restored_datetime = datetime.datetime(3016, 2, 10, 23, 0o3)

'''
There was a major rework of space.
It was actually a bit spread out, but this was the start.
'''
space_rework_datetime = datetime.datetime(3016, 4, 9, 12, 10)

'''
Some old panets were removed after the major rework
'''
deep_six_removed_datetime = datetime.datetime(3016, 4, 17, 22, 5)
phallorus_removed_datetime = datetime.datetime(3016, 4, 17, 22, 27)
eroticon_69_removed_datetime = datetime.datetime(3016, 4, 18, 11, 37)

'''
Various NPS stores were later additions
'''
leroy_tongs_datetime = datetime.datetime(3009, 1, 19, 0, 0)
clingons_datetime = datetime.datetime(3016, 1, 25, 0, 0)
gobbles_datetime = datetime.datetime(3016, 2, 12, 0, 0)

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
max_route_length = 30

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
def mars_present(map_date):
    """
    Returns a boolean indicating whether Mars appears on the specified date.
    """
    return ((map_date.month, map_date.day) in mars_dates)

'''Where was The <3 Boat ?'''
def love_boat_sector(year):
    """
    Returns the sector where The <3 Boat appeared in the specified year, if known
    """
    # TODO Add <3 Boat locations for 3008, 3010, and 3011
    if (year == 3009):
        return 157
    if (year == 3016):
        return 676
    if (year == 3017):
        return 926
    return None

'''Where was Planet X ?'''
def planet_x_sector(year):
    """
    Returns the sector where Planet X appeared in the specified year, if known.
    For 3016, returns a dict, indexed by date, of sectors.
    """
    # TODO Add Planet X locations for 3007, 3008 and 3009
    if (year == 3010):
        return 516
    if (year == 3015):
        return 516
    if (year == 3016):
        # Planet X moved around this year
        return planet_x_3016_locations()
    return None

def planet_x_3016_locations():
    """
    Returns a dict, indexed by date, of planet X locations
    """
    the_list = {datetime.date(3016, 12, 25): 552,
                datetime.date(3016, 12, 26): 123,
                datetime.date(3016, 12, 27): 142,
                datetime.date(3016, 12, 28): 669,
                datetime.date(3016, 12, 29): 1011,
                datetime.date(3016, 12, 30): 313,
                datetime.date(3016, 12, 31): 828,
               }
    return the_list

'''The <3 Boat appears on a regular schedule'''
def love_boat_present(map_date):
    """
    Returns a boolean indicating whether The <3 Boat appears on the specified date.
    """
    # Just Valentine's Day
    return ((map_date.month, map_date.day) == (2, 14))

'''Planet X appears on a regular schedule'''
def planet_x_present(map_date):
    """
    Returns a boolean indicating whether Planet X appears on the specified date.
    """
    # Christmastime
    return ((map_date.month == 12) and (map_date.day >= 25))

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
    # TODO Should rework all of this lot into a single table somehow
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
    # Pinon Sol vanished with the reboot
    removed_planet_1 = ('Pinon Sol', 707)
    # Hedrok went for rework a bit later
    removed_planet_2 = ('Hedrok', 888)
    replacement_planet = ('Yipikaitain', 888)
    # And then reappeared
    restored_planet = ('Hedrok', 707)

    # There was a huge rework of planets after SSW was revived
    v2_planets = [('Earth', 1),
                  ('Boria', 65),
                  ('Solaris', 81),
                  ('Trinoc', 202),
                  ('New Ceylon', 227),
                  ('Yeranus', 353),
                  ('Nortonia', 366),
                  ('Ahlnuldia', 471),
                  ('Laxloo', 493),
                  ('Xiao MeiMei', 612),
                  ('Lucky Spaceman Distilleries', 631),
                  ('Pharma', 721),
                  ('Hedrok', 867),
                  ('Barnimus', 880),
                  ('Yipikaitain', 987),
                  ('Tranquility', 995),
                  ('Flambe', 1004)]
    leftovers = [('Deep Six Fauna', 142),
                 ('Phallorus', 123),
                 ('Eroticon 69', 313)]

    # Is the date after the huge re-work ?
    if (map_datetime > space_rework_datetime):
        if ((map_datetime > eroticon_69_removed_datetime) and
            (cycle(map_datetime) < 21)):
            retval = v2_planets
        elif (map_datetime > phallorus_removed_datetime):
            retval = v2_planets + leftovers[2:]
        elif (map_datetime > deep_six_removed_datetime):
            retval = v2_planets + leftovers[1:]
        else:
            retval = v2_planets + leftovers
    else:
        # Map alterations
        if (map_datetime > planets_moved_datetime):
            retval += moved_planets_after
            retval += new_planets
        else:
            retval += moved_planets_before
        if (map_datetime > flambe_added_datetime):
            retval.append(flambe)
        if (map_datetime > reboot_datetime):
            retval.remove(removed_planet_1)
        if (map_datetime > hedrok_removed_datetime):
            retval.remove(removed_planet_2)
            retval.append(replacement_planet)
        if (map_datetime > hedrok_restored_datetime):
            retval.append(restored_planet)

    # Intermittent planets
    map_date = map_datetime.date()
    if (mars_present(map_date)):
        retval.append(mars)
    if (love_boat_present(map_date)):
        sector = love_boat_sector(map_date.year)
        if (sector):
            retval.append((love_boat[0],sector))
    if (planet_x_present(map_date)):
        sector = planet_x_sector(map_date.year)
        if (sector):
            if type(sector) is dict:
                retval.append((planet_x[0],sector[map_date]))
            else:
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
    cycle_16_map_change_datetime = datetime.datetime(3011, 7, 3, 23, 59)
    cycle_19_map_change_datetime = datetime.datetime(3016, 4, 25, 23, 59)

    if (cycle(map_datetime) < 13):
        return maze_free_sectors
    elif (cycle(map_datetime) == 13):
        if (map_datetime < space_mazified_datetime):
            return ssw_missing_links.cycle_13_war_links
        else:
            return ssw_missing_links.cycle_13_late_links
    elif (cycle(map_datetime) == 14):
        return ssw_missing_links.cycle_14_links
    elif (cycle(map_datetime) == 15):
        return ssw_missing_links.cycle_15_links
    elif (cycle(map_datetime) == 16):
        if (map_datetime < cycle_16_map_change_datetime):
            return ssw_missing_links.cycle_16_war_links
        else:
            return ssw_missing_links.cycle_16_late_links
    elif (cycle(map_datetime) == 17):
        return ssw_missing_links.cycle_17_links
    elif (cycle(map_datetime) == 18):
        return ssw_missing_links.cycle_18_links
    elif (cycle(map_datetime) == 19):
        # Map was reworked after the war ended but before cycle 20 started
        if (map_datetime > war_end[19]):
            if (map_datetime < cycle_19_map_change_datetime):
                return ssw_missing_links.cycle_19_post_war_links_1
            else:
                return ssw_missing_links.cycle_19_post_war_links_2
        return ssw_missing_links.cycle_19_links
    elif (cycle(map_datetime) == 20):
        return ssw_missing_links.cycle_20_links
    elif (cycle(map_datetime) == 21):
        return ssw_missing_links.cycle_21_links
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
    # New stores
    new_stores = [
        (leroy_tongs_datetime, ('Leroy Tong`s Trancendental Soul Food', 923)),
        (clingons_datetime, ('Clingon`s Around Yeranus', 30)),
        (gobbles_datetime, ('Gobble`s Chez Le` Turkle', 719))]
    # Major rework when SSW was revived
    v2_stores = [('Captain Jork`s Last Chance Saloon', 1075),
                 ('Clingon`s Around Yeranus', 353),
                 ('Leroy Tong`s Trancendental Soul Food', 923),
                 ('Lucky Spaceman Liquor Store', 631),
                 ('Gobble`s Chez Le` Turkle', 719),
                 ('Salty Bob`s Waterin` Hole', 1),
                 ('Syawillim', 502)]

    # Is the date after the huge re-work ?
    if (map_datetime > space_rework_datetime):
        return v2_stores

    # Relocations
    if (map_datetime > planets_moved_datetime):
        retval.append(lsd_store_after)
    else:
        retval.append(lsd_store_before)
    # Additions
    for d,p in new_stores:
        if (map_datetime > d):
            retval.append(p)
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
months = dict([(datetime.date(2008,x,0o1).strftime('%b'),x) for x in range(1,13)])

'''List of all valid sector numbers'''
all_sectors = list(range(1,1090))

'''Number of sectors in each row(and column)'''
sectors_per_row = 33

'''List of valid coordinate (row or column) numbers'''
coord_range = list(range(0,sectors_per_row))

def sector_to_coords(sector_number):
    '''
    Convert a sector number to a (col,row) coordinate tuple
    Sector numbers start from 1, but we number rows and cols from 0
    '''
    # Sector numbers start from 1, but we'll number rows and cols from 0
    row = (sector_number - 1) // sectors_per_row
    col = (sector_number - 1) % sectors_per_row
    return (col,row)

def coords_to_sector(column, row):
    '''
    Convert a row and column to a sector number
    Sector numbers start from 1, but we number rows and cols from 0
    '''
    return (row * sectors_per_row) + column + 1

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
    except KeyError:
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

def routes_of_length(length,
                     from_sector,
                     to_sector,
                     can_move_diagonally,
                     missing_links={},
                     avoiding_sectors=[]):
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
        if can_move(from_sector,
                    s,
                    missing_links,
                    avoiding_sectors) and (direct_distance(s,
                                                           to_sector) <= length) :
            # It is
            retval.append([s])
    # Here's the recursive bit - termination condition is that we've got there
    if length > 0:
        # No idea whether new_retval is strictly necesary, but better to be safe
        new_retval = []
        for route in retval:
            # Find routes from the end of route to to_sector
            temp = routes_of_length(length,
                                    route[-1],
                                    to_sector,
                                    can_move_diagonally,
                                    missing_links,
                                    avoiding_sectors+route)
            for s in temp:
                new_retval.append(route+s)
        retval = new_retval
    return retval
 
def a_route_of_length(length,
                      from_sector,
                      to_sector,
                      can_move_diagonally,
                      missing_links={},
                      avoiding_sectors=[]):
    '''
    Find any one route of the specified length between the two sectors
    '''
    print(file=flog)
    print("a_route_of_length(%d, %d, %d, %s, ..., %s)" % (length, from_sector, to_sector, str(can_move_diagonally), str(avoiding_sectors)), file=flog)
    if (length == 0) and (from_sector == to_sector):
        # We just need to stay in from_sector
        print(" Returning []", file=flog)
        return []
    elif (length == 1) and to_sector in adjacent_sectors(from_sector,
                                                         can_move_diagonally):
        if can_move(from_sector, to_sector, missing_links, avoiding_sectors):
            print(" Returning [%d]" % to_sector, file=flog)
            return [to_sector]
        else:
            # There is no route
            print(" Returning None (1)", file=flog)
            return None
    length -= 1
    for s in adjacent_sectors(from_sector, can_move_diagonally):
        print(" Trying via %d" % s, file=flog)
        # Figure out whether s is 1 closer to to_sector
        if can_move(from_sector,
                    s,
                    missing_links,
                    avoiding_sectors) and (direct_distance(s,
                                                           to_sector) <= length) :
            print(" Recursing", file=flog)
            temp = a_route_of_length(length,
                                     s,
                                     to_sector,
                                     can_move_diagonally,
                                     missing_links,
                                     avoiding_sectors+[from_sector,s])
            if temp != None:
                print(" Returning [%d] + %s" % (s, str(temp)), file=flog)
                return [s] + temp
    # If we get here, there are no routes of the specified length
    print(" Returning None (2)", file=flog)
    return None
 
def routes(from_sector,
           to_sector,
           can_move_diagonally,
           missing_links={},
           avoiding_sectors=[],
           max_length=max_route_length):
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
        retval = routes_of_length(route_length,
                                  from_sector,
                                  to_sector,
                                  can_move_diagonally,
                                  missing_links,
                                  avoiding_sectors)
        route_length += 1
    return retval

def a_route(from_sector,
            to_sector,
            can_move_diagonally,
            missing_links={},
            avoiding_sectors=[],
            max_length=max_route_length,
            min_length=0):
    '''
    Find a route from one sector to another
    Returns an ordered list of intermediate sectors
    Will return one shortest-distance route
    '''
    #print "Looking for a route from %d to %d" % (from_sector, to_sector)
    if (from_sector in avoiding_sectors) or (to_sector in avoiding_sectors):
        # No route is possible
        return None
    route_length = direct_distance(from_sector, to_sector)
    if min_length > route_length:
        route_length = min_length
    # Here's another optimisation - if all the sectors adjacent to either
    # the source or destination are impassable, drop out early
    # But only if we actually need to move
    if route_length > 0:
        if len(set(adjacent_sectors(from_sector,
                                    can_move_diagonally)) - set(avoiding_sectors)) == 0:
            return None
        if len(set(adjacent_sectors(to_sector,
                                    can_move_diagonally)) - set(avoiding_sectors)) == 0:
            return None
    retval = None
    # Find a shortest-distance route first
    # If there aren't any, find routes that are 1 longer, etc.
    while (retval == None) and (route_length < max_length):
        #print "In a_route(%d,%d,...,%s) - looking for route of length %d" % (from_sector, to_sector, str(avoiding_sectors), route_length)
        retval = a_route_of_length(route_length,
                                   from_sector,
                                   to_sector,
                                   can_move_diagonally,
                                   missing_links,
                                   avoiding_sectors)
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

def accessible_sectors(from_sector,
                       can_move_diagonally,
                       missing_links={},
                       avoiding_sectors=[],
                       drones=[],
                       max=max_route_length):
    '''
    Figure out which sectors can be reached from the specified start sector.
    Returns a set of sectors.
    '''
    # Is start_sector accessible ?
    if from_sector in avoiding_sectors:
        return set()
    retval = set([from_sector])
    # Now keep adding adjacent accessible sectors that aren't already in the list
    # until there are no more sectors to check
    for d in range(0, max):
        new_retval = retval.copy()
        for sector in retval:
            try:
                missing = missing_links[sector]
            except KeyError:
                missing = []
            for adj in adjacent_sectors(sector, can_move_diagonally):
                if adj not in avoiding_sectors and adj not in missing:
                    new_retval.add(adj)
        retval = new_retval
    return retval


HOSTILITY_RE = re.compile('<B>PvP Hostility Level:</B> ([-\d]*) \(PvP:(\d*) - PsP:(\d*)\)')
POWERUPS_RE = re.compile('<B>Powerup Distribution:</B> (\d*)%')
MILITARY_CONTROL_RE = re.compile('<B>MILITARY CONTROL:</B><BR> ([^<]*)<BR>')
MAJORITY_AVG_RE = re.compile('<b>Majority AVG:</b> (\d*)% of (\d*) HOURS')
UNIVERSAL_ALIGNMENT_RE = re.compile('<B>UNIVERSAL ALIGNMENT:</B><BR> ([^<]*)<BR>')
YIN_RE = re.compile('<B>Yin: </B>(\w*) ')
YANG_RE = re.compile('<B>Yang: </B>(\w*) ')
HIGH_RE = re.compile('<B>High:</B> (\d*)')

WARP_RE = re.compile('<br>IR Warp from #(\d*) to #(\d*) \((\d*) fuel\)')
JELLYFISH_RE = re.compile('Space Jellyfish in sector!')
BLACKHOLE_RE = re.compile('Black Hole in sector!')
TRADING_PORT_RE = re.compile('(Trader .* Trading Port #\d*)')
BUYING_RE = re.compile('Buying:</b> ([^<]*)')
SELLING_RE = re.compile('Selling:</b> ([^<]*)')
LAST_DENSITY_RE = re.compile('Last Recorded Density: ([^<]*)')
PLANET_RE = re.compile('Planet:</b> ([^<]*)')
LINKS_RE = re.compile('Links To: ([0-9, ]*)')
PORT_ALIGNMENT_RE = re.compile('Alignment: ([^<.]*)')
NPC_STORE_RE = re.compile('NPC Store:</b> ([^<]*)')
IPT_RE = re.compile('Emergency IPT</b> to ([^<]*)')
LUVSAT_RE = re.compile('LuvSat in sector!')
ASTEROID_RE = re.compile('There is an asteroid in this sector:</b><br>(\S*) Ore')
PORT_GE_OC_RE = re.compile('GE: ([\d-]*) OC: ([\d-]*)')
DRONES_RE = re.compile('<b>Drones:</b> ([^<]*)')
YOUR_DRONES_RE = re.compile('Your Drones:</b> ([^<]*)')
NAME_RE = re.compile('<b>(.*?)</b><br>')
NOTES_RE = re.compile('<p><i>(.*)</i></p>')

PRICE_RE = re.compile('(\S*) Ore \((\d*) SB\)')
LINK_RE = re.compile('(\d*)')
DENSITY_RE = re.compile('Density: (\d*)')
CONTENT_RE = re.compile('(.*) \((\d*)\)')

TELEPORTER_RE = re.compile('(.*) \((\d*)\)')

class SectorMapParser():
    '''
    Class to parse the sector map
    '''
    def __init__(self, page):
        self.soup = BeautifulSoup(page)

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
        self.density = {}
        self.last_density = {}
        self.names = {}
        self.notes = {}
        self.warp_costs = {}

        self.parse_soup(self.soup)

        # This is fairly arbitrary - a balance between time taken and accuracy
        self.max_distance = 15
        # Populated on-demand in self.distances()
        self.the_distances = None

    def _add_warp_cost(self, start, end, fuel):
        '''
        Add a warp cost to self.warp_costs, overwriting any existing value
        '''
        if start not in self.warp_costs:
            self.warp_costs[start] = {}
        self.warp_costs[start][end] = fuel

    def warp_cost(self, start_sector, end_sector):
        '''
        Returns the fuel cost for a warp between the two specified sectors, if known.
        Returns None for "unknown".
        '''
        if start_sector == end_sector:
            return 0
        try:
            d = self.warp_costs[start_sector]
        except KeyError:
            return None
        try:
            return d[end_sector]
        except KeyError:
            return None

    def distances(self):
        '''
        Return a list, indexed by distance (up to self.max_distance), of
        lists, indexed by sector, of lists of sectors that are within the
        specified distance of the specified sector.
        '''
        # TODO the_distances is derived from missing_links, which is
        # fixed for a given map, so in theory at least we could
        # calculate this once and store it in a file somewhere
        if not self.the_distances:
            self.the_distances = self.distances_array(self.max_distance)
        return self.the_distances

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

    def parse_prices(self, text):
        """Parse a price list into a dict"""
        result = {}
        for m in PRICE_RE.finditer(text):
            result[m.group(1)] = int(m.group(2))
        return result

    def parse_links(self, text):
        """Parse a string with a list of links into an actual list"""
        result = []
        for m in LINK_RE.finditer(text):
            try:
                result.append(int(m.group(1)))
            except ValueError:
                pass
        return result

    def parse_universe_state_popup(self, popup):
        """Parse all the universe info from 'popup'."""
        m = HOSTILITY_RE.search(popup)
        if m:
            self.pvp_hostility = int(m.group(1))
            self.pvps = int(m.group(2))
            self.psps = int(m.group(3))
            assert self.pvp_hostility == self.pvps - self.psps
        m = POWERUPS_RE.search(popup)
        if m:
            self.powerups_percentage = int(m.group(1))
            # Note that "powerups percentage" can exceed 100%
        m = MILITARY_CONTROL_RE.search(popup)
        if m:
            self.military_control = m.group(1)
            assert self.military_control in ssw_societies.full_names
        m = MAJORITY_AVG_RE.search(popup)
        if m:
            self.control_percentage = int(m.group(1))
            assert self.control_percentage < 101
            self.control_hours = int(m.group(2))
        m = UNIVERSAL_ALIGNMENT_RE.search(popup)
        if m:
            self.universal_alignment = m.group(1)
            assert self.universal_alignment in ssw_societies.full_names
        m = YIN_RE.search(popup)
        if m:
            self.yin = m.group(1)
        m = YANG_RE.search(popup)
        if m:
            self.yang = m.group(1)
        m = HIGH_RE.search(popup)
        if m:
            self.high = int(m.group(1))

    def parse_sector_popup(self, popup, num):
        """Parse all the info about sector 'num' from 'popup'."""
        ore_buys = []
        ore_sells = []
        # Find any buy prices
        m = BUYING_RE.search(popup)
        if m:
            prices = self.parse_prices(m.group(1))
            for ore,cost in six.iteritems(prices):
                if not ore in self.ores_bought:
                    self.ores_bought[ore] = []
                self.ores_bought[ore].append((cost, num))
                ore_buys.append((ore, cost))
        # And any sell prices
        m = SELLING_RE.search(popup)
        if m:
            prices = self.parse_prices(m.group(1))
            for ore,cost in six.iteritems(prices):
                if not ore in self.ores_sold:
                    self.ores_sold[ore] = []
                self.ores_sold[ore].append((cost, num))
                ore_sells.append((ore, cost))
        # Is there a warp fuel cost ?
        m = WARP_RE.search(popup)
        if m:
            start = int(m.group(1))
            end = int(m.group(2))
            fuel = int(m.group(3))
            self._add_warp_cost(start, end, fuel)
            # TODO If warp costs are always the same both ways, populate both here
        # Are there jellyfish ?
        if JELLYFISH_RE.search(popup):
            self.jellyfish.append(num)
        # Is there a Luvsat ?
        if LUVSAT_RE.search(popup):
            self.luvsats.append(num)
        # A black hole ?
        if BLACKHOLE_RE.search(popup):
            self.black_holes.append(num)
        # A planet ?
        m = PLANET_RE.search(popup)
        if m:
            self.planets.append((m.group(1), num))
        # What's the last recorded density ?
        # Note that things may have moved around since this was recorded
        m = LAST_DENSITY_RE.search(popup)
        if m:
            self.known_sectors += 1
            self.last_density[num] = int(m.group(1))
        else:
            self.unknown_sectors.append(num)
        # What links are there ?
        m = LINKS_RE.search(popup)
        if m:
            links = self.parse_links(m.group(1))
            for s in adjacent_sectors(num, self.can_move_diagonally()):
                if s not in links:
                    if not num in self.missing_links:
                        self.missing_links[num] = []
                    self.missing_links[num].append(s)
        # Trading port alignment ?
        m = PORT_ALIGNMENT_RE.search(popup)
        if m:
            port_alignment = m.group(1)
        m = PORT_GE_OC_RE.search(popup)
        if m:
            good = int(m.group(1))
            order = int(m.group(2))
        # Any NPC stores ?
        m = NPC_STORE_RE.search(popup)
        if m:
            self.npc_stores.append((m.group(1), num))
        # Any IPTs ?
        m = IPT_RE.search(popup)
        if m:
            self.ipts.append((m.group(1), num))
        # Any asteroids ?
        m = ASTEROID_RE.search(popup)
        if m:
            self.asteroids.append((m.group(1), num))
        # Any drones ?
        m = DRONES_RE.search(popup)
        if m:
            self.drones.append((m.group(1), num))
        m = YOUR_DRONES_RE.search(popup)
        if m:
            self.your_drones.append((int(m.group(1)), num))
        # A trading port ?
        # Relies on having already parsed port prices, alignment, etc
        m = TRADING_PORT_RE.search(popup)
        if m:
            port_name = m.group(1)
            port = TradingPort(port_name,
                               num,
                               good,
                               order,
                               ore_buys,
                               ore_sells)
            # port_alignment should be what we derive from GE/OC
            assert port_alignment == ssw_societies.full_name(port.society_initial()), "port_alignment = %s, not %s" % (port_alignment, ssw_societies.full_name(port.society_initial()))
            self.trading_ports.append(port)
        m = NAME_RE.search(popup)
        if m:
            self.names[num] = m.group(1)
        m = NOTES_RE.search(popup)
        if m:
            self.notes[num] = m.group(1)

    def ipt_in_sector(self, sector):
        '''
        Returns the destination of any IPT in the sector, or None.
        '''
        for p,s in self.ipts:
            if s == sector:
                return p
        return None

    def planet_in_sector(self, sector):
        '''
        Returns the name of any planet in the sector, or None.
        '''
        for n,s in self.planets:
            if s == sector:
                return n
        return None

    def asteroid_in_sector(self, sector):
        '''Returns the ore of any asteroid in the sector, or None'''
        for asteroid in self.asteroids:
            if asteroid[1] == sector:
                return asteroid
        return None

    def black_hole_in_sector(self, sector):
        ''' Returns True if there is a black hole in the sector, False otherwise'''
        return sector in self.black_holes

    def npc_store_in_sector(self, sector):
        ''' Returns the name of any NPC store in the sector, or None'''
        for store in self.npc_stores:
            if store[1] == sector:
                return store
        return None

    def jellyfish_in_sector(self, sector):
        ''' Returns True if there are space jellyfish in the sector, False otherwise'''
        return sector in self.jellyfish

    def luvsat_in_sector(self, sector):
        ''' Returns True if there is a luvsat in the sector, False otherwise'''
        return sector in self.luvsats

    def trading_port_in_sector(self, in_sector):
        '''
        Returns the trading port (if any) in the specified sector
        '''
        for port in self.trading_ports:
            if port.sector == in_sector:
                return port
        return None

    def sector_of_planet(self, name):
        '''
        Returns the sector containing the specified planet, or None.
        '''
        for n,s in self.planets:
            if n == name:
                return s
        return None

    def sector_density(self, sector):
        '''
        Returns the calculated density of the specified sector
        (for the last recorded density, if any, just access self.last_density[sector])
        '''
        density = 0
        for item in self.density.keys():
            if item == u'planet':
                if self.planet_in_sector(sector):
                    density += self.density[item]
            elif item == u'asteroid':
                if self.asteroid_in_sector(sector):
                    density += self.density[item]
            elif item == u'black hole':
                if self.black_hole_in_sector(sector):
                    density += self.density[item]
            elif item == u'npc store':
                if self.npc_store_in_sector(sector):
                    density += self.density[item]
            elif item == u'space jellyfish':
                if self.jellyfish_in_sector(sector):
                    density += self.density[item]
            elif item == u'trading port':
                if self.trading_port_in_sector(sector):
                    density += self.density[item]
            elif item == u'ipt beacon':
                if self.ipt_in_sector(sector):
                    density += self.density[item]
            elif item == u'luvsat':
                if self.luvsat_in_sector(sector):
                    density += self.density[item]
            else:
                print("Unexpected item type %s" % item)
        # TODO Add in drones, if any
        return density

    def parse_soup(self, soup):
        '''
        Internal - parse the soup created from the map file
        '''
        # Find the span with overall universe info
        for span in soup.body.find_all('span'):
            # Ignore new spans that aren't what we're after
            if 'onmouseover' in span.attrs:
                # Extract the map's date
                self.extract_date(six.text_type(span.contents[0].string))
                # parse out more interesting information
                popup = span.attrs['onmouseover']
                self.parse_universe_state_popup(popup)

        # Parse the number of each thing we know about
        for td in soup.body.find_all('td', width='8'):
            m = DENSITY_RE.search(td.div.attrs['title'])
            if m:
                density = int(m.group(1))
            for td2 in td.next_siblings:
                m = CONTENT_RE.search(six.text_type(td2.string))
                if m:
                    item = m.group(1).lower()
                    item_count = int(m.group(2))
                    break
            self.expected_totals[item] = item_count
            self.density[item] = density

        # Iterate through each sector
        for td in soup.body.find_all('td', width='4%'):
            # Find the sector number
            link = td.find('a')
            sector = int(six.text_type(link.string))
            # Find the popup text
            div = td.find('div')
            popup = div.attrs['onmouseover']
            # Parse the popup and store the result
            self.parse_sector_popup(popup, sector)
            # Parse the sector colour
            self.extract_explored(link.attrs['style'], sector)

        # Find the teleporter dropdown
        for form in soup.body.find_all('form'):
            if form.attrs['name'] == 'telform':
                teleporter = form
                for option in teleporter.find_all('option'):
                    m = TELEPORTER_RE.search(option.string)
                    if m:
                        planet = m.group(1)
                        sector = int(m.group(2))
                        if (planet, sector) not in self.planets:
                            # TODO What should we do here ?
                            print("Telporter menu item %s (%d) not found in map" % (planet, sector))

    # TODO Can these three methods be merged together ?
    def enhance_map_with_planets(self, expected_planets):
        '''
        Adds any missing planets to the map.
        '''
        if len(self.planets) < len(expected_planets):
            unknown_planets = [planet for planet in expected_planets if planet not in self.planets]
            self.planets += unknown_planets
            print("Added %d planet(s) - %s" % (len(unknown_planets),
                                               str(unknown_planets)))
            for name, sector in unknown_planets:
                if (sector not in self.unknown_sectors) and (sector not in self.forgotten_sectors):
                    print("*** Added planet %s to known sector %d. Out-of-date planet list ?" % (name, sector))

    def enhance_map_with_npc_stores(self, expected_npc_stores):
        '''
        Adds any missing NPC stores to the map.
        '''
        # TODO We end up with duplicates because of weird apostrophes in some names
        # For now, leave the list alone. Nothing currently uses it anyway
        return
        if len(self.npc_stores) < len(expected_npc_stores):
            unknown_npc_stores = [npc_store for npc_store in expected_npc_stores if npc_store not in self.npc_stores]
            self.npc_stores += unknown_npc_stores
            print("Added %d NPC store(s) - %s" % (len(unknown_npc_stores),
                                                  str(unknown_npc_stores)))
            for name, sector in unknown_npc_stores:
                if (sector not in self.unknown_sectors) and (sector not in self.forgotten_sectors):
                    print("*** Added NPC store %s to known sector %d. Out-of-date NPC store list ?" % (name, sector))

    def enhance_map_with_asteroids(self, expected_asteroids):
        '''
        Adds any missing asteroids to the map.
        '''
        if len(self.asteroids) < len(expected_asteroids):
            unknown_asteroids = [asteroid for asteroid in expected_asteroids if asteroid not in self.asteroids]
            self.asteroids += unknown_asteroids
            print("Added %d asteroid(s) - %s" % (len(unknown_asteroids),
                                                 str(unknown_asteroids)))
            for name, sector in unknown_asteroids:
                if (sector not in self.unknown_sectors) and (sector not in self.forgotten_sectors):
                    print("*** Added asteroid %s to known sector %d. Out-of-date asteroid list ?" % (name, sector))

    def enhance_map_with_trading_ports(self, expected_trading_ports):
        '''
        Adds any missing trading ports to the map.
        '''
        if len(self.trading_ports) < len(expected_trading_ports):
            unknown_trading_ports = [port for port in expected_trading_ports if not self.trading_port_in_sector(port.sector)]
            self.trading_ports += unknown_trading_ports
            print("Added %d trading port(s) - %s" % (len(unknown_trading_ports),
                                                     '[' + ', '.join([port.name for port in unknown_trading_ports]) + ']'))
            for port in unknown_trading_ports:
                if (port.sector not in self.unknown_sectors) and (port.sector not in self.forgotten_sectors):
                    print("*** Added trading port %s to known sector %d. Out-of-date trading port list ?" % (port.name, port.sector))

    def enhance_map(self):
        '''
        Adds known info to a partially-populated map.
        Can include black holes, NPC stores and planets, because they all stay put (more-or-less).
        Missing links, asteroids and trading ports move at reset, so we may also know where they are.
        IPTs, jellyfish and luvsats move daily, so nothing is added regarding those.
        If the map is for today, it also retrieves the lists of planets, NPC stores, asteroids,
        and trading ports from the databuddy and enhances the map with those, too.
        '''
        self.enhance_map_with_planets(self.expected_planets())

        if len(self.black_holes) < len(expected_black_holes):
            unknown_black_holes = [black_hole for black_hole in expected_black_holes if black_hole not in self.black_holes]
            self.black_holes += unknown_black_holes
            print("Added %d black hole(s)" % len(unknown_black_holes))

        self.enhance_map_with_npc_stores(self.expected_npc_stores())

        if len(self.missing_links) < len(self.expected_missing_links()):
            unknown_missing_links = [(sector,links) for sector,links in six.iteritems(self.expected_missing_links()) if sector not in self.missing_links]
            for sector, links in unknown_missing_links:
                self.missing_links[sector] = links
            print("Added %d missing link(s)" % len(unknown_missing_links))

        # If it's today's map, we can also pull info from the databuddy
        if (ssw_utils.now_in_ssw() - self.datetime) > datetime.timedelta(1):
            return

        p = ssw_get_planets.get_planets()
        self.enhance_map_with_planets(p)

        s = ssw_get_stores.get_npc_stores()
        self.enhance_map_with_npc_stores(s)

        a = ssw_get_asteroids.get_asteroids()
        self.enhance_map_with_asteroids(a)

        # TODO the prices here will reflect what you're currently wearing,
        # while those from the map will reflect what you were wearing at the time
        # it was captured. We should probably check for disparities and address them.
        t = ssw_get_trading_ports.get_trading_ports()
        self.enhance_map_with_trading_ports(t)

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
        for key,value in six.iteritems(self.expected_totals):
            if key == 'planets':
                if len(self.planets) != value:
                    return False,'Expected %d planets, found %d' % (value,
                                                                    len(self.planets))
            elif key == 'asteroid':
                if len(self.asteroids) != value:
                    return False,'Expected %d asteroids, found %d' % (value,
                                                                      len(self.asteroids))
            elif key == 'black hole':
                if len(self.black_holes) != value:
                    return False,'Expected %d black holes, found %d' % (value,
                                                                        len(self.black_holes))
            elif key == 'npc store':
                if len(self.npc_stores) != value:
                    return False,'Expected %d npc stores, found %d' % (value,
                                                                       len(self.npc_stores))
            elif key == 'space jellyfish':
                if len(self.jellyfish) != value:
                    return False,'Expected %d jellyfish, found %d' % (value,
                                                                      len(self.jellyfish))
            elif key == 'trading port':
                if len(self.trading_ports) != value:
                    return False,'Expected %d trading ports, found %d' % (value,
                                                                          len(self.trading_ports))
            elif key == 'ipt beacon':
                if len(self.ipts) != value:
                    return False,'Expected %d IPT beacons, found %d' % (value,
                                                                        len(self.ipt_beacons))
            elif key == 'luvsat':
                if len(self.luvsats) != value:
                    return False,'Expected %d luvsats, found %d' % (value,
                                                                    len(self.luvsats))

        if not quiet:
            # These are more tests of this code than tests of the map file itself,
            # but this is the one place we know will be called once after parsing
            for sector in set(self.expected_missing_links()) - set(self.missing_links):
                if sector not in self.unknown_sectors + self.forgotten_sectors:
                    print("WARNING Didn't find expected missing links from sector %d" % (sector))
            for sector in set(self.missing_links) - set(self.expected_missing_links()):
                print("WARNING Didn't expect to find missing links in sector %d" % (sector))
            for planet, sector in set(self.expected_planets()) - set(self.planets):
                if sector not in self.unknown_sectors + self.forgotten_sectors:
                    print("WARNING Planet %s is missing from sector %d" % (planet, sector))
            for planet, sector in set(self.planets) - set(self.expected_planets()):
                if ((planet, sector) not in temporary_planets) and ((planet, None) not in temporary_planets):
                    print("WARNING Didn't expect to find planet %s in sector %d" % (planet, sector))
            if self.expected_asteroids() < len(self.asteroids):
                print("WARNING: code expects fewer asteroids")
            elif self.expected_asteroids() > len(self.asteroids) + len(self.unknown_sectors) + len(self.forgotten_sectors):
                print("WARNING: code expects more asteroids")
            for sector in set(expected_black_holes) - set(self.black_holes):
                if sector not in self.unknown_sectors + self.forgotten_sectors:
                    print("WARNING Black hole is missing from sector %d" % (sector))
            for sector in set(self.black_holes) - set(expected_black_holes):
                print("WARNING Didn't expect to find black hole in sector %d" % (sector))
            for store, sector in set(self.expected_npc_stores()) - set(self.npc_stores):
                if sector not in self.unknown_sectors + self.forgotten_sectors:
                    print("WARNING NPC store %s is missing from sector %d" % (store, sector))
            for store, sector in set(self.npc_stores) - set(self.expected_npc_stores()):
                print("WARNING Didn't expect to find NPC store %s in sector %d" % (store, sector))
            if expected_jellyfish < len(self.jellyfish):
                print("WARNING: code expects fewer jellyfish")
            elif expected_jellyfish > len(self.jellyfish) + len(self.unknown_sectors) + len(self.forgotten_sectors):
                print("WARNING: code expects more jellyfish")
            if expected_trading_ports < len(self.trading_ports):
                print("WARNING: code expects fewer trading ports")
            elif expected_trading_ports > len(self.trading_ports) + len(self.unknown_sectors) + len(self.forgotten_sectors):
                print("WARNING: code expects more trading ports")
            if expected_ipts < len(self.ipts):
                print("WARNING: code expects fewer IPT beacons")
            elif expected_ipts > len(self.ipts) + len(self.unknown_sectors) + len(self.forgotten_sectors):
                print("WARNING: code expects more IPT beacons")
            if expected_luvsats < len(self.luvsats):
                print("WARNING: code expects fewer luvsats")
            elif expected_luvsats > len(self.luvsats) + len(self.unknown_sectors) + len(self.forgotten_sectors):
                print("WARNING: code expects more luvsats")
            for planet, sector in self.ipts:
                if (planet, self.sector_of_planet(planet)) not in self.planets:
                    print("WARNING: IPT in sector %d goes to unknown planet %s" % (sector, planet))

        # If we get here, all is good
        return True,''

    def extract_date(self, text):
        '''
        Internal - Extracts the date of the map
        '''
        #text = text.replace('\xa0', ' ')
        text = text.replace('&nbsp;', ' ')
        temp = text.find('UTC:')
        assert temp > -1, text
        words = text[temp:].split()
        self.datetime = datetime.datetime(int(words[4].split('<')[0]),
                                          int(months[words[2]]),
                                          int(words[3][:-1]),
                                          int(words[1][:-3]),
                                          int(words[1][3:]))
        #print "Map for " + str(self.datetime)

    def extract_explored(self, text, num):
        '''
        Internal - Figures out from the sector colour whether it has been explored,
                   never visited, or forgotten
        '''
        # TODO self.sector_colour seems to be write-only
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
            assert num in self.last_density
            self.known_sectors -= 1
            self.forgotten_sectors.append(num)
        elif (colour == "153, 153, 153") or (colour == "#999999;"):
            # Never explored
            self.sector_colour = 'dark grey'
            assert num not in self.last_density
        elif (colour == "255, 204, 0") or (colour == "#ffcc00;"):
            self.sector_colour = 'yellow'
        # We want to be able to parse HTML files that aren't SSW maps,
        # but we also want to notice when sector colours change...
        elif num != 0:
            assert 0, 'Unrecognised sector colour ' + colour + ' in sector ' + str(num)

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

    def route_traverses_unexplored_sectors(self, route):
        '''
        Will we pass through unexplored or forgotten sectors on a route ?
        Return True or False.
        '''
        for sector in route:
            if (sector in self.unknown_sectors) or (sector in self.forgotten_sectors):
                return True
        return False

    def distances_array(self, max_distance):
        '''
        Return a dict, indexed by distance (up to max_distance) of dicts
        indexed by sector of lists of sectors that are the specified distance
        from the starting sector.
        '''
        retval = {}
        # Note that we only include flying distances, not via IPT or planets
        for d in range(0, max_distance+1):
            per_sector = {}
            for s in all_sectors:
                per_sector[s] = set()
                if d == 0:
                    per_sector[s].add(s)
                elif d == 1:
                    # For every sector we can get to in one less move, add all
                    # the sectors we can get to in one move
                    for s1 in retval[d-1][s]:
                        for s2 in accessible_sectors(s1,
                                                     self.can_move_diagonally(),
                                                     self.missing_links,
                                                     max=1):
                            per_sector[s].add(s2)
                else:
                    # We can do that faster if we've already populated retval[1]
                    for s1 in retval[d-1][s]:
                        per_sector[s].update(retval[1][s1])
            retval[d] = per_sector
        return retval

    def nearest(self,
                to_sector,
                planets_or_ipts,
                max_length,
                for_society=None,
                unexplored_sector_society=None):
        '''
        Internal - Where's the nearest planet/IPT to a sector ?
        Returns a tuple of (name, sector, distance, drones en route, possible drones)
        where "possible drones" is True if the route traverses sectors where we don't know
        whether drones are present or not.
        This is really just the code common to nearest_planet() and nearest_ipt()
        Check for it returning None for the sector to see whether it found one.
        Note that we assume that direction doesn't matter
        '''
        route = None
        enemy_drones = self.enemy_drones(for_society, unexplored_sector_society)
        for d in range(0, self.max_distance+1):
            #print("nearest(%d) - checking distance %d" % (to_sector, d))
            for name, sector in planets_or_ipts:
                if sector in self.distances()[d][to_sector]:
                    #print("nearest() checking %s in %d" % (name, sector))
                    #print("nearest(%d) checking %s in sector %d at distance %d" % (to_sector, name, sector, d+1))
                    drones = []
                    # find drones en route
                    # Unfortunately, we have to find the actual route
                    # Sometimes the route is blocked by drones, so we have to keep looking
                    # TODO Probably need to check all routes of that length
                    route = a_route(sector,
                                    to_sector,
                                    self.can_move_diagonally(),
                                    self.missing_links,
                                    enemy_drones,
                                    min_length = d)
                    #print("nearest() checking route %s" % route)
                    if route == None:
                        continue
                    drones = drones_en_route(route, self.drones)
                    return (name, sector, d, drones, self.route_traverses_unexplored_sectors(route))
        return ("", None, max_length, [], False)

    def nearest_planet(self,
                       to_sector,
                       max_length=max_route_length,
                       for_society=None,
                       unexplored_sector_society=None):
        '''
        Where's the nearest planet to a sector ?
        Returns a tuple of (planet name, sector, distance, drones en route, possible drones)
        where "possible drones" is True if the route traverses sectors where we don't know
        whether drones are present or not.
        '''
        (name, sector, distance, drones, possible) = self.nearest(to_sector,
                                                                  self.planets,
                                                                  max_length,
                                                                  for_society,
                                                                  unexplored_sector_society)
        # For nearest planet, we want to go from the planet to the sector,
        # but "nearest" does the opposite, so we need to allow for drones
        # at the sector of interest, too
        return (name,
                sector,
                distance,
                drones + drones_en_route([to_sector],
                                         self.drones),
                possible or self.route_traverses_unexplored_sectors([to_sector]))
 
    def nearest_ipt(self,
                    to_sector,
                    max_length=max_route_length,
                    for_society=None,
                    unexplored_sector_society=None):
        '''
        Where's the nearest IPT to a sector ?
        Returns a tuple of (IPT destination, sector, distance, drones en route, possible drones)
        where "possible drones" is True if the route traverses sectors where we don't know
        whether drones are present or not.
        '''
        temp = self.nearest(to_sector,
                            self.ipts,
                            max_length,
                            for_society,
                            unexplored_sector_society)
        return temp

    def nearest_planet_or_ipt(self,
                              to_sector,
                              max_length=max_route_length,
                              for_society=None,
                              unexplored_sector_society=None):
        '''
        Where's the nearest planet or IPT to a sector ?
        Returns a tuple of (IPT dest or planet name, sector, distance, drones en route, possible drones)
        where "possible drones" is True if the route traverses sectors where we don't know
        whether drones are present or not.
        '''
        (ipt_dest, ipt_sector, ipt_dist, ipt_drones, ipt_poss) = self.nearest_ipt(to_sector,
                                                                                  max_length,
                                                                                  for_society,
                                                                                  unexplored_sector_society)
        (planet_name, planet_sector, planet_dist, planet_drones, planet_poss) = self.nearest_planet(to_sector,
                                                                                                    max_length,
                                                                                                    for_society,
                                                                                                    unexplored_sector_society)
        if ipt_dist < planet_dist:
            return (ipt_dest, ipt_sector, ipt_dist, ipt_drones, ipt_poss)
        else:
            return (planet_name, planet_sector, planet_dist, planet_drones, ipt_drones)

    def shortest_distance(self,
                          from_sector,
                          to_sector,
                          for_society=None,
                          unexplored_sector_society=None,
                          max_length=max_route_length):
        '''
        How long to get between the two sectors by the shortest route ?
        Returns a tuple with (the distance, None or a tuple of via sectors,
        list of drones en route, possible drones)
        where "possible drones" is True if the route traverses sectors where we don't know
        whether drones are present or not.
        Distance will be None if there's no route between the two
        '''
        enemy_drones = self.enemy_drones(for_society,
                                         unexplored_sector_society)
        # Short-circuiting at this point saves an awful lot of effort when there are lots of drones around
        # Otherwise, we can get hung up trying to find a route between a planet or IPT and a drone-free sector
        if (for_society != None):
            if (from_sector in enemy_drones) or (to_sector in enemy_drones):
                return (None, None, None)
        # Could go via a planet
        (dest_name, dest_sector, dest_dist, dest_drones, dest_poss) = self.nearest_planet(to_sector,
                                                                                          max_length,
                                                                                          for_society,
                                                                                          unexplored_sector_society)
        # If we can't get to the destination from a planet,
        # there's no point looking for a route from the source to a planet or IPT
        if (dest_sector == None):
            (via_dest, via_sector, via_dist, via_drones, via_poss) = ('',
                                                                      None,
                                                                      sectors_per_row,
                                                                      [],
                                                                      False)
        else:
            (via_dest, via_sector, via_dist, via_drones, via_poss) = self.nearest_planet_or_ipt(from_sector,
                                                                                                max_length,
                                                                                                for_society,
                                                                                                unexplored_sector_society)
        # Flying distance can't be less than direct distance
        if (via_dist + dest_dist) < direct_distance(from_sector, to_sector):
            return (via_dist + dest_dist,
                    (via_sector, dest_sector),
                    via_drones + dest_drones,
                    via_poss or dest_poss)
        # or, could just fly between the two
        fly_dist = None
        fly_drones = []
        fly_poss = False
        for d in range(0, self.max_distance+1):
            #print "shortest_distance(%d,%d) - checking distance %d" % (from_sector, to_sector, d)
            if to_sector in self.distances()[d][from_sector]:
                #print "shortest_distance() found it"
                fly_dist = d
                #print "shortest_distance(%d,%d) - fly_dist = %d" % (from_sector, to_sector, d)
                if len(self.drones):
                    # Unfortunately, we have to find the exact route to
                    # figure out fly_drones
                    # Sometimes a route is blocked by drones so we have to keep looking
                    # TODO Probably need to check all routes of that length
                    route = a_route(from_sector,
                                    to_sector,
                                    self.can_move_diagonally(),
                                    self.missing_links,
                                    enemy_drones,
                                    min_length = d)
                    if route == None:
                        continue
                    fly_drones = drones_en_route(route, self.drones)
                    fly_poss = self.route_traverses_unexplored_sectors(route)
                break
        if (dest_sector == None) or (via_sector == None):
            # There's no route between the two via a planet
            # fly_dist is either None or the quickest route
            return (fly_dist, None, fly_drones, fly_poss)
        if (fly_dist == None) or ((via_dist + dest_dist) < fly_dist):
            # Going via a planet is quickest (or the only possible way)
            return (via_dist + dest_dist,
                    (via_sector, dest_sector),
                    via_drones + dest_drones,
                    via_poss or dest_poss)
        # Going direct is quickest
        return (fly_dist, None, fly_drones, fly_poss)

    def shortest_route(self,
                       from_sector,
                       to_sector,
                       for_society=None,
                       unexplored_sector_society=None,
                       max_length=max_route_length):
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
            enemy_drones = self.enemy_drones(for_society,
                                             unexplored_sector_society)
            if (from_sector in enemy_drones) or (to_sector in enemy_drones):
                return (sectors_per_row, fail_str, [])

        (start_planet, start_sector, start_dist, start_drones, start_poss) = self.nearest_planet(from_sector,
                                                                                                 max_length,
                                                                                                 for_society,
                                                                                                 unexplored_sector_society)
        # If we can't get to from_sector from a planet,
        # there's no point looking for the rest of the route
        if (start_sector == None):
            (end_name, end_sector, end_dist, end_drones, end_poss) = ('', None, sectors_per_row, [], False)
        else:
            (end_name, end_sector, end_dist, end_drones, end_poss) = self.nearest_planet_or_ipt(to_sector,
                                                                                                max_length,
                                                                                                for_society,
                                                                                                unexplored_sector_society)
        # Similarly, if we can't get back from to_sector,
        # there's no point looking for a route to to_sector
        if (end_sector == None):
           (dist, route, drones, poss) = (None, [], [], False)
        else:
           (dist, route, drones, poss) = self.shortest_distance(from_sector,
                                                                to_sector,
                                                                for_society,
                                                                unexplored_sector_society,
                                                                max_length)
        if dist == None:
            return (sectors_per_row, fail_str, [], False)
        if start_sector == None:
            return (sectors_per_row, "No route to %d%s" % (to_sector, soc_str), [], False)
        if end_sector == None:
            return (sectors_per_row, "No route out of %d%s" % (from_sector, soc_str), [], False)
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
            return (moves,
                    "%d %s - %s (%d), to %d, to %d (%s)" % (moves,
                                                            move_str,
                                                            start_planet,
                                                            start_sector,
                                                            from_sector,
                                                            end_sector,
                                                            end_name),
                    start_drones + drones + end_drones,
                    start_poss or poss or end_poss)
        return (moves,
                "%d %s - %s (%d), to %d, %s to %d, to %d (%s)" % (moves,
                                                                  move_str,
                                                                  start_planet,
                                                                  start_sector,
                                                                  from_sector,
                                                                  route_str,
                                                                  to_sector,
                                                                  end_sector,
                                                                  end_name),
                start_drones + drones + end_drones,
                start_poss or poss or end_poss)

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

