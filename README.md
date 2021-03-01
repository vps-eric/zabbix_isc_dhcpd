Based on: https://github.com/jpmenil/zabbix-templates/isc-dhcp

# On the DHCP Server
1. Download this repo
2. Install dependencies:  
  1a. pip3 install -r ./requirements.txt
3. Move ```userparameter_dhcp.conf``` to ```/etc/zabbix/zabbix_agentd.d/```
4. Edit ```/etc/zabbix/zabbix_agentd.d/userparameter_dhcp.conf``` to reflect the full path to your script.
5. Add lines like ```#= NAME =#``` to the end of all range statements, if you want.
6. Copy ```./.env_example``` to ```./.env``` and make any changes neccessary.

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

# Import templates in zabbix
* add graphs
