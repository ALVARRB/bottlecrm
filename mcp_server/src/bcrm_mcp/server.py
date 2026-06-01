"""FastMCP server entry point (stdio) for BottleCRM.

Wraps the plain async tool functions in ``bcrm_mcp.tools`` as FastMCP tools and
exposes a ``build_server(client=None)`` factory plus a ``main()`` console entry
point (the ``bcrm-mcp`` script points at ``bcrm_mcp.server:main``).

The real :class:`CrmClient` is built lazily on first tool call so that
constructing the server (e.g. in tests, or to introspect tools) never requires
``BCRM_BASE_URL`` / ``BCRM_TOKEN``. Pass ``client=`` to inject one.
"""

from fastmcp import FastMCP

from bcrm_mcp import tools
from bcrm_mcp.client import CrmClient
from bcrm_mcp.config import Settings

# Tool annotation hints (mcp.types.ToolAnnotations fields). Passed as plain
# dicts to ``@mcp.tool(annotations=...)`` — FastMCP 3.x accepts a dict and
# coerces it to a ToolAnnotations model.
_READ_ONLY = {"readOnlyHint": True, "destructiveHint": False, "openWorldHint": True}
_WRITE = {"readOnlyHint": False, "destructiveHint": False, "openWorldHint": True}
_DESTRUCTIVE = {"readOnlyHint": False, "destructiveHint": True, "openWorldHint": True}


def build_server(client=None):
    """Build and return a FastMCP server with all CRM tools registered.

    ``client`` may be injected (tests pass a stub); when ``None`` a real
    :class:`CrmClient` is constructed lazily from env on the first tool call.
    """
    mcp = FastMCP("BottleCRM")
    _client = client

    def get_client():
        nonlocal _client
        if _client is None:
            s = Settings.from_env()
            _client = CrmClient(s.base_url, s.token)
        return _client

    @mcp.tool(annotations=_READ_ONLY)
    async def crm_search(
        entity: str,
        query: str = "",
        filters: dict | None = None,
        limit: int = 20,
        offset: int = 0,
    ):
        """Search/list CRM records of an entity (leads, contacts, accounts, opportunities, tasks, cases, invoices, solutions). Returns compact rows; limit is capped at 50."""
        return await tools.crm_search(
            get_client(), entity, query or None, filters, limit, offset
        )

    @mcp.tool(annotations=_READ_ONLY)
    async def crm_get(entity: str, id: str):
        """Fetch one CRM record's full detail by id."""
        return await tools.crm_get(get_client(), entity, id)

    @mcp.tool(annotations=_WRITE)
    async def crm_create(entity: str, data: dict):
        """Create a CRM record. `data` is validated server-side by the API."""
        return await tools.crm_create(get_client(), entity, data)

    @mcp.tool(annotations=_WRITE)
    async def crm_update(entity: str, id: str, data: dict):
        """Partially update a CRM record (PATCH semantics)."""
        return await tools.crm_update(get_client(), entity, id, data)

    @mcp.tool(annotations=_DESTRUCTIVE)
    async def crm_delete(entity: str, id: str, confirm: bool = False):
        """Delete a CRM record. DESTRUCTIVE and irreversible — you must pass confirm=true to proceed."""
        return await tools.crm_delete(get_client(), entity, id, confirm)

    @mcp.tool(annotations=_WRITE)
    async def crm_action(
        entity: str,
        id: str,
        action: str,
        params: dict | None = None,
        confirm: bool = False,
    ):
        """Run a non-CRUD action (e.g. convert a lead, add_comment, send an invoice). Call list_actions to see allowed actions per entity. Outward-facing actions like `send` (emails a customer) require confirm=true."""
        return await tools.crm_action(
            get_client(), entity, id, action, params, confirm
        )

    @mcp.tool(annotations=_READ_ONLY)
    async def crm_describe(entity: str):
        """Describe an entity's writable/readable fields and enums (from the live API schema)."""
        return await tools.crm_describe(get_client(), entity)

    @mcp.tool(annotations=_READ_ONLY)
    def list_actions():
        """Return the allowed non-CRUD actions for each entity."""
        return tools.list_actions()

    return mcp


def main():
    """Console entry point — runs the server over stdio (default transport)."""
    build_server().run()


if __name__ == "__main__":
    main()
