from . import AIDISCA_RRTYPE, AIDISCA_TYPE_NAME
import struct
from dataclasses import dataclass, field

PROTO_REGISTRY = {"mcp": 1, "a2a": 2}
EXT_AGENT_CARD = 1

@dataclass
class AIDISCARecord:
    proto: int
    capabilities: str
    endpoint: str
    cert_usage: int
    selector: int
    matching_type: int
    cert_assoc_data: bytes
    extensions: bytes = b""

    def encode(self) -> bytes:
        capabilities_b = self.capabilities.encode("utf-8")
        endpoint_b = self.endpoint.encode("utf-8")
        if len(capabilities_b) > 65535:
            raise ValueError("Capabilities field is too long")
        if len(endpoint_b) > 65535:
            raise ValueError("Service Endpoint field is too long")
        if len(self.cert_assoc_data) > 65535:
            raise ValueError("Certificate Association Data is too long")
        if len(self.extensions) > 65535:
            raise ValueError("Extensions field is too long")
        header = struct.pack(
            "!BBBBHHHH",
            self.proto,
            self.cert_usage,
            self.selector,
            self.matching_type,
            len(capabilities_b),
            len(endpoint_b),
            len(self.cert_assoc_data),
            len(self.extensions),
        )
        return header + capabilities_b + endpoint_b + self.cert_assoc_data + self.extensions

    @classmethod
    def decode(cls, rdata: bytes) -> "AIDISCARecord":
        if len(rdata) < 12:
            raise ValueError("AIDISCA RDATA too short")
        proto, usage, selector, matching, cap_len, endpoint_len, cert_len, ext_len = struct.unpack("!BBBBHHHH", rdata[:12])
        pos = 12
        end_cap = pos + cap_len
        end_endpoint = end_cap + endpoint_len
        end_cert = end_endpoint + cert_len
        end_ext = end_cert + ext_len
        if end_ext != len(rdata):
            raise ValueError("AIDISCA length fields do not match RDATA length")
        return cls(
            proto=proto,
            cert_usage=usage,
            selector=selector,
            matching_type=matching,
            capabilities=rdata[pos:end_cap].decode("utf-8"),
            endpoint=rdata[end_cap:end_endpoint].decode("utf-8"),
            cert_assoc_data=rdata[end_endpoint:end_cert],
            extensions=rdata[end_cert:end_ext],
        )

    def parse_extensions(self) -> list[tuple[int, bytes]]:
        entries = []
        pos = 0
        while pos < len(self.extensions):
            if pos + 4 > len(self.extensions):
                raise ValueError("malformed extension data")
            code, length = struct.unpack("!HH", self.extensions[pos:pos+4])
            pos += 4
            if pos + length > len(self.extensions):
                raise ValueError("malformed extension length")
            entries.append((code, self.extensions[pos:pos+length]))
            pos += length
        return entries

    def agent_card_url(self) -> str | None:
        for code, value in self.parse_extensions():
            if code == EXT_AGENT_CARD:
                return value.decode("utf-8")
        return None
        
    def summary(self) -> str:
        lines = [
            f"AI Agent Proto               : {protocolval_to_proto(self.proto).upper()} ({self.proto})",
            f"Capabilities                 : {self.capabilities}",
            f"Service Endpoint             : {self.endpoint}",
            f"Cert Usage                   : {self.cert_usage}",
            f"Selector                     : {self.selector}",
            f"Matching Type                : {self.matching_type}",
            f"Certificate Association Data : {self.cert_assoc_data.hex().upper()}",
        ]

        agentcardurl = self.agent_card_url()
        if agentcardurl:
            lines.append(f"Extensions                   : Agent Card = {agentcardurl}")
        else:
            lines.append("Extensions                   : none")
        
        lines.append("\n")
        return "\n".join(lines)


def protocol_to_value(name: str) -> int:
    try:
        return PROTO_REGISTRY[name.lower()]
    except KeyError:
        raise ValueError(f"unsupported AI Agent Proto: {name}")

def protocolval_to_proto(protoval: int) -> str:
    return next((k for k, v in PROTO_REGISTRY.items() if v == protoval), None)

def agent_card_extension(url: str) -> bytes:
    value = url.encode("utf-8")
    if len(value) > 65535:
        raise ValueError("Agent Card extension value too long")
    return struct.pack("!HH", EXT_AGENT_CARD, len(value)) + value

def presentation_format_aidisca(
    domain: str,
    ttl: int,
    record: AIDISCARecord,
) -> str:
    lines = [
        f"{domain} {ttl} IN AIDISCA (",
        f"  {record.proto} "
        f"{record.cert_usage} "
        f"{record.selector} "
        f"{record.matching_type}",
        f'  "{record.capabilities}"',
        f'  "{record.endpoint}"',
        f"  {record.cert_assoc_data.hex().upper()}",
    ]

    if record.extensions:
        extension_strings = []

        for code, value in parse_extensions(record.extensions):
            length = len(value)

            escaped_header = (
                f"\\{(code >> 8) & 0xFF:03o}"
                f"\\{code & 0xFF:03o}"
                f"\\{(length >> 8) & 0xFF:03o}"
                f"\\{length & 0xFF:03o}"
            )

            extension_value = value.decode("utf-8", errors="replace")
            extension_strings.append(escaped_header + extension_value)

        lines.append(f'  "{",".join(extension_strings)}"')

    lines.append(")")
    return "\n".join(lines)

def verbose_summary_aidisca(
    domain: str,
    ttl: int,
    record: AIDISCARecord,
    agentcardurl: str,
    capabilities_source: str,
    certfile: str,
    authtoken: str
) -> str:
    lines = [
        "AIDISCA Record Summary",
        "----------------------",
        f"Domain Name                  : {domain}",
        f"AI Agent Proto               : {protocolval_to_proto(record.proto).upper()} ({record.proto})",
        f"Capabilities                 : {record.capabilities}",
        f"Capabilities Source          : {capabilities_source}",
        f"Service Endpoint             : {record.endpoint}",
        f"Cert Usage                   : {record.cert_usage}",
        f"Selector                     : {record.selector}",
        f"Matching Type                : {record.matching_type}",
        f"Certificate Source           : {certfile}",
        f"Certificate Association Data : {record.cert_assoc_data.hex().upper()}",
    ]

    if authtoken:
        lines.append("Authentication               : Bearer token provided")

    if agentcardurl:
        lines.append(f"Extensions                   : Agent Card = {agentcardurl}")
    else:
        lines.append("Extensions                   : none")
    
    lines.append("\n")
    return "\n".join(lines)
