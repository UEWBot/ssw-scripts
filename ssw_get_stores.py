#!/usr/bin/python

'''
Script to list the current set of NPC stores in SSW
'''

# Copyright 2016 Squiffle

import re, urllib

npc_stores_url = "http://www.secretsocietywars.com/databuddy_ajax.php?factor=stores"

# File contains both stores in space and on planets. The matches only those in space
SPACE_STORE_RE = re.compile("img src='(.*?)'.*red;'>(.*?)<.* In Sector (\d*)<br \/>(.*)")

def parse_npc_stores(data):
    """
    Parse the list of NPC stores from the SSW server.
    Returns a list of 2-tuples containing store name and sector number.
    """
    npc_stores = []

    d = dict(eval(data))
    for text, prices in d["aaData"]:
        m = SPACE_STORE_RE.search(text)
        if m:
            img = m.group(1)
            name = m.group(2)
            sector = int(m.group(3))
            desc = m.group(4)
            # We discard the image url and the description for now
            npc_stores.append((name, sector))
    return npc_stores

def get_npc_stores():
    """
    Download the NPC store data from the SSW server,
    parse it, and return a list of 2-tuples containing store name and sector number.
    """
    f = urllib.urlopen(npc_stores_url)
    npc_stores = f.read()
    return parse_npc_stores(npc_stores)

def main():
    """
    Get the NPC store data and write out the list of NPC stores.
    """
    npc_stores = get_npc_stores()

    # No format to match here. One per line makes it easy to parse
    for p in npc_stores:
        print p

if __name__ == '__main__':
    main()

