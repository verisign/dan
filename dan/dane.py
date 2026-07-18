from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization


def parse_dane(value: str | None) -> tuple[int, int, int]:
    if not value:
        return (3, 1, 1)
    parts = value.replace(" ", ",").split(",")
    parts = [p for p in parts if p != ""]
    if len(parts) != 3:
        raise ValueError("--dane must have format usage,selector,matching-type, for example 3,1,1")
    usage, selector, matching = [int(p) for p in parts]
    if usage not in (0, 1, 2, 3):
        raise ValueError("Cert Usage must be 0, 1, 2, or 3")
    if selector not in (0, 1):
        raise ValueError("Selector must be 0 (full cert) or 1 (SPKI)")
    if matching not in (0, 1, 2):
        raise ValueError("Matching Type must be 0 (exact), 1 (SHA-256), or 2 (SHA-512)")
    return usage, selector, matching


def load_pem_certificate(path: str) -> x509.Certificate:
    with open(path, "rb") as f:
        data = f.read()
    return x509.load_pem_x509_certificate(data)


def certificate_association_data(cert: x509.Certificate, selector: int, matching_type: int) -> bytes:
    if selector == 0:
        selected = cert.public_bytes(serialization.Encoding.DER)
    elif selector == 1:
        selected = cert.public_key().public_bytes(
            serialization.Encoding.DER,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        )
    else:
        raise ValueError("unsupported selector")

    if matching_type == 0:
        return selected
    if matching_type == 1:
        digest = hashes.Hash(hashes.SHA256())
    elif matching_type == 2:
        digest = hashes.Hash(hashes.SHA512())
    else:
        raise ValueError("unsupported matching type")
    digest.update(selected)
    return digest.finalize()
