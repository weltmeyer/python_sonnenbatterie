#!/usr/bin/env python3
# I suspect that I haven't got to grips with the way phthon does things, but soppusely this will setup the path to allod for the sonnen batteri moduel to be in a separate location
# To me having to do this for testing seems a horrendous hack
import os, sys
script_path = os.path.realpath(os.path.dirname(__name__))
os.chdir(script_path)
sys.path.append("..")
from login import *
from pprint import pprint
from sonnenbatterie.sonnenbatterie import sonnenbatterie
if __name__ == '__main__':
  sb = sonnenbatterie(SONNEN_USERNAME, SONNEN_PASSWORD, SONNEN_IP)
  battery_reserve = sb.get_battery_reserve()
  current_charge = sb.get_current_charge_level()
  print("\nConfigurations")
  pprint(sb.get_configurations())
  print("\nCurrent charge level")
  pprint(sb.get_current_charge_level())
  print("\nBattery reserve")
  pprint(sb.get_battery_reserve())
  print("\nSetting absolute reserve to 7")
  pprint(sb.set_battery_reserve(7))
  print("\nUpdated battery reserve")
  pprint(sb.get_battery_reserve())
  print("\nSet relative limit (no offset)")
  pprint(sb.set_battery_reserve_relative_to_current_charge())
  print("\nBattery reserve with no offset against charge of "+str(current_charge))
  pprint(sb.get_battery_reserve())
  pprint("\nSet relative limit (offset of -5)")
  pprint(sb.set_battery_reserve_relative_to_current_charge(-5))
  print("\nBattery reserve with offset of -5  against charge of "+str(current_charge))
  pprint(sb.get_battery_reserve())
  print("\nSet relative limit (offset of 0 and minimum of 20)")
  pprint(sb.set_battery_reserve_relative_to_current_charge(-5, 20))
  print("\nBattery reserve with offset of 0 against minimum charge of 20")
  pprint(sb.get_battery_reserve())
  print("\nSet relative limit (offset of 0 and minimum of 80)")
  pprint(sb.set_battery_reserve_relative_to_current_charge(0, 80))
  print("\nBattery reserve with offset of 0 against minimum charge of 80")
  pprint(sb.get_battery_reserve())
  print("\nGoing to battery reserve of 5")
  pprint(sb.set_battery_reserve(5))
  print("\nReset battery reserve")
  pprint(sb.get_battery_reserve())

