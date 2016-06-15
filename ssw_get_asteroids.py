#!/usr/bin/python

'''
Script to list the current set of asteroids in SSW
'''

# Copyright 2016 Squiffle

import re, urllib
import ssw_utils

asteroids_url = "http://www.secretsocietywars.com/databuddy_ajax.php?factor=asteroids"
ORE_RE = re.compile("(\w*) Ore")

def parse_asteroids(data):
    """
    Parse the list of asteroids from the SSW server.
    Returns a dict, keyed by ore, of arrays of sector numbers
    """
    asteroids = {}

    d = dict(eval(data))
    for ore_str, sector_str in d["aaData"]:
        sector = int(sector_str)
        m = ORE_RE.search(ore_str)
        if m:
            ore = m.group(1)
            if ore not in asteroids:
                asteroids[ore] = []
            asteroids[ore].append(sector)
    return asteroids

def get_asteroids():
    """
    Download the asteroid data from the SSW server,
    parse it, and return a dict, keyed by ore, of arrays of sector numbers
    """
    f = urllib.urlopen(asteroids_url)
    asteroids = f.read()
    return parse_asteroids(asteroids)

def main():
    """
    Get the list of asteroids and print it out, in the same format as ss_trade_routes
    """
    a = get_asteroids()

    for ore in sorted(a.keys()):
        # Use the same format as in ssw_trade_routes
        print "%d of %d %s asteroids in %s" % (len(a[ore]),
                                               len(a[ore]),
                                               ore,
                                               ssw_utils.sector_str(a[ore]))

if __name__ == '__main__':
    main()

