"""Integration tests: merge then diff to verify round-trip behaviour."""

from envdiff.differ import diff_envs, has_differences
from envdiff.merger import MergeStrategy, merge_envs


BASE = {
    "DB_HOST": "db.staging.example.com",
    "DB_PORT": "5432",
    "APP_ENV": "staging",
    "LOG_LEVEL": "debug",
}

OVERRIDE = {
    "DB_HOST": "db.prod.example.com",
    "DB_PORT": "5432",  # same value — no conflict
    "APP_ENV": "production",
    "NEW_RELIC_KEY": "abc123",
}


class TestMergeThenDiff:
    def test_right_merge_produces_no_diff_with_override(self):
        """After merging with RIGHT strategy, diffing merged vs override
        should show no mismatches (only keys unique to each side)."""
        merged = merge_envs(BASE, OVERRIDE, strategy=MergeStrategy.RIGHT)
        result = diff_envs(merged, OVERRIDE)
        assert not result.value_mismatches

    def test_left_merge_preserves_base_values(self):
        merged = merge_envs(BASE, OVERRIDE, strategy=MergeStrategy.LEFT)
        result = diff_envs(merged, BASE)
        # LOG_LEVEL only in base; NEW_RELIC_KEY added from override
        assert "LOG_LEVEL" not in result.only_in_right
        assert not result.value_mismatches

    def test_merged_env_contains_all_keys(self):
        merged = merge_envs(BASE, OVERRIDE)
        assert "NEW_RELIC_KEY" in merged
        assert "LOG_LEVEL" in merged

    def test_right_merge_then_diff_shows_only_log_level_left_only(self):
        merged = merge_envs(BASE, OVERRIDE, strategy=MergeStrategy.RIGHT)
        result = diff_envs(merged, OVERRIDE)
        assert "LOG_LEVEL" in result.only_in_left
        assert not has_differences(
            diff_envs(
                {k: v for k, v in merged.items() if k != "LOG_LEVEL"},
                OVERRIDE,
            )
        )

    def test_prefix_merge_isolates_changes(self):
        """Only APP_ keys from override are merged; DB_ keys stay from base."""
        merged = merge_envs(BASE, OVERRIDE, prefix="APP_")
        assert merged["DB_HOST"] == BASE["DB_HOST"]
        assert merged["APP_ENV"] == "production"
