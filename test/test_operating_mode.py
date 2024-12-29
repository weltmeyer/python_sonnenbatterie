#!/usr/bin/env python3
# I suspect that I haven't got to grips with the way phthon does things, but soppusely this will setup the path to allod for the sonnen batteri moduel to be in a separate location
# To me having to do this for testing seems a horrendous hack
import os
import sys
script_path = os.path.realpath(os.path.dirname(__name__))
os.chdir(script_path)
sys.path.append("..")
from login import *
from pprint import pprint
from sonnenbatterie.sonnenbatterie import sonnenbatterie
from sonnenbatterie.const import *

def main():
  sb = sonnenbatterie(SONNEN_USERNAME, SONNEN_PASSWORD, SONNEN_IP)
  operating_mode_num = sb.get_operating_mode()
  operating_mode_name = sb.get_operating_mode_name()
  print("\nConfigurations")
  pprint(sb.get_configurations())
  print("\nOperating mode (num)")
  pprint(sb.get_operating_mode())
  print("\nOperating mode (name)")
  pprint(sb.get_operating_mode_name())
  print("Setting operating mode num to 1")
  pprint(sb.set_operating_mode(1))
  print("\nNew Operating mode (num)")
  pprint(sb.get_operating_mode())
  print("\nNew Operating mode (name)")
  pprint(sb.get_operating_mode_name())
  print(f"Resetting operating mode num to {operating_mode_num}")
  pprint(sb.set_operating_mode(operating_mode_num))
  print("\nReset Operating mode (num)")
  pprint(sb.get_operating_mode())
  print("\nReset Operating mode (name)")
  pprint(sb.get_operating_mode_name())
  print("Setting operating mode name to "+SONNEN_OPERATING_MODE_AUTOMATIC_SELF_CONSUMPTION_NAME)
  pprint(sb.set_operating_mode_by_name(SONNEN_OPERATING_MODE_AUTOMATIC_SELF_CONSUMPTION_NAME))
  print("\nNew Operating mode (num)")
  pprint(sb.get_operating_mode())
  print("\nNew Operating mode (name)")
  pprint(sb.get_operating_mode_name())
  print(f"Resetting operating mode num to {operating_mode_num}")
  pprint(sb.set_operating_mode(operating_mode_num))
  print("\nVerifiying operating mode")
  pprint(sb.get_operating_mode())

if __name__ == '__main__':
  main()
