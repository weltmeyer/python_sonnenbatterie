#!/usr/bin/env python3
# I suspect that I haven't got to grips with the way phthon does things, but soppusely this will setup the path to allod for the sonnen batteri moduel to be in a separate location
# To me having to do this for testing seems a horrendous hack
import os
import sys
import time

import requests

from login import *

script_path = os.path.realpath(os.path.dirname(__name__))
os.chdir(script_path)
sys.path.append("..")
from sonnenbatterie.sonnenbatterie import sonnenbatterie

def main():
    print("Starting login")
    try:
        sb = sonnenbatterie(SONNEN_USERNAME, SONNEN_PASSWORD, SONNEN_IP)
    except requests.exceptions.Timeout as e:
        print("Timeout connection "+str(type(e))+", details "+str(e))    
        exit()
    except Exception as e:
        print("non timeout exception getting connection"+str(type(e))+", details "+str(e)) 
        exit()
    print("Logged in")
    sb.set_request_connect_timeout(30)
    sb.set_request_read_timeout(30)
    counter = 0
    while True and counter < 5:
        counter = counter + 1
        reserve = -1
        current_level = -1
        tou = "Not retrieved"
        mode = "Not retrieved"
        status = "Not Retrieved"
        try:
            reserve = sb.get_battery_reserve()
        except requests.exceptions.Timeout as e:
            print("Timeout getting reserve "+str(type(e))+", details "+str(e))    
        except Exception as e:
            print("non timeout exception getting reserve "+str(type(e))+", details "+str(e)) 
        
        try:
            tou = sb.sb2.get_tou_schedule_string()
        except requests.exceptions.Timeout as e:
            print("Timeout getting tou "+str(type(e))+", details "+str(e))    
        except Exception as e:
            print("non timeout exception getting tou "+str(type(e))+", details "+str(e)) 

        try:
            mode = sb.get_operating_mode_name()
        except requests.exceptions.Timeout as e:
            print("Timeout getting mode "+str(type(e))+", details "+str(e))    
        except Exception as e:
            print("non timeout exception getting mode "+str(type(e))+", details "+str(e)) 

        try:
            status = sb.get_status()
            current_level = status["RemainingCapacity_Wh"]
        except requests.exceptions.Timeout as e:
            print("Timeout getting tou "+str(type(e))+", details "+str(e))    
        except Exception as e:
            print("non timeout exception getting tou "+str(type(e))+", details "+str(e)) 

        print("Loop "+str(counter)+", retrireved data : current_level "+str(current_level)+", reserve "+str(reserve)+", mode "+mode+", tou "+tou)
        time.sleep(15)

if __name__ == '__main__':
    main()