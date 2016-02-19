#!/usr/bin/python

'''
Script to find trade routes (and LuvSats) from an SSW sector map
'''

# Copyright 2008, 2015 Squiffle

# TODO: Figure out shortest trade and mining routes as well as most profitable.
# TODO: Add command-line options for max_trade_routes, max_mine_routes, min_buy_routes and routes_to_print.
# TODO: max_trade_routes and max_mining_routes are a bit wrong.
#       They're the number of different *profits* that we'll list.
#       While routes_to_print controls the number of routes we'll print for each profit
#       Ideally, we'd print the shortest 10 routes that net the best profit.
# TODO: Change command-line to allow printing of just buy or sell prices
# TODO: I think the script needs to be split in two.
#       luvsats, asteroids, sectors to probe and even shield ore are unrelated
#       to trade routes, although it's useful to share some of the code.
#       Should be do-able after moving some code to ssw_map_utils
# TODO: I think we might miss some trade routes when space is partially drone-filled.
#       We exclude enemy sectors, but do we find all the best routes from what's left ?

import ssw_sector_map2 as ssw_sector_map
import ssw_map_utils, ssw_societies
import operator, sys, getopt, datetime

version = 1.02

class Invalid_Ore(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)
                        
fout = sys.stdout

def port_str(tuple):
    '''
    Converts a (sector, alignment) tuple to a string suitable for printing
    '''
    return "%d (%s)" % tuple

def ports_str(sectors):
    '''
    Converts a list of (sector, alignment) tuples to a string suitable for printing
    '''
    retval = "port(s) "
    if len(sectors) == 0:
        retval = 'no ports'
    else:
        retval = ', '.join(map(port_str,sectors))
    return retval

def sector_str(sectors):
    '''
    Converts a list of sectors to a string suitable for printing
    '''
    retval = "sector(s) "
    if len(sectors) == 0:
        retval = 'no sectors'
    else:
        retval = ', '.join(map(str,sectors))
    return retval

def planet_str(planets):
    '''
    Converts a list of planets to a string suitable for printing
    '''
    retval = ""
    if len(planets) == 0:
        retval = 'no planets'
    else:
        retval = ', '.join(planets)
    return retval

def drone_str_for_sectors(sectors, drones_by_sector):
    '''
    Returns a string detailing who (if anyone) owns each sector in the list.
    '''
    # TODO: If we see any drones in the map, then no drones => neutral.
    #       If we see no drones, probably want to suppress this altogether.
    def to_str(sector):
        try:
            return drones_by_sector[sector]
        except:
            return ''
    drone_list = map(to_str, sectors)
    return '[' + ', '.join(drone_list) + ']'

def drones_str(drones):
    '''
    Converts the list of drones en route to a string of societies.
    '''
    if len(drones):
        return '[' + ', '.join(set(drones)) + ' drones]'
    return '[no drones]'

def print_best_ore_prices(p, ore_best_sectors, indent, society, buy, sell, unexplored_sector_society=None):
    '''
    Prints the best routes for ore_best_sectors
    Returns the number of routes printed
    '''
    assert (buy or sell)
    routes_printed = 0
    # TODO print the alignment info that's in ore_best_sectors
    best_sectors = [sector for sector, alignment in ore_best_sectors]
    routes = ssw_map_utils.best_routes(p, best_sectors, None, society, unexplored_sector_society)
    for dis, route, drones, src, dest in routes:
        print >>fout, "%s%s" % (indent, route),
        # Only count routes that can be taken
        if dis < ssw_sector_map.sectors_per_row:
            routes_printed += 1
            # Figure out the power impact of the trade(s)
            port = p.trading_port(dest)
            assert port, "Trying to trade in sector %d" % dest
            if buy:
                good = port.good
                order = port.order
            else:
                good = -port.good
                order = -port.order
            print >>fout, "[GE:%+d OC:%+d]" % (good, order),
            if len(p.drones):
                print >>fout, drones_str(drones)
            else:
                print >>fout
        else:
            print >>fout
    return routes_printed

