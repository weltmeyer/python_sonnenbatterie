#!/usr/bin/env python3

import os
import sys
from pprint import pprint

from login import *
from sonnenbatterie import sonnenbatterie

script_path = os.path.realpath(os.path.dirname(__name__))
os.chdir(script_path)
sys.path.append("..")

if __name__ == "__main__":
    sb = sonnenbatterie(SONNEN_USERNAME, SONNEN_PASSWORD, SONNEN_IP)
    pprint(sb.sb2.get_configurations())  # retrieve configuration overview
    pprint(sb.sb2.get_battery_module_data())  # get battery module data
    pprint(sb.sb2.get_inverter_data())  # retrieve inverter data
    pprint(sb.sb2.get_latest_data())  # get latest date from sonnenbatterie
    pprint(sb.sb2.get_powermeter_data())  # get data from power meters
    pprint(sb.sb2.get_status_data())  # get overall status information
    pprint(sb.sb2.get_io_data())  # get io status
