import requests
import hashlib
import json
# pylint: disable=unused-wildcard-import
from .const import *
# pylint: enable=unused-wildcard-import


class sonnenbatterie:
    def __init__(self,username,password,ipaddress):
        self.username=username
        self.password=password
        self.ipaddress=ipaddress
        self.baseurl='http://'+self.ipaddress+'/api/'
        self._login()


    def _login(self):
        password_sha512 = hashlib.sha512(self.password.encode('utf-8')).hexdigest()
        req_challenge=requests.get(self.baseurl+'challenge')
        req_challenge.raise_for_status()
        challenge=req_challenge.json()
        response=hashlib.pbkdf2_hmac('sha512',password_sha512.encode('utf-8'),challenge.encode('utf-8'),7500,64).hex()
        
        #print(password_sha512)
        #print(challenge)
        #print(response)
        getsession=requests.post(self.baseurl+'session',{"user":self.username,"challenge":challenge,"response":response})
        getsession.raise_for_status()
        #print(getsession.text)
        token=getsession.json()['authentication_token']
        #print(token)
        self.token=token
    
    def _get(self,what,isretry=False):
        response=requests.get(self.baseurl+what,
            headers={'Auth-Token': self.token},
        )
        if not isretry and response.status_code==401:
            self._login()
            return self._get(what,True)
        if response.status_code != 200:
            response.raise_for_status()

        return response.json()    

    def _put(self, what, payload, isretry=False):
        response=requests.put(self.baseurl+what,
            headers={'Auth-Token': self.token,'Content-Type': 'application/json'} , json=payload
        )
        if not isretry and response.status_code==401:
            self._login()
            return self._get(what,True)
        if response.status_code != 200:
            response.raise_for_status()
        return response.json()


    def set_configuration(self, name, value):
        # All configurations names and values are hendled as strings, so force that
        payload = {str(name): str(value)}
        return self._put(SONNEN_API_PATH_CONFIGURATIONS, payload)

    def get_powermeter(self):
        return self._get(SONNEN_API_PATH_POWER_METER)
        
    def get_batterysystem(self):
        return self._get(SONNEN_API_PATH_BATTERY_SYSTEM)
        
    def get_inverter(self):
        return self._get(SONNEN_API_PATH_INVERTER)
    
    def get_systemdata(self):
        return self._get(SONNEN_API_PATH_SYSTEM_DATA)

    def get_status(self):
        return self._get(SONNEN_API_PATH_STATUS)
        
    def get_battery(self):
        return self._get(SONNEN_API_PATH_BATTERY)
        
    def get_latest_data(self):
        return self._get(SONNEN_API_PATH_LATEST_DATA)
    
    def get_current_charge_level(self):
        return self.get_latest_data().get(SONNEN_LATEST_DATA_CHARGE_LEVEL)
    
    def get_configurations(self):
        return self._get(SONNEN_API_PATH_CONFIGURATIONS)
    
    def get_configuration(self, name):
        return self._get(SONNEN_API_PATH_CONFIGURATIONS+"/"+name).get(name) 

    def get_operating_mode(self):
        return self.get_configuration(SONNEN_CONFIGURATION_OPERATING_MODE)
    
    def get_operating_mode_name(self):
        operating_mode_num = self.get_operating_mode()
        return SONNEN_OPERATING_MODES_TO_OPERATING_MODE_NAMES.get(operating_mode_num)
    
    def set_operating_mode(self, operating_mode):
        return self.set_configuration(SONNEN_CONFIGURATION_OPERATING_MODE, operating_mode)
    
    def set_operaing_mode_by_name(self, operating_mode_name):
        return self.set_operating_mode(SONNEN_OPERATING_MODE_NAMES_TO_OPERATING_MODES.get(operating_mode_name))
    
    def get_battery_reserve(self):
        return self.get_configuration(SONNEN_CONFIGURATION_BACKUP_RESERVE)
    
    def set_battery_reserve(self, reserve=5):
        reserve = int(reserve)
        if (reserve < 0) or (reserve > 100):
            raise Exception("Reserve must be between 0 and 100, you specified "+reserve)
        return self.set_configuration(SONNEN_CONFIGURATION_BACKUP_RESERVE, reserve)
    
    # set the reserve to the current battery level adjusted by the offset if provided
    # (a positive offset means that the reserve will be set to more than the current level
    # a negative offser means less than the current level)
    # If the new reserve is less than the minimum reserve then use the minimum reserve
    # the reserve will be tested to ensure it's >= 0 or <= 100
    def set_battery_reserve_relative_to_currentCharge(self, offset=0, minimum_reserve=0):
        current_level = self.get_current_charge_level()
        target_level = current_level +offset
        if (target_level <  minimum_reserve):
            target_level = minimum_reserve
        if (target_level < 0) :
            target_level = 0
        elif (target_level > 100):
            target_level = 100
        return self.set_battery_reserve(target_level)
        
    def get_time_of_use_schedule_as_string(self):
        return self.get_configuration(SONNEN_CONFIGURATION_TOU_SCHEDULE)
    
    def get_time_of_use_schedule_as_objects(self):
        return json.loads(self.get_configuration(SONNEN_CONFIGURATION_TOU_SCHEDULE))
    
    # In this case the schedule is a JSON representation of an array of time of use entries (the string versions), each entry has a start time and stop time and a threshold_p_max (max grid power for the entire building including charging)
    def set_time_of_use_schedule_from_string(self, schedule):
        return self.set_configuration(SONNEN_CONFIGURATION_TOU_SCHEDULE, schedule)
   
    # In this case the schedule is a array representation of an array of disctionary formatted time of use entries, each entry has a start time and stop time and a threshold_p_max (max grid power for the entire building including charging)
    def set_time_of_use_schedule_from_objects(self, schedule):
        return self.set_configuration(SONNEN_CONFIGURATION_TOU_SCHEDULE, json.dumps(schedule))
   