def print_routes(p, sources, destinations, society, trade_at_start, unexplored_sector_society=None, max=200):
    '''
    Prints the best routes from each source sector to each destination sector
    Returns the number of routes printed
    '''
    routes = []
    routes_printed = 0
    for src in sources:
        for x in ssw_map_utils.best_routes(p, destinations, src, society, unexplored_sector_society):
            routes.append(x)
    routes = sorted(routes,key=operator.itemgetter(0))
    for route in routes[:max]:
        print >>fout, "    %s " % (route[1]),
        # Is there actually a route between those sectors ?
        if route[0] < ssw_sector_map.sectors_per_row:
            # This one counts
            routes_printed += 1
            # Figure out the power impact of the trade(s)
            good = 0
            order = 0
            if trade_at_start:
                port = p.trading_port(route[3])
                assert port, "Trying to buy from sector %d" % route[3]
                good = port.good
                order = port.order
            port = p.trading_port(route[4])
            assert port, "Trying to sell to sector %d" % route[4]
            good -= port.good
            order -= port.order
            print >>fout, "[GE:%+d OC:%+d]" % (good, order),
            if len(p.drones):
                print >>fout, drones_str(route[2])
            else:
                print >>fout
        else:
            print >>fout
    print >>fout
    return routes_printed

def print_ore_buy_routes(p, ore, price_list, indent, min_buy_routes, society, unexplored_sector_society=None, header_indent=''):
    '''
    Prints the list of routes to buy the ore, with an optional header line
    '''
    buy_routes_printed = 0
    if len(price_list) > 0:
        for price, sectors in price_list:
            if (buy_routes_printed >= min_buy_routes):
                break
            print >>fout, "%sBuy %s for %d:" % (header_indent, ore, price)
            buy_routes_printed += print_best_ore_prices(p, sectors, indent, society, True, False, unexplored_sector_society)
    else:
        print >>fout, "%sNowhere to buy %s" % (header_indent, ore)

def parse_asteroid_line(line):
    '''
    Parse a line listing the asteroids of one ore.
    Returns a tuple of (ore, list of sectors).
    '''
    ar = line.split(' ')
    # Skip spaces
    i = 0
    while i < len(ar) and ar[i] == '':
        i += 1
    # Skip "X of X", which is 3 elements of the array
    i += 3
    ore = ar[i]
    # Skip text until we find a number
    # Note that we expect a comma after most numbers, so don't check the last character
    while i < len(ar) and not ar[i][:-1].isdigit():
        i += 1
    # Read the sector number, then skip to the next number
    sectors = []
    while i < len(ar):
        if ar[i][0] == '[':
            break
        tmp = ar[i]
        if tmp[-1] == ',':
            tmp = tmp[:-1]
        sectors.append(int(tmp))
        i += 1
    return (ore, sectors)

def import_asteroids_file(filename, p):
    '''
    Add details of asteroids from a previous run this same cycle.
    This is useful when you're at degree 33 and you start forgetting
    details of sectors with enemy drones. Save the output with "-mta"
    from an earlier run and use it to supplement your asteroid knowledge.
    '''
    ast_file = open(filename)
    # Skip down to the list of asteroids
    for line in ast_file:
        if line == 'Asteroids\n':
            break;
    # Now read the list of asteroids for each ore
    for line in ast_file:
        if line == '\n':
            # We're done
            break
        # Now parse the line itself
        ore, sectors = parse_asteroid_line(line)
        # Append each one to the list in the map, unless it's already there
        for sector in sectors:
            if (ore, sector) not in p.asteroids:
                print >>fout, "Adding %s asteroid in sector %d to map" % (ore, sector)
                p.asteroids.append((ore, sector))
    ast_file.close()

def total_distance(port_set, distances):
    '''
    Return the total travel distance to visit the list of ports.
    Port_set may well contain one port multiple times.
    Distances is a dict, keyed by port, of distance.
    '''
    distance = 0
    for port in set(port_set):
        distance += distances[port]
    return distance

