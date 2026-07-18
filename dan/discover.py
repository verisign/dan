import dns.resolver
import dns.rdatatype

from .aidisca import AIDISCARecord
from .aiindex import AIINDEXRecord
from . import AIDISCA_RRTYPE, AIDISCA_TYPE_NAME
from . import AIINDEX_RRTYPE, AIINDEX_TYPE_NAME

def discover_aidisca(domain_name: str, server: str | None = None) -> list[AIDISCARecord]:
    resolver = dns.resolver.Resolver()

    if server:
        resolver.nameservers = [server]

    answers = resolver.resolve(
        domain_name,
        dns.rdatatype.from_text(AIDISCA_TYPE_NAME),
    )

    records = []

    for answer in answers:
        rdata = answer.to_wire()
        record = AIDISCARecord.decode(rdata)
        records.append(record)

    return records 

def discover_aiindex(domain_name: str, server: str | None = None) -> list[AIINDEXRecord]:
    resolver = dns.resolver.Resolver()

    if server:
        resolver.nameservers = [server]

    answers = resolver.resolve(
        domain_name,
        dns.rdatatype.from_text(AIINDEX_TYPE_NAME),
    )

    records = []

    for answer in answers:
        rdata = answer.to_wire()
        record = AIINDEXRecord.decode(rdata)
        records.append(record)

    return records 
