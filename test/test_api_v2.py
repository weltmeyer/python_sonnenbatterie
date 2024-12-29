#!/usr/bin/env python3
import asyncio
import os
import sys
import time

script_path = os.path.realpath(os.path.dirname(__name__))
os.chdir(script_path)
sys.path.append("..")

from sonnenbatterie2.sonnenbatterie2 import SonnenBatterieV2, AsyncSonnenBatterieV2

from pprint import pprint

from login import *

def main():
    print("\nTesting SonnenBatterieV2 - Sync API\n")
    sb2 = SonnenBatterieV2(SONNEN_IP, SONNEN_TOKEN)
    pprint(sb2.get_configurations())  # retrieve configuration overview
    pprint(sb2.get_battery_module_data())  # get battery module data
    pprint(sb2.get_inverter_data())  # retrieve inverter data
    pprint(sb2.get_latest_data())  # get latest date from sonnenbatterie
    pprint(sb2.get_powermeter_data())  # get data from power meters
    pprint(sb2.get_status())  # get overall status information
    pprint(sb2.get_io_data())  # get io status

async def async_main():
    print("\nTesting AsyncSonnenBatterieV2 - ASync API\n")
    sb2 = AsyncSonnenBatterieV2(SONNEN_IP, SONNEN_TOKEN)
    pprint(await sb2.get_configurations())  # retrieve configuration overview
    pprint(await sb2.get_battery_module_data())  # get battery module data
    pprint(await sb2.get_inverter_data())  # retrieve inverter data
    pprint(await sb2.get_latest_data())  # get latest date from sonnenbatterie
    pprint(await sb2.get_powermeter_data())  # get data from power meters
    pprint(await sb2.get_status())  # get overall status information
    pprint(await sb2.get_io_data())  # get io status
    await sb2.logout()

if __name__ == "__main__":
    start = time.time()
    main()
    print("--- %s seconds sync ---" % (time.time() - start))
    start = time.time()
    asyncio.run(async_main())
    print("--- %s seconds async ---" % (time.time() - start))