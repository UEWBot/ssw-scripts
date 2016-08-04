#!/usr/bin/python

'''
Script to facilitate updating the sector map when at degree 33
'''

# Copyright 2008, 2015 Squiffle

# TODO: Would be nice to somehow check that the enemy list is up-to-date
# TODO: Command-line options to change filenames
# TODO: Command-line option to set jellyfish_sectors_for_empaths

from __future__ import absolute_import
from __future__ import print_function
import ssw_sector_map2 as ssw_sector_map
import ssw_map_utils

version = 0.1

# Defaults
map_filename = "ssw_sector_map.htm"
enemy_sectors_filename = "ssw_enemy_sectors.txt"
jellyfish_sectors_for_empaths = 2

# If enemy sectors file exists, read it
try:
    file = open(enemy_sectors_filename)
except IOError:
    print()
    print("**** Cannot open file %s - assuming no known enemy sectors" % enemy_sectors_filename)
    enemy_sectors = []
else:
    lines = file.readlines()
    file.close()

    # Parse out the list of known enemy sectors
    for line in lines:
        if line.find("sector(s) to probe") > -1:
            start = line.find('[')
            enemy_sectors = [int(x) for x in line[start+1:-2].split(',')]

# Parse the map, and check that it's valid and current
page = open(map_filename)

p = ssw_sector_map.SectorMapParser(page)

map_valid,reason = p.valid()
if not map_valid:
    print("Sector map file %s is invalid - %s" % (map_filename, reason))
    sys.exit(2)

if not ssw_map_utils.is_todays(p):
    print()
    print("**** Map is more than 24 hours old")

# Get the list of unexplored sectors in the current map
unexplored_sectors = ssw_map_utils.all_unknown_sectors(p)

# Calculate which of those aren't known enemy sectors
probe = set(unexplored_sectors) - set(enemy_sectors)

# Which unknown sectors are known to jellyfish ?
unknown_sectors_with_jellyfish = ssw_map_utils.unknown_sectors_with_jellyfish(p)

# Tell user which sectors to probe and whether to talk to the empaths
# Not worth doing the jellyfish thing for one sector
if len(unknown_sectors_with_jellyfish) >= jellyfish_sectors_for_empaths:
    print("Visit the empaths to explore these sectors: %s" % str(sorted(list(unknown_sectors_with_jellyfish))))
    probe = probe - unknown_sectors_with_jellyfish

if len(probe) > 0:
    print("Launch %d probes to explore these sectors: %s" % (len(probe), str(sorted(list(probe)))))
    print("Don't forget to run 'ssw_trade_routes.py -mtws > %s' after saving the updated map!" % enemy_sectors_filename)
else:
    print("No warp probes needed.")

