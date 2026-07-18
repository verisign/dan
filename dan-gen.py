#!/usr/bin/env python3
import argparse
import sys
import os
import certifi

os.environ.setdefault("SSL_CERT_FILE", certifi.where())
os.environ.setdefault("REQUESTS_CA_BUNDLE", certifi.where())

from dan import AIDISCA_RRTYPE, AIINDEX_RRTYPE, AIDISCA_TYPE_NAME, AIINDEX_TYPE_NAME
from dan.aidisca import (
    AIDISCARecord,
    agent_card_extension,
    protocol_to_value,
    presentation_format_aidisca,
    verbose_summary_aidisca
)
from dan.mcp_adapter import get_mcp_capabilities
from dan.a2a_adapter import extract_a2a_metadata
from dan.dane import parse_dane, load_pem_certificate, certificate_association_data
from dan.dnswire import ensure_fqdn, rfc3597_record_one_line
from dan.aiindex import (
    AIINDEXRecord,
    presentation_format_aiindex,
    verbose_summary_aiindex
)

def parse_comma_list(value: str) -> list[str]:
    items = [item.strip() for item in value.split(",")]
    items = [item for item in items if ensure_fqdn(item)]
    if not items:
        raise ValueError("At least one agent name is required")
    return items

def _capabilities_string(values: str | list[str]) -> str:
    if isinstance(values, str):
        parts = values.split(",")
    else:
        parts = values

    clean = []
    for part in parts:
        value = str(part).strip()
        if value and value not in clean:
            clean.append(value)

    if not clean:
        raise ValueError("Capabilities cannot be empty")

    return ",".join(clean)


def gen_aidisca(args) -> int:
    proto = args.proto.lower()

    if proto == "mcp" and not args.endpoint:
        print("--endpoint is required for MCP.", file=sys.stderr)
        return 2

    if proto == "a2a" and not args.card:
        print("--card is required for A2A.", file=sys.stderr)
        return 2

    proto_val = protocol_to_value(args.proto)
    cert_usage, selector, matching_type = parse_dane(args.dane)

    endpoint = args.endpoint
    capabilities_source = "operator override"
    extensions = b""
    if proto == "a2a":
        try:
            card_endpoint, card_capabilities = extract_a2a_metadata(args.card)

            if not endpoint and card_endpoint:
                endpoint = card_endpoint

            if args.capabilities:
                capabilities = _capabilities_string(args.capabilities)
            else:
                capabilities = _capabilities_string(card_capabilities)
                capabilities_source = "A2A Agent Card"

            extensions += agent_card_extension(args.card)

        except Exception as exc:
            print(f"Could not derive A2A metadata: {exc}", file=sys.stderr)
            print(
                "For A2A, provide a valid --card, or provide "
                "--endpoint and --capabilities manually.",
                file=sys.stderr,
            )
            return 2

    elif args.capabilities:
        capabilities = _capabilities_string(args.capabilities)

    elif proto == "mcp":
        try:
            result = get_mcp_capabilities(args.endpoint, args.auth_token)
            capabilities = _capabilities_string(result.capabilities)
            capabilities_source = result.source
        except Exception as exc:
            print("Could not derive Capabilities from MCP service endpoint.", file=sys.stderr)
            print(f"Reason: {exc}", file=sys.stderr)
            print('Re-run with --capabilities "tool_one,tool_two".', file=sys.stderr)
            return 2

    else:
        print(
            "Capabilities are required unless they can be derived from "
            "A2A Agent Card or MCP tools/list.",
            file=sys.stderr,
        )
        return 2

    if not endpoint:
        if proto == "a2a":
            print(
                "Could not determine Service Endpoint from A2A Agent Card. "
                "Provide --service-endpoint explicitly.",
                file=sys.stderr,
            )
        else:
            print("--service-endpoint is required for MCP.", file=sys.stderr)
        return 2

    cert = load_pem_certificate(args.cert_file)
    cert_assoc_data = certificate_association_data(cert, selector, matching_type)

    record = AIDISCARecord(
        proto=proto_val,
        capabilities=capabilities,
        endpoint=endpoint,
        cert_usage=cert_usage,
        selector=selector,
        matching_type=matching_type,
        cert_assoc_data=cert_assoc_data,
        extensions=extensions,
    )
    rdata = record.encode()

    print()
    print(
        rfc3597_record_one_line(
            args.domain,
            AIDISCA_RRTYPE,
            rdata,
            args.ttl,
        )
    )

    if args.pf:
        print()
        print("Presentation Format")
        print("----------------------")
        print(
            presentation_format_aidisca(
                ensure_fqdn(args.domain),
                args.ttl,
                record,
            )
        )

    if args.verbose:
        print()
        print("Presentation Format")
        print("----------------------")
        print(
            presentation_format_aidisca(
                ensure_fqdn(args.domain),
                args.ttl,
                record,
            )
        )

        print()
        print(
            verbose_summary_aidisca(
                ensure_fqdn(args.domain),
                args.ttl,
                record,
                args.card,
                capabilities_source,
                args.cert_file,
                args.auth_token,
            )
        )
        print()

    print()
    return 0


