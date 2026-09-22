# Synthetic MCP conversation

This walkthrough uses the public CC0 bundle at `examples/transfer-fixture/bundle.json`. Copy that file into an empty workspace before starting the server. The bundle has 32 saved rows and assigned answers. The numbers in a real tool result come from that file; this page does not restate scores.

Install and start:

```sh
python -m pip install 'eval-audit[mcp]'
mkdir -p /absolute/workspace
cp examples/transfer-fixture/bundle.json /absolute/workspace/bundle.json
eval-audit-mcp --workspace /absolute/workspace --output-root audit-output
```

Client configuration, with paths you choose:

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

The server speaks stdio. Leave its stdout for the protocol.

## Conversation

Researcher: Inspect `bundle.json` and tell me whether it is a complete audit.

Assistant calls `inspect_bundle` with `source` `bundle.json` and `format` `generic`.

The tool returns `status` `inspected`, `record_count` 32, comparison and source-hash fields, and a limitation that inspection did not publish an audit. There is no `audit_id`. The output root has no completed-audit receipt.

Researcher: Audit the same bundle.

Assistant calls `run_audit` with `source` `bundle.json`.

The tool returns `status` `complete`, a new `audit_id`, `model_runs_executed` 0, `same_source_group`, gate and metric summaries, and `reports` URIs `audit://<audit_id>/report/markdown` and `audit://<audit_id>/report/json`. The summary lists at most one page of findings and does not include response text. Calling `run_audit` again writes a second directory with the same `same_source_group`.

Researcher: Show the first finding without the saved answer, then the markdown report.

Assistant calls `get_finding` with that `audit_id`, the `finding_id` from the summary, and `include_raw` false. The result has source references and no response excerpt.

Assistant reads the resource `audit://<audit_id>/report/markdown`. That read returns the report body, which can include saved response text.

Researcher: Stop the server and start it again with the same workspace and output root. Export the report for the same `audit_id`.

Assistant calls `export_report` with `format` `markdown`. The tool returns the existing workspace-relative path, the same URI, and the receipt hash. It does not write a new file.

## Disclosure

If the assistant host is a cloud service, the summary, any `include_raw` excerpts, and any report resource it reads are sent to that service. Local execution does not keep those excerpts on the machine.

The tools do not run a model, a collection script, or a shell command. A completed audit is not approval of a behavioral claim. Details are in [MCP.md](../../docs/MCP.md) and [SERVICE.md](../../docs/SERVICE.md).
