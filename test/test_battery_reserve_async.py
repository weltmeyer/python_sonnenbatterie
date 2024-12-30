#!/usr/bin/env python3
# I suspect that I haven't got to grips with the way phthon does things, but soppusely this will setup the path to allod for the sonnen batteri moduel to be in a separate location
# To me having to do this for testing seems a horrendous hack
import asyncio
import os, sys
script_path = os.path.realpath(os.path.dirname(__name__))
os.chdir(script_path)
sys.path.append("..")
from login import *
from pprint import pprint
from sonnenbatterie.sonnenbatterie import AsyncSonnenBatterie

async def main():
  sb = AsyncSonnenBatterie(SONNEN_USERNAME, SONNEN_PASSWORD, SONNEN_IP)
  battery_reserve = await sb.get_battery_reserve()
  current_charge = await sb.get_current_charge_level()
  print("\nCurrent Configuration")
  pprint(await sb.get_configurations())
  print("\nCurrent charge level")
  pprint(await sb.get_current_charge_level())
  print("\nCurrent battery reserve")
  pprint(await sb.get_battery_reserve())
  print("\nSetting absolute reserve to 7")
  pprint(await sb.set_battery_reserve(7))
  print("\nUpdated battery reserve")
  pprint(await sb.get_battery_reserve())
  print("\nSet relative limit (no offset)")
  pprint(await sb.set_battery_reserve_relative_to_current_charge())
  print("\nBattery reserve with no offset against charge of "+str(current_charge))
  pprint(await sb.get_battery_reserve())
  print("\nSet relative limit (offset of -5)")
  pprint(await sb.set_battery_reserve_relative_to_current_charge(-5))
  print("\nBattery reserve with offset of -5 against charge of "+str(current_charge))
  pprint(await sb.get_battery_reserve())
  print("\nSet relative limit (offset of 0 and minimum of 20)")
  pprint(await sb.set_battery_reserve_relative_to_current_charge(-5, 20))
  print("\nBattery reserve with offset of 0 against minimum charge of 20")
  pprint(await sb.get_battery_reserve())
  print("\nSet relative limit (offset of 0 and minimum of 80)")
  pprint(await sb.set_battery_reserve_relative_to_current_charge(0, 80))
  print("\nBattery reserve with offset of 0 against minimum charge of 80")
  pprint(await sb.get_battery_reserve())
  print("\nGoing to battery reserve of 10")
  pprint(await sb.set_battery_reserve(10))
  print("\nReset battery reserve")
  pprint(await sb.set_battery_reserve(battery_reserve))
  print("\nVerify battery reserve")
  pprint(await sb.get_battery_reserve())
  await sb.logout()

if __name__ == '__main__':
  asyncio.run(main())