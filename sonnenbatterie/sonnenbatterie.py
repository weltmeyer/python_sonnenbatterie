import sys
sys.path.append("..")
import hashlib
import requests

from sonnenbatterie2 import SonnenBatterieV2
from .const import *


class sonnenbatterie:
    def __init__(self,username,password,ipaddress):
        self.username=username
        self.password=password
        self.ipaddress=ipaddress
        self.baseurl='http://'+self.ipaddress+'/api/'
        self.setpoint='v2/setpoint/'
        self._batteryLoginTimeout = DEFAULT_BATTERY_LOGIN_TIMEOUT 
        self._batteryConnectTimeout = DEFAULT_CONNECT_TO_BATTERY_TIMEOUT 
        self._batteryReadTimeout = DEFAULT_READ_FROM_BATTERY_TIMEOUT 
        self._batteryRequestTimeout = (self._batteryConnectTimeout, self._batteryReadTimeout)

        self._login()

        self.sb2 = SonnenBatterieV2(ip_address=self.ipaddress, api_token=self.token)


    def _login(self):
        password_sha512 = hashlib.sha512(self.password.encode('utf-8')).hexdigest()
        req_challenge=requests.get(self.baseurl+'challenge', timeout=self._batteryLoginTimeout)
        req_challenge.raise_for_status()
        challenge=req_challenge.json()
        response=hashlib.pbkdf2_hmac('sha512',password_sha512.encode('utf-8'),challenge.encode('utf-8'),7500,64).hex()
        
        #print(password_sha512)
        #print(challenge)
        #print(response)
        getsession=requests.post(self.baseurl+'session',{"user":self.username,"challenge":challenge,"response":response}, timeout=self._batteryLoginTimeout)
        getsession.raise_for_status()
        #print(getsession.text)
        token=getsession.json()['authentication_token']
        #print(token)
        self.token=token

    def set_login_timeout(self, timeout:int = 120):
        self._batteryLoginTimeout = timeout
    
    def get_login_timeout(self) -> int:
        return self._batteryLoginTimeout
    
    def set_request_connect_timeout(self, timeout:int = 60):
        self._batteryConnectTimeout = timeout
        self._batteryRequestTimeout = (self._batteryConnectTimeout, self._batteryReadTimeout)

    def get_request_connect_timeout(self) -> int:
        return self._batteryConnectTimeout
    
    def set_request_read_timeout(self, timeout:int = 60):
        self._batteryReadTimeout = timeout
        self._batteryRequestTimeout = (self._batteryConnectTimeout, self._batteryReadTimeout)

    def get_request_read_timeout(self) -> int:
        return self._batteryReadTimeout
    
    def _get(self,what,isretry=False):
        # This is a synchronous call, you may need to wrap it in a thread or something for asynchronous operation        
        url = self.baseurl+what
        response=requests.get(url,
            headers={'Auth-Token': self.token}, timeout=self._batteryRequestTimeout
        )
        if not isretry and response.status_code==401:
            self._login()
            return self._get(what,True)
        if response.status_code != 200:
            response.raise_for_status()

        return response.json()    

    def _put(self, what, payload, isretry=False):
        # This is a synchronous call, you may need to wrap it in a thread or something for asynchronous operation
        url = self.baseurl+what
        response=requests.put(url,
            headers={'Auth-Token': self.token,'Content-Type': 'application/json'} , json=payload, timeout=self._batteryRequestTimeout
        )
        if not isretry and response.status_code==401:
            self._login()
            return self._put(what, payload,True)
        if response.status_code != 200:
            response.raise_for_status()
        return response.json()

    def _post(self, what, isretry=False):
        # This is a synchronous call, you may need to wrap it in a thread or something for asynchronous operation
        url = self.baseurl+what
        print("Posting "+url)
        response=requests.post(url,
            headers={'Auth-Token': self.token,'Content-Type': 'application/json'}, timeout=self._batteryRequestTimeout
        )
        if not isretry and response.status_code==401:
            self._login()
            return self._post(what, True)
        if response.status_code != 200:
            response.raise_for_status()
        return response
    
    # these are special purpose endpoints, there is no associated data that I'm aware of
    # while I don't have details I belive this is probabaly only useful in manual more
    # and it's probabaly possible to extact the actuall flow rate in operation  
    # looking at the status.state_battery_inout value
    # irritatingly there is no mechanism in the API to do a single set to you have to work out if
    # the direction of the flow and then call the appropriate API 
    # more general purpose endpoints

    # API v1 calls
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

    # API v2 calls
    def set_configuration(self, name, value):
        return self.sb2.set_config_item(name, value)

    def get_latest_data(self):
        return self.sb2.get_latest_data()

    def get_configurations(self):
        return self.sb2.get_configurations()
    
    def get_configuration(self, name):
        return self.sb2.get_config_item(name)
    

    # these have special handling in some form, for example converting a mode as a number into a string
    def get_current_charge_level(self):
        return self.get_latest_data().get(SONNEN_LATEST_DATA_CHARGE_LEVEL)

    def get_operating_mode(self):
        return self.get_configuration(SONNEN_CONFIGURATION_OPERATING_MODE)
    
    def get_operating_mode_name(self):
        operating_mode = self.get_operating_mode()
        return SONNEN_OPERATING_MODES_TO_OPERATING_MODE_NAMES.get(operating_mode[SONNEN_CONFIGURATION_OPERATING_MODE])
    
    def set_operating_mode(self, operating_mode):
        return self.set_configuration(SONNEN_CONFIGURATION_OPERATING_MODE, operating_mode)
    
    def set_operating_mode_by_name(self, operating_mode_name):
        return self.set_operating_mode(SONNEN_OPERATING_MODE_NAMES_TO_OPERATING_MODES.get(operating_mode_name))
    
    def get_battery_reserve(self):
        return self.get_configuration(SONNEN_CONFIGURATION_BACKUP_RESERVE)
    
    def set_battery_reserve(self, reserve=5):
        reserve = int(reserve)
        if (reserve < 0) or (reserve > 100):
            raise Exception(f"Reserve must be between 0 and 100, you specified {reserve}")
        return self.set_configuration(SONNEN_CONFIGURATION_BACKUP_RESERVE, reserve)
    
    # set the reserve to the current battery level adjusted by the offset if provided
    # (a positive offset means that the reserve will be set to more than the current level
    # a negative offser means less than the current level)
    # If the new reserve is less than the minimum reserve then use the minimum reserve
    # the reserve will be tested to ensure it's >= 0 or <= 100
    def set_battery_reserve_relative_to_current_charge(self, offset=0, minimum_reserve=0):
        current_level = self.get_current_charge_level()
        target_level = current_level +offset
        if target_level <  minimum_reserve:
            target_level = minimum_reserve
        if target_level < 0:
            target_level = 0
        elif target_level > 100:
            target_level = 100
        return self.set_battery_reserve(target_level)
