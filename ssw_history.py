#!/usr/bin/python

'''
Script to print out some SSW history
'''

# Copyright 2011, 2015-2016 Squiffle

# TODO Replace some hard-coded dates and sectors with stuff derived from ssw_sector_map

import ssw_sector_map2 as ssw_sector_map
import ssw_map_utils
import operator, sys, getopt, datetime

version = 1.00

def usage(progname):
    '''
    Tell them how to run the program
    '''
    print "Usage: %s [-h]" % progname
    print
    print " Secret Society Wars history"
    print
    print "  -h|--help - print usage and exit"
    print
    print " Version %.2f. Brought to you by Squiffle" % version

def ssw_was_running(date):
    '''
    True if the server was actually up.
    '''
    return (date < ssw_sector_map.shutdown_datetime) or (date > ssw_sector_map.reboot_datetime)

def server_shutdowns():
    '''
    The dates of server shutdowns and restarts.
    '''
    retval = []
    retval.append((ssw_sector_map.shutdown_datetime, "SSW was shut down"))
    retval.append((ssw_sector_map.reboot_datetime, "SSW came back from the dead"))
    return retval

def cycle_dates():
    '''
    The date of each cycle
    Returns a list of (date, event string) tuples
    '''
    retval = []
    cycle = 0
    # zip() would truncate. map() appends None.
    for start, war_end in map(None,
                              ssw_sector_map.cycle_start,
                              ssw_sector_map.war_end):
        # First entry is a fake
        if (cycle > 0):
            retval.append((start, "Cycle %d started" % cycle))
            if (war_end == None):
                today = ssw_map_utils.today_in_ssw()
                length = today - start
                retval.append((today,
                               "War ongoing, after %d days" % length.days))
            else:
                length = war_end - start
                retval.append((war_end,
                               "War %d ended, after %d days" % (cycle, length.days)))
        cycle += 1
    return retval

def space_changes():
    '''
    When space had a major rework
    Returns a list of (date, event string) tuples
    '''
    retval = [(ssw_sector_map.space_mazified_datetime,
               "Space became a maze"),
              (ssw_sector_map.space_rework_datetime,
               "Space was changed substantially, including moving planets and NPC stores")]
    retval.sort()
    return retval

def planet_changes():
    '''
    When planets moved and appeared
    Returns a list of (date, event string) tuples
    '''
    retval = [(ssw_sector_map.flambe_added_datetime,
               "Flambe appeared in sector 1070"),
              (ssw_sector_map.planets_moved_datetime,
               "Pharma moved from sector 102 to sector 721"),
              (ssw_sector_map.planets_moved_datetime,
               "New Ceylon moved from sector 92 to sector 227"),
              (ssw_sector_map.planets_moved_datetime,
               "Lucky Spaceman Distilleries moved from sector 49 to sector 631"),
              (ssw_sector_map.planets_moved_datetime,
               "Pinon Sol appeared in sector 707"),
              (ssw_sector_map.planets_moved_datetime,
               "Hedrok appeared in sector 888"),
              (ssw_sector_map.reboot_datetime,
               "Pinon Sol vanished again"),
              (ssw_sector_map.hedrok_removed_datetime,
               "Hedrok vanished, replaced by Yipikaitain"),
              (ssw_sector_map.hedrok_restored_datetime,
               "Hedrok reappeared, in sector 707"),
              (ssw_sector_map.deep_six_removed_datetime,
               "Deep Six Fauna was deep sixed"),
              (ssw_sector_map.phallorus_removed_datetime,
               "Phallorus disappeared"),
              (ssw_sector_map.eroticon_69_removed_datetime,
               "Eroticon 69 disappeared")]
    retval.sort()
    return retval

def npc_store_changes():
    '''
    When NPC stores moved and appeared
    Returns a list of (date, event string) tuples
    '''
    retval = [(ssw_sector_map.leroy_tongs_datetime,
               "Leroy Tong's appeared in sector 923"),
              (ssw_sector_map.planets_moved_datetime,
               "Lucky Spaceman Liquor Store moved from sector 49 to sector 631"),
              (ssw_sector_map.clingons_datetime,
               "Clingon's appeared in sector 30"),
              (ssw_sector_map.gobbles_datetime,
               "Gobble's appeared in sector 719")]
    retval.sort()
    return retval

def mars():
    '''
    Mars locations
    Returns a list of (date, event string) tuples
    '''
    retval = []
    today = ssw_map_utils.today_in_ssw()
    this_ssw_year = today.year
    for year in range(3008,this_ssw_year+1):
        for month, day in ssw_sector_map.mars_dates:
            date = datetime.datetime(year, month, day, 0, 0)
            if (date <= today) and ssw_was_running(date):
                retval.append((date, "Mars was in sector 4"))
    return retval

def love_boat():
    '''
    The <3 boat locations
    Returns a list of (date, event string) tuples
    '''
    retval = []
    today = ssw_map_utils.today_in_ssw()
    this_ssw_year = today.year
    end_year = this_ssw_year
    if (today > today.replace(month=2,day=13)):
        end_year += 1
    for year in range(3008,end_year):
        sector = ssw_sector_map.love_boat_sector(year)
        date = datetime.datetime(year, 2, 14, 0, 0)
        if ssw_was_running(date):
            if (sector == None):
                retval.append((date, "The <3 Boat was somewhere unrecorded"))
            else:
                retval.append((date, "The <3 Boat was in sector %d" % sector))
    return retval

def planet_x():
    '''
    Planet X locations
    Returns a list of (date, event string) tuples
    '''
    retval = []
    today = ssw_map_utils.today_in_ssw()
    this_ssw_year = today.year
    end_year = this_ssw_year
    if (today > today.replace(month=12,day=24)):
        end_year += 1
    for year in range(3007,end_year):
        sector = ssw_sector_map.planet_x_sector(year)
        start_date = datetime.datetime(year, 12, 25, 0, 0)
        end_date = datetime.datetime(year+1, 1, 1, 0, 0)
        if ssw_was_running(start_date):
            if (sector == None):
                retval.append((start_date,
                               "Planet X appeared somewhere unrecorded"))
                if (end_date < today):
                    retval.append((end_date, "Planet X disappeared again"))
            else:
                retval.append((start_date,
                               "Planet X appeared in sector %d" % sector))
                if (end_date < today):
                    retval.append((end_date,
                                   "Planet X disappeared from sector %d" % sector))
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
        print "On %s, %s" % (str(date).split(' ')[0], event)

if __name__ == '__main__':
    main(*sys.argv[1:])
    
