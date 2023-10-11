from napalm import get_network_driver
from os import getenv

LDAP_username = getenv("LDAP_username")
LDAP_password = getenv("LDAP_password")

if False:

    driver = get_network_driver("datacom")
    CNF2_ASW1 = driver("172.20.117.11",LDAP_username,LDAP_password)

    CNF2_ASW1.open()

    cli_o = CNF2_ASW1._send_command("sh uptime\n")

    facts =  CNF2_ASW1.get_facts()
    interfaces = CNF2_ASW1.get_interfaces()
    interfaces_ip = CNF2_ASW1.get_interfaces_ip()
    vlans1 = CNF2_ASW1.get_vlans()
    vlans2 = CNF2_ASW1.get_vlans_membership()

if True:
    driver = get_network_driver("junos")
    #BUE3_AR1 = driver("172.21.4.66", LDAP_username, LDAP_password)	
    BUE3_LSR1 = driver("172.20.113.12", LDAP_username, LDAP_password)


    BUE3_LSR1.open()

    a = BUE3_LSR1.get_vlans()



print()