def add_ports_to_port_sets(port_sets, ports, ore):
    '''
    If port_sets is empty, return a list of dicts, keyed by ore, with one of ports in each entry.
    Otherwise, return a list of dicts, keyed by ore, with the content of port_sets
    and one of ports added.
    Thus is there are 3 port_sets and len(ports) is 2, a list of length 6 will result.
    '''
    retval = []
    for port in ports:
        for port_set in port_sets:
            new_port_set = port_set.copy()
            new_port_set[ore] = port
            retval.append(new_port_set)
        if len(port_sets) == 0:
            port_set = {}
            port_set[ore] = port
            retval.append(port_set)
    return retval
    
def usage(progname, map_file):
    '''
    Prints usage information
    '''
    print "Usage: %s [-s] [-m] [-t] [-h] [-j] [-p] [-c] [-b] [-l] [-a] [-w] [-y] [-n] [-e] [-x] [-d {a|e|i|o|t}] [-r ore] [-g ore_list] [-i asteroids_filename] [-o output_filename] [map_filename]" % progname
    print
    print " Find trade or mining routes"
    print
    print "  -s|--no-summary - don't print the summary"
    print "  -m|--no-trade - don't print trade routes"
    print "  -t|--no-mining - don't print mining routes"
    print "  -h|--help - print usage and exit"
    print "  -j|--dont-enhance - just use the map file, no other knowledge"
    print "  -p|--prices - print ore price list"
    print "  -c|--cheapest_ore - print where to buy each ore"
    print "  -b|--shield_ore - print places to buy shield ore (Bofhozonite) cheapest"
    print "  -l|--luvsats - print routes to luvsats"
    print "  -a|--asteroids - list asteroids"
    print "  -w|--probe - list sectors to probe"
    print "  -y|--your-drones - list where your drones are"
    print "  -n|--control - list number of sectors controlled by each society"
    print "  -e|--empire - assume that unexplored sectors contain Amaranth drones"
    print "  -x|--links - print the missing links"
    print "  -d|--drones {a|e|i|o|t} - avoid drones not belonging to the specified society"
    print "  -r|--ore - list all the places to get the specified ore"
    print "  -i|--input - read extra asteroid info from the specified file"
    print "  -o|--output - write output to the specified file"
    print "  -g|--groceries - report the best route to buy all the specified ores"
    print "                   ore_list is comma-separated, with no whitespace"
    print "  map_filename defaults to %s" % map_file
    print "  default is to just print trade and mining routes"
    print
    print " Version %.2f. Brought to you by Squiffle" % version

def parse_ore_list_arg(arg_str):
    '''
    Parse the string as a comma-separated list of ores
    Return the list
    Note that this is very generous - an arg of 'l' will return ['Lolnium', 'Lmaozium'] because both start with 'l'.
    '''
    retval = []
    strs = arg_str.split(',')
    for str in strs:
        new_ores = [ore for ore in ssw_sector_map.all_ores if ore.lower().startswith(str.lower())]
        if len(new_ores) == 0:
            # No matches at all
            raise Invalid_Ore, str
        retval += new_ores
    return retval

