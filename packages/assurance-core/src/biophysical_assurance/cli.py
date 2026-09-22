"""Command-line entry point for synthetic assurance replay."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .core import load_scenario, replay, verify_receipts
from .evidence import make_auth_tag, verify_auth_tag
from .parsing import read_json
from .storage import publish_bundle, read_receipts


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Offline synthetic BioPhysical Assurance replay"
    )
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run", help="replay a scenario and write evidence")
    run.add_argument("scenario")
    run.add_argument(
        "--out", help="new evidence directory; existing directories are rejected"
    )
    run.add_argument("--auth-key-file", help="optional external HMAC key file, v2 only")
    run.add_argument(
        "--key-id",
        help="identifier of the external HMAC key, required with --auth-key-file",
    )
    verify = sub.add_parser(
        "verify", help="verify evidence and recompute policy decisions"
    )
    verify.add_argument("scenario")
    verify.add_argument("receipts", help="receipts.jsonl or evidence directory")
    verify.add_argument(
        "--auth-key-file", help="required if the evidence directory contains auth.json"
    )
    return parser


def _run(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    if bool(args.auth_key_file) != bool(args.key_id):
        parser.error("--auth-key-file and --key-id must be supplied together")
    scenario = load_scenario(args.scenario)
    if args.auth_key_file and scenario["schema_version"] != "bpa.scenario.v2":
        parser.error("authenticated bundles require a v2 scenario")
    report, receipts = replay(scenario)
    tag = None
    if args.auth_key_file:
        tag = make_auth_tag(
            scenario_sha256=report["scenario_sha256"],
            last_receipt_sha256=report["last_receipt_sha256"],
            key=Path(args.auth_key_file).read_bytes(),
            key_id=args.key_id,
        )
    output = args.out or f"out/{scenario['scenario_id']}"
    publish_bundle(output, report, receipts, tag)
    print(f"evidence: {output}")
    print(
        f"decision regression: {'PASS' if report['pass'] else 'FAIL'}; "
        f"false_allows={report['false_allows']}; false_denies={report['false_denies']}"
    )
    return 0 if report["pass"] else 1


def _verify(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    scenario = load_scenario(args.scenario)
    receipts = read_receipts(args.receipts)
    valid = verify_receipts(receipts, scenario)
    source = Path(args.receipts)
    bundle = source if source.is_dir() else source.parent
    report_file = bundle / "report.json"
    if source.is_dir() and not report_file.exists():
        valid = False
    if report_file.exists():
        valid = valid and read_json(report_file) == replay(scenario)[0]
    tag_file = bundle / "auth.json"
    if tag_file.exists():
        if not args.auth_key_file:
            parser.error(
                "bundle contains auth.json; supply --auth-key-file to verify authentication"
            )
        tag = read_json(tag_file)
        valid = valid and verify_auth_tag(
            tag,
            scenario_sha256=receipts[0]["scenario_sha256"] if receipts else "",
            last_receipt_sha256=receipts[-1]["sha256"] if receipts else "",
            key=Path(args.auth_key_file).read_bytes(),
        )
    elif args.auth_key_file:
        parser.error("--auth-key-file was supplied but auth.json is missing")
    print("valid evidence" if valid else "invalid evidence")
    return 0 if valid else 1


def main() -> int:
    parser = _parser()
    args = parser.parse_args()
    try:
        return _run(args, parser) if args.command == "run" else _verify(args, parser)
    except (OSError, TypeError, ValueError, KeyError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
