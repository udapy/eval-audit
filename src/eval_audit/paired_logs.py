"""Strict paired JSON log envelopes, separate from legacy single-log adapters.

The envelope has baseline and target logs. Only explicitly tested MCQ text
layouts are accepted. Logprobs, binary .eval archives and multi-task dumps
require a separate conversion. Answers are parsed without consulting gold.
"""
from __future__ import annotations

from eval_audit.parsing import parse_answer
from eval_audit.schema import AuditInputError


def _object(value, name):
    if not isinstance(value, dict):
        raise AuditInputError(f"{name} must be an object")
    return value


def _text(value, name):
    if not isinstance(value, str) or not value.strip():
        raise AuditInputError(f"{name} must be nonempty text")
    return value


def paired_bundle(payload: dict, format: str, max_records: int) -> dict:
    from eval_audit.service import ServiceError

    if not all(isinstance(payload.get(key), dict) for key in ("baseline", "target")):
        raise ServiceError("UNSUPPORTED_LAYOUT", "Provide a paired envelope with baseline and target JSON logs. A single log cannot establish a paired comparison.")
    rows, items, identity = [], {}, None
    for condition in ("baseline", "target"):
        log = payload[condition]
        if format == "inspect":
            meta = _object(log.get("eval"), "eval")
            model, task = _text(meta.get("model"), "eval.model"), _text(meta.get("task"), "eval.task")
            samples = log.get("samples")
        else:
            meta = _object(log.get("config"), "config")
            model = _text(meta.get("model_name"), "config.model_name")
            tasks = _object(log.get("samples"), "samples")
            if len(tasks) != 1:
                raise ServiceError("UNSUPPORTED_LAYOUT", "Each paired log must contain exactly one task.")
            task, samples = next(iter(tasks.items()))
            _text(task, "task")
        if identity is not None and identity != (model, task):
            raise AuditInputError("Paired model and task identities must match")
        identity = model, task
        if not isinstance(samples, list) or not samples:
            raise AuditInputError("samples must be a nonempty array")
        if len(rows) + len(samples) > max_records:
            raise ServiceError("SIZE_LIMIT", "Record limit exceeded before log conversion.")
        for sample in samples:
            _object(sample, "sample")
            item = sample.get("id" if format == "inspect" else "doc_id")
            if not isinstance(item, (str, int)) or isinstance(item, bool):
                raise AuditInputError("Every sample requires an explicit item ID")
            item = str(item)
            allowed = ["A", "B", "C", "D"]
            if format == "inspect":
                choices = sample.get("choices")
                if choices is not None:
                    if not isinstance(choices, list) or not 2 <= len(choices) <= 10 or not all(isinstance(v, str) for v in choices):
                        raise AuditInputError("choices must contain 2 to 10 text choices")
                    allowed = list("ABCDEFGHIJ"[:len(choices)])
                output = _object(sample.get("output"), "output")
                response = output.get("completion")
                if response is None:
                    options = output.get("choices")
                    if not isinstance(options, list) or len(options) != 1:
                        raise AuditInputError("Expected one output choice or completion text")
                    response = _object(_object(options[0], "choice").get("message"), "message").get("content")
                prompt = sample.get("input", "")
                if not isinstance(prompt, str):
                    raise AuditInputError("This adapter supports text input only")
            else:
                responses = sample.get("resps")
                if not isinstance(responses, list) or len(responses) != 1:
                    raise AuditInputError("Expected one generation in resps")
                response = responses[0]
                if isinstance(response, list) and len(response) == 1:
                    response = response[0]
                prompt = sample.get("prompt", "")
                if not isinstance(prompt, str):
                    raise AuditInputError("prompt must be text")
            if not isinstance(response, str):
                raise ServiceError("UNSUPPORTED_LAYOUT", "Only text generations are supported; likelihood outputs are not answers.")
            gold = sample.get("target")
            if format == "lm-eval" and type(gold) is int and 0 <= gold < len(allowed):
                gold = allowed[gold]
            if gold not in allowed:
                raise AuditInputError("target must be a single allowed answer label")
            # Derived answer is explicitly labeled; never gold-conditioned.
            parsed = parse_answer(response, tuple(allowed))
            row = {"dataset_id": task, "model_label": model, "run_id": "paired-log-import",
                   "condition": condition, "item_id": item, "gold": gold,
                   "stored_answer": parsed.answer, "response_text": response,
                   "response_completeness": sample.get("response_completeness", "unknown"),
                   "allowed_answers": allowed}
            rows.append(row)
            definition = {"dataset_id": task, "item_id": item, "definition_gold": gold,
                          "question_with_options": prompt or f"Item {item}; question text unavailable",
                          "source_locator": f"paired-{format}:{task}:{item}",
                          "provenance_status": "paired_log_derivative"}
            if item in items and items[item] != definition:
                raise AuditInputError("Paired item definitions disagree")
            items[item] = definition
    model, task = identity
    return {"profile": "generic-v1", "rows": rows, "items": list(items.values()),
            "provenance_notes": [
                f"Explicit paired {format} logs; original envelope preserved by AuditService.",
                "Stored answers in this derivative are strict parser results, not provider-stored answers.",
                "Completeness remains unknown unless explicitly supplied. No model run was performed."],
            "comparisons": [{"comparison_id": "paired-log-comparison", "dataset_id": task,
                             "model_label": model, "run_id": "paired-log-import",
                             "baseline_condition": "baseline", "target_condition": "target"}]}
