Based on: https://github.com/jpmenil/zabbix-templates/isc-dhcp

This is a heavily modified version of the original project. It reports only on shared networks. No command-line arguments exist from the original version of this program (so mistakes can't be made).

# Requirements
The DHCPd config MUST comply with all of the following assumptions:
- ALL range statements are within a subnet block
- ALL subnet blocks are within a shared-network block
These requirements are subject to change in the future.

# On the DHCP Server
1. Download this repo
2. Install dependencies:  
  1a. pip3 install -r ./requirements.txt
3. Move ```userparameter_dhcp.conf``` to ```/etc/zabbix/zabbix_agentd.d/```
4. Edit ```/etc/zabbix/zabbix_agentd.d/userparameter_dhcp.conf``` to reflect the full path to your script.
5. Add lines like ```#= NAME =#``` to the end of all range statements, if you want.
6. Copy ```./.env_example``` to ```./.env``` and make any changes necessary.

# Generate an OMAPI key for dhcp (if you have not already done so)
1. ```/usr/sbin/dnssec-keygen -a HMAC-MD5 -b 512 -n HOST defomapi```
2. ```cat ./Kdefomapi*```
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
