import json

import aiohttp
import requests

from .const import (
    DEFAULT_CONNECT_TO_BATTERY_TIMEOUT,
    DEFAULT_READ_FROM_BATTERY_TIMEOUT,
    SONNEN_CONFIGURATION_TOU_SCHEDULE, DEFAULT_BATTERY_LOGIN_TIMEOUT, SONNEN_LATEST_DATA_CHARGE_LEVEL,
    SONNEN_CONFIGURATION_OPERATING_MODE, SONNEN_OPERATING_MODES_TO_OPERATING_MODE_NAMES,
    SONNEN_CONFIGURATION_BACKUP_RESERVE, SONNEN_OPERATING_MODE_NAMES_TO_OPERATING_MODES
)
from timeofuse import TimeofUseSchedule
from timeofuse.timeofuse import create_time_of_use_schedule_from_json


class SonnenBatterieV2:
    def __init__(self, ip_address, api_token):
        self.api_token = api_token
        self.ip_address = ip_address
        # noinspection HttpUrlsUsage
        self.base_url = f'http://{ip_address}/api/v2/'
        self._batteryConnectTimeout = DEFAULT_CONNECT_TO_BATTERY_TIMEOUT
        self._batteryReadTimeout = DEFAULT_READ_FROM_BATTERY_TIMEOUT
        self._batteryRequestTimeout = (self._batteryConnectTimeout, self._batteryReadTimeout)

    def set_request_connect_timeout(self, timeout:int = 60):
        self._batteryConnectTimeout = timeout
        self._batteryRequestTimeout = (self._batteryConnectTimeout, self._batteryRequestTimeout)

    def get_request_connect_timeout(self) -> int:
        return self._batteryConnectTimeout

    def set_request_read_timeout(self, timeout:int = 120):
        self._batteryReadTimeout = timeout
        self._batteryRequestTimeout = (self._batteryReadTimeout, self._batteryRequestTimeout)

    def get_request_read_timeout(self) -> int:
        return self._batteryReadTimeout

    def _get(self, what, isretry=False):
        url = self.base_url + what
        response = requests.get(
            url,
            headers={'Auth-Token': self.api_token},
            timeout=self._batteryRequestTimeout,
        )
        if not isretry and response.status_code == 401:
            return self._get(what, isretry=True)

        if response.status_code != 200:
            response.raise_for_status()

        return response.json()

    def _put(self, what, payload, isretry=False):
        url = self.base_url + what
        response = requests.put(
            url,
            headers={'Auth-Token': self.api_token, 'Content-Type': 'application/json'},
            json=payload,
            timeout=self._batteryRequestTimeout,
        )
        if not isretry and response.status_code == 401:
            return self._put(what, payload, isretry=True)

        if response.status_code != 200:
            response.raise_for_status()

        return response.json()

    def _post(self, what, isretry=False):
        url = self.base_url + what
        response = requests.post(
            url,
            headers={'Auth-Token': self.api_token, 'Content-Type': 'application/json'},
            timeout=self._batteryRequestTimeout,
        )
        if not isretry and response.status_code == 401:
            return self._post(what, isretry=True)

        if response.status_code != 200:
            response.raise_for_status()

        return response.json()

    # GET API
    def get_config_item(self, item):
        return self._get(f"configurations/{item}")

    def get_configurations(self):
        return self._get("configurations")

    def get_battery_module_data(self):
        return self._get("battery")

    def get_inverter_data(self):
        return self._get("inverter")

    def get_latest_data(self):
        return self._get("latestdata")

    def get_powermeter_data(self):
        return self._get("powermeter")

    def get_status(self):
        return self._get("status")

    # deprecate with 0.7.x -> get_status
    def get_status_data(self):
        return self._get("status")

    def get_io_data(self):
        return self._get("io")

    # POST API
    def set_manual_flow(self, direction, watts) -> bool:
        response = self._post(f"setpoint/{direction}/{watts}")
        return response

    def charge_battery(self, watts:int):
        return self.set_manual_flow("charge", watts)

    def discharge_battery(self, watts:int):
        return self.set_manual_flow("discharge", watts)

    # PUT API
    """ set item in configurations and return value as reported back
        by the SonnenBatterieV2 API
    """
    def set_config_item(self, item:str, value:str|int) -> str:
        payload = {str(item): str(value)}
        return self._put(f"configurations", payload)[item]

    # API Helpers
    def get_current_charge_level(self):
        return self.get_latest_data().get(SONNEN_LATEST_DATA_CHARGE_LEVEL)

    def get_operating_mode(self) -> int:
        return int(self.get_config_item(SONNEN_CONFIGURATION_OPERATING_MODE)[SONNEN_CONFIGURATION_OPERATING_MODE])

    def get_operating_mode_name(self):
        operating_mode = self.get_operating_mode()
        return SONNEN_OPERATING_MODES_TO_OPERATING_MODE_NAMES.get(operating_mode)

    def set_operating_mode(self, operating_mode) -> int:
        return int(self.set_config_item(SONNEN_CONFIGURATION_OPERATING_MODE, operating_mode))

    def set_operating_mode_by_name(self, operating_mode_name) -> int:
        return int(self.set_operating_mode(SONNEN_OPERATING_MODE_NAMES_TO_OPERATING_MODES.get(operating_mode_name)))

    def get_battery_reserve(self):
        return self.get_config_item(SONNEN_CONFIGURATION_BACKUP_RESERVE)[SONNEN_CONFIGURATION_BACKUP_RESERVE]

    def set_battery_reserve(self, reserve=5):
        reserve = int(reserve)
        if (reserve < 0) or (reserve > 100):
            raise Exception(f"Reserve must be between 0 and 100, you specified {reserve}")
        return self.set_config_item(SONNEN_CONFIGURATION_BACKUP_RESERVE, reserve)

    # set the reserve to the current battery level adjusted by the offset if provided
    # (a positive offset means that the reserve will be set to more than the current level
    # a negative offser means less than the current level)
    # If the new reserve is less than the minimum reserve then use the minimum reserve
    # the reserve will be tested to ensure it's >= 0 or <= 100
    def set_battery_reserve_relative_to_current_charge(self, offset=0, minimum_reserve=0):
        current_level = self.get_current_charge_level()
        target_level = current_level + offset
        if target_level < minimum_reserve:
            target_level = minimum_reserve
        if target_level < 0:
            target_level = 0
        elif target_level > 100:
            target_level = 100
        return self.set_battery_reserve(target_level)

    def get_tou_schedule_string(self) -> str:
        return self.get_config_item(SONNEN_CONFIGURATION_TOU_SCHEDULE)[SONNEN_CONFIGURATION_TOU_SCHEDULE]

    def get_tou_schedule_json(self) -> json:
        return json.loads(self.get_tou_schedule_string())

    def get_tou_schedule_object(self) -> TimeofUseSchedule:
        return create_time_of_use_schedule_from_json(self.get_tou_schedule_json())

    def set_tou_schedule_string(self, schedule:str):
        return self.set_config_item(SONNEN_CONFIGURATION_TOU_SCHEDULE, schedule)

    def set_tou_schedule_json(self, schedule):
        # We need to convert object to valid json string
        return self.set_tou_schedule_string(json.dumps(schedule))

    def clear_tou_schedule_string(self):
        return self.set_tou_schedule_string("[]")

    def clear_tou_schedule_json(self):
        return self.set_tou_schedule_string("[]")