def gen_aiindex(args) -> int:
    all_agents = parse_comma_list(args.agents)
    record = AIINDEXRecord(
        agents=all_agents
    )
    rdata = record.encode()

    print()
    print(
        rfc3597_record_one_line(
            args.domain,
            AIINDEX_RRTYPE,
            rdata,
            args.ttl,
        )
    )

    if args.pf:
        print()
        print("Presentation Format")
        print("----------------------")
        print(
            presentation_format_aiindex(
                ensure_fqdn(args.domain),
                args.ttl,
                record,
            )
        )

    if args.verbose:
        print()
        print("Presentation Format")
        print("----------------------")
        print(
            presentation_format_aiindex(
                ensure_fqdn(args.domain),
                args.ttl,
                record,
            )
        )

        print()
        print(
            verbose_summary_aiindex(
                ensure_fqdn(args.domain),
                args.ttl,
                record,
            )
        )
        print()

    print()

    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="DAN generation tool for AIDISCA and AIINDEX records."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    aidisca = sub.add_parser("aidisca", help="Generate an AIDISCA ({AIDISCA_RRTYPE}) record")
    aidisca.add_argument(
        "--proto",
        choices=["mcp", "a2a"],
        required=True,
        help="AI Agent Proto field",
    )
    aidisca.add_argument(
        "--domain",
        required=True,
        help="Domain name where the AIDISCA record is published",
    )
    aidisca.add_argument(
        "--endpoint",
        help=(
            "Service Endpoint field. Required for MCP. "
            "Optional override for A2A; otherwise derived from Agent Card."
        ),
    )
    aidisca.add_argument(
        "--capabilities",
        help="Comma-separated Capabilities field; overrides automatic extraction",
    )
    aidisca.add_argument(
        "--cert-file",
        required=True,
        help="PEM certificate file used to compute Certificate Association Data",
    )
    aidisca.add_argument(
        "--dane",
        default="3,1,1",
        help="DANE parameters as CertUsage,Selector,MatchingType. Default: 3,1,1",
    )
    aidisca.add_argument(
        "--card",
        help="A2A Agent Card URL. Required for A2A. Encoded as an Agent Card extension.",
    )
    aidisca.add_argument(
        "--auth-token",
        help="Bearer token for MCP capability discovery; never written to DNS output",
    )
    aidisca.add_argument(
        "--ttl",
        type=int,
        default=60,
        help="DNS TTL. Default: 60",
    )
    aidisca.add_argument(
        "--pf",
        action="store_true",
        help="Print only AIDISCA presentation format.",
    )
    aidisca.add_argument(
        "--verbose",
        action="store_true",
        help="Print only verbose summary",
    )
    aidisca.set_defaults(func=gen_aidisca)

    aiindex = sub.add_parser("aiindex", help="Generate an AIINDEX ({AIINDEX_RRTYPE}) record")
    aiindex.add_argument(
        "--domain",
        required=True,
        help="Domain name where the AIINDEX record is published",
    )
    aiindex.add_argument(
        "--agents",
        required=True,
        help="Comma separated AIDISCA publication names.",
    )
    aiindex.add_argument(
        "--ttl",
        type=int,
        default=60,
        help="DNS TTL. Default: 60",
    )
    aiindex.add_argument(
        "--pf",
        action="store_true",
        help="Print only AIINDEX presentation format.",
    )
    aiindex.add_argument(
        "--verbose",
        action="store_true",
        help="Print only verbose summary",
    )
    aiindex.set_defaults(func=gen_aiindex)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())

