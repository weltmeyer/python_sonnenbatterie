import json
import sys
import base64, binascii, hashlib, hmac, string

from sonnenbatterie2.sonnenbatterie2 import AsyncSonnenBatterieV2

sys.path.append("..")
import hashlib
import requests

import aiohttp

from sonnenbatterie2 import SonnenBatterieV2
from .const import *


# noinspection PyPep8Naming
class sonnenbatterie:
    # noinspection HttpUrlsUsage
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

        self.token = None
        self.sb2 = SonnenBatterieV2(ip_address=self.ipaddress, api_token=self.token)
        self.login()


    def login(self):

        # returns a salt after battery got updated to a certain version (>1.18??)
        salt = requests.get(self.baseurl+'salt/'+self.username, timeout=self._batteryLoginTimeout, allow_redirects=False)
        if salt.status_code==200:
            self.create_session_token_new(salt.json()["salt"])
        else:
            password_sha512 = hashlib.sha512(self.password.encode('utf-8')).hexdigest()
            req_challenge=requests.get(self.baseurl+'challenge', timeout=self._batteryLoginTimeout)
            req_challenge.raise_for_status()
            challenge=req_challenge.json()
            response=hashlib.pbkdf2_hmac('sha512',password_sha512.encode('utf-8'),challenge.encode('utf-8'),7500,64).hex()
            
            getsession=requests.post(self.baseurl+'session',{"user":self.username,"challenge":challenge,"response":response}, timeout=self._batteryLoginTimeout)
            getsession.raise_for_status()
            token=getsession.json()['authentication_token']
            self.token=token

        # API v2 uses the same session token
        self.sb2.api_token = self.token


    def create_response_from_values(self, username, password, challenge, salt):
        pw_sha512_hex = hashlib.sha512(password.encode("utf-8")).hexdigest()
        pw_bytes = pw_sha512_hex.encode("utf-8")
        dk = hashlib.pbkdf2_hmac("sha512", pw_bytes, salt.encode("utf-8"), 7500, dklen=64)
        derived_hex = dk.hex()
        key = derived_hex.encode("utf-8")
        response = hmac.new(key, challenge.encode("utf-8"), hashlib.sha256).hexdigest()
        return response

    def create_session_token_new(self, salt=None):
        session = requests.Session()

        # Step 1: challenge
        r = session.get(f"{self.baseurl}challenge", timeout=self._batteryLoginTimeout)
        r.raise_for_status()
        try:
            challenge = r.json()
            if isinstance(challenge, dict):
                challenge = challenge.get("challenge") or next(iter(challenge.values()))
        except Exception:
            challenge = r.text.strip()

        # Step 2: salt (unless already fetched by login())
        if salt is None:
            r = session.get(f"{self.baseurl}salt/{self.username}", timeout=self._batteryLoginTimeout)
            r.raise_for_status()
            salt = r.json()["salt"]

        # Step 3: loop: POST /session, maybe retry with new_challenge
        for _ in range(2):
            response = self.create_response_from_values(self.username, self.password, challenge, salt)
            payload = {
                "user": self.username,
                "challenge": challenge,
                "response": response,
            }

            r = session.post(
                url=f"{self.baseurl}session",
                data=payload,
                timeout=self._batteryLoginTimeout,
            )
            if r.status_code >= 400:
                # Keep the HTTP status (via r.response). Never include the
                # payload, challenge, salt or response: together they allow an
                # offline brute-force of the password.
                raise requests.HTTPError(
                    f"Login failed with HTTP {r.status_code}: {r.text[:200]}",
                    response=r,
                )
            data = r.json()

            if "new_challenge" in data and data["new_challenge"]:
                challenge = data["new_challenge"]
                continue

            if "authentication_token" in data and data["authentication_token"]:
                self.token = data["authentication_token"]
                return

            raise RuntimeError(f"Unexpected /session response: {json.dumps(data)}")

        raise RuntimeError("Failed to obtain authentication_token")

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
            self.login()
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
            self.login()
            return self._put(what, payload,True)
        if response.status_code != 200:
            response.raise_for_status()
        return response.json()

    def _post(self, what, isretry=False):
        # This is a synchronous call, you may need to wrap it in a thread or something for asynchronous operation
        url = self.baseurl+what
        response=requests.post(url,
            headers={'Auth-Token': self.token,'Content-Type': 'application/json'}, timeout=self._batteryRequestTimeout
        )
        if not isretry and response.status_code==401:
            self.login()
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

    def get_api_configuration(self):
        return self._get(SONNEN_API_PATH_API_CONFIGURATION)

    def get_commissioning_settings(self):
        return self._get(SONNEN_API_COMMISSIONING_SETTINGS)


    # API v2 calls
    def _call_v2(self, method, *args):
        # the v2 API uses our session token: on 401 log in again (which also
        # updates sb2's token) and retry once
        try:
            return getattr(self.sb2, method)(*args)
        except requests.HTTPError as e:
            if e.response is None or e.response.status_code != 401:
                raise
        self.login()
        return getattr(self.sb2, method)(*args)

    def set_configuration(self, name, value):
        return self._call_v2('set_config_item', name, value)

    def get_latest_data(self):
        return self._call_v2('get_latest_data')

    def get_configurations(self):
        return self._call_v2('get_configurations')

    # deprecate with 0.7.0 -> get_config_item
    def get_configuration(self, name):
        return self._call_v2('get_config_item', name)

    def get_config_item(self, name):
        return self._call_v2('get_config_item', name)
    

    # these have special handling in some form, for example converting a mode as a number into a string
    def get_current_charge_level(self):
        return self.get_latest_data().get(SONNEN_LATEST_DATA_CHARGE_LEVEL)

    def get_operating_mode(self) -> int:
        return int(self.get_config_item(SONNEN_CONFIGURATION_OPERATING_MODE)[SONNEN_CONFIGURATION_OPERATING_MODE])
    
    def get_operating_mode_name(self):
        operating_mode = self.get_operating_mode()
        return SONNEN_OPERATING_MODES_TO_OPERATING_MODE_NAMES.get(operating_mode)
    
    def set_operating_mode(self, operating_mode) -> int:
        return int(self.set_configuration(SONNEN_CONFIGURATION_OPERATING_MODE, operating_mode))
    
    def set_operating_mode_by_name(self, operating_mode_name) -> int:
        return self.set_operating_mode(SONNEN_OPERATING_MODE_NAMES_TO_OPERATING_MODES.get(operating_mode_name))
    
    def get_battery_reserve(self):
        return self.get_config_item(SONNEN_CONFIGURATION_BACKUP_RESERVE)[SONNEN_CONFIGURATION_BACKUP_RESERVE]
    
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