""" Async API calls """


class AsyncSonnenBatterieV2:
    def __init__(self, ip_address, api_token):
        self._ip_address = ip_address
        self._api_token = api_token

        # noinspection HttpUrlsUsage
        self.base_url = f"http://{self._ip_address}/api/v2/"

        self._timeout_total = DEFAULT_BATTERY_LOGIN_TIMEOUT
        self._timeout_connect = DEFAULT_CONNECT_TO_BATTERY_TIMEOUT
        self._timeout_read = DEFAULT_READ_FROM_BATTERY_TIMEOUT
        self._timeout = self._set_timeouts()

        self._session = None

    async def logout(self):
        if self._session:
            await self._session.close()
            self._session = None

    def _set_timeouts(self) -> aiohttp.ClientTimeout:
        return aiohttp.ClientTimeout(
            total=self._timeout_total,
            connect=self._timeout_connect,
            sock_connect=self._timeout_connect,
            sock_read=self._timeout_read,
        )


    """ Base functions """


    async def _get(self, what, isretry=False) -> json:
        if self._session is None:
            self._session = aiohttp.ClientSession()

        url = self.base_url + what
        response = await self._session.get(
            url=url,
            headers={'Auth-Token': self._api_token},
            timeout=self._timeout,
        )

        if not isretry and response.status == 401:
            return await self._get(what, isretry=True)
        if response.status != 200:
            response.raise_for_status()

        return await response.json()


    async def _put(self, what, payload, isretry=False):
        if self._session is None:
            self._session = aiohttp.ClientSession()

        url = self.base_url + what
        response = await self._session.put(
            url=url,
            headers={'Auth-Token': self._api_token},
            json=payload,
            timeout=self._timeout,
        )


        if not isretry and response.status == 401:
            return await self._put(what, payload, isretry=True)
        if response.status != 200:
            response.raise_for_status()

        return await response.json()


    async def _post(self, what, isretry=False) -> json:
        if self._session is None:
            self._session = aiohttp.ClientSession()

        url = self.base_url + what
        response = await self._session.post(
            url=url,
            headers={'Auth-Token': self._api_token},
            timeout=self._timeout,
        )

        if not isretry and response.status == 401:
            return await self._post(what, isretry=True)
        if response.status != 200:
            response.raise_for_status()

        return await response.json()


    """ API function """

    # GET
    async def get_config_item(self, item:str) -> json:
        return await self._get(f"configurations/{item}")

    async def get_configurations(self) -> json:
        return await self._get("configurations")

    async def get_battery_module_data(self) -> json:
        return await self._get("battery")

    async def get_inverter_data(self) -> json:
        return await self._get("inverter")

    async def get_latest_data(self) -> json:
        return await self._get("latestdata")

    async def get_powermeter_data(self) -> json:
        return await self._get("powermeter")

    async def get_status(self) -> json:
        return await self._get("status")

    async def get_status_data(self) -> json:
        return await self._get("status")

    async def get_io_data(self) -> json:
        return await self._get("io")

    # POST
    async def set_manual_flow(self, direction, watts) -> json:
        return await self._post(f"setpoint/{direction}/{watts}")

    async def charge_battery(self, watts:int) -> json:
        return await self.set_manual_flow("charge", watts)

    async def discharge_battery(self, watts:int) -> json:
        return await self.set_manual_flow("discharge", watts)

    # PUT
    async def set_config_item(self, item:str, value:str|int) -> json:
        payload = {str(item): str(value)}
        return await self._put(f"configurations", payload)

    # API Helpers
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

    async def set_operating_mode(self, operating_mode) -> int:
        result = await self.set_config_item(
            SONNEN_CONFIGURATION_OPERATING_MODE,
            operating_mode
        )
        return int(result[SONNEN_CONFIGURATION_OPERATING_MODE])

    async def set_operating_mode_by_name(self, operating_mode_name) -> int:
        result = await self.set_config_item(
            SONNEN_CONFIGURATION_OPERATING_MODE,
            SONNEN_OPERATING_MODE_NAMES_TO_OPERATING_MODES.get(operating_mode_name)
        )
        return int(result[SONNEN_CONFIGURATION_OPERATING_MODE])

    async def set_battery_reserve(self, battery_reserve) -> json:
        reserve = int(battery_reserve)
        if (reserve < 0) or (reserve > 100):
            raise Exception(f"Reserve must be between 0 and 100, you spcified {reserve}")
        return await self.set_config_item(SONNEN_CONFIGURATION_BACKUP_RESERVE, reserve)

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

    async def get_tou_schedule_string(self) -> str:
        return (await self.get_config_item(SONNEN_CONFIGURATION_TOU_SCHEDULE))[SONNEN_CONFIGURATION_TOU_SCHEDULE]

    async def get_tou_schedule_json(self) -> json:
        return json.loads(await self.get_tou_schedule_string())

    async def get_tou_schedule_object(self) -> json:
        return create_time_of_use_schedule_from_json(await self.get_tou_schedule_json())

    async def set_tou_schedule_string(self, schedule:str) -> json:
        return await self.set_config_item(SONNEN_CONFIGURATION_TOU_SCHEDULE, schedule)

    async def set_tou_schedule_json(self, schedule:str|list) -> json:
        # We need to convert object to valid json string
        return await self.set_tou_schedule_string(json.dumps(schedule))

    async def clear_tou_schedule_string(self) -> json:
        return await self.set_tou_schedule_string("[]")

    async def clear_tou_schedule_json(self) -> json:
        return await self.set_tou_schedule_string("[]")