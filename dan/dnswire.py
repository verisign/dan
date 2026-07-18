import re


def ensure_fqdn(name: str) -> str:
    if not name:
        raise ValueError("domain name must not be empty")
    return name if name.endswith(".") else name + "."


def encode_dns_name(name: str) -> bytes:
    name = ensure_fqdn(name)
    if name == ".":
        return b"\x00"
    out = bytearray()
    for label in name[:-1].split("."):
        label_bytes = label.encode("ascii")
        if len(label_bytes) > 63:
            raise ValueError(f"DNS label too long: {label}")
        out.append(len(label_bytes))
        out.extend(label_bytes)
    out.append(0)
    return bytes(out)


def decode_dns_names(data: bytes) -> list[str]:
    names = []
    pos = 0
    while pos < len(data):
        labels = []
        while True:
            if pos >= len(data):
                raise ValueError("truncated DNS name")
            ln = data[pos]
            pos += 1
            if ln == 0:
                break
            if ln & 0xC0:
                raise ValueError("DNS name compression is not allowed in AIINDEX RDATA")
            if pos + ln > len(data):
                raise ValueError("truncated DNS label")
            labels.append(data[pos:pos+ln].decode("ascii"))
            pos += ln
        names.append(".".join(labels) + ".")
    return names


def hex_lines(data: bytes, width: int = 64) -> list[str]:
    h = data.hex().upper()
    return [h[i:i+width] for i in range(0, len(h), width)]


def rfc3597_record(domain_name: str, rrtype: int, rdata: bytes, ttl: int = 60) -> str:
    lines = hex_lines(rdata)
    if len(lines) == 1:
        return f"{ensure_fqdn(domain_name)} {ttl} IN TYPE{rrtype} \\# {len(rdata)} {lines[0]}"
    body = "\n  ".join(lines)
    return f"{ensure_fqdn(domain_name)} {ttl} IN TYPE{rrtype} \\# {len(rdata)} (\n  {body}\n)"

def rfc3597_record_one_line(owner_name: str, rrtype: int, rdata: bytes, ttl: int) -> str:
    return f"{ensure_fqdn(owner_name)} {ttl} IN TYPE{rrtype} \\# {len(rdata)} {rdata.hex().upper()}"
    
def parse_rfc3597_hex(text: str) -> bytes:
    cleaned = re.sub(r"[^0-9A-Fa-f]", "", text)
    if len(cleaned) % 2:
        raise ValueError("hex data has odd length")
    return bytes.fromhex(cleaned)

