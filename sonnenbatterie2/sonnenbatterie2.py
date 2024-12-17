import json

import requests

from sonnenbatterie.const import (
    DEFAULT_CONNECT_TO_BATTERY_TIMEOUT,
    DEFAULT_READ_FROM_BATTERY_TIMEOUT,
    SONNEN_CONFIGURATION_TOU_SCHEDULE
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
            print("Aaargh", response.json())
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

    def get_status_data(self):
        return self._get("status")

    def get_io_data(self):
        return self._get("io")

    # POST API
    def set_manual_flow(self, direction, watts):
        response = self._post(f"setpoint/{direction}/{watts}")
        return response.status_code == 201

    def charge_battery(self, watts:int):
        return self.set_manual_flow("charge", watts)

    def discharge_battery(self, watts:int):
        return self.set_manual_flow("discharge", watts)

    # PUT API
    def set_config_item(self, item:str, value:str):
        payload = {str(item): str(value)}
        return self._put(f"configurations", payload)

    # API Helpers
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
