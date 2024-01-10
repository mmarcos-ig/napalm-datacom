from napalm import get_network_driver
from os import getenv
from re import findall

import traceback

import time

LDAP_username = getenv("LDAP_username")
LDAP_password = getenv("LDAP_password")

if True:

    if False:
        driver = get_network_driver("datacom")
        CNF2_ASW1 = driver("172.20.117.11",LDAP_username,LDAP_password)


        CNF2_ASW1.open()
        print(f"Connected ({time.time() - now})")

    driver = get_network_driver("datacom")

    with open("hosts_Datacom1_4100.txt") as hostsfile:
        hosts_text = hostsfile.read()

    hosts = findall("(\d+\.\d+\.\d+\.\d+)/\d+", hosts_text)

    for i in hosts:

        try:

            print(f"Running getters on {i}...", end="")
            devicex = driver(i,LDAP_username,LDAP_password)
            
            devicex.open()
            
            facts =  devicex.get_facts()
            interfaces =  devicex.get_interfaces()
            interfaces_ip =  devicex.get_interfaces_ip()
            vlans =  devicex.get_vlans()
            vlans_membership =  devicex.get_vlans_membership()

            if True:

                with open(f"facts_{i}.txt", "w+") as f:
                    f.write(repr(facts))
                with open(f"interfaces_{i}.txt", "w+") as f:
                    f.write(repr(interfaces))
                with open(f"interfaces_ip_{i}.txt", "w+") as f:
                    f.write(repr(interfaces_ip))
                with open(f"vlans_{i}.txt", "w+") as f:
                    f.write(repr(vlans))
                with open(f"vlans_membership_{i}.txt", "w+") as f:
                    f.write(repr(vlans_membership))

            facts =  None
            interfaces =  None
            interfaces_ip =  None
            vlans = None
            vlans_membership = None

            devicex.close()

            print("Success!")
            
        except:
            print("Fail!")
            with open(f"error_{i}.txt", "w+") as f:
                f.write(traceback.format_exc())

if False:
    driver = get_network_driver("ios")
    MVD1_ASW1 = driver("172.20.84.11", LDAP_username, LDAP_password)	
    #BUE3_LSR1 = driver("172.20.113.12", LDAP_username, LDAP_password)


    MVD1_ASW1.open()

    a = MVD1_ASW1.get_vlans()

    MVD1_ASW1.close()



print()