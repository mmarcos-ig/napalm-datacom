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
    
    def _netmiko_close__(
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
        from re import search

        # example input: "159 d, 10 h, 33 m, 14 s"

        uptime = 0
        time_list = uptime_str.split(",")
        for element in time_list:
            if "y" in element:
                uptime += int(element.split()[0])*YEAR_SECONDS
            if "d" in element:
                uptime += int(element.split()[0])*DAY_SECONDS 
            if "h" in element:
                uptime += int(element.split()[0])*HOUR_SECONDS 
            if "m" in element:
                uptime += int(element.split()[0])*60
            if "s" in element:
                uptime += int(element.split()[0])

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

        a = self._send_command("sh uptime\n")

        b = findall("\S*System uptime: .*", a)
        if len(b) > 0:
            facts["uptime"] = self.convert_uptime(sub("\S*System uptime: ", "", b[0]).replace("\r",""))

        facts['vendor'] = "Datacom"

        a = self._send_command("sh firmware\n")

        b = findall("Firmware version: \d+\.{0,1}\d*\.{0,1}\d*", a)
        if len(b) > 0:
            facts['os_version'] = sub("Firmware version: ", "", b[0]).replace("\r","")

        a = self._send_command("sh system\n")

        b = findall("\s+Product ID:\s+.*", a)
        if len(b):
            facts['serial_number'] = sub("\s+Product ID:\s+", "", b[0]).replace("\r","")

        b = findall("\s+Model:\s+(.*)", a)
        if len(b) > 0:
            facts['model'] = sub("\s+Model:\s+", "", b[0]).replace("\r","")

        facts['hostname'] = self.prompt

        facts['fqdn'] = ""

        a = self._send_command("sh ip int\n")

        facts['interface_list'] = findall("VLAN \d+", a)

        a = self._send_command("sh int desc\n")

        b = findall("\w+\s+\d+/*\d*\s*:.*", a)
        if len(b) > 0:
            facts["interface_list"].extend( [sub("\s*:\s*\w*.*","",x) for x in b] )

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

        a = self._send_command("sh int status\n")
        a = a.split("Information of ")[1:]

        b = self._send_command("sh int swit\n")
        b = b.split("Information of ")[1:]

        for i in range(len(a)):
            fields_a = [x.strip() for x in a[i].split("\n")]
            fields_b = [x.strip() for x in b[i].split("\n")]
            id = fields_a[0]

            interfaces[id]={"last_flapped":-1}

            for field in fields_a:
                if "Port admin" in field:
                    interfaces[id]['is_enabled'] = True if 'Up' in field else False
                if "Link status" in field:
                    interfaces[id]['is_up'] = True if 'Up' in field else False
                if "Name" in field:
                    interfaces[id]['description'] = field.split("Name:")[1].strip()
                if "MAC address" in field:
                    interfaces[id]['mac_address'] = field.split("MAC address:")[1].strip()
                if "Speed-duplex" in field:
                    interfaces[id]['speed'] = field.split("Speed-duplex:")[1].strip()
            interfaces[id]['mtu'] = [field.split("MTU:")[1].strip() for field in fields_b if "MTU" in field]
            interfaces[id]['mtu'] = int(interfaces[id]['mtu'][0].split(" ")[0]) if len(interfaces[id]['mtu']) > 0 else ""

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

        a = self._send_command("sh ip int\n")

        a = [x.strip() for x in a.split("\n") if "/" in x]
        a = [[y.strip() for y in x.split("  ") if y.strip() not in ["", None]] for x in a]

        for x in a:
            interfaces_ip[x[0]] = {}
            interfaces_ip[x[0]]["ipv4"] = {}
            interfaces_ip[x[0]]["ipv4"][x[1].split("/")[0]] = {"prefix_length": x[1].split("/")[1]}

        a = self._send_command("sh ipv6 int\n")

        a = [x.strip() for x in a.split("\n") if "/" in x]
        a = [[y.strip() for y in x.split("  ") if y.strip() not in ["", None]] for x in a]

        for x in a:
            interfaces_ip[x[0]] = {}
            interfaces_ip[x[0]]["ipv6"] = {}
            interfaces_ip[x[0]]["ipv6"][x[2].split("::")[0]] = {"prefix_length": x[2].split("::")[1]}

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

        interfaces = {}

        a = self._send_command("sh vlan summary id all\n")
        a = [x for x in a.split("\n")]
        b = []

        for x in range(len(a)):
            o = a[x]

            port_lists = findall("[U,T,G,R,A,I]\(\w+\d+/*\d* to \w+\d+/*\d*\)", o)
            single_ports = findall("[U,T,G,R,A,I]\(\w+\d+/*\d*\)", o)
            number_id = findall("\d+",o)
            type_status = findall("[D,S]/[A,D]/[R,P,C,I]", o)
            
            if search("\s*\d{1,4}\s+.*\s+\w/\w/*\w*\s+[\S ]+\s*", o):
                b.append({'id': number_id[0],'type_status': type_status[0], 'ports':[]})
                b[-1]['name'] = o.split(b[-1]['id'])[1].split(b[-1]['type_status'])[0].strip()

            if len(b)>0:

                b[-1]['ports'].extend([u[2:-1] for u in single_ports])
                    
                for y in port_lists:
                    d = [z.replace(")","") for z in y.split("(")[1].split(" to ")]
                    membership_pl = y[0][0]
                    ll = int(d[0].split("/")[1])
                    ul = int(d[1].split("/")[1])

                    b[-1]['ports'].extend( [f"{d[0].split('/')[0]}/{v}" for v in range(ll,ul+1)] )

        vlans = {}

        for vlan in b:
            vlans[vlan['id']] = {'name':vlan['name'],'interfaces':vlan['ports']}

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

        interfaces = {}

        a = self._send_command("sh vlan summary id all\n")
        a = [x for x in a.split("\n")]
        b = []

        for x in range(len(a)):
            o = a[x]

            port_lists = findall("[U,T,G,R,A,I]\(\w+\d+/*\d* to \w+\d+/*\d*\)", o)
            single_ports = findall("[U,T,G,R,A,I]\(\w+\d+/*\d*\)", o)
            number_id = findall("\d+",o)
            type_status = findall("[D,S]/[A,D]/[R,P,C,I]", o)
            
            if search("\s*\d{1,4}\s+.*\s+\w/\w/*\w*\s+[\S ]+\s*", o):
                b.append({'id': number_id[0],'type_status': type_status[0], 'ports':[]})
                b[-1]['name'] = o.split(b[-1]['id'])[1].split(b[-1]['type_status'])[0].strip()

            if len(b)>0:

                b[-1]['ports'].extend([f"{u[0]}|{u[2:-1]}" for u in single_ports])
                    
                for y in port_lists:
                    d = [z.replace(")","") for z in y.split("(")[1].split(" to ")]
                    membership_pl = y[0][0]
                    ll = int(d[0].split("/")[1])
                    ul = int(d[1].split("/")[1])

                    b[-1]['ports'].extend( [f"{membership_pl}|{d[0].split('/')[0]}/{v}" for v in range(ll,ul+1)] )

        vlans = {}

        for vlan in b:
            vlans[vlan['id']] = {'name':vlan['name'],'interfaces':vlan['ports']}

        return vlans

