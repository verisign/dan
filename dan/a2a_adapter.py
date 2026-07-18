from urllib.parse import urljoin
import requests

def _as_list(value):
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def extract_a2a_metadata(agent_card_url: str) -> tuple[str | None, list[str]]:
    """Fetch an A2A Agent Card and return Service Endpoint + Capabilities.

    For A2A, the Agent Card is the discovery source.

    Service Endpoint:
      - Prefer serviceEndpoint/service_endpoint.
      - Fall back to url/endpoint if present.
      - Resolve relative paths against the Agent Card URL.

    Capabilities:
      - Use capabilities/skills as published.
      - For dict entries, prefer id, then name, displayName, description.
    """
    response = requests.get(agent_card_url, timeout=15)
    response.raise_for_status()
    card = response.json()

    endpoint = (
        card.get("serviceEndpoint")
        or card.get("service_endpoint")
        or card.get("url")
        or card.get("endpoint")
    )

    if endpoint:
        endpoint = urljoin(agent_card_url, str(endpoint))

    capabilities: list[str] = []

    for key in ("capabilities", "skills"):
        for item in _as_list(card.get(key)):
            if isinstance(item, str):
                capabilities.append(item)
            elif isinstance(item, dict):
                for candidate in ("id", "name", "displayName", "description"):
                    value = item.get(candidate)
                    if value:
                        capabilities.append(str(value))
                        break

    return endpoint, _dedupe_preserve_order(capabilities)


def _dedupe_preserve_order(values: list[str]) -> list[str]:
    seen = set()
    out = []

    for value in values:
        clean = str(value).strip()
        if clean and clean not in seen:
            seen.add(clean)
            out.append(clean)

    return out