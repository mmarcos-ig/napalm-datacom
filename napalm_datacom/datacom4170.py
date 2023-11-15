# -*- coding: utf-8 -*-
# Copyright 2016 Dravetech AB. All rights reserved.
#
# The contents of this file are licensed under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with the
# License. You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under
# the License.

"""
Napalm driver for Datacom.

Read https://napalm.readthedocs.io for more information.
"""

from napalm.base import NetworkDriver

from napalm_datacom.netmiko.ssh_dispatcher import ConnectHandler
from netmiko import NetMikoTimeoutException
from napalm.base.exceptions import ConnectionException
from napalm.base.netmiko_helpers import netmiko_args
from typing import Optional, Dict
from socket import error as socket_error

from napalm.base.exceptions import (
    #ReplaceConfigException,
    #MergeConfigException,
    ConnectionClosedException,
    #CommandErrorException,
    #CommitConfirmException,
)

# from napalm.base.exceptions import (
#     ConnectionException,
#     SessionLockedException,
#     MergeConfigException,
#     ReplaceConfigException,
#     CommandErrorException,
# )

from re import findall, search, sub

HOUR_SECONDS = 3600
DAY_SECONDS = 24 * HOUR_SECONDS
YEAR_SECONDS = 365 * DAY_SECONDS

### WORKING ON COMPLETING DEVICE METHODS IN BASE_CONNECTION.PY
### PARTICULARLY: SESSION PREPARATION OF _OPEN()

