#!/usr/bin/env python3
# I suspect that I haven't got to grips with the way phthon does things, but soppusely this will setup the path to allod for the sonnen batteri moduel to be in a separate location
# To me having to do this for testing seems a horrendous hack
import os, sys, json
script_path = os.path.realpath(os.path.dirname(__name__))
os.chdir(script_path)
sys.path.append("..")
from login import *
from pprint import pprint
from sonnenbatterie.timeofuse import timeofuse, timeofuseschedule
if (__name__ == '__main__'):
    tous = timeofuseschedule()  
    print("\nEmpty schedule")
    pprint(tous.get_as_tou_schedule())
    tou=timeofuse.create_time_of_use_entry()
    print("\nOverlapping midnight schedule")
    pprint(tous.add_entry(tou))
    print ("\nAdding non overlaping entry")
    tou=timeofuse.create_time_of_use_entry(10,0,11,0)
    pprint(tous.add_entry(tou))
    print ("\nAdding fully overlaping entry")
    tou=timeofuse.create_time_of_use_entry(9,0,12,0)
    try:
        tous.add_entry(tou)
        print ("\nOpps, no exception, tnis is a bug")
    except Exception as e:
        print ("\nExpected exception message "+str(e.args))

    pprint(tous.get_as_tou_schedule())

    print ("\nAdding overlaping start entry")
    tou=timeofuse.create_time_of_use_entry(9,0,10,30)
    try:
        tous.add_entry(tou)
        print ("\nOpps, no exception, tnis is a bug")
    except Exception as e:
        print ("\nExpected exception message "+str(e.args))
    pprint(tous.get_as_tou_schedule())

    print ("\nAdding overlaping end entry")
    tou=timeofuse.create_time_of_use_entry(10,30, 11, 30)
    try:
        tous.add_entry(tou)
        print ("\nOpps, no exception, tnis is a bug")
    except Exception as e:
        print ("\nExpected exception message "+str(e.args))
    pprint(tous.get_as_tou_schedule())

    print ("\nAdding exacty match overlaping entry")
    tou=timeofuse.create_time_of_use_entry(10,0,11,0)
    try:
        tous.add_entry(tou)
        print ("\nOpps, no exception, tnis is a bug")
    except Exception as e:
        print ("\nExpected exception message "+str(e.args))
    pprint(tous.get_as_tou_schedule())

    print ("\Building based on returned entry")
    old_schedule = tous.get_as_tou_schedule()
    tous = timeofuseschedule() 
    tous.load_tou_schedule(old_schedule)

    print("\nAfter schedule load")
    pprint(tous.get_as_tou_schedule())
    print("\nAfter deleting index entry")
    pprint(tous.delete_entry(1))
    js = json.dumps(tous.get_as_tou_schedule())
    print("Dumped json data "+js)
    
