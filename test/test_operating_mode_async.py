#!/usr/bin/env python3
# I suspect that I haven't got to grips with the way phthon does things, but soppusely this will setup the path to allod for the sonnen batteri moduel to be in a separate location
# To me having to do this for testing seems a horrendous hack
import asyncio
import os
import sys
script_path = os.path.realpath(os.path.dirname(__name__))
os.chdir(script_path)
sys.path.append("..")

from login import *
from pprint import pprint
from sonnenbatterie import AsyncSonnenBatterie
from sonnenbatterie.const import *

async def main():
  sb = AsyncSonnenBatterie(SONNEN_USERNAME, SONNEN_PASSWORD, SONNEN_IP)
  operating_mode_num = await sb.get_operating_mode()
  operating_mode_name = await sb.get_operating_mode_name()
  print("\nConfigurations")
  pprint(await sb.get_configurations())
  print("\nOperating mode (num)")
  pprint(await sb.get_operating_mode())
  print("\nOperating mode (name)")
  pprint(await sb.get_operating_mode_name())
  print("Setting operating mode num to 1")
  pprint(await sb.set_operating_mode(1))
  print("\nNew Operating mode (num)")
  pprint(await sb.get_operating_mode())
  print("\nNew Operating mode (name)")
  pprint(await sb.get_operating_mode_name())
  print(f"Resetting operating mode num to {operating_mode_num}")
  pprint(await sb.set_operating_mode(operating_mode_num))
  print("\nReset Operating mode (num)")
  pprint(await sb.get_operating_mode())
  print("\nReset Operating mode (name)")
  pprint(await sb.get_operating_mode_name())
  print("Setting operating mode name to "+SONNEN_OPERATING_MODE_AUTOMATIC_SELF_CONSUMPTION_NAME)
  pprint(await sb.set_operating_mode_by_name(SONNEN_OPERATING_MODE_AUTOMATIC_SELF_CONSUMPTION_NAME))
  print("\nNew Operating mode (num)")
  pprint(await sb.get_operating_mode())
  print("\nNew Operating mode (name)")
  pprint(await sb.get_operating_mode_name())
  print(f"Resetting operating mode num to {operating_mode_num}")
  pprint(await sb.set_operating_mode(operating_mode_num))
  print("\nVerifiying operating mode")
  pprint(await sb.get_operating_mode())
  await sb.logout()

if __name__ == '__main__':
  asyncio.run(main())
