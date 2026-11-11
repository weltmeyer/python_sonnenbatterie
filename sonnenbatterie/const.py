DEFAULT_BATTERY_LOGIN_TIMEOUT=10
DEFAULT_CONNECT_TO_BATTERY_TIMEOUT=6
DEFAULT_READ_FROM_BATTERY_TIMEOUT=6

SONNEN_OPERATING_MODE_UNKNOWN_NAME="Unknown Operating Mode"
SONNEN_OPERATING_MODE_UNKNOWN="0"
SONNEN_OPERATING_MODE_MANUAL_NAME="Manual"
SONNEN_OPERATING_MODE_AUTOMATIC_SELF_CONSUMPTION_NAME="Automatic - Self-Consumption"
SONNEN_OPERATING_MODE_BATTERY_MODULE_EXTENSION_30_PERCENT_NAME="Battery-Module-Extension (30%)"
SONNEN_OPERATING_MODE_TIME_OF_USE_NAME="Time-Of-Use"
SONNEN_OPERATING_MODE_NAMES_TO_OPERATING_MODES =  {
    SONNEN_OPERATING_MODE_MANUAL_NAME : 1,
    SONNEN_OPERATING_MODE_AUTOMATIC_SELF_CONSUMPTION_NAME: 2,
    SONNEN_OPERATING_MODE_BATTERY_MODULE_EXTENSION_30_PERCENT_NAME: 6,
    SONNEN_OPERATING_MODE_TIME_OF_USE_NAME: 10
}
SONNEN_OPERATING_MODES_TO_OPERATING_MODE_NAMES = {v:k for k,v in SONNEN_OPERATING_MODE_NAMES_TO_OPERATING_MODES.items()}

SONNEN_OPEATING_MODES=[SONNEN_OPERATING_MODE_MANUAL_NAME, SONNEN_OPERATING_MODE_AUTOMATIC_SELF_CONSUMPTION_NAME, SONNEN_OPERATING_MODE_BATTERY_MODULE_EXTENSION_30_PERCENT_NAME,SONNEN_OPERATING_MODE_TIME_OF_USE_NAME ]

SONNEN_CONFIGURATION_OPERATING_MODE="EM_OperatingMode"
SONNEN_CONFIGURATION_TOU_SCHEDULE="EM_ToU_Schedule"
SONNEN_CONFIGURATION_BACKUP_RESERVE="EM_USOC"
SONNEN_LATEST_DATA_CHARGE_LEVEL="USOC"

SONNEN_API_PATH_CONFIGURATIONS="v2/configurations"
SONNEN_API_PATH_LATEST_DATA="v2/latestdata"
SONNEN_API_PATH_POWER_METER="powermeter"
SONNEN_API_PATH_BATTERY_SYSTEM="battery_system"
SONNEN_API_PATH_INVERTER="inverter"
SONNEN_API_PATH_SYSTEM_DATA="system_data"
SONNEN_API_PATH_STATUS="v1/status"
SONNEN_API_PATH_BATTERY="battery"
SONNEN_API_PATH_API_CONFIGURATION="json_api/json_api_configuration"
SONNEN_API_COMMISSIONING_SETTINGS="v1/commissioning_assistant/special_function"

# Unofficial endpoints, used by the battery's own web dashboard (found in its
# code). Read-only GETs; they need the session token from the username/
# password login (the static API token can't read them). Experimental: their
# responses on a cascade (several batteries acting as one system) are only
# confirmed for masters so far (see cascade.py).
# - role in a cascade: {"role": "none"|"master"|"slave", "data": ..., "country": ...},
#   on a master data = {"master": {serial: {...}}, "slaves": {serial: {...}}}
SONNEN_API_PATH_STACKING_STATUS="stacking_status"
# - backup/protect configuration of a cascade: {"master": {...}, "slaves": [...]},
#   HTTP 400 "not a stack" on a single battery
SONNEN_API_PATH_STACKING_PROTECT="v1/commissioning_assistant/special_function/stacking/protect"
# - inverter sync status of a cascade: {"master": {...}, "slaves": [...]},
#   needs a role above User (HTTP 401 for User, works for Installer)
SONNEN_API_PATH_INVERTER_STACKING_STATUS="v1/commissioning_assistant/inverter/stacking/status"
# - configuration items, incl. DE_Ticket_Number (the serial number), which
#   the static API token can't read (v2/configurations/DE_Ticket_Number: 403)
SONNEN_API_PATH_CONFIGS="configs"
SONNEN_CONFIG_SERIAL_NUMBER="DE_Ticket_Number"

SONNEN_CHARGE_PATH="charge"
SONNEN_DISCHARGE_PATH="discharge"
