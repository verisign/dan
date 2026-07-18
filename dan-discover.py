#!/usr/bin/env python3

import argparse
import sys

from dan.discover import discover_aidisca
from dan.discover import discover_aiindex
from dan.aidisca import (
    AIDISCARecord,
    agent_card_extension,
    protocol_to_value,
    presentation_format_aidisca,
    verbose_summary_aidisca
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Discover AI agent metadata using DAN records."
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    aidisca = subparsers.add_parser(
        "aidisca",
        help="Discover a known AI agent publication name using AIDISCA.",
    )

    aidisca.add_argument(
        "--domain",
        required=True,
        help="AI agent publication domain name.",
    )

    aidisca.add_argument(
        "--dns",
        help="Optional DNS server to query, for example 127.0.0.1.",
    )

    aiindex = subparsers.add_parser(
        "aiindex",
        help="Discover AI agent publication names using AIINDEX.",
    )

    aiindex.add_argument(
        "--domain",
        required=True,
        help="AI Index location.",
    )

    aiindex.add_argument(
        "--dns",
        help="Optional DNS server to query, for example 127.0.0.1.",
    )

    args = parser.parse_args()

    if args.command == "aidisca":
        records = discover_aidisca(args.domain, server=args.dns)

        print(f"Found {len(records)} AIDISCA record(s)")
        print()

        for i, record in enumerate(records, start=1):
            print(f"Agent Name : {args.domain}")
            print()
            print(record.summary())
            print()

        return 0

    if args.command == "aiindex":
        records = discover_aiindex(args.domain, server=args.dns)

        print(f"Found {len(records)} AIINDEX record(s)")
        print()

        for i, record in enumerate(records, start=1):
            print(f"Domain Name : {args.domain}")
            print()
            print(record.summary())
            print()

        return 0

    parser.print_help()
    return 1 

if __name__ == "__main__":
    raise SystemExit(main())
