#!/bin/python3

import argparse
import ipaddress
import json
import os
import re

from dotenv import load_dotenv


class Range:
    _regex = re.compile(r'range\s+((?:\d+\.){3}\d+)\s+((?:\d+\.){3}\d+)\s*;')

    @classmethod
    def parse(cls, l: str) -> 'Range':
        match = Range._regex.fullmatch(l)

        if match is None or len(match.groups()) != 2:
            return None

        ok, s = Range._parse_address(match.group(1))
        if not ok:
            print(f'Invalid start address for range: {s}')
            return None

        ok, e = Range._parse_address(match.group(2))
        if not ok:
            print(f'Invalid end address for range: {s}')
            return None

        return Range(s, e)

    def __init__(self, s: ipaddress.IPv4Address, e: ipaddress.IPv4Address):
        self.start = s
        self.end = e

    @staticmethod
    def _parse_address(s: str) -> (bool, ipaddress):
        try:
            return True, ipaddress.ip_address(s)
        except ValueError:
            return False, None

    def __str__(self):
        return f'range {self.start} {self.end}'

    def retrieve_lease_counts(self, state_type: str) -> (int, int):
        """
        State type comes from the leases_states dict in check_dhcp_leases.py
        """
        from check_dhcp_leases import check as query_omapi
        return query_omapi(f'{self.start}-{self.end}', state_type)


class Subnet:
    _regex = re.compile(r'subnet\s+((?:\d+\.){3}\d+)\s+netmask\s+((?:\d+\.){3}\d+)\s*\{')

    @classmethod
    def parse(cls, l: str) -> 'Subnet':
        match = Subnet._regex.fullmatch(l)

        if match is None or len(match.groups()) != 2:
            return None

        try:
            return Subnet(ipaddress.ip_network(f'{match.group(1)}/{match.group(2)}'))
        except ValueError:
            print(f'Invalid subnet definition: {match.group(1)}/{match.group(2)}')
            return None

    def __init__(self, network: ipaddress.IPv4Network):
        self.net = network
        self.ranges = []

    def add_range(self, r: Range) -> bool:
        if not isinstance(r, Range):
            return False
        self.ranges.append(r)

    def __str__(self):
        return f'subnet {self.net.with_netmask}'

    def retrieve_lease_counts(self, state_type: str) -> (int, int):
        state_count = 0
        total = 0
        for r in self.ranges:
            _state_count, _total = r.retrieve_lease_counts(state_type)
            state_count += _state_count
            total += _total

        return state_count, total


class SharedNetwork:
    _regex = re.compile(r'shared-network\s+([\w\d_-]+)\s*\{')

    @classmethod
    def parse(cls, l: str) -> 'SharedNetwork':
        match = SharedNetwork._regex.fullmatch(l)
        if match is None or len(match.groups()) != 1:
            return None

        return SharedNetwork(match.group(1))

    def __init__(self, name: str):
        self.name = name
        self.subnets = []

    def add_subnet(self, s: Subnet) -> bool:
        if not isinstance(s, Subnet):
            return False
        self.subnets.append(s)

    def __str__(self):
        s = f'shared-network {self.name}\n'
        for subnet in self.subnets:
            s += f'    {subnet}\n'
            for r in subnet.ranges:
                s += f'        {r}\n'

        return s

    def retrieve_lease_counts(self, state_type: str) -> (int, int):
        state_count = 0
        total = 0
        for s in self.subnets:
            _state_count, _total = s.retrieve_lease_counts(state_type)
            state_count += _state_count
            total += _total

        return state_count, total


def parse_isc_dhcp_config(path: str):
    shared_nets = []

    current_sn = None
    with open(path, 'r') as f:
        for line in f.readlines():
            # skip empty lines
            line = line.strip()
            if line == '' or line[0] == '#':
                continue

            temp_sn = SharedNetwork.parse(line)
            if temp_sn is not None:
                if current_sn is not None:
                    shared_nets.append(current_sn)
                current_sn = temp_sn
                continue

            temp_subnet = Subnet.parse(line)
            if temp_subnet is not None:
                current_sn.add_subnet(temp_subnet)
                continue

            temp_range = Range.parse(line)
            if temp_range is not None:
                current_subnet = current_sn.subnets[len(current_sn.subnets) - 1]
                current_subnet.add_range(temp_range)
                continue

    return shared_nets


def parse_cmdline_args():
    parser = argparse.ArgumentParser(
        prog="Zabbix Lease Reporting v3",
        description="Reports ISC DHCP lease count for shared networks for Zabbix ingestion",
        epilog="Please remember to edit the omapi key and key name in the OMAPI class."
    )
    parser.add_argument(
        "-p",
        "--print-networks",
        help="Use this option to check that the discovered networks match the networks defined in the DHCP config",
        action="store_true"
    )
    parser.add_argument(
        "-P",
        "--print-networks-encoded",
        help="Prints discovered networks for Zabbix to ingest",
        action="store_true"
    )
    parser.add_argument(
        "-q",
        "--query-network",
        help="The name of the shared network to get lease information for",
        type=str,
        default=None
    )
    parser.add_argument(
        "-t",
        "--lease-query-type",
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
        default="active"
    )
    parser.add_argument(
        "-f",
        "--query-output-format",
        choices=[
            "count",
            "percentage"
        ],
        type=str,
        default="count"
    )

    return parser.parse_args()


def main():
    args = parse_cmdline_args()
    load_dotenv()

    isc_dhcp_config = parse_isc_dhcp_config(os.getenv('DHCP_CONF'))
    if args.print_networks:
        for sn in isc_dhcp_config:
            print(sn)
    elif args.print_networks_encoded:
        print(json.dumps({"data": list([{'{#NAME}': sn.name} for sn in isc_dhcp_config])}))
    elif args.query_network is not None:
        sn = next((_sn for _sn in isc_dhcp_config if _sn.name == args.query_network), None)
        if sn is None:
            print(f'Shared network {args.query_network} is unknown.')
            return

        state_count, total = sn.retrieve_lease_counts(args.lease_query_type)

        if args.query_output_format == "count":
            print(state_count)
        elif args.query_output_format == "percentage":
            print(state_count / total * 100)


if __name__ == '__main__':
    main()
