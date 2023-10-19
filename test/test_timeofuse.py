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
from sonnenbatterie.const import SONNEN_OPERATING_MODE_TIME_OF_USE_NAME
if (__name__ == '__main__'):
    sb = sonnenbatterie(SONNEN_USERNAME, SONNEN_PASSWORD, SONNEN_IP)
    operating_mode_name = sb.get_operating_mode_name()
    print("\nOrigional operating mode is "+operating_mode_name)
    print("\nSetting operating mode name to "+SONNEN_OPERATING_MODE_TIME_OF_USE_NAME)
    pprint(sb.set_operating_mode_by_name(SONNEN_OPERATING_MODE_TIME_OF_USE_NAME))
    print("\nSet operating mode to "+sb.get_operating_mode_name())
    tous = timeofuseschedule()  
    print("\nExtract tou schedule as string")
    orig_battery_tou_string=sb.get_time_of_use_schedule_as_string()
    orig_battery_tou_json = sb.get_time_of_use_schedule_as_json_objects()
    pprint(sb.get_time_of_use_schedule_as_string())
    print("\nExtract tou schedule as json objects")
    pprint(sb.get_time_of_use_schedule_as_json_objects())
    print("\nExtract tou schedule as text schedule")
    pprint(sb.get_time_of_use_schedule_as_schedule())
    print("\nLoad tou schedule from json")
    tous.load_tou_schedule_from_json(sb.get_time_of_use_schedule_as_json_objects())
    print("\nLoaded tou schedule")
    pprint(tous.get_as_tou_schedule())
    print ("\nCreate a new TOU Schedule 10:00 - 11:00 and 14:00 - 15:00")
    tous_new =  timeofuseschedule()  
    tous_new.add_entry(timeofuse.create_time_of_use_entry(10,00,11,00))
    tous_new.add_entry(timeofuse.create_time_of_use_entry(14,00,15,00))
    print("Setting new TOU schedule to ")
    pprint(tous_new.get_as_tou_schedule())
    sb.set_time_of_use_schedule_from_json_objects(tous_new.get_as_tou_schedule())
    print("Sleeping for 60 seconds so you can chect the change has been applied")
    time.sleep(60)
    print("\nExtract replaced tou schedule as objects")
    pprint(sb.get_time_of_use_schedule_as_json_objects())
    print("\nExtract restored tou schedule as objects")
    pprint(sb.get_time_of_use_schedule_as_json_objects())
    print("\nRestoring origional TOU schedule to "+orig_battery_tou_string)
    sb.set_time_of_use_schedule_from_json_objects(orig_battery_tou_json)
    print("Sleeping for 60 seconds so you can chect the change has been applied")
    time.sleep(60)
    print("\nReetting operating mode name to "+operating_mode_name)
    pprint(sb.set_operating_mode_by_name(operating_mode_name))
    print("\nReset operating mode to "+sb.get_operating_mode_name())
