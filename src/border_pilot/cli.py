"""Command-line entrypoint for BorderPilot.

Usage:
    python -m border_pilot.cli run --query "wireless earbuds" --markets amazon_us,amazon_de
    python -m border_pilot.cli demo
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import List


def _parse_csv(value: str) -> List[str]:
    return [v.strip() for v in (value or "").split(",") if v.strip()]


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="border-pilot", description="BorderPilot CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_run = sub.add_parser("run", help="Run the full workflow once.")
    p_run.add_argument("--query", required=True, help="Seed query, e.g. 'wireless earbuds'")
    p_run.add_argument("--markets", default="amazon_us,amazon_de,amazon_uk,amazon_jp",
                        help="Comma-separated target marketplaces")
    p_run.add_argument("--json", action="store_true", help="Print final state as JSON only")

    p_demo = sub.add_parser("demo", help="Run a canned demo run.")

    args = parser.parse_args(argv)

    from border_pilot.orchestrator import run as run_workflow

    if args.cmd == "demo":
        final = run_workflow(
            "wireless earbuds",
            target_marketplaces=["amazon_us", "amazon_de", "amazon_uk", "amazon_jp"],
        )
        _print(final, as_json=False)
        return 0

    if args.cmd == "run":
        final = run_workflow(
            args.query,
            target_marketplaces=_parse_csv(args.markets),
        )
        if args.json:
            print(json.dumps(final, ensure_ascii=False, indent=2, default=str))
        else:
            _print(final, as_json=False)
        return 0

    parser.print_help()
    return 1


def _print(final: dict, *, as_json: bool) -> None:
    if as_json:
        print(json.dumps(final, ensure_ascii=False, indent=2, default=str))
        return
    print("=" * 72)
    print("BorderPilot - run trace")
    print("=" * 72)
    for line in final.get("trace", []) or []:
        print(line)

    print("\n--- Top trends ---")
    for t in (final.get("trends") or [])[:5]:
        print(f" - {t.get('name')} ({t.get('marketplace')}) - "
              f"trend={t.get('trend')} score={t.get('score')}")

    market = final.get("market_analysis") or {}
    print("\n--- Analyst brief ---")
    print(f" decision : {market.get('decision')}")
    print(f" rationale: {market.get('rationale')}")
    print(f" TAM est. : {market.get('tam_estimate_usd')}")
    print(f" sweet spot: {market.get('price_sweet_spot')}")
    print(f" competitors: {', '.join(market.get('top_competitors') or []) or '-'}")

    print("\n--- Listings ---")
    for mp, draft in (final.get("listings") or {}).items():
        print(f"\n[{mp}] ({draft.get('language')}) quality={draft.get('quality_score')}")
        print(f" title : {draft.get('title')}")
        for b in (draft.get("bullet_points") or [])[:5]:
            print(f" bullet: {b}")
        print(f" price : {draft.get('price_hint')}")

    report = final.get("quality_report") or {}
    print("\n--- Quality report ---")
    print(f" overall : {report.get('overall_score')}")
    print(f" decision: {report.get('recommendation')}")
    for c in (report.get("checks") or [])[:8]:
        print(f" - {c.get('marketplace')} :: {c.get('name')} "
              f"-> {c.get('score')} ({c.get('note')})")


if __name__ == "__main__":
    sys.exit(main())
