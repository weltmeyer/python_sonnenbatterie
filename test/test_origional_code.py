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
# this is based on the test code by rust dust
if __name__ == '__main__':
  sb = sonnenbatterie(SONNEN_USERNAME, SONNEN_PASSWORD, SONNEN_IP)
  print("\nPower:\n")
  pprint(sb.get_powermeter())
  print("\nBattery System:\n")
  pprint(sb.get_batterysystem())
  print("\nInverter:\n")
  pprint(sb.get_inverter())
  print("\nSystem Data:\n")
  pprint(sb.get_systemdata())
  print("\nStatus:\n")
  pprint(sb.get_status())
  print("\nBattery:\n")
  pprint(sb.get_battery())
