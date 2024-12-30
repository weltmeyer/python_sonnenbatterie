#!/usr/bin/env python3
# I suspect that I haven't got to grips with the way phthon does things, but soppusely this will setup the path to allod for the sonnen batteri moduel to be in a separate location
# To me having to do this for testing seems a horrendous hack
import asyncio
import os, sys
import threading
script_path = os.path.realpath(os.path.dirname(__name__))
os.chdir(script_path)
sys.path.append("..")

from login import *
from pprint import pprint
from sonnenbatterie.sonnenbatterie import AsyncSonnenBatterie
from sonnenbatterie.const import *

async def test_set_flow():
  sb = AsyncSonnenBatterie(SONNEN_USERNAME, SONNEN_PASSWORD, SONNEN_IP)
  operating_mode_name = await sb.get_operating_mode_name()
  current_flow = (await sb.get_status())["Pac_total_W"]
  print(f"current total flow is {current_flow}")
  print(f"Setting operating mode name to {SONNEN_OPERATING_MODE_MANUAL_NAME}")
  pprint(await sb.set_operating_mode_by_name(SONNEN_OPERATING_MODE_MANUAL_NAME))
  e = threading.Event() 
  print("Waiting 5 seconds for things to settle down")
  e.wait(5)
  manual_flow = (await sb.get_status())["Pac_total_W"]
  print(f"Flow on manual is {manual_flow}")
  print("Setting a charge rate of 100") 
  # set to a charge rate of 100
  set_resp = await sb.sb2.charge_battery(100)
  print(f"response to set charge is {set_resp}")
  print("Waiting 5 seconds for things to settle down")
  e.wait(5)
  manual_flow = (await sb.get_status())["Pac_total_W"]
  print(f"Flow with charge rate of 100 is {manual_flow}")
  print("Setting a discharge rate of 100") 
  # set to a charge rate of 100
  set_resp = await sb.sb2.discharge_battery(100)
  print(f"response to set discharge is {set_resp}")
  print("Waiting 5 for things to settle down")
  e.wait(5)
  manual_flow = (await sb.get_status())["Pac_total_W"]
  print(f"Flow with discharge rate of 100 is {manual_flow}")
  print(f"Returning operating mode to origional mode of {operating_mode_name}")
  pprint(await sb.set_operating_mode_by_name(operating_mode_name))
  await sb.logout()

if __name__ == '__main__':
  asyncio.run(test_set_flow())