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
from sonnenbatterie.sonnenbatterie import sonnenbatterie, AsyncSonnenBatterie


# this is based on the test code by rust dust

def main():
  print("\nMain (sync)\n==========")
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

async def async_main():
  print("\n\nAsync main\n==========\n")
  sb = AsyncSonnenBatterie(SONNEN_USERNAME, SONNEN_PASSWORD, SONNEN_IP)
  print("\nPower:\n")
  pprint(await sb.get_powermeter())
  print("\nBattery System:\n")
  pprint(await sb.get_batterysystem())
  print("\nInverter:\n")
  pprint(await sb.get_inverter())
  print("\nSystem Data:\n")
  pprint(await sb.get_systemdata())
  print("\nStatus:\n")
  pprint(await sb.get_status())
  print("\nBattery:\n")
  pprint(await sb.get_battery())
  await sb.logout()

if __name__ == '__main__':
  start = time.time()
  main()
  print("\nTotal time sync:", time.time() - start)
  start = time.time()
  asyncio.run(async_main())
  print("\nTotal time async:", time.time() - start)
