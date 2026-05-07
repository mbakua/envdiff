"""CLI command for tagging environment diff results."""

import argparse
import json
import sys
from envdiff.cli import _load
from envdiff.differ import diff_envs
from envdiff.tagger import tag_diff


def build_tag_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envdiff-tag",
        description="Tag environment variable keys with semantic labels.",
    )
    parser.add_argument("left", help="Base env file or '-' for current environment")
    parser.add_argument("right", help="Target env file or '-' for current environment")
    parser.add_argument(
        "--tag",
        metavar="NAME=PATTERN",
        action="append",
        dest="extra_tags",
        default=[],
        help="Custom tag in NAME=PATTERN format (repeatable)",
    )
    parser.add_argument(
        "--filter-tag",
        metavar="TAG",
        dest="filter_tag",
        default=None,
        help="Only show keys matching this tag",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="as_json",
        help="Output results as JSON",
    )
    return parser


def _parse_extra_tags(raw: list) -> dict:
    result = {}
    for item in raw:
        if "=" not in item:
            print(f"Warning: ignoring malformed --tag value: {item!r}", file=sys.stderr)
            continue
        name, _, pattern = item.partition("=")
        result.setdefault(name.strip(), []).append(pattern.strip())
    return result


def run_tag(args: argparse.Namespace) -> int:
    left_env = _load(args.left)
    right_env = _load(args.right)
    diff = diff_envs(left_env, right_env)
    extra_tags = _parse_extra_tags(args.extra_tags)
    tagged = tag_diff(diff, extra_tags or None)

    if args.filter_tag:
        keys = tagged.keys_for_tag(args.filter_tag)
        if not keys:
            print(f"No keys matched tag: {args.filter_tag!r}")
            return 0
        if args.as_json:
            print(json.dumps({args.filter_tag: sorted(keys)}, indent=2))
        else:
            print(f"[{args.filter_tag}]")
            for k in sorted(keys):
                print(f"  {k}")
        return 0

    if args.as_json:
        output = {tag: sorted(keys) for tag, keys in sorted(tagged.tags.items())}
        print(json.dumps(output, indent=2))
    else:
        for tag in tagged.all_tags():
            keys = tagged.keys_for_tag(tag)
            print(f"[{tag}] ({len(keys)} keys)")
            for k in sorted(keys):
                print(f"  {k}")
    return 0


def main():
    parser = build_tag_parser()
    args = parser.parse_args()
    sys.exit(run_tag(args))


if __name__ == "__main__":
    main()
