#!/usr/bin/python

'''
Utilities to extract higher-level info from a parsed SSW sector map
'''

# Copyright 2008, 2015 Squiffle

import ssw_sector_map2 as ssw_sector_map
import operator, datetime, unittest

version = 1.00

shield_ore = 'Bofhozonite'

def to_dict(a):
    '''
    Internal - Takes a list of (key,value) tuples
               Returns a dict indexed by key of lists of values
    '''
    # TODO There may be a better way to do this...
    retval = {}
    for (x,y) in a:
        if x not in retval:
            retval[x] = []
        retval[x].append(y)
    return retval

def enemy_drones_en_route(drones, society):
    '''
    Which of these drones are enemy ones ?
    '''
    return [soc for soc in drones if soc != society]

def drones_by_sector(in_map):
    '''
    Returns a dictionary, indexed by sector, of which society has drones there
    '''
    drones = {}
    for (society, sector) in in_map.drones:
        drones[sector] = society
    return drones

def sectors_by_society(in_map):
    '''
    Returns a dictionary, keyed by society, of lists of sectors with drones
    from that society.
    '''
    retval = {}
    for (society, sector) in in_map.drones:
        if society not in retval:
            retval[society] = []
        retval[society].append(sector)
    return retval

def best_route_to_sector(in_map,
                         to_sector,
                         from_sector=None,
                         society=None,
                         unexplored_sector_society=None):
    '''
    Find the best route to one sector
    Returns a (distance, route string, drone list, source, destination) tuple
    WARNING: from_sector comes after to_sectors. Take care when calling.
    '''
    src = from_sector
    if src == None:
        src = to_sector
    dist, route, drones = in_map.shortest_route(src,
                                                to_sector,
                                                society,
                                                unexplored_sector_society)
    return (dist, route, drones, from_sector, to_sector)

def best_routes(in_map,
                to_sectors,
                from_sector=None,
                society=None,
                unexplored_sector_society=None,
                sort=True):
    '''
    Find the best routes to the sectors in the list
    Returns a (sorted by distance) list of (distance,route string,drone list,from,to) tuples
    WARNING: from_sector comes after to_sectors. Take care when calling.
    '''
    result = []
    for sector in to_sectors:
        result.append(best_route_to_sector(in_map,
                                           sector,
                                           from_sector,
                                           society,
                                           unexplored_sector_society))
    if sort:
        result.sort(key=operator.itemgetter(0))
    return result

def asteroid_clusters(in_map):
    '''
    Returns a list of sets of asteroids (ore, sector tuples) that are all adjacent to one another.
    '''
    retval = []
    for ore, sector in in_map.asteroids:
        neighbours = [temp for temp in in_map.asteroids if temp[1] in ssw_sector_map.adjacent_sectors(sector, in_map.can_move_diagonally())]
        test_set = set(neighbours + [(ore, sector)])
        # TODO This "new_retval" approach works,
        # but I'm sure there's a better way using mappings
        added = False
        new_retval = []
        for the_set in retval:
            if the_set & test_set:
                the_set = the_set | test_set
                added = True
            new_retval.append(the_set)
        if not added:
            new_retval.append(test_set)
        retval = new_retval
    return retval

def asteroids_by_planets(in_map):
    '''
    Returns a list of asteroids (ore, sector tuples) that are adjacent to planets.
    '''
    retval = []
    for ore, sector in in_map.asteroids:
        for adj in ssw_sector_map.adjacent_sectors(sector,
                                                   in_map.can_move_diagonally()):
            if adj in [loc for name, loc in in_map.planets]:
                retval.append((ore, sector))
                # We only want to add it once, even if it's adjacent to multiple planets
                break
    return retval

def all_unknown_sectors(in_map):
    '''
    Every sector that needs to be (re-)explored
    '''
    return in_map.forgotten_sectors + in_map.unknown_sectors

def known_sectors(in_map):
    '''
    Every sector that doesn't need to be (re-)explored
    '''
    return set(ssw_sector_map.all_sectors) - set(all_unknown_sectors(in_map))

def today_in_ssw():
    '''
    Return the datetime representing 'now' in SSW
    '''
    today = datetime.datetime.now()
    # Map datetimes are 1000 years in the future
    return today.replace(today.year+1000)

