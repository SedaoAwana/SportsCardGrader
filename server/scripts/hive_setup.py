"""One-time Hive setup for The Binder publishing (manual ops tool).

Usage (from server/, with HIVE_ACCOUNT + HIVE_POSTING_KEY in the environment
or repo-root .env):

    .venv/bin/python scripts/hive_setup.py            # subscribe + RC check
    .venv/bin/python scripts/hive_setup.py --post-test  # also publish a hello post

Respects HIVE_DRY_RUN=true (logs ops instead of broadcasting).

Note: setting the community title/description ("The Binder") needs the
community owner/admin account (@meno as of 2026-08-16), not the app account —
see docs/hive-setup.md.
"""
import argparse
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import get_settings  # noqa: E402
from app.hive.client import HiveClient  # noqa: E402


async def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--post-test", action="store_true",
                        help="publish a hello post to the community")
    args = parser.parse_args()

    settings = get_settings()
    if not settings.hive_configured:
        print("HIVE_ACCOUNT / HIVE_POSTING_KEY are not set — nothing to do.")
        return 1

    client = HiveClient(settings.hive_node_list, account=settings.hive_account,
                        posting_key=settings.hive_posting_key,
                        dry_run=settings.hive_dry_run)

    rc = await client.get_rc_percent()
    print(f"@{settings.hive_account} Resource Credits: {rc:.1f}%"
          + (" — LOW, power up more HP" if rc < settings.hive_min_rc_percent else ""))

    print(f"Subscribing @{settings.hive_account} to {settings.hive_community} …")
    tx = await client.broadcast_ops([("custom_json", {
        "required_auths": [],
        "required_posting_auths": [settings.hive_account],
        "id": "community",
        "json": json.dumps(["subscribe", {"community": settings.hive_community}]),
    })])
    print(f"  -> {tx}")

    if args.post_test:
        permlink = "the-binder-hello"
        print(f"Publishing test post @{settings.hive_account}/{permlink} …")
        tx = await client.broadcast_ops([("comment", {
            "parent_author": "",
            "parent_permlink": settings.hive_community,
            "author": settings.hive_account,
            "permlink": permlink,
            "title": "The Binder is live",
            "body": "Card Scanner will publish scanned cards to this community. "
                    "https://github.com/Calvin-Sedao51/SportsCardGrader",
            "json_metadata": json.dumps({"app": "cardscanner/1.0",
                                         "tags": [settings.hive_community]}),
        })])
        print(f"  -> {tx}")
        print(f"  view: https://peakd.com/@{settings.hive_account}/{permlink}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
