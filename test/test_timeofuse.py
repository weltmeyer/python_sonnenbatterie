#!/usr/bin/env python3
# I suspect that I haven't got to grips with the way phthon does things, but soppusely this will setup the path to allod for the sonnen batteri moduel to be in a separate location
# To me having to do this for testing seems a horrendous hack
import os, sys, time
script_path = os.path.realpath(os.path.dirname(__name__))
os.chdir(script_path)
sys.path.append("..")
from login import *
from pprint import pprint
from sonnenbatterie.sonnenbatterie import sonnenbatterie
from sonnenbatterie.timeofuse import timeofuse, timeofuseschedule
if (__name__ == '__main__'):
    sb = sonnenbatterie(SONNEN_USERNAME, SONNEN_PASSWORD, SONNEN_IP)
    tous = timeofuseschedule()  
    print("\nExtract tou schedule as string")
    battery_tou_string=sb.get_time_of_use_schedule_as_string()
    pprint(sb.get_time_of_use_schedule_as_string())
    print("\nExtract tou schedule as objects")
    pprint(sb.get_time_of_use_schedule_as_objects())
    print("\nLoad tou schedule as objects")
    tous.load_tou_schedule(sb.get_time_of_use_schedule_as_objects())
    print("\nLoaded tou schedule")
    pprint(tous.get_as_tou_schedule())
    tous_new =  timeofuseschedule()  
    tous_new.add_entry(timeofuse.create_time_of_use_entry(10,00,11,00))
    tous_new.add_entry(timeofuse.create_time_of_use_entry(14,00,15,00))
    print("Setting new TOU schedule to ")
    pprint(tous_new.get_as_tou_schedule())
    sb.set_time_of_use_schedule_from_objects(tous_new.get_as_tou_schedule())
    print("Sleeping for 60 seconts so you can chect the change has been applied")
    time.sleep(60)
    print("\nExtract replaced tou schedule as objects")
    pprint(sb.get_time_of_use_schedule_as_objects())
    print("\nRevert tou schedule as tiring")
    sb.set_time_of_use_schedule_from_string(battery_tou_string)
    print("\nExtract restored tou schedule as objects")
    pprint(sb.get_time_of_use_schedule_as_objects())
