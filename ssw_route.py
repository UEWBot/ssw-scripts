#!/usr/bin/python

'''
Script to find a route through an SSW sector map
'''

# Copyright 2009, 2015 Squiffle

import ssw_sector_map2 as ssw_sector_map
import ssw_map_utils, ssw_societies, operator, sys, getopt, datetime

version = 1.00

fout = sys.stdout

def usage(progname, map_file):
    '''
    Prints usage information
    '''
    print "Usage: %s [-d {a|e|i|o|t}] [-e] [-m] [map_filename] sector [sectors]" % progname
    print
    print " Find route to visit the specified sectors"
    print " Looks for a route to the first sector from anywhere. If more"
    print " sectors are listed, looks for a route to travel through them."
    print " Currently only tries to visit them in the specified order."
    print
    print "  -d|--drones {a|e|i|o|t} - avoid drones not belonging to the specified society"
    print "  -e|--empire - assume that unexplored sectors contain Amaranth drones"
    print "  -h|--help - print this usage messge"
    print "  -m|--missing_links - dump the list of found missing links"
    print "  map_filename defaults to %s" % map_file
    print
    print " Version %.2f. Brought to you by Squiffle" % version

def main(*arguments):
    '''
    Do whatever the user wants !
    Returns the parsed map.
    '''
    # Defaults, changeable from the command line
    default_map_file = "ssw_sector_map.htm"
    map_file = default_map_file
    society = None
    unexplored_sector_society = None
    sectors_to_visit = []
    dump_missing_links = False

    global fout

    # Parse command-line options
    try:
        opts, args = getopt.getopt(arguments,"ed:hm",["empire","drones=","help","missing_links"])
    except getopt.GetoptError:
        usage(sys.argv[0], map_file)
        sys.exit(2)

    for arg in args:
        try:
            val = int(arg)
            if val in ssw_sector_map.all_sectors:
                sectors_to_visit.append(val)
            else:
                usage(sys.argv[0], default_map_file)
                sys.exit(2)
        except:
            if map_file == default_map_file:
                map_file = arg
            else:
                usage(sys.argv[0], default_map_file)
                sys.exit(2)

    for opt,arg in opts:
        if (opt == '-d') or (opt == '--drones'):
            try:
                society = ssw_societies.adjective(arg)
            except ssw_societies.Invalid_Society:
                print 'Unrecognised society "%s" - should be one of %s' % (arg, ssw_societies.initials)
                usage(sys.argv[0], map_file)
                sys.exit(2)
        elif (opt == '-e') or (opt == '--empire'):
            unexplored_sector_society = ssw_societies.adjective('a')
        elif (opt == '-h') or (opt == '--help'):
            usage(sys.argv[0], default_map_file)
            sys.exit(0)
        elif (opt == '-m') or (opt == '--missing_links'):
            dump_missing_links = True
    
    if (len(sectors_to_visit) == 0) and not dump_missing_links:
        usage(sys.argv[0], default_map_file)
        sys.exit(2)
             
    # Read and parse the sector map
    page = open(map_file)
    p = ssw_sector_map.SectorMapParser(page)
    
    # Don't print warnings if we're extracting missing links,
    # because there will likely be lots of "missing link" warnings
    map_valid,reason = p.valid(dump_missing_links)
    if not map_valid:
        print >>fout, "Sector map file is invalid - %s" % reason
        sys.exit(2)
    
    # Now add in any invariant information that we don't know
    p.enhance_map()

    if len(sectors_to_visit) > 0:
        # Find and print the route
        # TODO Find the best route through the listed sectors
        # Note that first time through the loop, from_sector == to_sector,
        # which means "find a route to this sector from anywhere"
        from_sector = sectors_to_visit[0]
        total_distance = 0
        overall_route = []
        drones = []
        for to_sector in sectors_to_visit:
            #print "Finding route from %d to %d" % (from_sector, to_sector)
            (distance, route_str, drone_list) = p.shortest_route(from_sector,
                                                                 to_sector,
                                                                 society,
                                                                 unexplored_sector_society)
            total_distance += distance
            overall_route.append(route_str)
            drones += drone_list
            from_sector = to_sector
        print "Total distance is %d" % total_distance
        for route in overall_route:
            print route,
        print ssw_map_utils.drones_str(drones)

    if dump_missing_links:
        var_str = "cycle_%d_links = " % p.cycle()
        indent = len(var_str) + 1
        indent_str = ' ' * indent
        print var_str,
        missing_link_str = str(p.missing_links)
        # Split the very long string over multiple lines
        start_idx = 0
        end_idx = 0
        while (end_idx < len(missing_link_str)):
            idx = missing_link_str.find(']', end_idx + 1)
            if (idx == -1):
                #print "Got to the end (idx == -1)"
                end_idx = len(missing_link_str)
                print indent_str + missing_link_str[start_idx-1:]
            else:
                total_len = indent + idx + 1 - start_idx
                #print "idx = %d. Total_len = %d" % (idx, total_len)
                if (total_len >= 79):
                    # We already printed the variable on the first line
                    if (start_idx > 0):
                        print indent_str,
                    # Include the following comma
                    print missing_link_str[start_idx:end_idx+2]
                    start_idx = end_idx + 3
                    #print "Set start_idx to %d" % start_idx
                end_idx = idx
                #print "Set end_idx to %d" % end_idx
    
    # Check that this is today's map
    if not ssw_map_utils.is_todays(p):
        print
        print "**** Map is more than 24 hours old"
    
    # Check for unknown sectors with jellyfish
    unknown_sectors_with_jellyfish = ssw_map_utils.unknown_sectors_with_jellyfish(p)
    if len(unknown_sectors_with_jellyfish) > 0:
        print
        print "**** Don't forget to feed the empaths at New Ceylon"
        print "**** That will explore %d sector(s) : %s" % (len(unknown_sectors_with_jellyfish),
                                                            str(sorted(list(unknown_sectors_with_jellyfish))))
    
    # Return the parsed map, in case we're a mere utility
    return p

if __name__ == '__main__':
    main(*sys.argv[1:])
    
