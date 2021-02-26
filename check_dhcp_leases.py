#!/bin/python3

from netaddr import iter_iprange
import argparse
import itertools
import json
import os
import pypureomapi
import re
import sys

DHCP_CONF = '/usr/pkg/etc/dhcp/dhcpd.conf' if os.path.isfile('/usr/pkg/etc/dhcp/dhcpd.conf') else '/etc/dhcp/dhcpd.conf'
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
    KEYNAME = 'defomapi'
    BASE64_ENCODED_KEY = '6h54k4gpHqzTLtNo2ZKZUKLWc5ugjMGXUkdYe05I3qMdESyRhuIu13wKDHcgVY3D+kwYUIlR0AZRYmDRso3hqg=='
    ip = '127.0.0.1'
    port = 7911
    OMAPI_OP_UPDATE = 3
    def __init__(self):
        self.conn = pypureomapi.Omapi(
            self.ip,
            self.port,
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

class Ranges:
    def discover():
        reg_range = re.compile('range\s(.*?);')
        reg_name = re.compile('#= (.*?) =#')
        ranges = []
        with open(DHCP_CONF, 'r') as f:
            for key, group in itertools.groupby(f, lambda line: line.startswith('\n')):
                if not key:
                    subnet_info = list(group)
                    name = [m.group(1) for l in subnet_info for m in [reg_name.search(l)] if m]
                    range_list = [m.group(1) for l in subnet_info for m in [reg_range.search(l)] if m]
                    if range_list:
                        for num, range in enumerate(range_list):
                            ip_start = range.split(' ')[0]
                            ip_end = range.split(' ')[1]
                            ips = list(iter_iprange(ip_start, ip_end, step=1))
                            myname = 'IP Range {0}'.format(str(num))
                            if num < len(name):
                                myname = name[num]
                            ranges.append({'{#NAME}': myname, '{#RANGE}': '{0}-{1}'.format(ip_start, ip_end), '{#TOTAL}': len(ips)})
        ranges_dict = {}
        ranges_dict['data'] = ranges
        return ranges_dict

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
        return (results[ip_type])

parser = argparse.ArgumentParser(
    prog="Zabbix Lease Reporting",
    description="""
    A simple reporting script for Zabbix to enable DHCP collection.
    """,
    epilog="""
    Please remember to edit the omapi key and key name in the OMAPI class.
    """,
)
parser.add_argument(
    "-d",
    "--discover",
    help="The initial discovery script for zabbix to return the IP ranges, names, and total number of IPs.",
    action="store_true"
)
parser.add_argument(
    "-c",
    "--check",
    help="Check and IP range (as reported by the --discover option)",
    action="store_true"
)
parser.add_argument(
    "--range",
    help="The range to check (written as: 192.168.1.2-192.168.1.254)",
    type=str,
    default=None
)
parser.add_argument(
    "--state",
    help="Get the number of leases in the specified range that are in this state.",
    choices=[
        "free",
        "active",
        "expired",
        "released",
        "abandoned",
        "reset",
        "backup",
        "reserved",
        "bootp"
    ],
    type=str,
    default=None
)
args = parser.parse_args()

if args.discover:
    ranges = Ranges.discover()
    print(json.dumps(ranges))
elif args.check:
    num_in_state = Ranges.check(args.range, args.state)
    print(num_in_state)
else:
    print("No option selected")
