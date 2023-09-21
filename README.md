# NAPALM Datacom

IGN Implementation of NAPALM Drivers for Datacom Switches.

https://github.com/mmarcos-ig/ign-napalm-datacom/tree/development

## Supported Huawei Network Devices

* Series 4370 WIP
* Series 4170 WIP
* Series 4100s
* Series 4050 WIP
* Series 2300 WIP

## Instructions

The driver is under development and iteration.

### Get info
| API   | Description  |
|--------|-----|
| get_facts() |Return general device information |
| get_interfaces() | Get interface information |
| get_interfaces_ip()|  Get interface IP information |
| get_vlans() | Get vlan information |

### Config

| API   | Description  |
|--------|-----|
|  cli() | Send any cli commands |

### Other tools
| API   | Description  |
|--------|-----|
|  |  |
|  |  |

### Plans to develop

* proper device and auxiliary methods (send_command(), write_channel(), send_config_set(), find_prompt(), etc)
* is_active()
* ping()
* other getters

## Quick start

Make sure to configure environment variables for LDAP user and password, else you can replace getenv() with strings containing those values

```python

from napalm import get_network_driver
from os import getenv

if True:
    LDAP_username = getenv("LDAP_username")
    LDAP_password = getenv("LDAP_password")
    #LDAP_username = "mmarcos"
    #LDAP_password = "<PASSWORD>"

driver = get_network_driver("datacom")
CNF2_ASW1 = driver("172.20.117.11",LDAP_username,LDAP_password)

CNF2_ASW1.open()

print( CNF2_ASW1.cli("sh uptime\n") )

print( CNF2_ASW1.get_facts() )
print( CNF2_ASW1.get_interfaces() )
print( CNF2_ASW1.get_interfaces_ip() )
print( CNF2_ASW1.get_vlans() )


```

