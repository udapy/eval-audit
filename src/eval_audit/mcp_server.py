"""Optional local MCP adapter. Stdio only; no listener, model, or shell.

Importing this module does not import the MCP SDK. The console script loads
that extra when the process starts.
"""
from __future__ import annotations

import argparse
import sys
from typing import Annotated, Any, Literal

from eval_audit.service import ServiceError

INSTRUCTIONS = (
    "Deterministic audit of saved multiple-choice results inside one configured workspace. "
    "inspect_bundle, get_finding, and export_report are read operations. "
    "run_audit creates a new audit directory under the configured output root and does not replace earlier audits. "
    "No tool runs a model, a collection script, or a shell command. "
    "Routine results omit response text. Read an audit:// report resource, or set include_raw, to request excerpts. "
    "A completed audit is not approval of a behavioral claim. "
    "Text returned to the assistant host can leave the machine when that host is a cloud assistant."
)

def _call(fn, *args, **kwargs):
    from mcp.server.mcpserver.exceptions import ToolError
    try:
        return fn(*args, **kwargs)
    except ServiceError as exc:
        raise ToolError(f"{exc.code}: {exc}") from exc


def build_server(workspace: str, output_root: str):
    """Return a configured server. Does not listen or start a transport."""
    global Field
    # Tool schemas are evaluated against this module's globals, not this frame.
    from pydantic import Field
    from mcp.server import MCPServer
    from mcp.server.mcpserver.exceptions import ResourceError, ResourceNotFoundError
    from mcp.types import ToolAnnotations

    from eval_audit import __version__
    from eval_audit.service import AuditService

    read_only = ToolAnnotations(read_only_hint=True, open_world_hint=False)
    creates_audit = ToolAnnotations(
        read_only_hint=False, destructive_hint=False, idempotent_hint=False, open_world_hint=False)
    service = AuditService(workspace, output_root)
    server = MCPServer(
        "eval-audit",
        title="Eval Audit",
        version=__version__,
        instructions=INSTRUCTIONS,
        log_level="WARNING",
    )

    def report_text(audit_id: str, report_format: str) -> str:
        try:
            exported = service.export_report(audit_id, format=report_format)
        except ServiceError as exc:
            message = f"{exc.code}: {exc}"
            if exc.code == "NOT_FOUND":
                raise ResourceNotFoundError(message) from exc
            raise ResourceError(message) from exc
        path = (service.workspace / exported["path"]).resolve()
        if not path.is_relative_to(service.workspace) or not path.is_file():
            raise ResourceError("PROCESSING_FAILURE: Report reference is not a completed workspace file.")
        return path.read_text(encoding="utf-8")

    @server.tool(title="Inspect a saved bundle", annotations=read_only)
    def inspect_bundle(
        source: Annotated[str, Field(description="Workspace path to a JSON bundle or bundle directory.")],
        format: Annotated[Literal["generic", "inspect", "lm-eval"], Field(
            description="Saved-log layout. inspect and lm-eval require a paired JSON envelope.")] = "generic",
    ) -> dict[str, Any]:
        """Validate a saved bundle and summarize its structure.

        Reads the workspace only and does not publish an audit. Does not run a
        model, collection script, or shell command.
        """
        return _call(service.inspect_bundle, source, format=format)

    @server.tool(title="Audit a saved bundle", annotations=creates_audit)
    def run_audit(
        source: Annotated[str, Field(description="Workspace path to a JSON bundle or bundle directory.")],
        format: Annotated[Literal["generic", "inspect", "lm-eval"], Field(
            description="Saved-log layout. inspect and lm-eval require a paired JSON envelope.")] = "generic",
        annotations: Annotated[str | None, Field(
            description="Optional workspace-relative JSONL annotations. Omit to audit without them.")] = None,
    ) -> dict[str, Any]:
        """Create a new completed audit for a saved bundle.

        Repeating the same input writes another artifact with the same source-hash
        group. It is not another model run. The summary omits response text and
        includes at most one page of findings; read the JSON report resource for
        the rest. Does not run a model, collection script, or shell command.
        """
        return _call(service.run_audit, source, format=format, annotations=annotations)

    @server.tool(title="Get one finding", annotations=read_only)
    def get_finding(
        audit_id: Annotated[str, Field(description="Service-issued 32-character audit identifier. Not a filesystem path.")],
        finding_id: Annotated[str, Field(description="Finding identifier returned for that audit.")],
        include_raw: Annotated[bool, Field(
            description="When true, add bounded response excerpts. Otherwise return source references only.")] = False,
    ) -> dict[str, Any]:
        """Return one finding from a completed audit.

        Identifiers must come from this server's receipts under the configured
        output root. Does not run a model, collection script, or shell command.
        """
        return _call(service.get_finding, audit_id, finding_id, include_raw=include_raw)

    @server.tool(title="Export a report reference", annotations=read_only)
    def export_report(
        audit_id: Annotated[str, Field(description="Service-issued 32-character audit identifier. Not a filesystem path.")],
        format: Annotated[Literal["markdown", "json"], Field(
            description="Existing report to reference. This tool does not return the report body.")] = "markdown",
    ) -> dict[str, Any]:
        """Return the workspace-relative path and audit:// URI of a completed report.

        Does not copy the report, choose a destination, or return its text. Read
        the URI as a resource for the body. Does not run a model, collection
        script, or shell command.
        """
        return _call(service.export_report, audit_id, format=format)

    @server.resource("audit://{audit_id}/report/markdown", mime_type="text/markdown")
    def read_markdown_report(audit_id: str) -> str:
        """Completed markdown report for one service-issued audit.

        The body can contain saved response text. Read it only when that text is required.
        """
        return report_text(audit_id, "markdown")

    @server.resource("audit://{audit_id}/report/json", mime_type="application/json")
    def read_json_report(audit_id: str) -> str:
        """Completed JSON report for one service-issued audit.

        The body can contain saved response text. Read it only when that text is required.
        """
        return report_text(audit_id, "json")

    return server


def main(argv: list[str] | None = None) -> None:
    """Start the stdio server. Protocol bytes use stdout; diagnostics use stderr."""
    parser = argparse.ArgumentParser(
        prog="eval-audit-mcp",
        description="Local stdio MCP server for deterministic saved multiple-choice audits.",
    )
    parser.add_argument("--workspace", required=True, help="Existing directory that contains saved inputs.")
    parser.add_argument("--output-root", required=True, help="Dedicated directory inside the workspace for audit artifacts.")
    args = parser.parse_args(argv)
    try:
        server = build_server(args.workspace, args.output_root)
    except ImportError as exc:
        missing = exc.name or ""
        if missing == "mcp" or missing.startswith("mcp.") or missing in {"pydantic", "mcp_types"}:
            print("The MCP extra is not installed. Install it with: python -m pip install 'eval-audit[mcp]'", file=sys.stderr)
            raise SystemExit(1) from None
        raise
    except ServiceError as exc:
        print(f"{exc.code}: {exc}", file=sys.stderr)
        raise SystemExit(2) from None
    server.run(transport="stdio")


if __name__ == "__main__":
    main()
