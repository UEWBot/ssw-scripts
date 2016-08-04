#!/usr/bin/python

'''
Utilities to deal with SSW societies and alignments
'''

# Copyright 2008, 2016 Squiffle

'''all the initials'''
initials = "AEIOT"

'''all the full names'''
full_names = ["The Order of the Amaranth",
              "The Order of the Eastern Star",
              "The Illuminati",
              "The Society of Oddfellows",
              "The Triad Cabbal"]

'''all the short names'''
short_names = ["Amaranth",
               "Eastern Star",
               "Illuminati",
               "Oddfellow",
               "Triad"]

'''all the adjectives'''
adjectives = ["Amaranthine",
              "Eastern Star",
              "Illuminati",
              "Oddfellowish",
              "Triadi"]

class Invalid_Society(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

def full_name(initial):
    '''
    Maps the initial letter of a society to the full name
    '''
    try:
        return full_names[initials.index(initial.upper())]
    except ValueError:
        raise Invalid_Society(initial)

def adjective(initial):
    '''
    Maps the initial letter of a society to the adjective
    '''
    for society in adjectives:
        if society[0].lower() == initial.lower():
            return society
    raise Invalid_Society(initial)

def initial(good, order):
    '''
    Maps a pair of Trading Port Good/Evil and Order/Chaos numbers to a society initial
    '''
    if good < 0:
        if order < 0:
            return 'E'
        elif order > 0:
            return 'T'
    elif good > 0:
        if order < 0:
            return 'O'
        elif order > 0:
            return 'I'
    return 'A'

