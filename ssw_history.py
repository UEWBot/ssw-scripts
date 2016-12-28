#!/usr/bin/python

'''
Script to print out some SSW history
'''

# Copyright 2011, 2015-2016 Squiffle

from __future__ import absolute_import
from __future__ import print_function
import ssw_sector_map2 as ssw_sector_map
import ssw_utils
import operator, sys, getopt, datetime
from six.moves import map
from six.moves import range

version = 1.00

# We assume this to be the start of SSW itself
cycle_1_start = ssw_sector_map.cycle_start[1]

def usage(progname):
    '''
    Tell them how to run the program
    '''
    print("Usage: %s [-h]" % progname)
    print()
    print(" Secret Society Wars history")
    print()
    print("  -h|--help - print usage and exit")
    print()
    print(" Version %.2f. Brought to you by Squiffle" % version)

def ssw_was_running(date):
    '''
    True if the server was actually up.
    '''
    server_up = date >= cycle_1_start
    server_up = server_up and ((date < ssw_sector_map.shutdown_datetime)
                                or (date > ssw_sector_map.reboot_datetime))
    return server_up

def server_shutdowns():
    '''
    The dates of server shutdowns and restarts.
    '''
    retval = []
    retval.append((ssw_sector_map.shutdown_datetime.date(), "SSW was shut down"))
    retval.append((ssw_sector_map.reboot_datetime.date(), "SSW came back from the dead"))
    return retval

def cycle_dates():
    '''
    The date of each cycle
    Returns a list of (date, event string) tuples
    '''
    retval = []
    starts = ssw_sector_map.cycle_start
    ends = ssw_sector_map.war_end
    for cycle in range(1, len(starts)):
        start = starts[cycle]
        retval.append((start.date(), "Cycle %d started" % cycle))
        try:
            war_end = ends[cycle]
        except IndexError:
            # This cycle is still ongoing
            war_end = ssw_utils.now_in_ssw()
            state_str = "ongoing"
        else:
            state_str = "ended"
        length = war_end - start
        retval.append((war_end.date(),
                       "War %d %s, after %d days" % (cycle, state_str, length.days)))
    return retval

def space_changes():
    '''
    When space had a major rework
    Returns a list of (date, event string) tuples
    '''
    retval = [(ssw_sector_map.space_mazified_datetime.date(),
               "Space became a maze"),
              (ssw_sector_map.space_rework_datetime.date(),
               "Space was changed substantially, including moving planets and NPC stores")]
    retval.sort()
    return retval

def changes(before, after, date):
    '''
    Compares the 'before' and 'after' lists, identifying any changes between the two.
    Returns a list of (date, change_string) tuples describing the changes.
    'before' and 'after' should both be lists of (item, sector) tuples.
    '''
    retval = []
    # Filter out all the items that are in both lists
    only_before = set(before) - set(after)
    only_after = set(after) - set(before)
    # Go through all the unique entries in the before list
    for diff in only_before:
        # Check for an item with the same name in the after list
        is_a_move = False
        for diff2 in only_after:
            if diff[0] == diff2[0]:
                retval.append((date.date(), '%s moved from sector %d to sector %d' % (diff[0], diff[1], diff2[1])))
                only_after.remove(diff2)
                is_a_move = True
                break
        # If it didn't move, it was removed
        if not is_a_move:
            retval.append((date.date(), '%s disappeared (from sector %d)' % (diff[0], diff[1])))
    # Any left in the after list are new additions
    for diff in only_after:
        retval.append((date.date(), '%s appeared in sector %d' % (diff[0], diff[1])))
    return retval

def _changes_from_dates(dates, expected):
    '''
    Code shared between planet_changes() and npc_store_changes().
    Calls expected() passing each of the datetimes in the dates list.
    Calls changes() to compare successive return values.
    '''
    # Get the list of items for each date (add 1s to be sure we get the 'after' list)
    items = []
    for date in dates:
        items.append(expected(date + datetime.timedelta(seconds=1)))
    # Now find the differences between each pair
    retval = []
    for i in range(1,len(dates)):
        retval += changes(items[i - 1], items[i], dates[i])
    retval.sort()
    return retval

def planet_changes():
    '''
    When planets moved and appeared
    Returns a list of (date, event string) tuples
    '''
    key_dates = [cycle_1_start,
                 ssw_sector_map.flambe_added_datetime,
                 ssw_sector_map.planets_moved_datetime,
                 ssw_sector_map.planets_moved_datetime,
                 ssw_sector_map.planets_moved_datetime,
                 ssw_sector_map.planets_moved_datetime,
                 ssw_sector_map.planets_moved_datetime,
                 ssw_sector_map.reboot_datetime,
                 ssw_sector_map.hedrok_removed_datetime,
                 ssw_sector_map.hedrok_restored_datetime,
                 ssw_sector_map.deep_six_removed_datetime,
                 ssw_sector_map.phallorus_removed_datetime,
                 ssw_sector_map.eroticon_69_removed_datetime]
    return _changes_from_dates(key_dates, ssw_sector_map.expected_planets)

