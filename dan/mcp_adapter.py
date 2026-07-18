import asyncio
import re
from dataclasses import dataclass
import httpx

@dataclass
class MCPCapabilityResult:
    capabilities: list[str]
    source: str

async def _list_tools_streamable_http(service_endpoint: str, auth_token: str | None) -> list[str]:
    """Using the official MCP Python SDK with Streamable HTTP transport."""
    from mcp import ClientSession
    from mcp.client.streamable_http import streamable_http_client

    headers = {"Authorization": f"Bearer {auth_token}"} if auth_token else None
    custom_client = httpx.AsyncClient(headers=headers)

    def custom_client_factory():
        return httpx.AsyncClient(headers=headers)

    try:
        # Newer SDK versions accept headers as a keyword argument.
        client_cm = streamable_http_client(service_endpoint, http_client=custom_client)
    except TypeError:
        try:
            client_cm = streamable_http_client(service_endpoint, httpx_client_factory=custom_client_factory)
        except TypeError:
            try:
                client_cm = streamable_http_client(service_endpoint, headers=headers)
            except TypeError:
                # Older SDK versions may not support headers on this helper.
                if auth_token:
                    raise RuntimeError("installed MCP SDK does not support auth headers for streamable HTTP")
                client_cm = streamable_http_client(service_endpoint)

    async with custom_client:
        async with client_cm as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                response = await session.list_tools()
                tools = getattr(response, "tools", response)
                names = []
                for tool in tools:
                    name = getattr(tool, "name", None)
                    if name:
                        names.append(str(name))
                return names


def get_mcp_capabilities(service_endpoint: str, auth_token: str | None = None) -> MCPCapabilityResult:
    """Connect to an MCP server and derive AIDISCA Capabilities via tools/list.

    This uses the official MCP Python SDK. If fails to get tools for some reasoon, 
    caller can ask the operator to provide --capabilities manually.
    """
    try:
        tool_names = asyncio.run(_list_tools_streamable_http(service_endpoint, auth_token))
    except ImportError as exc:
        raise RuntimeError(
            "MCP SDK is not installed. Install requirements.txt or provide --capabilities."
        ) from exc
    except Exception:
        import traceback
        traceback.print_exc()
        raise

    if not tool_names:
        raise RuntimeError("MCP tools/list returned no tools; provide --capabilities manually")

    return MCPCapabilityResult(
        capabilities=tool_names,
        source="Successfully extracted from MCP tools/list via official MCP Python SDK",
    )
