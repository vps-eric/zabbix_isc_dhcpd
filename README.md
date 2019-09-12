Based on: https://github.com/jpmenil/zabbix-templates/isc-dhcp

# on dhcp server
* install dependencies:
    * pip install pypureomapi
    * pip install netaddr
* mv userparameter_dhcp.conf /etc/zabbix/zabbix_agentd.d/
* mv check_dhcp_leases.py /usr/local/bin/
* Add lines like #= NAME =# to the end of all range statements, if you want.
* edit check_dhcp_leases.py to fix your omapi key and key name, also, probably the location of your dhcpd.conf file.

# import templates in zabbix
* add graphs

As far as i know, there is no native way implemented by ISC dhcp to request free lease.

Two choices, parse the dhcpd.leases file, or do it via omapi.

The script is using omapi and is far from perfect.

# Hacks by myself from original
* Deal with missing names of range statements
* Change template/code to pull all the values so you can make a stacked graph
* slightly hack up the template
* Zabbix 4.0