def is_todays(in_map):
    '''
    Check whether this is today's map
    '''
    if (today_in_ssw() - in_map.datetime) > datetime.timedelta(1):
        return False
    return True

def unknown_sectors_with_jellyfish(in_map):
    '''
    Check for unknown sectors with jellyfish
    '''
    return (set(in_map.unknown_sectors)
             | set(in_map.forgotten_sectors)) & set(in_map.jellyfish)

def society_of_port_in_sector(in_map, sector):
    '''
    Returns the initial of the alignment of the trading port in the specified sector
    '''
    for port in in_map.trading_ports:
        if port.sector == sector:
            return port.society_initial()
    return None

def drone_free_price_list(price_list, drones, society):
    '''
    Internal - Returns the list of (price, (sector, alignment)) tuples from price_list
               with no sectors with enemy drones
    '''
    if society == None:
        return price_list
    retval = []
    for price, (sector, alignment) in price_list:
        if (sector not in drones) or (drones[sector] == society):
            # We can get enter this sector
            retval.append((price, (sector, alignment)))
    return retval

def asteroids_by_ore(in_map, society=None):
    '''
    Returns a dictionary, keyed by ore, of lists of sectors with asteroids
    Includes no sectors with enemy drones if society is specified.
    '''
    asts = to_dict(in_map.asteroids)
    if society != None:
        # Filter out asteroids in drone-filled sectors
        drones = drones_by_sector(in_map)
        for ore,sectors in asts.iteritems():
            asts[ore] = [sec for sec in sectors if sec not in drones or drones[sec] == society]
    return asts

def dump_missing_links(in_map, fout):
    '''
    Writes out the missing links in the map
    '''
    #print >>fout, in_map.missing_links
    first = True
    line = "{"
    for sector in in_map.missing_links.keys():
        if not first:
            line += ","
            print >>fout, line
            line = ""
        line += "%d: %s" % (sector, str(in_map.missing_links[sector]))
        first = False
    line += "}"
    print >>fout, line
    return
    first = True
    print >>fout, "{",
    for sector in in_map.missing_links.keys():
        if not first:
            print >>fout, ","
        print >>fout, "%d: %s" % (sector, str(in_map.missing_links[sector])),
        first = False
    print >>fout, "}"

def ores_bought(in_map, ore):
    '''
    Internal - Same as in_map.ores_bought,
               but with each sector replaced with a (sector, port alignment) tuple
    '''
    retval = []
    for price, sector in in_map.ores_bought[ore]:
        retval.append((price, (sector, society_of_port_in_sector(in_map, sector))))
    return retval

def ores_sold(in_map, ore):
    '''
    Internal - Same as in_map.ores_sold,
               but with each sector replaced with a (sector, port alignment) tuple
    '''
    retval = []
    for price, sector in in_map.ores_sold[ore]:
        retval.append((price, (sector, society_of_port_in_sector(in_map, sector))))
    return retval

def asteroids(in_map, ore, society=None):
    '''
    Returns list of asteroids for the specified ore.
    Includes no sectors with enemy drones if society is specified.
    '''
    if society == None:
        drones = []
    else:
        drones = drones_by_sector(in_map)
    asts = asteroids(in_map, ore)
    return [sec for sec in asts if sec not in drones or drones[sec] == society]

def places_to_sell_ore(in_map, ore, society=None):
    '''
    Returns a list of tuples of (price, list of (sector, port alignment) tuples),
    sorted highest to lowest price
    Includes no sectors with enemy drones if society is specified.
    '''
    ore_bought_dict = to_dict(drone_free_price_list(ores_bought(in_map, ore),
                                                    drones_by_sector(in_map),
                                                    society))
    return sorted(ore_bought_dict.iteritems(),
                  key = operator.itemgetter(0),
                  reverse=True)

def best_places_to_sell_ore(in_map, ore, society=None):
    '''
    Returns a tuple of (highest price, list of (sector, port alignment) tuples) or None
    Includes no sectors with enemy drones if society is specified.
    '''
    retval = places_to_sell_ore(in_map, ore, society)
    if len(retval) > 0:
        return retval[0]
    return None

