#!/usr/bin/python

'''
Class to represent an SSW Trading Port
'''

# Copyright 2008-2016 Squiffle

from __future__ import absolute_import
import unittest
import ssw_societies

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
        return "Trader %s (sector %d)" % (self.name, self.sector)

    def alignment_str(self):
        '''Returns the alignment string (GE and OC numbers)'''
        return "GE: %d OC: %d" % (self.good, self.order)

    def society_initial(self):
        '''Returns the initial of the society with which the port is aligned'''
        return ssw_societies.initial(self.good, self.order)

    def __str__(self):
        return "%s, %s (%s), buys %s, sells %s" % (self.full_name(),
                                                   self.alignment_str(),
                                                   self.society_initial(),
                                                   self.buy_prices,
                                                   self.sell_prices)

if __name__ == "__main__":
    unittest.main()

