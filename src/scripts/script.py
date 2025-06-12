#!/usr/bin/env python3.10
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import DefaultDict, Dict, List

from src.partition import TRAIN_INTERVAL, get_timestamps

# ────────────────────────────────────────────────────────────────────
# 1. Шляхи
# ────────────────────────────────────────────────────────────────────
SRC_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = SRC_DIR / "data" / "json_data"       # …/src/data/json_data
CITIES   = ["LCHICAGO", "LSAN JOSE", "LPHOENIX"]

# ────────────────────────────────────────────────────────────────────
def read_json(path: Path) -> Dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


# ────────────────────────────────────────────────────────────────────
def init_city(city: str) -> tuple[DefaultDict[str, List[str]], Dict]:
    """member→events  та  events_info."""
    city_dir = DATA_DIR / city
    event_members = read_json(city_dir / "rsvp_events.json")
    member_events: DefaultDict[str, List[str]] = defaultdict(list)
    for evt, members in event_members.items():
        for m in members:
            member_events[m].append(evt)

    events_info = read_json(city_dir / "events_info.json")
    return member_events, events_info


def rsvp_in_window(
    member_events: DefaultDict[str, List[str]],
    events_info: Dict,
    member: str,
    start_ts: int,
    end_ts: int,
) -> int:
    return sum(
        start_ts <= events_info[e]["time"] <= end_ts
        for e in member_events.get(member, [])
        if e in events_info
    )


def top_k_users(
    member_events: DefaultDict[str, List[str]],
    events_info: Dict,
    start_ts: int,
    end_ts: int,
    k: int,
) -> List[str]:
    counts = {
        m: rsvp_in_window(member_events, events_info, m, start_ts, end_ts)
        for m in member_events
    }
    return sorted(counts, key=counts.get, reverse=True)[:k]


# ────────────────────────────────────────────────────────────────────
def main() -> None:
    argp = argparse.ArgumentParser("extract best users")
    argp.add_argument(
        "--number",
        "-n",
        type=int,
        default=100,
        help="top-N найактивніших користувачів",
    )
    n_best = argp.parse_args().number

    ts_start, ts_end = 1_262_304_000, 1_388_534_400    # 01-01-2010 .. 01-01-2014
    for city in CITIES:
        member_events, events_info = init_city(city)

        for ts in sorted(get_timestamps(ts_start, ts_end), reverse=True):
            window_start, window_end = ts - TRAIN_INTERVAL, ts + TRAIN_INTERVAL
            best_users = top_k_users(
                member_events,
                events_info,
                window_start,
                window_end,
                n_best,
            )
            out_path = (
                Path(__file__).parent
                / f"{city}_best_users_{window_start}_{window_end}.txt"
            )
            out_path.write_text(" ".join(best_users), encoding="utf-8")
            print(f"[{city}] {out_path.name} written ({len(best_users)} users)")


if __name__ == "__main__":
    main()

# (необов’язковий «запобіжник»)
if __name__ == "__main__" and (__package__ is None or __package__ == ""):
    import sys, textwrap
    msg = textwrap.dedent(
        """
        Запускайте цей скрипт пакетом:

            python -m src.scripts.script --number 100
        """
    )
    print(msg, file=sys.stderr)
    sys.exit(1)