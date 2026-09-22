# Local MCP server

`eval-audit-mcp` exposes the local audit service to an assistant over stdio. It audits saved multiple-choice bundles already on disk. The process uses the same `AuditService` as the CLI, described in [SERVICE.md](SERVICE.md).

The core package has no runtime dependencies. This server is the optional `mcp` extra:

```sh
python -m pip install 'eval-audit[mcp]'
eval-audit-mcp --workspace /absolute/workspace --output-root audit-output
```

`--workspace` is an existing directory. `--output-root` is a dedicated directory inside it; the server creates that directory when it is absent. Paths in tool arguments resolve inside the workspace. The tested dependency set for this extra is [mcp-reproducibility.json](mcp-reproducibility.json): `mcp>=2,<3`, tested at mcp 2.2.0 on Python 3.14.7.

## Why stdio and four tools

A local host starts the server as a subprocess and speaks the protocol on stdin and stdout. The entry point does not open a port. Diagnostics from startup go to stderr so they stay off the protocol stream.

The tools are the service methods:

| Tool | Effect |
|---|---|
| `inspect_bundle` | Validates structure and returns counts and source hashes. Writes no audit. |
| `run_audit` | Writes a new completed audit directory. A repeat of the same bytes is another artifact with the same source-hash group. |
| `get_finding` | Returns one finding. Response text is included only when `include_raw` is true. |
| `export_report` | Returns the workspace-relative path and `audit://` URI of an existing report. |

`inspect_bundle`, `get_finding`, and `export_report` are marked read-only. `run_audit` is marked as creating artifacts, additive, and non-idempotent, because a second call writes a second directory. These annotations are client hints.

Completed reports are resources:

- `audit://{audit_id}/report/markdown`
- `audit://{audit_id}/report/json`

The identifier is the 32-character id from `run_audit`. It is not a filesystem path. After a restart, the same workspace and output root can read a receipt that was written earlier. An identifier from another output root is rejected.

Summaries include at most one page of findings. The JSON report resource is how a client reads the rest. Routine tool results omit response text so a full trace is not sent unless a resource is read or `include_raw` is set.

The tools do not run a model, a collection script, or a shell command. A completed audit is a diagnostic artifact. It is not approval of a behavioral claim.

## What a connected assistant receives

Local processing means the audit runs on this machine. The assistant host still receives tool results and any resource body it reads. When that host is a cloud assistant, those excerpts leave the machine. Keep saved responses out of `include_raw` and report reads unless that disclosure is intended.

## Configuration

Copy the snippet below into the client you choose, with your own absolute workspace. This project does not edit a client configuration.

```json
{
  "mcpServers": {
    "eval-audit": {
      "command": "eval-audit-mcp",
      "args": ["--workspace", "/absolute/workspace", "--output-root", "audit-output"]
    }
  }
}
```

A synthetic walkthrough is in [the example](../examples/mcp/README.md). The public fixture is [examples/transfer-fixture/bundle.json](../examples/transfer-fixture/bundle.json).

## Inspector check

The automated tests use the SDK client over stdio. The MCP Inspector CLI is a separate check. It needs Node.js. It is not part of `eval-audit[mcp]` and it is not part of `make check`.

Write a session file with your own paths. The Inspector reads that file and does not need a change to `~/.mcp-inspector/mcp.json`.

```json
{
  "mcpServers": {
    "eval-audit": {
      "command": "eval-audit-mcp",
      "args": ["--workspace", "/absolute/workspace", "--output-root", "audit-output"]
    }
  }
}
```

```sh
npx @modelcontextprotocol/inspector --cli \
  --protocol-era auto \
  --config inspector-session.json \
  --server eval-audit \
  --method tools/list
```

An empty catalog at `~/.mcp-inspector/mcp.json` makes a bare command target report that no server is configured. The `--config` session file avoids that. `--protocol-era auto` lets the client speak to this SDK line. The browser UI is the same package with `--web`; this repository's recorded check used `--cli`.