""" AsyncSonnenbatterie """

class AsyncSonnenBatterie:
    # noinspection HttpUrlsUsage
    def __init__(self, username, password, ipaddress):
        self.username = username
        self.password = password
        self.ipaddress = ipaddress

        self.baseurl = 'http://' + self.ipaddress + '/api/'

        self._timeout_total = DEFAULT_BATTERY_LOGIN_TIMEOUT
        self._timeout_connect = DEFAULT_CONNECT_TO_BATTERY_TIMEOUT
        self._timeout_read = DEFAULT_READ_FROM_BATTERY_TIMEOUT

        self._timeout = self._set_timeouts()

        self.token = None
        self.sb2 = None

        self._session = None

    def _set_timeouts(self) -> aiohttp.ClientTimeout:
        return aiohttp.ClientTimeout(
            total=self._timeout_total,
            connect=self._timeout_connect,
            sock_connect=self._timeout_connect,
            sock_read=self._timeout_read,
        )

    async def logout(self):
        if self.sb2:
            await self.sb2.logout()
            self.sb2 = None

        if self._session:
            await self._session.close()
            self._session = None

        self.token = None

    async def login(self):
        if self._session is None:
            self._session = aiohttp.ClientSession()

        # returns a salt after battery got updated to a certain version (>1.18??)
        async with self._session.get(self.baseurl+'salt/'+self.username, timeout=self._timeout, allow_redirects=False) as r:
            salt = (await r.json())["salt"] if r.status == 200 else None

        if salt is not None:
            await self.create_session_token_new(salt)
        else:
            pw_sha512 = hashlib.sha512(self.password.encode('utf-8')).hexdigest()
            async with self._session.get(
                self.baseurl+'challenge',
                timeout=self._timeout,
            ) as req_challenge:
                req_challenge.raise_for_status()
                challenge = await req_challenge.json()

            response = hashlib.pbkdf2_hmac(
                'sha512',
                pw_sha512.encode('utf-8'),
                challenge.encode('utf-8'),
                7500,
                64
            ).hex()

            async with self._session.post(
                url = self.baseurl+'session',
                data = {"user":self.username,"challenge":challenge,"response":response},
                timeout=self._timeout,
            ) as session:
                session.raise_for_status()
                token = await session.json()
            self.token = token['authentication_token']

        # Initialize async API v2, or hand it the new token after a re-login
        if self.sb2 is None:
            self.sb2 = AsyncSonnenBatterieV2(ip_address=self.ipaddress, api_token=self.token)
        else:
            self.sb2.set_api_token(self.token)



    def create_response_from_values(self, username, password, challenge, salt):
        pw_sha512_hex = hashlib.sha512(password.encode("utf-8")).hexdigest()
        pw_bytes = pw_sha512_hex.encode("utf-8")
        dk = hashlib.pbkdf2_hmac("sha512", pw_bytes, salt.encode("utf-8"), 7500, dklen=64)
        derived_hex = dk.hex()
        key = derived_hex.encode("utf-8")
        response = hmac.new(key, challenge.encode("utf-8"), hashlib.sha256).hexdigest()
        return response

    async def create_session_token_new(self, salt=None):
        # Step 1: challenge
        async with self._session.get(f"{self.baseurl}challenge", timeout=self._timeout) as r:
            r.raise_for_status()
            try:
                challenge = await r.json()
                if isinstance(challenge, dict):
                    challenge = challenge.get("challenge") or next(iter(challenge.values()))
            except Exception:
                challenge = (await r.text()).strip()

        # Step 2: salt (unless already fetched by login())
        if salt is None:
            async with self._session.get(f"{self.baseurl}salt/{self.username}", timeout=self._timeout) as r:
                r.raise_for_status()
                salt = (await r.json())["salt"]

        # Step 3: loop: POST /session, maybe retry with new_challenge
        for _ in range(2):
            response = self.create_response_from_values(self.username,self.password,challenge,salt)
            async with self._session.post(
                url = self.baseurl+'session',
                data = {"user":self.username,"challenge":challenge,"response":response},
                timeout=self._timeout,
            ) as r:
                if r.status >= 400:
                    # Keep the HTTP status so callers can tell a rejected login
                    # (401) from a busy battery (502/503). Never include
                    # challenge, salt or response: together they allow an
                    # offline brute-force of the password.
                    raise aiohttp.ClientResponseError(
                        r.request_info,
                        r.history,
                        status=r.status,
                        message=f"Login failed: {(await r.text())[:200]}",
                        headers=r.headers,
                    )
                data = await r.json()

            if "new_challenge" in data and data["new_challenge"]:
                challenge = data["new_challenge"]
                continue

            if "authentication_token" in data and data["authentication_token"]:
                 self.token = data["authentication_token"]
                 return

            raise RuntimeError(f"Unexpected /session response: {json.dumps(data)}")

        raise RuntimeError("Failed to obtain authentication_token")




    """ Base functions """


    async def _request(self, method, what, headers, isretry=False, **kwargs) -> json:
        """Send a request with the session token; on 401 log in again and
        retry once. Responses are always released, also on errors."""
        if self.token is None or self._session is None:
            await self.login()

        async with self._session.request(
            method,
            url = self.baseurl + what,
            headers = {'Auth-Token': self.token, **headers},
            timeout = self._timeout,
            **kwargs,
        ) as response:
            if isretry or response.status != 401:
                response.raise_for_status()
                return await response.json()

        await self.login()
        return await self._request(method, what, headers, True, **kwargs)

    async def _get(self, what, isretry=False) -> json:
        return await self._request('GET', what, {}, isretry)

    async def _post(self, what, isretry=False) -> json:
        return await self._request('POST', what, {'Content-Type': 'application/json'}, isretry)

    async def _put(self, what, payload, isretry=False) -> json:
        return await self._request('PUT', what, {'Content-Type': 'application/json'}, isretry, json=payload)

    async def _call_v2(self, method, *args) -> json:
        """Call an API v2 method; the v2 API uses our session token, so on
        401 log in again (which also updates sb2's token) and retry once."""
        if self.sb2 is None:
            await self.login()
        try:
            return await getattr(self.sb2, method)(*args)
        except aiohttp.ClientResponseError as e:
            if e.status != 401:
                raise
        await self.login()
        return await getattr(self.sb2, method)(*args)


    """ API functions """


    async def get_powermeter(self) -> json:
        result = await self._get(SONNEN_API_PATH_POWER_METER)
        return result

    async def get_batterysystem(self) -> json:
        return await self._get(SONNEN_API_PATH_BATTERY_SYSTEM)

    async def get_inverter(self) -> json:
        return await self._get(SONNEN_API_PATH_INVERTER)

    async def get_systemdata(self) -> json:
        return await self._get(SONNEN_API_PATH_SYSTEM_DATA)

    async def get_status(self) -> json:
        return await self._get(SONNEN_API_PATH_STATUS)

    async def get_battery(self) -> json:
        return await self._get(SONNEN_API_PATH_BATTERY)

    async def get_api_configuration(self) -> json:
        return await self._get(SONNEN_API_PATH_API_CONFIGURATION)

    async def get_commissioning_settings(self):
        return await self._get(SONNEN_API_COMMISSIONING_SETTINGS)


    """ API v2 calls """
    async def set_configuration(self, name, value) -> json:
        return await self._call_v2('set_config_item', name, value)

    async def get_latest_data(self) -> json:
        return await self._call_v2('get_latest_data')

    async def get_configurations(self) -> json:
        return await self._call_v2('get_configurations')

    async def get_config_item(self, name) -> json:
        return await self._call_v2('get_config_item', name)


    """ Special functions """
    # GET
    async def get_current_charge_level(self) -> int:
        result = await self.get_latest_data()
        return result.get(SONNEN_LATEST_DATA_CHARGE_LEVEL)

    async def get_operating_mode(self) -> int:
        result = await self.get_config_item(SONNEN_CONFIGURATION_OPERATING_MODE)
        return int(result[SONNEN_CONFIGURATION_OPERATING_MODE])

    async def get_operating_mode_name(self) -> str:
        opmode = await self.get_operating_mode()
        return SONNEN_OPERATING_MODES_TO_OPERATING_MODE_NAMES.get(opmode)

    async def get_battery_reserve(self) -> int:
        result = await self.get_config_item(SONNEN_CONFIGURATION_BACKUP_RESERVE)
        return int(result[SONNEN_CONFIGURATION_BACKUP_RESERVE])

    #SET
    async def set_operating_mode(self, operating_mode) -> int:
        result = await self.set_configuration(
            SONNEN_CONFIGURATION_OPERATING_MODE,
            operating_mode
        )
        return int(result[SONNEN_CONFIGURATION_OPERATING_MODE])

    async def set_operating_mode_by_name(self, operating_mode_name) -> int:
        result = await self.set_configuration(
            SONNEN_CONFIGURATION_OPERATING_MODE,
            SONNEN_OPERATING_MODE_NAMES_TO_OPERATING_MODES.get(operating_mode_name)
        )
        return int(result[SONNEN_CONFIGURATION_OPERATING_MODE])

    async def set_battery_reserve(self, battery_reserve) -> json:
        reserve = int(battery_reserve)
        if (reserve < 0) or (reserve > 100):
            raise Exception(f"Reserve must be between 0 and 100, you spcified {reserve}")
        return await self.set_configuration(SONNEN_CONFIGURATION_BACKUP_RESERVE, reserve)

    # noinspection DuplicatedCode
    async def set_battery_reserve_relative_to_current_charge(self, offset=0, min_res=0) -> json:
        current_level = await self.get_current_charge_level()
        target_level = current_level + offset
        if target_level < min_res:
            target_level = min_res
        if target_level > 100:
            target_level = 100
        if target_level < 0:
            target_level = 0
        return await self.set_battery_reserve(target_level)
