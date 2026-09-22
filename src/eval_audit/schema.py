"""Frozen schema version 1 for eval-audit.

Dataclasses and validators only. No I/O, no provider imports, no Historical conclusions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction
from typing import Any, Literal

SCHEMA_VERSION = 1
ADAPTER_VERSION = "1"
HISTORICAL_PROFILE = "historical-v1"
GENERIC_PROFILE = "generic-v1"
ANSWER_BASES = ("stored", "strict")
PARSE_STATUSES = ("ok", "missing", "ambiguous", "invalid", "unavailable")
COMPLETENESS = ("complete", "possibly_truncated", "unknown")
SEVERITIES = ("info", "warning", "error")
FINDING_ORIGINS = ("computed", "human_annotation")
COMPARISON_STATUSES = ("complete", "invalid", "insufficient_data")
ANNOTATION_STATUSES = ("proposed", "reviewed")
ANNOTATION_ORIGINS = ("human", "agent")
GOLD_UNIQUENESS_VERDICTS = (
    "unique-correct",
    "contested",
    "invalid-key",
    "insufficient-evidence",
)
HISTORICAL_ALLOWED = ("A", "B", "C", "D")


class AuditError(Exception):
    """Unexpected runtime failure."""


class AuditInputError(AuditError):
    """Invalid input or configuration. CLI maps this to exit 2."""

    def __init__(
        self,
        message: str,
        *,
        artifact: str | None = None,
        row: str | int | None = None,
        field: str | None = None,
    ) -> None:
        self.artifact = artifact
        self.row = row
        self.field = field
        parts = [message]
        if artifact is not None:
            parts.append(f"artifact={artifact}")
        if row is not None:
            parts.append(f"row={row}")
        if field is not None:
            parts.append(f"field={field}")
        super().__init__("; ".join(parts))


class PairingError(AuditInputError):
    """Requested comparison cannot be paired. Status invalid, exit 2."""


@dataclass(frozen=True)
class SourceRef:
    artifact_id: str
    sha256: str
    json_pointer: str

    def validate(self) -> None:
        _nonempty(self.artifact_id, "source.artifact_id")
        _sha256(self.sha256, "source.sha256")
        _nonempty(self.json_pointer, "source.json_pointer")


@dataclass(frozen=True)
class ParseResult:
    answer: str | None
    status: str

    def validate(self, allowed: tuple[str, ...]) -> None:
        if self.status not in PARSE_STATUSES:
            raise AuditInputError("unknown parse_status", field="parse_status")
        if self.status == "ok":
            if self.answer not in allowed:
                raise AuditInputError("parsed_answer not in allowed_answers", field="parsed_answer")
        elif self.answer is not None:
            raise AuditInputError("non-ok parse must have null answer", field="parsed_answer")


@dataclass(frozen=True)
class Record:
    schema_version: int
    dataset_id: str
    model_label: str
    run_id: str
    condition: str
    item_id: str
    repeat_id: str | None
    permutation_id: str | None
    bank: str | None
    allowed_answers: tuple[str, ...]
    gold: str
    stored_answer: str | None
    stored_correct: bool | None
    response_text: str | None
    response_completeness: str
    parsed_answer: str | None
    parse_status: str
    source: SourceRef
    source_fields: dict[str, Any] = field(default_factory=dict)
    option_order: tuple[str, ...] | None = None
    gold_content_id: str | None = None

    def identity(self) -> tuple[Any, ...]:
        return (
            self.dataset_id,
            self.model_label,
            self.run_id,
            self.condition,
            self.item_id,
            self.repeat_id,
            self.permutation_id,
        )

    def pair_key(self) -> tuple[Any, ...]:
        return (self.item_id, self.repeat_id, self.permutation_id)

    def validate(self) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise AuditInputError(
                f"unknown schema_version {self.schema_version}",
                field="schema_version",
            )
        for name in ("dataset_id", "model_label", "run_id", "condition", "item_id"):
            _nonempty(getattr(self, name), name)
        _allowed_list(self.allowed_answers)
        if (self.option_order is None) != (self.gold_content_id is None):
            raise AuditInputError("option_order and gold_content_id must be supplied together", field="option_order")
        if self.option_order is not None:
            if not isinstance(self.option_order, tuple) or len(self.option_order) != len(self.allowed_answers):
                raise AuditInputError("option_order must match allowed_answers length", field="option_order")
            for content_id in self.option_order:
                _nonempty(content_id, "option_order")
            if len(set(self.option_order)) != len(self.option_order):
                raise AuditInputError("option_order must contain unique content IDs", field="option_order")
            _nonempty(self.gold_content_id, "gold_content_id")
            if self.gold_content_id not in self.option_order:
                raise AuditInputError("gold_content_id must occur in option_order", field="gold_content_id")
        if self.gold not in self.allowed_answers:
            raise AuditInputError("gold is not a member of allowed_answers", field="gold")
        if self.stored_answer is not None and self.stored_answer not in self.allowed_answers:
            raise AuditInputError(
                "stored_answer is not a member of allowed_answers",
                field="stored_answer",
            )
        if self.response_completeness not in COMPLETENESS:
            raise AuditInputError("unknown response_completeness", field="response_completeness")
        ParseResult(self.parsed_answer, self.parse_status).validate(self.allowed_answers)
        self.source.validate()
        if not isinstance(self.source_fields, dict):
            raise AuditInputError("source_fields must be an object", field="source_fields")


@dataclass(frozen=True)
class Artifact:
    artifact_id: str
    original_relative_path: str
    copied_relative_path: str
    sha256: str
    row_count: int
    assigned_labels: dict[str, str]

    def validate(self) -> None:
        _nonempty(self.artifact_id, "artifact_id")
        _nonempty(self.original_relative_path, "original_relative_path")
        _nonempty(self.copied_relative_path, "copied_relative_path")
        _sha256(self.sha256, "sha256")
        if self.row_count < 0:
            raise AuditInputError("row_count must be >= 0", field="row_count")


@dataclass(frozen=True)
class Comparison:
    comparison_id: str
    dataset_id: str
    model_label: str
    run_id: str
    baseline_condition: str
    target_condition: str
    bank_mapping: dict[str, str] | None = None

    def validate(self) -> None:
        for name in (
            "comparison_id",
            "dataset_id",
            "model_label",
            "run_id",
            "baseline_condition",
            "target_condition",
        ):
            _nonempty(getattr(self, name), name)
        if self.baseline_condition == self.target_condition:
            raise AuditInputError(
                "baseline_condition and target_condition must differ",
                field="target_condition",
            )
        if self.bank_mapping is not None:
            if not self.bank_mapping:
                raise AuditInputError("bank_mapping must be nonempty if present", field="bank_mapping")
            for key, value in self.bank_mapping.items():
                _nonempty(key, "bank_mapping.key")
                _nonempty(value, "bank_mapping.value")


@dataclass(frozen=True)
class Profile:
    name: str
    accuracy_drop_threshold: Fraction
    entropy_drop_threshold: float
    allowed_answers: tuple[str, ...]

    def validate(self) -> None:
        _nonempty(self.name, "profile.name")
        _allowed_list(self.allowed_answers)
        if self.accuracy_drop_threshold < 0:
            raise AuditInputError("accuracy_drop_threshold must be >= 0", field="accuracy_drop_threshold")
        if self.entropy_drop_threshold < 0:
            raise AuditInputError("entropy_drop_threshold must be >= 0", field="entropy_drop_threshold")


HISTORICAL_V1_PROFILE = Profile(
    name=HISTORICAL_PROFILE,
    accuracy_drop_threshold=Fraction(1, 10),
    entropy_drop_threshold=0.15,
    allowed_answers=HISTORICAL_ALLOWED,
)

# Same historical inequalities as historical-v1, named so a second dataset need not wear a Historical label.
GENERIC_V1_PROFILE = Profile(
    name=GENERIC_PROFILE,
    accuracy_drop_threshold=Fraction(1, 10),
    entropy_drop_threshold=0.15,
    allowed_answers=HISTORICAL_ALLOWED,
)


@dataclass(frozen=True)
class Manifest:
    schema_version: int
    adapter_version: str
    profile: str
    artifacts: tuple[Artifact, ...]
    normalized_file: str
    normalized_sha256: str
    comparisons: tuple[Comparison, ...]
    provenance_notes: tuple[str, ...]
    item_context_file: str | None = None
    item_context_sha256: str | None = None
    annotations_file: str | None = None
    annotations_sha256: str | None = None

    def validate(self) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise AuditInputError(
                f"unknown schema_version {self.schema_version}",
                field="schema_version",
            )
        _nonempty(self.adapter_version, "adapter_version")
        _nonempty(self.profile, "profile")
        _nonempty(self.normalized_file, "normalized_file")
        _sha256(self.normalized_sha256, "normalized_sha256")
        if not self.artifacts:
            raise AuditInputError("manifest must list at least one artifact", field="artifacts")
        ids = [a.artifact_id for a in self.artifacts]
        if len(ids) != len(set(ids)):
            raise AuditInputError("duplicate artifact_id", field="artifacts")
        for artifact in self.artifacts:
            artifact.validate()
        if not self.comparisons:
            raise AuditInputError("manifest must list at least one comparison", field="comparisons")
        cids = [c.comparison_id for c in self.comparisons]
        if len(cids) != len(set(cids)):
            raise AuditInputError("duplicate comparison_id", field="comparisons")
        for comparison in self.comparisons:
            comparison.validate()
        if (self.item_context_file is None) != (self.item_context_sha256 is None):
            raise AuditInputError("item_context_file and hash must be paired", field="item_context_file")
        if (self.annotations_file is None) != (self.annotations_sha256 is None):
            raise AuditInputError("annotations_file and hash must be paired", field="annotations_file")
        if self.item_context_sha256 is not None:
            _sha256(self.item_context_sha256, "item_context_sha256")
        if self.annotations_sha256 is not None:
            _sha256(self.annotations_sha256, "annotations_sha256")


@dataclass(frozen=True)
class ItemContext:
    dataset_id: str
    item_id: str
    question_with_options: str
    definition_gold: str
    source_artifact_sha256: str
    source_locator: str
    provenance_status: str

    def validate(self) -> None:
        _nonempty(self.dataset_id, "dataset_id")
        _nonempty(self.item_id, "item_id")
        _nonempty(self.question_with_options, "question_with_options")
        _nonempty(self.definition_gold, "definition_gold")
        _sha256(self.source_artifact_sha256, "source_artifact_sha256")
        _nonempty(self.source_locator, "source_locator")
        _nonempty(self.provenance_status, "provenance_status")


@dataclass(frozen=True)
class Annotation:
    annotation_id: str
    dataset_id: str
    item_id: str | None
    text: str
    author: str
    status: str
    origin: str
    gold_uniqueness: str | None = None
    source_references: tuple[str, ...] = ()

    def validate(self) -> None:
        _nonempty(self.annotation_id, "annotation_id")
        _nonempty(self.dataset_id, "dataset_id")
        _nonempty(self.text, "text")
        _nonempty(self.author, "author")
        if self.status not in ANNOTATION_STATUSES:
            raise AuditInputError("unknown annotation status", field="status")
        if self.origin not in ANNOTATION_ORIGINS:
            raise AuditInputError("unknown annotation origin", field="origin")
        if self.item_id is not None:
            _nonempty(self.item_id, "item_id")
            if self.gold_uniqueness is None:
                raise AuditInputError(
                    "item-scoped annotation requires gold_uniqueness",
                    field="gold_uniqueness",
                )
        if self.gold_uniqueness is not None and self.gold_uniqueness not in GOLD_UNIQUENESS_VERDICTS:
            raise AuditInputError("unknown gold_uniqueness verdict", field="gold_uniqueness")
        for ref in self.source_references:
            _nonempty(ref, "source_references")


@dataclass(frozen=True)
class Finding:
    finding_id: str
    code: str
    severity: Literal["info", "warning", "error"]
    scope: dict[str, str]
    answer_basis: str | None
    observed: dict[str, Any]
    sources: tuple[SourceRef, ...]
    explanation: str
    limitation: str
    origin: Literal["computed", "human_annotation"]

    def validate(self) -> None:
        _nonempty(self.finding_id, "finding_id")
        _nonempty(self.code, "code")
        if self.severity not in SEVERITIES:
            raise AuditInputError("unknown severity", field="severity")
        if self.origin not in FINDING_ORIGINS:
            raise AuditInputError("unknown origin", field="origin")
        if self.answer_basis is not None and self.answer_basis not in ANSWER_BASES:
            raise AuditInputError("unknown answer_basis", field="answer_basis")


@dataclass(frozen=True)
class GroupMetrics:
    dataset_id: str
    model_label: str
    run_id: str
    condition: str
    bank: str | None
    answer_basis: str
    n_total: int
    n_valid: int
    n_invalid: int
    n_correct: int
    accuracy_all: Fraction | None
    accuracy_valid: Fraction | None
    prediction_counts: dict[str, int]
    gold_counts: dict[str, int]
    entropy_bits: float | None


@dataclass(frozen=True)
class PairedRow:
    baseline: Record
    target: Record


@dataclass(frozen=True)
class ComparisonMetrics:
    comparison_id: str
    answer_basis: str
    status: str
    n_pairs: int
    baseline: GroupMetrics | None
    target: GroupMetrics | None
    accuracy_drop: Fraction | None
    entropy_drop: float | None
    accuracy_flag: bool | None
    entropy_flag: bool | None
    selectivity: Fraction | None
    bank_metrics: dict[str, dict[str, GroupMetrics | None]]


@dataclass(frozen=True)
class ItemInfluence:
    comparison_id: str
    item_id: str
    answer_basis: str
    original_accuracy_drop: Fraction | None
    without_accuracy_drop: Fraction | None
    accuracy_drop_difference: Fraction | None
    original_entropy_drop: float | None
    without_entropy_drop: float | None
    entropy_drop_difference: float | None
    original_selectivity: Fraction | None
    without_selectivity: Fraction | None
    selectivity_difference: Fraction | None


@dataclass(frozen=True)
class ControlResult:
    control_id: str
    comparison_id: str
    answer_basis: str
    label: str
    metrics: ComparisonMetrics


@dataclass(frozen=True)
class AuditReport:
    schema_version: int
    audit_status: str
    manifest: Manifest
    records: tuple[Record, ...]
    item_context: tuple[ItemContext, ...]
    annotations: tuple[Annotation, ...]
    group_metrics: tuple[GroupMetrics, ...]
    comparison_metrics: tuple[ComparisonMetrics, ...]
    controls: tuple[ControlResult, ...]
    item_influence: tuple[ItemInfluence, ...]
    findings: tuple[Finding, ...]
    inventory: dict[str, Any]


def profile_by_name(name: str) -> Profile:
    if name == HISTORICAL_PROFILE:
        HISTORICAL_V1_PROFILE.validate()
        return HISTORICAL_V1_PROFILE
    if name == GENERIC_PROFILE:
        GENERIC_V1_PROFILE.validate()
        return GENERIC_V1_PROFILE
    raise AuditInputError(f"unknown profile {name}", field="profile")


def validate_records(records: list[Record] | tuple[Record, ...]) -> None:
    seen: set[tuple[Any, ...]] = set()
    alphabets: dict[tuple[str, str, str], tuple[str, ...]] = {}
    for record in records:
        record.validate()
        ident = record.identity()
        if ident in seen:
            raise AuditInputError(
                "duplicate record identity",
                artifact=record.source.artifact_id,
                row=record.source.json_pointer,
                field="identity",
            )
        seen.add(ident)
        key = (record.dataset_id, record.model_label, record.run_id)
        previous = alphabets.get(key)
        if previous is None:
            alphabets[key] = record.allowed_answers
        elif previous != record.allowed_answers:
            raise AuditInputError(
                "incompatible alphabets in the same dataset/model/run",
                artifact=record.source.artifact_id,
                row=record.source.json_pointer,
                field="allowed_answers",
            )


def _nonempty(value: str, field: str) -> None:
    if not isinstance(value, str) or value.strip() == "":
        raise AuditInputError("expected a nonempty string", field=field)


def _sha256(value: str, field: str) -> None:
    if not isinstance(value, str) or len(value) != 64:
        raise AuditInputError("sha256 must be 64 hex characters", field=field)
    try:
        int(value, 16)
    except ValueError as exc:
        raise AuditInputError("sha256 must be 64 hex characters", field=field) from exc


def _allowed_list(allowed: tuple[str, ...]) -> None:
    if not allowed:
        raise AuditInputError("allowed_answers must be nonempty", field="allowed_answers")
    seen: set[str] = set()
    for label in allowed:
        _nonempty(label, "allowed_answers")
        if label in seen:
            raise AuditInputError("allowed_answers must be unique", field="allowed_answers")
        seen.add(label)
