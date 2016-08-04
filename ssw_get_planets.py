#!/usr/bin/python

'''
Script to list the current set of planets in SSW
'''

# Copyright 2016 Squiffle

from __future__ import absolute_import
from __future__ import print_function
import re, urllib

planets_url = "http://www.secretsocietywars.com/databuddy_ajax.php?factor=planets"
PLANET_RE = re.compile("img src='(.*?)'.*red;'>(\w*).*Sector:<\/b> (\d*)<br \/>(.*?)<br \/>")

def parse_planets(data):
    """
    Parse the list of planets from the SSW server.
    Returns an array of 2-tuples containing planet name and sector number.
    """
    planets = []

    d = dict(eval(data))
    for text, attractions in d["aaData"]:
        m = PLANET_RE.search(text)
        if m:
            img = m.group(1)
            name = m.group(2)
            sector = int(m.group(3))
            desc = m.group(4)
            # We discard the image url and the description for now
            planets.append((name, sector))
    return planets

def get_planets():
    """
    Download the planet data from the SSW server,
    parse it, and return an array of 2-tuples containing planet name and sector number.
    """
    f = urllib.urlopen(planets_url)
    planets = f.read()
    return parse_planets(planets)

def main():
    """
    Get the planet data and write out the list of planets.
    """
    planets = get_planets()

    # No format to match here. One per line makes it easy to parse
    for p in planets:
        print(p)

if __name__ == '__main__':
    main()

