from napalm import get_network_driver
from os import getenv

LDAP_username = getenv("LDAP_username")
LDAP_password = getenv("LDAP_password")

if True:

    driver = get_network_driver("datacom")
    CNF2_ASW1 = driver("172.20.117.11",LDAP_username,LDAP_password)

    CNF2_ASW1.open()

    facts =  CNF2_ASW1.get_facts()

    print(facts)

    CNF2_ASW1.close()

if False:
    driver = get_network_driver("ios")
    BUE3_AR1 = driver("172.21.4.66", LDAP_username, LDAP_password)	
    #BUE3_LSR1 = driver("172.20.113.12", LDAP_username, LDAP_password)


    BUE3_AR1.open()

    a = BUE3_AR1.get_vlans()

    BUE3_AR1.close()



print()