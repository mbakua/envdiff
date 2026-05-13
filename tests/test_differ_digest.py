"""Tests for envdiff.differ_digest."""

from __future__ import annotations

import pytest

from envdiff.differ import DiffResult, diff_envs
from envdiff.differ_digest import DiffDigest, _collect_issue_keys, _fingerprint, digest_diff


@pytest.fixture()
def clean_diff() -> DiffResult:
    return diff_envs({"A": "1", "B": "2"}, {"A": "1", "B": "2"})


@pytest.fixture()
def mixed_diff() -> DiffResult:
    return diff_envs(
        {"A": "1", "SECRET": "old", "ONLY_LEFT": "x"},
        {"A": "1", "SECRET": "new", "ONLY_RIGHT": "y"},
    )


class TestDigestDiff:
    def test_returns_diff_digest_type(self, clean_diff: DiffResult) -> None:
        assert isinstance(digest_diff(clean_diff), DiffDigest)

    def test_clean_diff_is_clean(self, clean_diff: DiffResult) -> None:
        assert digest_diff(clean_diff).is_clean is True

    def test_clean_diff_no_issue_keys(self, clean_diff: DiffResult) -> None:
        assert digest_diff(clean_diff).issue_keys == []

    def test_mixed_diff_is_not_clean(self, mixed_diff: DiffResult) -> None:
        assert digest_diff(mixed_diff).is_clean is False

    def test_mixed_diff_issue_keys_sorted(self, mixed_diff: DiffResult) -> None:
        d = digest_diff(mixed_diff)
        assert "ONLY_LEFT" in d.issue_keys
        assert "ONLY_RIGHT" in d.issue_keys
        assert "SECRET" in d.issue_keys
        assert d.issue_keys == sorted(d.issue_keys)

    def test_total_keys_counts_all(self, mixed_diff: DiffResult) -> None:
        d = digest_diff(mixed_diff)
        # A(match), SECRET(mismatch), ONLY_LEFT, ONLY_RIGHT => 4
        assert d.total_keys == 4

    def test_fingerprint_is_hex_string(self, clean_diff: DiffResult) -> None:
        fp = digest_diff(clean_diff).fingerprint
        assert isinstance(fp, str)
        assert len(fp) == 64
        int(fp, 16)  # must be valid hex

    def test_same_diff_same_fingerprint(self) -> None:
        env = {"X": "1", "Y": "2"}
        d1 = digest_diff(diff_envs(env, env))
        d2 = digest_diff(diff_envs(env, env))
        assert d1.fingerprint == d2.fingerprint

    def test_different_diffs_different_fingerprints(self) -> None:
        d1 = digest_diff(diff_envs({"A": "1"}, {"A": "1"}))
        d2 = digest_diff(diff_envs({"A": "1"}, {"A": "2"}))
        assert d1.fingerprint != d2.fingerprint

    def test_empty_diff_is_clean(self) -> None:
        d = digest_diff(diff_envs({}, {}))
        assert d.is_clean is True
        assert d.total_keys == 0


class TestCollectIssueKeys:
    def test_empty_when_no_issues(self, clean_diff: DiffResult) -> None:
        assert _collect_issue_keys(clean_diff) == []

    def test_includes_only_in_left(self) -> None:
        dr = diff_envs({"GONE": "x"}, {})
        assert "GONE" in _collect_issue_keys(dr)

    def test_includes_only_in_right(self) -> None:
        dr = diff_envs({}, {"NEW": "x"})
        assert "NEW" in _collect_issue_keys(dr)

    def test_includes_mismatch_keys(self) -> None:
        dr = diff_envs({"K": "a"}, {"K": "b"})
        assert "K" in _collect_issue_keys(dr)


class TestFingerprint:
    def test_returns_64_char_hex(self, clean_diff: DiffResult) -> None:
        fp = _fingerprint(clean_diff)
        assert len(fp) == 64

    def test_order_independent_for_matching_keys(self) -> None:
        d1 = diff_envs({"A": "1", "B": "2"}, {"A": "1", "B": "2"})
        d2 = diff_envs({"B": "2", "A": "1"}, {"B": "2", "A": "1"})
        assert _fingerprint(d1) == _fingerprint(d2)
