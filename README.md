Based on: https://github.com/jpmenil/zabbix-templates/isc-dhcp

# On the DHCP Server
1. Install dependencies:  
  1a. pip3 install -r ./requirements.txt
2. Move ```userparameter_dhcp.conf``` to ```/etc/zabbix/zabbix_agentd.d/```
3. Move ```check_dhcp_leases.py``` to ```/usr/local/bin/```
4. Add lines like ```#= NAME =#``` to the end of all range statements, if you want.
5. Edit check_dhcp_leases.py to fix your omapi key and key name, also, probably the location of your dhcpd.conf file.

# Generate an OMAPI key for dhcp (if you have not already done so)
1. /usr/sbin/dnssec-keygen -a HMAC-MD5 -b 512 -n HOST defomapi
2. cat ./Kdefomapi*
3. Copy your key
4. Add the omapi config to your dhcp config
Example:
```
omapi-port 7911;
omapi-key defomapi;
key defomapi {
     algorithm hmac-md5;
     secret *paste your key here*;
}
```

# Import templates in zabbix
* add graphs
