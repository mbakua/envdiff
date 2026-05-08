"""Tests for envdiff.annotator."""

import pytest

from envdiff.differ import DiffResult
from envdiff.annotator import (
    Annotation,
    AnnotatedDiff,
    annotate_diff,
    _infer_note,
    _severity_for,
)


@pytest.fixture
def clean_diff():
    return DiffResult(only_in_left=[], only_in_right=[], value_mismatches={}, matching_keys={"APP": "prod"})


@pytest.fixture
def mixed_diff():
    return DiffResult(
        only_in_left=["DB_PASSWORD", "API_HOST"],
        only_in_right=["NEW_FLAG"],
        value_mismatches={"APP_TOKEN": ("abc", "xyz"), "LOG_LEVEL": ("debug", "info")},
        matching_keys={"APP": "prod"},
    )


class TestAnnotation:
    def test_str_includes_severity_and_key(self):
        ann = Annotation("MY_KEY", "some note", "warning")
        result = str(ann)
        assert "WARNING" in result
        assert "MY_KEY" in result
        assert "some note" in result


class TestAnnotatedDiff:
    def test_for_key_returns_matching_annotations(self, mixed_diff):
        result = annotate_diff(mixed_diff)
        anns = result.for_key("DB_PASSWORD")
        assert all(a.key == "DB_PASSWORD" for a in anns)

    def test_by_severity_filters_correctly(self, mixed_diff):
        result = annotate_diff(mixed_diff)
        errors = result.by_severity("error")
        assert all(a.severity == "error" for a in errors)

    def test_has_errors_true_when_error_present(self, mixed_diff):
        result = annotate_diff(mixed_diff)
        assert result.has_errors() is True

    def test_has_errors_false_for_clean_diff(self, clean_diff):
        result = annotate_diff(clean_diff)
        assert result.has_errors() is False


class TestInferNote:
    def test_sensitive_missing_right_returns_security_note(self):
        note = _infer_note("DB_PASSWORD", "missing_right")
        assert note is not None
        assert "sensitive" in note.lower() or "security" in note.lower()

    def test_network_key_missing_right_returns_connectivity_note(self):
        note = _infer_note("API_HOST", "missing_right")
        assert note is not None
        assert "network" in note.lower() or "connectivity" in note.lower()

    def test_plain_key_missing_right_returns_generic_note(self):
        note = _infer_note("LOG_LEVEL", "missing_right")
        assert note is not None

    def test_missing_left_returns_note(self):
        note = _infer_note("NEW_FLAG", "missing_left")
        assert note is not None

    def test_mismatch_on_secret_returns_note(self):
        note = _infer_note("APP_SECRET", "mismatch")
        assert note is not None


class TestSeverityFor:
    def test_sensitive_missing_right_is_error(self):
        assert _severity_for("DB_PASSWORD", "missing_right") == "error"

    def test_plain_missing_right_is_warning(self):
        assert _severity_for("LOG_LEVEL", "missing_right") == "warning"

    def test_missing_left_is_info(self):
        assert _severity_for("NEW_FLAG", "missing_left") == "info"

    def test_mismatch_on_token_is_error(self):
        assert _severity_for("AUTH_TOKEN", "mismatch") == "error"

    def test_plain_mismatch_is_warning(self):
        assert _severity_for("APP_ENV", "mismatch") == "warning"


class TestAnnotateDiff:
    def test_returns_annotated_diff_type(self, mixed_diff):
        result = annotate_diff(mixed_diff)
        assert isinstance(result, AnnotatedDiff)

    def test_clean_diff_produces_no_annotations(self, clean_diff):
        result = annotate_diff(clean_diff)
        assert result.annotations == []

    def test_extra_annotations_are_included(self, clean_diff):
        result = annotate_diff(clean_diff, extra={"APP": "manually flagged"})
        assert any(a.key == "APP" for a in result.annotations)

    def test_all_missing_left_keys_annotated(self, mixed_diff):
        result = annotate_diff(mixed_diff)
        annotated_keys = {a.key for a in result.annotations}
        assert "NEW_FLAG" in annotated_keys

    def test_all_value_mismatch_keys_annotated(self, mixed_diff):
        result = annotate_diff(mixed_diff)
        annotated_keys = {a.key for a in result.annotations}
        assert "APP_TOKEN" in annotated_keys
        assert "LOG_LEVEL" in annotated_keys