def main(*arguments):
    '''
    Do whatever the user wants !
    Returns the parsed map.
    '''
    # Defaults, changeable from the command line
    map_file = "ssw_sector_map.htm"
    asteroids_file = ""
    enhance = True
    print_summary = True
    print_trade_routes = True
    print_mining_routes = True
    print_buy_prices = False
    print_sell_prices = False
    print_ore_buying_routes = False
    print_luvsats = False
    print_shields = False
    print_asteroids = False
    print_your_drones = False
    print_probe_sectors = False
    print_sectors_controlled = False
    print_missing_links = False
    max_trade_routes = 5
    max_mining_routes = 5
    min_buy_routes = 3
    routes_to_print = 5
    society = None
    unexplored_sector_society = None
    ore_of_interest = None
    output_filename = None
    ores_to_buy = []

    global fout

    # Parse command-line options
    try:
        opts, args = getopt.getopt(arguments,"smthjpcblawynexd:r:g:i:o:",["no-summary","no-trade","no-mining","help","dont-enhance","prices","cheapest-ore","shield-ore","luvsats","asteroids","probe","your-drones","control","empire","links","drones=","ore=","groceries=","input=","output="])
    except getopt.GetoptError:
        usage(sys.argv[0], map_file)
        sys.exit(2)

    if len(args) == 1:
        map_file = args[0]
    elif len(args) > 1:
        usage(sys.argv[0], map_file)
        sys.exit(2)

    for opt,arg in opts:
        if (opt == '-s') or (opt == '--no-summary'):
            print_summary = False
        elif (opt == '-m') or (opt == '--no-trade'):
            print_trade_routes = False
        elif (opt == '-t') or (opt == '--no-mining'):
            print_mining_routes = False
        elif (opt == '-h') or (opt == '--help'):
            usage(sys.argv[0], map_file)
            sys.exit(0)
        elif (opt == '-j') or (opt == '--dont-enhance'):
            enhance = False
        elif (opt == '-d') or (opt == '--drones'):
            try:
                society = ssw_societies.adjective(arg)
            except ssw_societies.Invalid_Society:
                print 'Unrecognised society "%s" - should be one of %s' % (arg, ssw_societies.initials)
                usage(sys.argv[0], map_file)
                sys.exit(2)
        elif (opt == '-p') or (opt == '--prices'):
            print_buy_prices = True
            print_sell_prices = True
        elif (opt == '-c') or (opt == '--cheapest-ore'):
            print_ore_buying_routes = True
        elif (opt == '-b') or (opt == '--shield-ore'):
            print_shields = True
        elif (opt == '-l') or (opt == '--luvsats'):
            print_luvsats = True
        elif (opt == '-a') or (opt == '--asteroids'):
            print_asteroids = True
        elif (opt == '-w') or (opt == '--probe'):
            print_probe_sectors = True
        elif (opt == '-y') or (opt == '--your-drones'):
            print_your_drones = True
        elif (opt == '-n') or (opt == '--control'):
            print_sectors_controlled = True
        elif (opt == '-e') or (opt == '--empire'):
            unexplored_sector_society = ssw_societies.adjective('a')
        elif (opt == '-x') or (opt == '--links'):
            print_missing_links = True
        elif (opt == '-r') or (opt == '--ore'):
            try:
                ores = parse_ore_list_arg(arg)
                if len(ores) == 1:
                    ore_of_interest = ores[0]
                else:
                    print 'Cannot interpret "%s" as one ore - it maps to %s' % (arg, str(ores))
                    usage(sys.argv[0], map_file)
                    sys.exit(2)
            except Invalid_Ore:
                print 'Unrecognised ore "%s"' % (arg)
                usage(sys.argv[0], map_file)
                sys.exit(2)
        elif (opt == '-g') or (opt == '--groceries'):
            ores_to_buy = parse_ore_list_arg(arg)
        elif (opt == '-o') or (opt == '--output'):
            output_filename = arg
            fout = open(output_filename, "w")
        elif (opt == '-i') or (opt == '--input'):
            asteroids_file = arg
    
    # Read and parse the sector map
    page = open(map_file)
    p = ssw_sector_map.SectorMapParser(page)
    
    map_valid,reason = p.valid()
    if not map_valid:
        print >>fout, "Sector map file is invalid - %s" % reason
        sys.exit(2)
    
    # Print summary
    if print_summary:
        print >>fout
        print >>fout, "Summary"
        if p.known_sectors == len(ssw_sector_map.all_sectors):
            print >>fout, "  %d (all) sectors explored" % p.known_sectors
        else:
            print >>fout, "  %d of %d sectors explored (%.1f%%)" % (p.known_sectors, len(ssw_sector_map.all_sectors), (100.0*p.known_sectors)/len(ssw_sector_map.all_sectors))
            if len(p.forgotten_sectors) > 0:
                print >>fout, "  %d sector(s) forgotten (%.1f%%)" % (len(p.forgotten_sectors), (100.0*len(p.forgotten_sectors))/len(ssw_sector_map.all_sectors))
        if len(p.drones) == 0:
            print >>fout, "  No sectors with drones"
        else:
            print >>fout, "  %d sector(s) with drones (%.1f%%)" % (len(p.drones), (100.0*len(p.drones))/len(ssw_sector_map.all_sectors))
            print >>fout, "  %d sector(s) with your drones (%d drone(s) in total)" % (len(p.your_drones), sum([d for d,s in p.your_drones]))
        if (len(p.planets) == len(p.expected_planets())):
            print >>fout, "  %d (all) planets" % len(p.planets)
        else:
            print >>fout, "  %d of %d planets" % (len(p.planets), len(p.expected_planets()))
        if (len(p.asteroids) == p.expected_asteroids()):
            print >>fout, "  %d (all) asteroids" % len(p.asteroids)
        else:
            print >>fout, "  %d of %d asteroids" % (len(p.asteroids), p.expected_asteroids())
        if (len(p.black_holes) == len(ssw_sector_map.expected_black_holes)):
            print >>fout, "  %d (all) black holes" % len(p.black_holes)
        else:
            print >>fout, "  %d of %d black holes" % (len(p.black_holes), len(ssw_sector_map.expected_black_holes))
        if (len(p.npc_stores) == len(p.expected_npc_stores())):
            print >>fout, "  %d (all) NPC stores" % len(p.npc_stores)
        else:
            print >>fout, "  %d of %d NPC stores" % (len(p.npc_stores), len(p.expected_npc_stores()))
        if (len(p.jellyfish) == ssw_sector_map.expected_jellyfish):
            print >>fout, "  %d (all) space jellyfish" % len(p.jellyfish)
        else:
            print >>fout, "  %d of %d space jellyfish" % (len(p.jellyfish), ssw_sector_map.expected_jellyfish)
        if (len(p.trading_ports) == ssw_sector_map.expected_trading_ports):
            print >>fout, "  %d (all) trading ports" % len(p.trading_ports)
        else:
            print >>fout, "  %d of %d trading ports" % (len(p.trading_ports), ssw_sector_map.expected_trading_ports)
        if (len(p.ipts) == ssw_sector_map.expected_ipts):
            print >>fout, "  %d (all) IPT Beacons" % len(p.ipts)
        else:
            print >>fout, "  %d of %d IPT Beacons" % (len(p.ipts), ssw_sector_map.expected_ipts)
        if (len(p.luvsats) == ssw_sector_map.expected_luvsats):
            print >>fout, "  %d (all) luvsats" % len(p.luvsats)
        else:
            print >>fout, "  %d of %d luvsats" % (len(p.luvsats), ssw_sector_map.expected_luvsats)
    
    if print_sectors_controlled:
        print >>fout
        print >>fout, "Sector control:"
        neutral = len(ssw_sector_map.all_sectors)
        for soc, sectors in sorted(ssw_map_utils.sectors_by_society(p).iteritems()):
            neutral -= len(sectors)
            print >>fout, "  %s - %d sector(s) (%.1f%%) - %s" % (soc, len(sectors), 100.0*len(sectors)/len(ssw_sector_map.all_sectors), str(sectors))
        print >>fout, "  Neutral - %d sector(s) (%.1f%%)" % (neutral, 100.0*neutral/len(ssw_sector_map.all_sectors))
    
    if print_probe_sectors:
        print >>fout
        if p.known_sectors == len(ssw_sector_map.all_sectors):
            print >>fout, "No sectors to probe"
        else:
            print >>fout, "%d sector(s) to probe: %s" % (len(ssw_map_utils.all_unknown_sectors(p)), str(ssw_map_utils.all_unknown_sectors(p)))

    if print_missing_links:
        print >>fout
        ssw_map_utils.dump_missing_links(p, fout)
    
    if enhance:
        # Now add in any invariant information that we don't know
        p.enhance_map()
    
    # And add in any asteroids if an asteroid file was provided
    if len(asteroids_file) > 0:
        import_asteroids_file(asteroids_file, p)
    
    # Extract list of drones by sector if we need it
    if print_asteroids:
        drones_by_sector = ssw_map_utils.drones_by_sector(p)
    
    if print_buy_prices or print_sell_prices:
        print >>fout
        print >>fout, "Best Trading Port prices:"
    
    # Find best ore sell prices if necessary
    if print_trade_routes or print_sell_prices or print_shields or print_ore_buying_routes or ore_of_interest != None or len(ores_to_buy) > 0:
        ore_buy = ssw_map_utils.places_to_buy_ores(p, society)
    
    if print_sell_prices:
        for (ore,price_list) in sorted(ore_buy.iteritems()):
            if len(price_list) > 0:
                (price,sectors) = price_list[0]
                print >>fout, " %s for sale for %d in %s" % (ore, price, ports_str(sectors))
    
    # Find best ore buy prices if necessary
    if print_trade_routes or print_mining_routes or print_buy_prices or ore_of_interest != None:
        ore_sell = ssw_map_utils.places_to_sell_ores(p, society)
    
    if print_buy_prices:
        print >>fout
        for (ore,price_list) in sorted(ore_sell.iteritems()):
            if len(price_list) > 0:
                (price,sectors) = price_list[0]
                print >>fout, " %s bought for %d in %s" % (ore, price, ports_str(sectors))
    
    if print_trade_routes:
        profits = []
        for ore,price_list in ore_sell.iteritems():
            for sell_price, sell_sectors in price_list:
                for buy_price, buy_sectors in ore_buy[ore]:
                    if sell_price > buy_price:
                        profits.append((ore,sell_price-buy_price,sell_price,buy_price,buy_sectors,sell_sectors))
    
        print >>fout
        # Print trade routes from least to greatest profit
        print >>fout, "%d Most Profitable Trade Routes" % max_trade_routes
        # Go through from highest to lowest profit
        trade_routes = 0
        for (ore,profit,sell_price,buy_price,buy_sectors,sell_sectors) in sorted(profits, key=operator.itemgetter(1), reverse=True):
            if (len(buy_sectors) > 0) and (len(sell_sectors) > 0) and (trade_routes < max_trade_routes):
                print >>fout, "  %d profit buying %s for %d from %s and selling in %s" % (profit,ore,buy_price,ports_str(buy_sectors),ports_str(sell_sectors)) 
                # Don't count it if there are no routes
                buy_sects = [sector for sector, alignment in buy_sectors]
                sell_sects = [sector for sector, alignment in sell_sectors]
                if 0 < print_routes(p, buy_sects, sell_sects, society, True, unexplored_sector_society, routes_to_print):
                    trade_routes += 1
        if trade_routes < max_trade_routes:
            if trade_routes == 0:
                print >>fout, "  No trade routes found"
            else:
                print >>fout, "  Only %d trade route(s) found" % trade_routes
    
    if print_mining_routes or print_asteroids or (ore_of_interest != None):
        asteroids = ssw_map_utils.asteroids_by_ore(p, society)
        all_asteroids = ssw_map_utils.asteroids_by_ore(p, None)

    if print_mining_routes:
        print >>fout
        # Print mining routes
        print >>fout, "%d Most Profitable Mining Routes" % max_mining_routes
        ast_list = []
        for ore,price_list in ore_sell.iteritems():
            if len(price_list) > 0:
                (sell_price, sell_sectors) = price_list[0]
                ast_list.append((ore, sell_price, sell_sectors))
        # Go through from highest to lowest sell price
        mining_routes = 0
        for (ore,sell_price,sell_sectors) in sorted(ast_list, key=operator.itemgetter(1), reverse=True):
            if (ore in asteroids) and (len(asteroids[ore]) > 0) and (len(sell_sectors) > 0) and (mining_routes < max_mining_routes):
                print >>fout, "  Mine %s in %s, sell for %d in %s" % (ore, str(asteroids[ore]),sell_price,ports_str(sell_sectors))
                sell_sects = [sector for sector, alignment in sell_sectors]
                if 0 < print_routes(p, asteroids[ore], sell_sects, society, False, unexplored_sector_society, routes_to_print):
                    mining_routes += 1
        if mining_routes < max_mining_routes:
            if mining_routes == 0:
                print >>fout, "  No mining routes found"
            else:
                print >>fout, "  Only %d mining route(s) found" % mining_routes
    
    if print_ore_buying_routes:
        print >>fout
        print >>fout, "Cheapest places to buy ores"
        for ore,price_list in sorted(ore_buy.iteritems(), key=operator.itemgetter(0)):
            print_ore_buy_routes(p, ore, price_list, "    ", min_buy_routes, society, unexplored_sector_society, '  ')
            print >>fout
    
    if print_shields and not print_ore_buying_routes:
        shields = ssw_map_utils.shield_ore
        print >>fout
        if shields in ore_buy:
            print_ore_buy_routes(p, shields, ore_buy[shields], '  ', min_buy_routes, society, unexplored_sector_society)
    
    if ore_of_interest != None:
        print >>fout
        if len(ore_buy[ore_of_interest]) > 0 or len(routes) > 0:
            print >>fout, "Places to get %s ore" % ore_of_interest
        if len(ore_buy[ore_of_interest]) == 0:
            print >>fout, "  Nowhere to buy it"
        # Buy it from trading ports
        routes_printed = 0
        for price, sector_list in ore_buy[ore_of_interest]:
            if routes_printed >= routes_to_print:
                break
            routes_printed += print_best_ore_prices(p, sector_list, "  Buy for " + str(price) + " - ", society, True, False, unexplored_sector_society)
    
        # Could mine it from asteroids
        try:
            routes = ssw_map_utils.best_routes(p, asteroids[ore_of_interest], None, society, unexplored_sector_society)
        except KeyError:
            routes = ()
        if len(routes) > 0:
            print >>fout, "  Or mine it :"
        else:
            print >>fout, "  Nowhere to mine it"
        # Note that we don't need to limit these because there can only be one per asteroid
        for distance, route, drones, src, dest in routes:
            # Don't print if no route
            if distance < ssw_sector_map.sectors_per_row:
                print >>fout, "   %s" % (route)
    
        if len(ore_sell[ore_of_interest]) > 0:
            print >>fout, "Places to get rid of %s ore" % ore_of_interest
        else:
            print >>fout, "Nowhere to sell %s ore" % ore_of_interest
        routes_printed = 0
        for price, sector_list in ore_sell[ore_of_interest]:
            if routes_printed >= routes_to_print:
                break
            routes_printed += print_best_ore_prices(p, sector_list, "  Sell for " + str(price) + " - ", society, False, True, unexplored_sector_society)
    
        # TODO: List some profitable trade routes, too ? (max_trade_routes ?)
        pass

    if len(ores_to_buy) >0:
        print >>fout
        print >>fout, "Best way to buy %s:" % ', '.join(ores_to_buy)
        # These are keyed by port/sector number
        route_by_port = {}
        distances = {}
        # These are keyed by ore name
        ores_str = {}
        ports = {}
        # First, find the best places to buy each of the ores
        for ore in ores_to_buy:
            # Cheapest price is the first in the list
            (price, sector_list) = ore_buy[ore][0]
            ports[ore] = sector_list
            ores_str[ore] = '%s for %d' % (ore, price)
            for sector in sector_list:
                (distance, route, drones, src, dest) = ssw_map_utils.best_route_to_sector(p, sector, None, society, unexplored_sector_society)
                distances[sector] = distance
                route_by_port[sector] = route
        # Now check whether we can save time by buying two ores at once
        # Find all the combos of ports we could use
        port_sets = []
        for ore in ores_to_buy:
            port_sets = add_ports_to_port_sets(port_sets, ports[ore], ore)
        # Find the distance for each port_set, and stuff it in there
        dist_port_sets = [(total_distance(port_set.values(), distances), port_set) for port_set in port_sets]
        # Now sort dist_port_sets by total distance
        dist_port_sets.sort(key=operator.itemgetter(0))
        # There may be multiple routes with the same length,
        # in which case we report all of them
        for best_dist_port_set in dist_port_sets:
            if best_dist_port_set[0] > dist_port_sets[0][0]:
                break
            for port in set(best_dist_port_set[1].values()):
                intro = '    Buy ' + ', '.join([ore for ore in ores_to_buy if best_dist_port_set[1][ore] == port])
                print >>fout, '%s - %s' % (intro, route_by_port[port])
            print >>fout, '  Total distance = %d moves' % best_dist_port_set[0]
            print >>fout

    if print_asteroids:
        print >>fout
        print >>fout, "Asteroids"
        for ore in sorted(all_asteroids.keys()):
            print >>fout, "  %d of %d %s asteroids in %s" % (len(all_asteroids[ore]),
                                                             p.expected_asteroids()/len(all_asteroids.keys()),
                                                             ore,
                                                             sector_str(all_asteroids[ore])),
            if (len(p.drones) > 0):
                print >>fout, " %s" % ( drone_str_for_sectors(all_asteroids[ore],
                                                              drones_by_sector))
            else:
                print >>fout
        print >>fout
        print >>fout, "Asteroid clusters"
        for group in sorted(ssw_map_utils.asteroid_clusters(p), key=len, reverse=True):
            if len(group) > 1:
                ores = sorted([ore for ore, sector in group])
                sectors = sorted([sector for ore, sector in group])
                print >>fout, "  %d asteroids %s in sectors %s" % (len(group), str(ores), str(sectors)),
                if (len(p.drones) > 0):
                    print >>fout, " %s" % (drone_str_for_sectors(sectors, drones_by_sector))
                else:
                    print >>fout
        print >>fout
        print >>fout, "Asteroids next to planets"
        for ore, sector in sorted(ssw_map_utils.asteroids_by_planets(p),key=operator.itemgetter(0)):
            if sector in drones_by_sector:
                drones = " ['"+ drones_by_sector[sector] + "']"
            else:
                drones = ""
            planets = [planet for (planet, loc) in p.planets if loc in ssw_sector_map.adjacent_sectors(sector, p.can_move_diagonally())]
            planets_str = planet_str(planets)
            print >>fout, "  %s asteroid in sector %d next to %s%s" % (ore, sector, planets_str, drones)
        # Only display asteroid ownership if we know of at least one droned sector
        if (len(p.drones) > 0):
            for soc in ssw_societies.adjectives:
                print >>fout
                print >>fout, "%s Asteroid sectors" % soc
                all_ast_sectors = []
                for ore,sectors in all_asteroids.items():
                    all_ast_sectors += [sector for sector in sectors if sector in drones_by_sector and drones_by_sector[sector] == soc]
                print >>fout, "  %s (%d)" % (str(all_ast_sectors), len(all_ast_sectors))
    
    if print_luvsats:
        print >>fout
        print >>fout, "LuvSats"
        for dis,route,drones,src,dest in ssw_map_utils.best_routes(p, p.luvsats, None, society, unexplored_sector_society):
            print >>fout, " %s" % (route)
    
    if print_your_drones:
        print >>fout
        print >>fout, "Your Drones"
        for drones, sector in p.your_drones:
            print >>fout, " %d drones in sector %d" % (drones, sector)

    # Check that this is today's map
    if not ssw_map_utils.is_todays(p):
        print
        print "**** Map is more than 24 hours old"
        print "From cycle %d," % p.cycle(),
        if (p.war_ongoing()):
            print "before",
        else:
            print "after",
        print "the war ended"
    
    # Check for unknown sectors with jellyfish
    unknown_sectors_with_jellyfish = ssw_map_utils.unknown_sectors_with_jellyfish(p)
    if len(unknown_sectors_with_jellyfish) > 0:
        print
        print "**** Don't forget to feed the empaths at New Ceylon"
        print "**** That will explore %d sector(s) : %s" % (len(unknown_sectors_with_jellyfish), str(sorted(list(unknown_sectors_with_jellyfish))))
    
    if output_filename != None:
        fout.close()

    # Return the parsed map, in case we're a mere utility
    return p

if __name__ == '__main__':
    main(*sys.argv[1:])
    