class DatacomDriver(NetworkDriver):
    """Napalm driver for Datacom."""

    def __init__(self, hostname, username, password, timeout=60, optional_args=None):
        """Constructor."""
        self.device = None
        self.hostname = hostname
        self.username = username
        self.password = password
        self.timeout = timeout

        if optional_args is None:
            optional_args = {}

        self.prompt = ""

        self.transport = optional_args.get("transport", "ssh")

        self.netmiko_optional_args = netmiko_args(optional_args)

        default_port = {"ssh": 22, "telnet": 23}
        self.netmiko_optional_args.setdefault("port", default_port[self.transport])
        
        self.device = None

        self.profile = "4100s"

    def open(self):
        """Open a SSH connection to the device."""

        device_type = "datacom_os"
        if self.transport == "telnet":
            device_type = "datacom_os_telnet"
        self.device = self._netmiko_open__(
            device_type, netmiko_optional_args=self.netmiko_optional_args
        )

    def _netmiko_open__(
        self, device_type: str, netmiko_optional_args: Optional[Dict] = None
    ) -> ConnectHandler:
        """Standardized method of creating a Netmiko connection using napalm attributes."""
        if netmiko_optional_args is None:
            netmiko_optional_args = {}
        try:
            self._netmiko_device = ConnectHandler(
                device_type=device_type,
                host=self.hostname,
                username=self.username,
                password=self.password,
                timeout=self.timeout,
                **netmiko_optional_args
            )
        except NetMikoTimeoutException:
            raise ConnectionException("Cannot connect to {}".format(self.hostname))

        return self._netmiko_device

    def _send_command(self, command):
        """Wrapper for self.device.send.command().

        If command is a list will iterate through commands until valid command.
        """
        try:
            if isinstance(command, list):
                for cmd in command:
                    output = self._send_command(cmd)
                    if "% Invalid" not in output:
                        break
            else:
                return self.device.send_command(command)
        except (socket_error, EOFError) as e:
            raise ConnectionClosedException(str(e))

    def close(self):
        """Close the connection to the device"""
        self._netmiko_device.disconnect()
        pass

    @staticmethod
    def convert_uptime(uptime_str):

        """ convert uptime string to uptime integer in seconds """

        # example input: "159 d, 10 h, 33 m, 14 s" (*4100s)
        # example input: "22:39:16 up 172 days, 15 min, ..." (*4170s)

        uptime = 0
        time_list = uptime_str.split(",")
        for element in time_list:
            if "days" in element:
                a = element.split("up")[1].split("days")[0]
                if a:
                    uptime += int(a)*DAY_SECONDS
            if "min" in element:
                uptime += int(element.split("min")[0])*60 

        return uptime

    def get_facts(self):
        """ Return a set of facts from the device
         
        Example Output:

        {
            "uptime": 46203557,
            "vendor": "Datacom",
            "os_version": "15.2.6",
            "serial_number": "4421053",
            "model": "DM4100 - ETH24GX+2XX+S+L3",
            "hostname": "SAO3-ASW5#",
            "fqdn": "",
            "interface_list": [
                "VLAN 25",
                "VLAN 319",
                ...
            ]
        }
        """

        facts = {}

        a = self._send_command("sh system uptime\n")
        if a:
            facts["uptime"] = self.convert_uptime(a.replace("sh system uptime",""))

        facts['vendor'] = "Datacom"

        a = self._send_command("sh firmware\n")

        b = findall("\s*(\S+)\s+Active\s+", a)
        if len(b) > 0:
            facts['os_version'] = b[0].strip()

        a = self._send_command("sh inventory\n")

        b = findall("\s+Serial number\s*:\s+(.*)\s*", a)
        if len(b) > 0:
            facts['serial_number'] = b[0].strip()

        b = findall("\s*Product model\s*:\s+(.*)", a)
        if len(b) > 0:
            facts['model'] = b[0].strip()

        facts['hostname'] = self.device.prompt

        facts['fqdn'] = ""

        a = self._send_command("show running-config interface\n")

        facts['interface_list'] = findall("interface ([\w\- /]+)",a)

        return facts
        
    def get_interfaces(self):
        """
        Get interface details.

        last_flapped is not implemented

        Example Output:

        {
            "Eth 1/1": {
                "mac_address": "00:04:DF:5A:27:30",
                "description": "== SSA2-ASW2 Eth1/1 ==",
                "is_enabled": true,
                "speed": "Auto",
                "is_up": true,
                "mtu": 9198
            },
            "Eth 1/2": {
                "mac_address": "00:04:DF:5A:27:31",
                "description": "",
                "is_enabled": false,
                "speed": "Auto",
                "is_up": false,
                "mtu": 9198
            },
            ...
        }

        """
    
        interfaces = {}

        a = self._send_command("sh int\n")
        b = a.split("interface")[1:]
        b[-1] = b[-1].split("---------------------")[0]

        for intf in b:
            fields_a = [x.strip() for x in intf.split("\n")]
            id = fields_a[0]

            interfaces[id] = {"last_flapped":-1}

            for field in fields_a:
                if "Port admin" in field:
                    interfaces[id]['is_enabled'] = True if 'Enabled' in field else False
                if "Link Status" in field:
                    interfaces[id]['is_up'] = True if 'Up' in field else False
                if "Description" in field:
                    interfaces[id]['description'] = field.split(":")[1].strip()
                if "Speed/Duplex" in field:
                    interfaces[id]['speed'] = findall("\s*Speed/Duplex\s*:\s+(.*)",field)[0]
                if "MTU" in field:
                    interfaces[id]['mtu'] = findall("\s*MTU\s*:\s+(.*)",field)[0].strip()

        a = self._send_command("show inventory chassis 1 slot 1 macs\n")
        b = findall("[\w\- /]+\s+[0-9a-f:]{17}",a)

        for intf in b:
            id = intf.split(":")[0][0:-2].strip()
            if id in interfaces:
                interfaces[id]['mac_address'] = findall("[0-9a-f:]{17}",intf)[0]

        return interfaces

    def get_interfaces_ip(self):
        """
        Get interface ip details.

        Returns a dict of dicts

        Example Output:

        {
            "lo 0": {
                "ipv4": {
                    "172.21.5.121": {
                        "prefix_length": "32"
                    }
                }
            },
            "MGMT-ETH": {
                "ipv4": {
                    "192.168.0.25": {
                        "prefix_length": "24"
                    }
                }
            },
            ...
        }

        """

        interfaces_ip = {}

        a = self._send_command("show running-config interface\n")

        b = [x for x in a.split("interface") if ("ipv4 address" in x or "ipv6 address" in x)]

        for x in b:

            id = x.split("\n")[0].strip()
            address = x.split("address")[1].split("\n")[0].strip().split("/")
            length = address[1]
            address = address[0]

            if "ipv4" in x:
                interfaces_ip[id] = {"ipv4":{address:{"prefix_length":length}}}
            else:
                interfaces_ip[id] = {"ipv6":{address:{"prefix_length":length}}}

        return interfaces_ip

    def get_vlans(self):
        """
        Get interface ip details.

        Returns a dict of dicts

        Example Output:
        {
            "27": {
                "name": "SOD1_Mgmt",
                "interfaces": [
                    "Eth1/4",
                    "Eth1/26"
                ]
            },
            "32": {
                "name": "NL:SAO3-CGR1-01",
                "interfaces": [
                    "Eth1/21",
                    "Eth1/26"
                ]
            },
            ...
        }

        """

        vlans = {}

        a = self._send_command("show running-config dot1q\n")

        b = [x.split("\n") for x in a.split(" vlan")[1:]]

        for x in b:

            id = x[0].strip()
            name = x[1].replace("name","").strip()
            interfaces = findall("\s*interface ([\w\-/]*)", ",".join(x))

            vlans[id] = {'name':name, 'interfaces':interfaces}

        return vlans
        
        
    
    def get_vlans_membership(self):
        """ 
        Similar to get_vlans except it also returns port membership
        Example Output:
        {
            "27": {
                "name": "SOD1_Mgmt",
                "interfaces": [
                    "T|Eth1/4",
                    "T|Eth1/26"
                ]
            },
            "32": {
                "name": "NL:SAO3-CGR1-01",
                "interfaces": [
                    "U|Eth1/21",
                    "T|Eth1/26"
                ]
            },
            ...
        }
        """

        vlans = {}

        a = self._send_command("show running-config dot1q\n")

        b = [x.split("\n") for x in a.split(" vlan")[1:]]

        for x in b:
            interfaces = []

            id = x[0].strip()
            name = x[1].replace("name","").strip()

            for y in range(len(x)):
                if "interface" in x[y]:
                    intf_id = x[y].replace("interface","").strip()
                    if "untagged" in x[y+1]:
                        intf_m = "U"
                    else:
                        intf_m = "T"
                    interfaces.append( intf_m+"|"+intf_id )

            vlans[id] = {'name':name, 'interfaces':interfaces}

        return vlans

