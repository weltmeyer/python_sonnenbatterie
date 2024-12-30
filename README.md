# python_sonnenbatterie

Python module to access the REST API of a [Sonnenbatterie](https://sonnenusa.com/en/products/).

This modules contains two distinct sets of APIs:
- the original sonnen API (v1)
- the new v2 API

Both are available in a synchronous and an asynchronous version:
- `sonnenbatterie` - SonnenAPI v1, synchronous
- `AsyncSonnenBatterie` - SonnenAPI v1, asynchronous
- `SonnenBatterieV2` - SonnenAPI v2, synchronous
- `AsyncSonnenBatterieV2` - SonnenAPI v2, asynchronous

The major difference between those two is the method to authenticate. With API v1 you need
to login using a username and a password. The newer API requires a token that can be found
in the web UI of your Sonnenbatterie.
Also, the v2 API provides a unified view across the different Sonnenbatterie models wheres
the v1 API may provide more details in specific setups.

When using the v1 API you'll autmatically get access to the v2 API by using the `sb2` 
attribute of the v1 client object.

## Installation

### Using `pip`

``` bash
pip3 install sonnenbatterie
```

### Manual installation
[Download the archive from pypi.org](https://pypi.org/project/sonnenbatterie/#files) and unpack where needed ;)

## Usage

### SonnenAPI v1 - sync
``` python
# API v1
from sonnenbatterie import sonnenbatterie

sb_host = '192.168.1.2'
sb_user = 'User'
sb_pass = 'Password'

# Init class, establish connection
sb = sonnenbatterie(sb_host, sb_user, sb_pass)

print(sb.get_status())	        # retrieve general information
print(sb.get_powermeters())     # retrieive power meter details
print(sb.get_batterysystem())   # retrieve battery system data
print(sb.get_inverter())        # retrieve inverter status
print(sb.get_systemdata())      # retrieve system data
print(sb.get_battery())         # get battery information
```

### SonnenAPI v1 - async
``` python
# API v1
from sonnenbatterie import AsyncSonnenBatterie

sb_host = '192.168.1.2'
sb_user = 'User'
sb_pass = 'Password'

# Init class, establish connection
sb = AsyncSonnenBatterie(sb_host, sb_user, sb_pass)

print(await sb.get_status())	      # retrieve general information
print(await sb.get_powermeters())     # retrieive power meter details
print(await sb.get_batterysystem())   # retrieve battery system data
print(await sb.get_inverter())        # retrieve inverter status
print(await sb.get_systemdata())      # retrieve system data
print(await sb.get_battery())         # get battery information

# Async needs to close the connection!
await sb.logout()
```

### SonnenAPI v2 - sync
``` python
# API v2
# can either be access directly, see below, or
# via sb.sb2 (gets initialiazed automatically when creating a V1 object)

from sonnebatterie2 import SonnenBatterieV2

sb_host = '192.168.1.2'
sb_token = 'SeCrEtToKeN'        # retrieve via Web UI of SonnenBatterie

sb2 = SonnenBatterieV2(sb_host, sb_token)
print(sb2.get_configurations())         # retrieve configuration overview
print(sb2.get_battery_module_data())    # get battery module data
print(sb2.get_inverter_data())          # retrieve inverter data
print(sb2.get_latest_data())            # get latest date from sonnenbatterie
print(sb2_get_powermeter_data())        # get data from power meters
print(sb2.get_status())                 # get overall status information
print(sb2.get_io_data())                # get io status
```

### SonnenAPI v2 - async
``` python
# API v2
# can either be access directly, see below, or
# via sb.sb2 (gets initialiazed automatically when creating a V1 object)

from sonnebatterie2 import AsyncSonnenBatterieV2

sb_host = '192.168.1.2'
sb_token = 'SeCrEtToKeN'        # retrieve via Web UI of SonnenBatterie

sb2 = AsyncSonnenBatterieV2(sb_host, sb_token)
print(await sb2.get_configurations())         # retrieve configuration overview
print(await sb2.get_battery_module_data())    # get battery module data
print(await sb2.get_inverter_data())          # retrieve inverter data
print(await sb2.get_latest_data())            # get latest date from sonnenbatterie
print(await sb2_get_powermeter_data())        # get data from power meters
print(await sb2.get_status())                 # get overall status information
print(await sb2.get_io_data())                # get io status
# Async needs to close the connection!
await sb.logout()
```
