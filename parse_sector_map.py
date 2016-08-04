#!/usr/bin/python

from __future__ import absolute_import
from __future__ import print_function
import six.moves.html_parser, six.moves.html_entities
import six
from six.moves import range
from six.moves import zip

class TradingPostParser(six.moves.html_parser.HTMLParser):
    entitydefs = six.moves.html_entities.entitydefs

    def __init__(self):
        six.moves.html_parser.HTMLParser.__init__(self)
        self.ores_bought = {}
        self.ores_sold = {}
        self.planets = 0
        self.asteroids = 0
        self.black_holes = 0
        self.npc_stores = 0
        self.jellyfish = 0
        self.trading_ports = 0
        self.ipts = 0
        self.luvsats = 0

    def parse_density(self, text):
        if text.find('Last Recorded Density:') > -1:
#            print "*** Density"
            pass

    def parse_planet(self, text):
        if text.find('Planet:') > -1:
#            print "*** Planet"
            self.planets += 1

    def parse_asteroid(self, text):
        if text.find('There is an asteroid in this sector:') > -1:
#            print "*** Asteroid"
            self.asteroids += 1

    def parse_black_hole(self, text):
        if text.find('Black Hole in sector') > -1:
#            print "*** Black Hole"
            self.black_holes += 1

    def parse_npc_store(self, text):
        if text.find('NPC Store:') > -1:
#            print "*** NPC Store"
            self.npc_stores += 1

    def parse_jellyfish(self, text):
        if text.find('Space Jellyfish in sector') > -1:
#            print "*** Jellyfish"
            self.jellyfish += 1

    def parse_trading_port(self, text):
        temp = text.find('Trading Port')
        if temp > -1:
            words = text[temp:].split()
            words2 = words[2][1:].split('<')
            sector = int(words2[0])
#            print "*** Trading Port in sector %d" % sector
            buy_idx = len(words)
            if words[2].find("Buying:") > -1:
                buy_idx = 2
#                print "is buying"
            sell_idx = len(words)
            end_idx = len(words)
            for i in range(2,sell_idx):
                if words[i].find("Selling:") > -1:
#                    print "is selling"
                    sell_idx = i
                if words[i].find("Links") > -1:
                    if end_idx == len(words):
                        end_idx = i
                if words[i].find("Emergency") > -1:
                    end_idx = i
            ores_bought = words[buy_idx+1:sell_idx:4]
            buy_prices = words[buy_idx+3:sell_idx:4]
            for ore,price in zip(ores_bought,buy_prices):
                if ore not in self.ores_bought:
                    self.ores_bought[ore] = []
                self.ores_bought[ore].append((int(price[1:]),sector))
            ores_sold = words[sell_idx+1:end_idx:4]
            sell_prices = words[sell_idx+3:end_idx:4]
            for ore,price in zip(ores_sold,sell_prices):
                if ore not in self.ores_sold:
                    self.ores_sold[ore] = []
                self.ores_sold[ore].append((int(price[1:]),sector))
            self.trading_ports += 1
#        print

    def parse_ipt(self, text):
        if text.find('Emergency IPT') > -1:
#            print "*** IPT"
            self.ipts += 1
        pass

    def parse_luvsat(self, text):
        if text.find('LuvSat in sector') > -1:
#            print "*** LuvSat"
            self.luvsats += 1

    def parse_sector_description(self, text):
        self.parse_density(text)
        self.parse_planet(text)
        self.parse_asteroid(text)
        self.parse_black_hole(text)
        self.parse_npc_store(text)
        self.parse_jellyfish(text)
        self.parse_trading_port(text)
        self.parse_ipt(text)
        self.parse_luvsat(text)

    def handle_starttag(self, tag, atts):
        if tag == "div":
            for (key,val) in atts:
                if not key.find('onmouseover'):
                    self.parse_sector_description(val)

#    def handle_entityref(self, name):
#        if self.indiv:
#            self.handle_data(self.entitydefs.get(name, "?"))
#
#    def handle_data(self, data):
#        if self.indiv:
#            print "%d - handle_data(%s)" % (self.indiv, data)
#            self.text.append(data)

#    def handle_endtag(self, tag):
#        if tag == "div":
#            print "%d - handle_endtag(div)" % self.indiv
#            assert self.indiv > 0
#            if self.text:
#                print "".join(self.text) 


file = open("ssw_sector_map.htm")
html = file.read()
file.close()

p = TradingPostParser()
try:
    p.feed(html)
except six.moves.html_parser.HTMLParseError as inst:
    print("Unable to parse map file - %s" % inst, file=fout)
    sys.exit(2)
p.close()

ore_best_sell = {}
ore_best_buy = {}

for (ore,price_list) in six.iteritems(p.ores_bought):
    print("%s bought :" % ore)
    max_price = 0
    for price, sector in price_list:
        if price > max_price:
            max_price = price
            best_sector = sector
        print(" for %d in sector %d" % (price, sector))
    print("best price = %d" % max_price)
    ore_best_sell[ore] = (max_price,best_sector)
for (ore,price_list) in six.iteritems(p.ores_sold):
    print("%s sold :" % ore)
    min_price = 200
    for price, sector in price_list:
        if price < min_price:
            min_price = price
            best_sector = sector
        print(" for %d in sector %d" % (price, sector))
    print("best price = %d" % min_price)
    ore_best_buy[ore] = (min_price,best_sector)

for ore,(sell_price,sell_sector) in six.iteritems(ore_best_sell):
    (buy_price,buy_sector) = ore_best_buy[ore]
    print("%d profit buying %s for %d from %d and selling in %d" % (sell_price-buy_price,ore,buy_price,buy_sector,sell_sector)) 

print()
print("%d planets" % p.planets)
print("%d asteroids" % p.asteroids)
print("%d black holes" % p.black_holes)
print("%d NPC stores" % p.npc_stores)
print("%d space jellyfish" % p.jellyfish)
print("%d trading ports" % p.trading_ports)
print("%d IPT Beacons" % p.ipts)
print("%d luvsat" % p.luvsats)

print()

