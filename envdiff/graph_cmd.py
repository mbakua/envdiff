"""CLI command: envdiff graph — visualise environment relationships."""
from __future__ import annotations

import argparse
import json
import sys
from typing import Dict, List, Tuple

from envdiff.differ import diff_envs
from envdiff.differ_graph import DiffGraph, build_graph
from envdiff.parser import parse_env_file


def build_graph_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="envdiff graph",
        description="Build a relationship graph from labelled env-file pairs.",
    )
    p.add_argument(
        "pairs",
        nargs="+",
        metavar="LABEL:FILE",
        help="Two or more label:file entries. Every unique pair is diffed.",
    )
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text).",
    )
    p.add_argument(
        "--show-stable",
        action="store_true",
        help="Include edges with no differences in the output.",
    )
    return p


def _parse_label_files(pairs: List[str]) -> Dict[str, str]:
    result: Dict[str, str] = {}
    for item in pairs:
        if ":" not in item:
            raise SystemExit(f"Invalid pair {item!r}: expected LABEL:FILE")
        label, _, path = item.partition(":")
        result[label.strip()] = path.strip()
    return result


def run_graph(args: argparse.Namespace) -> None:
    label_files = _parse_label_files(args.pairs)
    if len(label_files) < 2:
        raise SystemExit("At least two label:file pairs are required.")

    envs = {label: parse_env_file(path) for label, path in label_files.items()}
    labels = list(envs.keys())

    labeled_diffs: Dict[Tuple[str, str], object] = {}
    for i in range(len(labels)):
        for j in range(i + 1, len(labels)):
            src, tgt = labels[i], labels[j]
            labeled_diffs[(src, tgt)] = diff_envs(envs[src], envs[tgt])

    graph: DiffGraph = build_graph(labeled_diffs)  # type: ignore[arg-type]

    if args.format == "json":
        payload = {
            "nodes": [
                {"label": n.label, "issue_count": n.issue_count}
                for n in graph.nodes.values()
            ],
            "edges": [
                {
                    "source": e.source,
                    "target": e.target,
                    "mismatch_count": e.mismatch_count,
                    "has_differences": e.has_differences,
                }
                for e in graph.edges
                if args.show_stable or e.has_differences
            ],
        }
        print(json.dumps(payload, indent=2))
    else:
        print(f"Environments: {', '.join(graph.nodes)}")
        print()
        for src, tgt, count in graph.most_divergent():
            print(f"  {src} <-> {tgt}: {count} mismatch(es)")
        if args.show_stable:
            for edge in graph.edges:
                if not edge.has_differences:
                    print(f"  {edge.source} <-> {edge.target}: identical")


def main(argv: List[str] | None = None) -> None:
    parser = build_graph_parser()
    args = parser.parse_args(argv)
    run_graph(args)


if __name__ == "__main__":
    main()
