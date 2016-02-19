#!/usr/bin/python

# Copyright 2008 Squiffle
#
# Script to help find those 3 pieces in prime-numbered sectors.

# TODO : Clean up UI if user makes a mistake

# Of course ideally, we'd use the number of times each sector appears
# as the "value" of visiting it, and the number of turns to get there
# as the "cost" and we'd find a solution to maximise value and minimise
# cost. I think that means solving the travelling salesman problem, though.

import sys
import getopt

all_sectors = range(1,1090)

# all prime numbers less than 1090
# from some webpage somewhere
primes = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29,
          31, 37, 41, 43, 47, 53, 59, 61, 67, 71,
          73, 79, 83, 89, 97, 101, 103, 107, 109, 113,
          127, 131, 137, 139, 149, 151, 157, 163, 167, 173,
          179, 181, 191, 193, 197, 199, 211, 223, 227, 229,
          233, 239, 241, 251, 257, 263, 269, 271, 277, 281,
          283, 293, 307, 311, 313, 317, 331, 337, 347, 349,
          353, 359, 367, 373, 379, 383, 389, 397, 401, 409,
          419, 421, 431, 433, 439, 443, 449, 457, 461, 463,
          467, 479, 487, 491, 499, 503, 509, 521, 523, 541,
          547, 557, 563, 569, 571, 577, 587, 593, 599, 601,
          607, 613, 617, 619, 631, 641, 643, 647, 653, 659,
          661, 673, 677, 683, 691, 701, 709, 719, 727, 733,
          739, 743, 751, 757, 761, 769, 773, 787, 797, 809,
          811, 821, 823, 827, 829, 839, 853, 857, 859, 863,
          877, 881, 883, 887, 907, 911, 919, 929, 937, 941,
          947, 953, 967, 971, 977, 983, 991, 997, 1009, 1013,
          1019, 1021, 1031, 1033, 1039, 1049, 1051, 1061, 1063, 1069,
          1087]

# If we've already found a piece, where was it ?
found1 = None

# List of sectors we've searched
visited = []

# List of sets of three sectors that meet the search criteria
triples = []

# List of sectors worth visiting.
# Sectors are added multiple times if they occur in multiple triples
sectors_to_visit = []

def usage():
    '''
    Print usage info for the script
    '''
    print "Usage: %s sum [-f sector_found] [list of visited sectors]" % (sys.argv[0])
    print "    where sector_found is the sector where a piece has been found"
    print "    and list of visited sectors is a list of sectors that have been checked"
    print "    all sector are number in the range %d..%d" % (all_sectors[0], all_sectors[-1])
    print "    e.g. %s 1201 -f 151 3 5 7" % sys.argv[0]
    print "      - visited 3, 5, 7, and 151 and found a piece in 151"

def find_triple(first, second, sum, primes):
    '''
    Given the first 2 sectors, is there a possible third ?
    If so, add the triple to triples and the 3 sectors to sectors_to_visit
    '''
    k = sum - (first + second)
    if (k in primes) and (second < k):
        triples.append((first, second, k))
        sectors_to_visit.append(first)
        sectors_to_visit.append(second)
        sectors_to_visit.append(k)

def compare(x, y):
    '''
    Compare two (sector, count) tuples
    '''
    # First compare the counts
    if x[1] == y[1]:
        # Then the sector numbers
        return cmp(x[0], y[0])
    # Largest count first
    return -cmp(x[1], y[1])

# Parse command-line arguments
if (len(sys.argv) < 2):
    usage()
    sys.exit(2)

# Sum comes first
sum = int(sys.argv[1])

# Check for piece found already
try:
    opts, args = getopt.getopt(sys.argv[2:], "f:")
except getopt.GetOptError:
    usage()
    sys.exit(2)

visited_start = 2
for opt,arg in opts:
    found1 = int(arg)
    if found1 not in all_sectors:
        usage()
        sys.exit(2)
    visited_start = 4

# Rest are sectors that have been visited
for v in sys.argv[visited_start:]:
    if int(v) not in all_sectors:
        usage()
        sys.exit(2)
    else:
        visited.append(int(v))

# For convenience, take a found sector out of the visited list
if (found1 != None) and (found1 in visited):
    visited.remove(found1)

# Sectors we've visited aren't candidates
for i in visited:
    try:
        primes.remove(i)
    except ValueError:
        # Doesn't matter if it's not in the list
        print "%d isn't prime" % i

# Search for the candidate sectors
if found1 != None:
    for j in primes:
        find_triple(found1, j, sum, primes)
else:
    for i in primes:
        for j in primes:
            if i < j :
                find_triple(i, j, sum, primes)

# Print all solutions
#print "Prime sectors that sum to %d (%d combos):" % (sum, len(triples))
#
#for (i,j,k) in triples:
#    print "%d + %d + %d" % (i,j,k)
#print

# List best sectors to search
temp = [(s, sectors_to_visit.count(s)) for s in set(sectors_to_visit)]
freqs = sorted(temp, compare)
print "Sectors by frequency (max %d to visit):" % len(freqs)
print "(there are %d prime sectors, %d sectors total)" % (len(primes), len(all_sectors))
for (sector, count) in freqs:
    print "Sector %d (%d occurrences)" % (sector, count)