def places_to_sell_ores(in_map, society=None):
    '''
    Returns a dictionary of list of tuples of (price, list of (sector, port alignment) tuples),
    keyed by ore name
    Includes no sectors with enemy drones if society is specified.
    '''
    ore_best_sell = {}
    for ore in in_map.ores_bought.iterkeys():
        ore_best_sell[ore] = places_to_sell_ore(in_map, ore, society)
    return ore_best_sell

def best_places_to_sell_ores(in_map, society=None):
    '''
    Returns a dictionary of tuples of (highest price, list of (sector, port alignment) tuples),
    keyed by ore name
    Includes no sectors with enemy drones if society is specified.
    '''
    ore_best_sell = {}
    for ore in in_map.ores_bought.iterkeys():
        ore_best_sell[ore] = best_places_to_sell_ore(in_map, ore, society)
    return ore_best_sell

def places_to_buy_ore(in_map, ore, society=None):
    '''
    Returns a list of tuples of (price, list of (sector, port alignment) tuples),
    sorted lowest to highest price
    Includes no sectors with enemy drones if society is specified.
    '''
    ore_sold_dict = to_dict(drone_free_price_list(ores_sold(in_map, ore),
                                                  drones_by_sector(in_map),
                                                  society))
    return sorted(ore_sold_dict.iteritems(), key = operator.itemgetter(0))

def best_places_to_buy_ore(in_map, ore, society=None):
    '''
    Returns a tuple of (cheapest price, list of (sector, port alignment) tuples) or None
    Includes no sectors with enemy drones if society is specified.
    '''
    retval = places_to_buy_ore(in_map, ore, society)
    if len(retval) > 0:
        return retval[0]
    return None

def places_to_buy_ores(in_map, society=None):
    '''
    Returns a dictionary of lists of tuples of (price, list of (sector, port alignment) tuples),
    keyed by ore name
    Includes no sectors with enemy drones if society is specified.
    '''
    ore_best_buy = {}
    for ore in in_map.ores_sold.iterkeys():
        ore_best_buy[ore] = places_to_buy_ore(in_map, ore, society)
    return ore_best_buy

def best_places_to_buy_ores(in_map, society=None):
    '''
    Returns a dictionary of tuples of (cheapest price, list of (sector, port alignment) tuples),
    keyed by ore name
    Includes no sectors with enemy drones if society is specified.
    '''
    ore_best_buy = {}
    for ore in in_map.ores_sold.iterkeys():
        ore_best_buy[ore] = best_places_to_buy_ore(in_map, ore, society)
    return ore_best_buy

# TODO Add more unit tests (all the other functions take a map parameter)

class ToDictNormal(unittest.TestCase):
    def testEmptyList(self):
        '''to_dict musthandle an empty list'''
        result = to_dict([])
        self.assertEqual(result, {})

    def testSingleValues(self):
        '''to_dict should create lists of single values where appropriate'''
        result = to_dict([(1, 'a')])
        self.assertEqual(result, {1: ['a']})

    def testMultiValues(self):
        '''to_dict should create lists of values where appropriate'''
        result = to_dict([(1, 'a'), (1, 'b')])
        self.assertEqual(result, {1: ['a', 'b']})

class EnemyDrones(unittest.TestCase):
    def testNoMatch(self):
        '''enemy_drones_en_route should return the same list if there are no matches'''
        input = ['a', 'b', 'c']
        result = enemy_drones_en_route(input, 'd')
        self.assertEqual(result, input)

    def testOneMatch(self):
        '''enemy_drones_en_route should remove a single match'''
        result = enemy_drones_en_route(['a', 'b', 'c'], 'b')
        self.assertEqual(result, ['a', 'c'])

    def testMultiMatch(self):
        '''enemy_drones_en_route should remove multiple matches'''
        result = enemy_drones_en_route(['a', 'b', 'c', 'a'], 'a')
        self.assertEqual(result, ['b', 'c'])

    def testAllMatch(self):
        '''enemy_drones_en_route should return an empty list if all match'''
        result = enemy_drones_en_route(['a', 'a'], 'a')
        self.assertEqual(result, [])

    def testEmptyList(self):
        '''enemy_drones_en_route should handle an empty list'''
        result = enemy_drones_en_route([], 'a')
        self.assertEqual(result, [])

if __name__ == "__main__":
    unittest.main()