def npc_store_changes():
    '''
    When NPC stores moved and appeared
    Returns a list of (date, event string) tuples
    '''
    # Dates of interest
    key_dates = [cycle_1_start,
                 ssw_sector_map.leroy_tongs_datetime,
                 ssw_sector_map.planets_moved_datetime,
                 ssw_sector_map.clingons_datetime,
                 ssw_sector_map.gobbles_datetime]
    return _changes_from_dates(key_dates, ssw_sector_map.expected_npc_stores)

def mars():
    '''
    Mars locations
    Returns a list of (date, event string) tuples
    '''
    retval = []
    first_ssw_year = cycle_1_start.year
    today = ssw_utils.now_in_ssw()
    this_ssw_year = today.year
    for year in range(first_ssw_year, this_ssw_year + 1):
        for month, day in ssw_sector_map.mars_dates:
            date = datetime.datetime(year, month, day, 0, 0)
            if (date <= today) and ssw_was_running(date):
                retval.append((date.date(), "Mars was in sector %d" % ssw_sector_map.mars[1]))
    return retval

def love_boat():
    '''
    The <3 boat locations
    Returns a list of (date, event string) tuples
    '''
    retval = []
    today = ssw_utils.now_in_ssw()
    this_ssw_year = today.year
    end_year = this_ssw_year
    if (today > today.replace(month=2,day=13)):
        end_year += 1
    for year in range(3008,end_year):
        sector = ssw_sector_map.love_boat_sector(year)
        date = datetime.datetime(year, 2, 14, 0, 0)
        if ssw_was_running(date):
            if (sector == None):
                retval.append((date.date(), "The <3 Boat was somewhere unrecorded"))
            else:
                retval.append((date.date(), "The <3 Boat was in sector %d" % sector))
    return retval

def planet_x():
    '''
    Planet X locations
    Returns a list of (date, event string) tuples
    '''
    retval = []
    today = ssw_utils.now_in_ssw()
    for year in range(3007, 3016):
        sector = ssw_sector_map.planet_x_sector(year)
        start_date = datetime.datetime(year, 12, 25, 0, 0)
        end_date = datetime.datetime(year+1, 1, 1, 0, 0)
        if ssw_was_running(start_date):
            if (sector == None):
                retval.append((start_date.date(),
                               "Planet X appeared somewhere unrecorded"))
                if (end_date < today):
                    retval.append((end_date.date(), "Planet X disappeared again"))
            else:
                retval.append((start_date.date(),
                               "Planet X appeared in sector %d" % sector))
                if (end_date < today):
                    retval.append((end_date.date(),
                                   "Planet X disappeared from sector %d" % sector))
    sectors = ssw_sector_map.planet_x_3016_locations()
    for day in range(25, 32):
        date = datetime.datetime(3016, 12, day, 0, 0)
        if today >= date:
            sector = sectors[date.date()]
            retval.append((date.date(), "Planet X was in sector %d" % sector))
    return retval

def main(*arguments):
    '''
    Do whatever the user wants
    '''
    # Parse command-line options
    try:
        opts, args = getopt.getopt(arguments,"h",["help"])
    except getopt.GetoptError:
        usage(sys.argv[0])
        sys.exit(2)

    if len(args) > 0:
        usage(sys.argv[0])
        sys.exit(2)

    for opt,arg in opts:
        if (opt == '-h') or (opt == '--help'):
            usage(sys.argv[0])
            sys.exit(0)

    # TODO Provide command-line options to change these
    include_cycle_dates = True
    include_space_changes = True
    include_planet_changes = True
    include_npc_store_changes = True
    include_love_boat = True
    include_planet_x = True
    include_mars = True
    include_shutdowns = True

    events = []
    if (include_cycle_dates):
        events += cycle_dates()
    if (include_planet_changes):
        events += planet_changes()
    if (include_space_changes):
        events += space_changes()
    if (include_npc_store_changes):
        events += npc_store_changes()
    if (include_love_boat):
        events += love_boat()
    if (include_planet_x):
        events += planet_x()
    if (include_mars):
        events += mars()
    if (include_shutdowns):
        events += server_shutdowns()
    events.sort()
    for date, event in events:
        print("On %s, %s" % (str(date).split(' ')[0], event))

if __name__ == '__main__':
    main(*sys.argv[1:])
    
