import struct
from dataclasses import dataclass, field
from .dnswire import encode_dns_name, decode_dns_names

@dataclass
class AIINDEXRecord:
    agents: list[str]
    extensions: bytes = b""

    def encode(self) -> bytes:
        name_list = b"".join(encode_dns_name(n) for n in self.agents)
        if len(name_list) > 65535:
            raise ValueError("AI Agent Domain Name List is too long")
        if len(self.extensions) > 65535:
            raise ValueError("Extensions field is too long")
        return struct.pack("!HH", len(name_list), len(self.extensions)) + name_list + self.extensions

    @classmethod
    def decode(cls, rdata: bytes) -> "AIINDEXRecord":
        if len(rdata) < 4:
            raise ValueError("AIINDEX RDATA too short")
        name_len, ext_len = struct.unpack("!HH", rdata[:4])
        if 4 + name_len + ext_len != len(rdata):
            raise ValueError("AIINDEX length fields do not match RDATA length")
        names = decode_dns_names(rdata[4:4+name_len])
        return cls(agents=names, extensions=rdata[4+name_len:])

    def summary(self) -> str:
        lines = [
            "AIINDEX Record",
            "--------------",
            "",
            "AI Agent Domain Name List:",
        ]

        for name in self.agents:
            lines.append(f" - {name}")

        if self.extensions:
            lines.extend(
                [
                    "",
                    f"Extensions: {self.extensions.hex().upper()}",
                ]
            )
        return "\n".join(lines)

def presentation_format_aiindex(
    domain: str,
    ttl: int,
    record: AIINDEXRecord,
    ) -> str:
    lines = [
        f"{domain} {ttl} IN AIINDEX ("
    ]

    for name in record.agents:
        lines.append(f"  {name}")

    if record.extensions:
        lines.append(f' "{record.extensions.hex().upper}"')

    lines.append(")")
    return "\n".join(lines)

def verbose_summary_aiindex(
    domain: str,
    ttl: int,
    record: AIINDEXRecord,
    ) -> str:
    lines = [
        "AIINDEX Record Summary",
        "----------------------",
        f"Domain Name                  : {domain}",
        "AI Agent Domain Name List    :",
    ]        
    for name in record.agents:
        lines.append(f"  - {name}")
    lines.append("Extensions                   : none")
    return "\n".join(lines)
