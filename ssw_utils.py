#!/usr/bin/python

'''
Low-level utilities for SSW scripts
'''

# Copyright 2008, 2015-2016 Squiffle

from __future__ import absolute_import
import operator, datetime, unittest
from six.moves import map

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

def drones_str(drones, possible_drones):
    '''
    Converts the list of drones en route to a string of societies.
    Possible drones is a boolean indicating whether to add "plus unexplored sectors".
    '''
    end = 'drones'
    if possible_drones:
        end += ', plus unexplored sectors'
    if len(drones):
        return '[' + ', '.join(set(drones)) + ' %s]' % end
    return '[no %s]' % end

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

def now_in_ssw():
    '''
    Return the datetime representing 'now' in SSW
    '''
    today = datetime.datetime.now()
    # Map datetimes are 1000 years in the future
    return today.replace(today.year+1000)

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

#TODO There is no function "enemy_drones_en_route()"...
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

