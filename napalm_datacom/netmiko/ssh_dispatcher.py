

from typing import Any, Type
from napalm_datacom.netmiko.datacom.datacom_os import (
    DatacomOsSSH
)
from napalm_datacom.netmiko.base_connection import BaseConnection

CLASS_MAPPER_BASE = {
    "datacom_os": DatacomOsSSH
}

new_mapper = {}
for k, v in CLASS_MAPPER_BASE.items():
    new_mapper[k] = v
    alt_key = k + "_ssh"
    new_mapper[alt_key] = v
CLASS_MAPPER = new_mapper



platforms = list(CLASS_MAPPER.keys())
platforms = list(CLASS_MAPPER.keys())
platforms.sort()
platforms_base = list(CLASS_MAPPER_BASE.keys())
platforms_base.sort()
platforms_str = "\n".join(platforms_base)
platforms_str = "\n" + platforms_str


telnet_platforms = [x for x in platforms if "telnet" in x]
telnet_platforms_str = "\n".join(telnet_platforms)
telnet_platforms_str = "\n" + telnet_platforms_str

def ConnectHandler(*args: Any, **kwargs: Any) -> "BaseConnection":
    """Factory function selects the proper class and creates object based on device_type."""
    device_type = kwargs["device_type"]
    if device_type not in platforms:
        if device_type is None:
            msg_str = platforms_str
        else:
            msg_str = telnet_platforms_str if "telnet" in device_type else platforms_str
        raise ValueError(
            "Unsupported 'device_type' "
            "currently supported platforms are: {}".format(msg_str)
        )
    ConnectionClass = ssh_dispatcher(device_type)
    return ConnectionClass(*args, **kwargs)

def ssh_dispatcher(device_type: str) -> Type["BaseConnection"]:
    """Select the class to be instantiated based on vendor/platform."""
    return CLASS_MAPPER[device_type]