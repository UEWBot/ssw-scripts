#!/usr/bin/python

# Script to figure out how things move over time

# Copyright 2008, 2015-2016 Squiffle

import ssw_sector_map2 as ssw_sector_map
import ssw_utils
import operator, sys, getopt, datetime, copy, glob

version = 0.01

# Defaults, changeable from the command line
map_files = glob.glob('*.htm')
track_asteroids = False
track_black_holes = False # takes > 1 hour
track_npc_stores = True
track_jellyfish = False # Who knows how long this would take
track_trading_port_movement = False
track_trading_port_prices = False
track_ipt_beacons = False
track_luvsats = True
fout = sys.stdout

def bool_to_str(the_bool):
    '''
    Returns "" or "not " if the boolean is True or False, respectively
    '''
    if the_bool:
        return ""
    else:
        return "not "

def cmp_map_datetimes(x,y):
    '''
    Comparison function for two datetimes
    '''
    if x.datetime > y.datetime:
        return 1
    elif x.datetime == y.datetime:
        return 0
    else:
        return -1

def mean(seq):
    '''
    Return the mean of the numbers in a list
    '''
    return sum(seq)/float(len(seq))

def median1(seq):
    '''
    Alternative function to calculate the median of the numbers in a list
    '''
    "Return the median of the list of numbers."
    # Sort the list and take the middle element.
    n = len(seq)
    copy = seq[:] # So that "numbers" keeps its original order
    copy.sort()
    if n & 1:         # There is an odd number of elements
        return copy[n // 2]
    else:
        return (copy[n // 2 - 1] + copy[n // 2]) / 2

def median(seq):
    '''
    Find the median of the numbers in a list
    '''
    return sorted(seq)[len(seq)/2]

def mode(seq):
    '''
    Return the mode of the numbers in a list
    '''
    return max([seq.count(y),y] for y in seq)[1]

def sum_of_squares(sector_pairings):
    '''
    Takes a list of tuples where each tuple is a pair of secotr numbers
    For each pair, caluclates the distance between the two sectors
    Returns the sum of the squares of those distances
    '''
    sum = 0
    for pairing in sector_pairings:
        distance = ssw_sector_map.direct_distance(pairing[0],pairing[1])
        sum += (distance*distance)
    return sum

def closest_mapping(from_sectors,to_sectors):
    '''
    Takes two lists of sector numbers of the same length
    Finds the mapping from one to the other that represents the minimal movement
    and returns it as a list of tuples where each tuple is a pair of sector numbers,
    one from each list
    Returns an empty list if the two lists of sectors have different lengths
    '''
#    print "closest_mapping(%s,%s)" % (from_sectors,to_sectors)
#    print "len(from_sectors) = %d, len(to_sectors) = %d" % (len(from_sectors),len(to_sectors))
    if len(from_sectors) != len(to_sectors):
        return []
    if len(from_sectors) == 1:
        # There's only one way to pair them up
#        print "returning [(%d,%d)]" % (from_sectors[0],to_sectors[0])
        return [(from_sectors[0],to_sectors[0])]
    # Find the sum of the squares of the distance for each possible pairing
    best_pairings = []
    best_distance = len(from_sectors) * ssw_sector_map.sectors_per_row * ssw_sector_map.sectors_per_row
#    for a in from_sectors:
#        new_from_sectors = copy.copy(from_sectors)
#        new_from_sectors.remove(a)
    a = from_sectors[0]
    new_from_sectors = copy.copy(from_sectors[1:])
    for b in to_sectors:
        new_to_sectors = copy.copy(to_sectors)
        new_to_sectors.remove(b)
#        print "Recursing with (%s,%s)" % (new_from_sectors,new_to_sectors)
        pairings = [(a,b)] + closest_mapping(new_from_sectors,new_to_sectors)
#        print "pairings = %s" % pairings
#        print len(from_sectors)
#        assert len(pairings) == len(from_sectors)
        temp = sum_of_squares(pairings)
#        print "sum_of_squares() returned %d" % temp
#        print "best_distance = %d" % best_distance
        if temp < best_distance:
            best_distance = temp
            best_pairings = pairings
            # Optimisation - if it can't get any better, stop looking
            if best_distance == 0:
                break
#    print "Returning %s" % best_pairings
    return copy.copy(best_pairings)

def usage():
    '''
    Print how to use this script
    '''
    print "Usage: %s [map_filenames]" % sys.argv[0]
    print
    print " Find how things move in SSW"
    print
    print "  default is to %strack asteroids, to %strack black holes, to %strack NPC stores, to %strack jellyfish, to %strack trading port movement, to %strack trading port prices, to %strack IPT beacons and to %strack luvsats" % (bool_to_str(track_asteroids),bool_to_str(track_black_holes),bool_to_str(track_npc_stores),bool_to_str(track_jellyfish),bool_to_str(track_trading_port_movements),bool_to_str(track_trading_port_prices),bool_to_str(track_ipt_beacons),bool_to_str(track_luvsats))
    print
    print " Version %.2f. Brought to you by Squiffle" % version

# Parse command-line options
if len(sys.argv) > 1:
    map_files = sys.argv[1:]
else:
    # TODO Need to find some default map files
    pass

# Read and parse each sector map
maps = []
for filename in map_files:
    page = open(filename)
    p = ssw_sector_map.SectorMapParser(page)

    (map_valid, reason) = p.valid()
    if map_valid:
        maps.append((filename,p))
    else:
        print >>fout, '"%s" doesn\'t seem to be an SSW map file - %s' % (filename, reason)

# Sort maps by date
maps.sort(key=operator.itemgetter(1),cmp=cmp_map_datetimes)

# Print summary
temp = (len(map_files) - len(maps))
if temp > 0 :
    print >>fout, "%d file(s) weren't SSW map files" % temp
    print >>fout
print >>fout, "%d map file(s) parsed" % len(maps)
for f,m in maps:
    print >>fout, "  %s - map for %s" % (f, str(m.datetime))

# Calculate how things move over time if we have more than one map
if len(maps) < 2:
    print >>fout, "No comparisons possible"
    sys.exit(0)

# TODO We have two styles of lists to compare
# - luvsats and black holes are straight lists of sectors
# - asteroids, IPTs and NPC stores are lists of (name,sector) tuples
# should be able to factor out common code
# Jellyfish are in the first category, but probably too numerous
# Trading ports are different again
if track_asteroids:
    for f,m in maps[:-1]:
        f2,m2 = maps[maps.index((f,m))+1]
        print >>fout
        print >>fout, "Longest distances from %s to %s for asteroids:" % (str(m.datetime),str(m2.datetime))
        # Pair up matching items in the two lists
        l1 = ssw_utils.to_dict(m.asteroids)
        l2 = ssw_utils.to_dict(m2.asteroids)
        for ore in l1.keys():
            mapping = closest_mapping(l1[ore],l2[ore])
            if len(mapping) > 0:
                longest = 0
                for i in mapping:
                    d = ssw_sector_map.direct_distance(i[0],i[1]) 
                    if d > longest:
                        longest = d
                print >>fout, " %s - %d" % (ore,longest)
            else:
                print >>fout, " Can't map for %s - %d asteroids became %d" % (ore, len(l1[ore]), len(l2[ore]))

if track_black_holes:
    print >>fout
    for f,m in maps[:-1]:
        f2,m2 = maps[maps.index((f,m))+1]
        mapping = closest_mapping(m.black_holes,m2.black_holes)
        if len(mapping) > 0:
            longest = 0
            for i in mapping:
                d = ssw_sector_map.direct_distance(i[0],i[1]) 
                if d > longest:
                    longest = d
            print >>fout, "Longest distance from %s to %s for black_holes - %d" % (str(m.datetime),str(m2.datetime),longest)
        else:
            print >>fout, "Can't map - %d black holes became %d" % (len(m.black_holes), len(m2.black_holes))

if track_npc_stores:
    for f,m in maps[:-1]:
        f2,m2 = maps[maps.index((f,m))+1]
        print >>fout
        print >>fout, "Longest distances from %s to %s for NPC stores:" % (str(m.datetime),str(m2.datetime))
        # Pair up matching items in the two lists
        l1 = ssw_utils.to_dict(m.npc_stores)
        l2 = ssw_utils.to_dict(m2.npc_stores)
        for store in l1.keys():
            mapping = closest_mapping(l1[store],l2[store])
            if len(mapping) > 0:
                longest = 0
                for i in mapping:
                    d = ssw_sector_map.direct_distance(i[0],i[1]) 
                    if d > longest:
                        longest = d
                print >>fout, " %s - %d" % (store,longest)
            else:
                print >>fout, " Can't map for %s - %d stores became %d" % (store, len(l1[ore]), len(l2[ore]))

if track_jellyfish:
    print >>fout
    print >>fout, "You've got to be kidding - do you know how long it would take to track jellyfish ?"

if track_trading_port_movement or track_trading_port_prices:
    print >>fout
    for f,m in maps[:-1]:
        f2,m2 = maps[maps.index((f,m))+1]
        if track_trading_port_movement:
            # First look at any actual movement of trading ports
            print m.trading_ports
            print m2.trading_ports
            mapping = closest_mapping(m.trading_ports,m2.trading_ports)
            if len(mapping) > 0:
                longest = 0
                for i in mapping:
                    d = ssw_sector_map.direct_distance(i[0],i[1]) 
                    if d > longest:
                        longest = d
                print >>fout, "Longest distance from %s to %s for trading ports - %d" % (str(m.datetime),str(m2.datetime),longest)
            else:
                print >>fout, "Can't map - %d trading ports became %d" % (len(m.trading_ports), len(m2.trading_ports))
        if track_trading_port_prices:
            for ore in m.ores_sold.keys():
                print >>fout, " %s sold in %d ports on %s vs %d on %s" % (ore, len(m.ores_sold[ore]), str(m.datetime), len(m2.ores_sold[ore]), str(m2.datetime))
                count = 0
                prices = [price for price,s in m.ores_sold[ore]]
                for price,port in m.ores_sold[ore]:
                    if port not in [s for p,s in m2.ores_sold[ore]]:
                        count += 1
    #                    print >>fout, " Port in %d stopped selling %s at %d" % (port,ore,price)
                print >>fout, " %d ports stopped selling %s" % (count, ore)
                print >>fout, " Prices for %s ranged from %d to %d. Mean = %f, median = %d, mode = %d" % (ore, min(prices), max(prices), mean(prices), median(prices), mode(prices))
                count = 0
                prices = [price for price,s in m2.ores_sold[ore]]
                for price,port in m2.ores_sold[ore]:
                    if port not in [s for p,s in m.ores_sold[ore]]:
                        count += 1
    #                    print >>fout, " Port in %d started selling %s at %d" % (port,ore,price)
                print >>fout, " %d ports started selling %s" % (count, ore)
                print >>fout, " Prices for %s now range from %d to %d. Mean = %f, median = %d, mode = %d" % (ore, min(prices), max(prices), mean(prices), median(prices), mode(prices))
            # TODO Look at price changes

for f,m in maps:
    print m.ipts

if track_ipt_beacons:
    # IPT beacons are tricky - there aren't always the same number of IPTs to any given planet
    # presumably they both move and change destination
    print >>fout
    for f,m in maps[:-1]:
        print >>fout
        f2,m2 = maps[maps.index((f,m))+1]
        print m.ipts
        print m2.ipts
        # Pair up matching items in the two lists
        l1 = ssw_utils.to_dict(m.ipts)
        l2 = ssw_utils.to_dict(m2.ipts)
        print l1
        print l2
#        for dest in l1.keys():
#            mapping = closest_mapping(l1[dest],l2[dest])
#            if len(mapping) > 0:
#                longest = 0
#                for i in mapping:
#                    d = ssw_sector_map.direct_distance(i[0],i[1]) 
#                    if d > longest:
#                        longest = d
#                print >>fout, "Longest distance from %s to %s for IPT to %s - %d" % (str(m.datetime),str(m2.datetime),dest,longest)
#            else:
#                print >>fout, "Can't map - %d IPT beacons became %d" % (len(l1), len(l2))

if track_luvsats:
    print >>fout
    for f,m in maps[:-1]:
        f2,m2 = maps[maps.index((f,m))+1]
        mapping = closest_mapping(m.luvsats,m2.luvsats)
        if len(mapping) > 0:
            longest = 0
            for i in mapping:
                d = ssw_sector_map.direct_distance(i[0],i[1]) 
                if d > longest:
                    longest = d
            print >>fout, "Longest distance from %s to %s for luvsats - %d" % (str(m.datetime),str(m2.datetime),longest)
        else:
            print >>fout, "Can't map - %d luvsats became %d" % (len(m.luvsats), len(m2.luvsats))

