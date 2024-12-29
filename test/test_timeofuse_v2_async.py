#!/usr/bin/env python3
# I suspect that I haven't got to grips with the way phthon does things, but soppusely this will setup the path to allod for the sonnen batteri moduel to be in a separate location
# To me having to do this for testing seems a horrendous hack
import asyncio
import os
import sys
import time
script_path = os.path.realpath(os.path.dirname(__name__))
os.chdir(script_path)
sys.path.append("..")

from login import *
from pprint import pprint
from sonnenbatterie2 import AsyncSonnenBatterieV2
from timeofuse import TimeofUseSchedule
from timeofuse.timeofuse import create_time_of_use_entry
from sonnenbatterie2.const import SONNEN_OPERATING_MODE_TIME_OF_USE_NAME

async def test_timeofuse():
    sb = AsyncSonnenBatterieV2(SONNEN_IP, SONNEN_TOKEN)
    operating_mode_name = await sb.get_operating_mode_name()
    print(f"\nOriginal operating mode is {operating_mode_name}")
    print(f"\nSetting operating mode name to {SONNEN_OPERATING_MODE_TIME_OF_USE_NAME}")
    pprint(await sb.set_operating_mode_by_name(SONNEN_OPERATING_MODE_TIME_OF_USE_NAME))
    print(f"\nSet operating mode to {await sb.get_operating_mode_name()}")
    tous = TimeofUseSchedule()
    print("\nExtract tou schedule as string")
    orig_battery_tou_string = await sb.get_tou_schedule_string()
    orig_battery_tou_json = await sb.get_tou_schedule_json()
    pprint(await sb.get_tou_schedule_string())
    print("\nExtract tou schedule as json objects")
    pprint(await sb.get_tou_schedule_json())
    print("\nExtract tou schedule as text schedule")
    pprint(await sb.get_tou_schedule_object())
    print("\nLoad tou schedule from json")
    tous.load_tou_schedule_from_json(await sb.get_tou_schedule_json())
    print("\nLoaded tou schedule")
    print(tous.get_as_tou_schedule())
    ### Disabled since Sonnen seems to have changed the format
    print ("\nCreate a new TOU Schedule 10:00 - 11:00 and 14:00 - 15:00")
    tous_new = TimeofUseSchedule()
    tous_new.add_entry(create_time_of_use_entry(10,00,11,00))
    tous_new.add_entry(create_time_of_use_entry(14,00,15,00))
    print("Setting new TOU schedule to ")
    print(tous_new.get_as_tou_schedule())
    await sb.set_tou_schedule_json(tous_new.get_as_tou_schedule())
    print("Sleeping for 60 seconds so you can check the change has been applied")
    time.sleep(60)
    print("\nExtract replaced tou schedule as objects")
    pprint(await sb.get_tou_schedule_json())
    print("\nExtract restored tou schedule as string")
    pprint(await sb.get_tou_schedule_string())
    ### Disabled since Sonnen seems to have changed the format
    print(f"\nRestoring origional TOU schedule to {orig_battery_tou_string}")
    await sb.set_tou_schedule_json(orig_battery_tou_json)
    print("Sleeping for 60 seconds so you can check the change has been applied")
    time.sleep(60)
    print(f"\nResetting operating mode name to {operating_mode_name}")
    pprint(await sb.set_operating_mode_by_name(operating_mode_name))
    print(f"\nReset operating mode to {await sb.get_operating_mode_name()}")
    await sb.logout()

if __name__ == '__main__':
    asyncio.run(test_timeofuse())