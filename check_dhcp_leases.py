#!/bin/python3

from netaddr import iter_iprange
from dotenv import load_dotenv
import os
import pypureomapi

load_dotenv()

# See https://github.com/isc-projects/dhcp/blob/31e68e5e3b863a4859562e0bb808888d74af7497/server/dhcpd.8#L533
leases_states = {
    1: 'free',
    2: 'active',
    3: 'expired',
    4: 'released',
    5: 'abandoned',
    6: 'reset',
    7: 'backup',
    8: 'reserved',
    9: 'bootp'
}

class OMAPI:
    KEYNAME = os.getenv('KEYNAME')
    BASE64_ENCODED_KEY = os.getenv('BASE64_ENCODED_KEY')
    IP = os.getenv('IP')
    Port = int(os.getenv('Port'))
    OMAPI_OP_UPDATE = int(os.getenv('OMAPI_OP_UPDATE'))
    def __init__(self):
        self.conn = pypureomapi.Omapi(
            self.IP,
            self.Port,
            self.KEYNAME.encode('utf_8'),
            self.BASE64_ENCODED_KEY.encode('utf_8')
        )
    def get_lease_state(self, ip):
        msg = pypureomapi.OmapiMessage.open(b"lease")
        msg.obj.append((b"ip-address", pypureomapi.pack_ip(str(ip))))
        response = self.conn.query_server(msg)
        if response.opcode != self.OMAPI_OP_UPDATE:
            print('ZBX_NOTSUPPORTED')
        else:
            return ord(response.obj[0][1][-1:])


def check(ipsList, ip_type):
    ip_start = ipsList.split('-')[0]
    ip_end = ipsList.split('-')[1]
    ips = list(iter_iprange(ip_start, ip_end, step=1))
    results = {
        'Total': len(ips),
        'free': 0,
        'active': 0,
        'expired': 0,
        'abandoned': 0,
        'reset': 0,
        'backup': 0,
        'reserved': 0,
        'bootp': 0,
        'released': 0
    }
    omapi= OMAPI()
    for ip in ips:
        state = omapi.get_lease_state(ip)
        try:
            results[leases_states[state]] += 1
        except KeyError:
            print ('ZBX_NOTSUPPORTED')
    return (results[ip_type], results['Total'])
