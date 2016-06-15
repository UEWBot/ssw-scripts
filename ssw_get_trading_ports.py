#!/usr/bin/python

'''
Script to list the current set of trading ports in SSW
'''

# Copyright 2016 Squiffle

import re, urllib
import ssw_sector_map2 as ssw_sector_map

traders_url = "http://www.secretsocietywars.com/databuddy_ajax.php?factor=traders"
TRADER_RE = re.compile(">(.* Trading Port #(\d*)).*Sells:(.*)Buys:(.*)")
ORE_RE = re.compile("(\w*) Ore.*?: (\d*) starbux")

def parse_traders(data):
    """
    Parse the list of traders from the SSW server.
    Returns a list of TradingPort objects
    """
    traders = []

    d = dict(eval(data))
    for text, ge_str, oc_str in d["aaData"]:
        ge = int(ge_str)
        oc = int(oc_str)
        m = TRADER_RE.search(text)
        if m:
            name = m.group(1)
            num = int(m.group(2))
            sells = m.group(2)
            ore_sells = []
            for m2 in ORE_RE.finditer(m.group(3)):
                ore = m2.group(1)
                price = int(m2.group(2))
                ore_sells.append((ore, price))
            buys = m.group(3)
            ore_buys = []
            for m2 in ORE_RE.finditer(m.group(4)):
                ore = m2.group(1)
                price = int(m2.group(2))
                ore_buys.append((ore, price))
        t = ssw_sector_map.TradingPort(name, num, ge, oc, ore_buys, ore_sells)
        traders.append(t)
    return traders

def get_trading_ports():
    """
    Download the trading port data from the SSW server,
    parse it, and return a list of TradingPort objects
    """
    f = urllib.urlopen(traders_url)
    traders = f.read()
    return parse_traders(traders)

def main():
    """
    Get the list of traders and write it out in the same format as ssw_trade_routes.
    """
    t = get_trading_ports()

    for trader in t:
        # This is the same format as ssw_trade_routes
        print trader

if __name__ == '__main__':
    main()

