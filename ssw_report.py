#!/usr/bin/python

'''
Script to create my daily trade reports
'''

# Copyright 2008, 2015-2016 Squiffle

# TODO: Add command-line options to specify filenames

import ssw_sector_map2 as ssw_sector_map
import ssw_trade_routes, ssw_societies
import sys, getopt

version = 0.1

# Defaults
for_33ers = False
temp_filename = '/tmp/cbrand_ssw_output.txt'
options = ['--no-summary', '--cheapest-ore']
options_33 = options + ['--drones']
society = ssw_societies.adjective('i')

def usage(progname):
    '''
    Prints usage information
    '''
    print
    print "usage: %s [-3 society|-h|--help]" % progname
    print
    print "  -3|-33 - print report for 33ers"
    print "  society - which society to report for."
    print "  -h|--help - print this usage info and exit"
    print
    print " Version %.2f. Brought to you by Squiffle" % version

# Parse command-line options
try:
    opts, args = getopt.getopt(sys.argv[1:], "3:h", ["33=", "help"])
except getopt.GetoptError:
    usage(sys.argv[0])
    sys.exit(2)

for opt,arg in opts:
    if (opt == '-3') or (opt == '--33'):
        for_33ers = True
        try:
            society = ssw_societies.adjective(arg)
        except ssw_societies.Invalid_Society:
            print "Can't map %s to a society - should be one of %s" % (arg,
                                                                       ssw_societies.initials)
            usage(sys.argv[0])
            sys.exit(2)
        options_33.append(arg)
    elif (opt == '-h') or (opt == '--help'):
        usage(sys.argv[0])
        sys.exit(2)

if len(args) > 0:
    usage(sys.argv[0])
    sys.exit(2)

# Call ssw_trade_routes with the appopriate arguments
if for_33ers:
    # This one is easy - just call with the appropriate options
    p = ssw_trade_routes.main(*options_33)
else:
    options += ['--output', temp_filename]
    p = ssw_trade_routes.main(*options)

    # We need to pre-pend the "featured trade route" and trading port info
    # Find a trade route to feature
    file = open(temp_filename)
    best_ore = ''
    ore = ''
    price = 0
    best_length = ssw_sector_map.sectors_per_row 
    for line in file.xreadlines():
        # Look for the start of the next ore block
        if 'profit buying' in line:
            words = line.split()
            new_price = int(words[0])
            # Routes are in price order
            if best_ore != '' and new_price < price:
                # No point in looking further unless there were no routes for that ore
                break
            # If we get here, either this is the first ore in the list,
            # and thus a candidate for the best route, or we've found another
            # ore at the same price, in which case we need to compare
            # route lengths, or we rejected all earlier ores due to a lack or routes
            ore = words[3]
            price = new_price
        # If we have an ore, look for the first (shortest) route
        elif ore != '' and 'moves -' in line:
            words = line.split()
            length = int(words[0])
            if length < best_length:
                # This is an improvement
                best_length = length
                best_ore = ore
                route = line
            # Either way, this is (one of) the best routes for this ore
            ore = ''
    file.close()

    print "Today's featured trade route is for %s:" % best_ore
    print route

    # Dump out the number of trading ports we're missing
    missing_ports = ssw_sector_map.expected_trading_ports - len(p.trading_ports)
    if missing_ports > 0:
        ports_str = "port"
        if missing_ports > 1:
            ports_str = "ports"
        print "Note that I'm missing %d trading %s, so there may be better routes out there" % (missing_ports, ports_str)

    print

    # Then the bulk of the report
    file = open(temp_filename)
    found_blank_line = False
    for line in file.xreadlines():
        # Throw away everything up to and including the first blank line
        # to remove any "added asteroid" output
        if found_blank_line:
            print line,
        else:
            if len(line) == 1:
                found_blank_line = True
    file.close()

# Finally, append my signature
print "Squiffle"

