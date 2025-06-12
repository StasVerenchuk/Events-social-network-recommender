from __future__ import annotations

import argparse
import datetime as dt
import subprocess
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Dict, List

from .measurements import recommendation_measurement               # noqa: F401
from .partition import TRAIN_INTERVAL, get_timestamps, get_partitioned_repo_wrapper
from .preprocessing import (
    load_events,
    load_groups,
    load_members,
    load_rsvps,
)
from .recommenders.content_recommender import ContentRecommender
from .recommenders.grp_freq_recommender import (
    GroupFrequencyRecommender,
)
from .recommenders.location_recommender import LocationRecommender   # noqa: F401
from .recommenders.hybrid_recommender import LearningToRank                 # noqa: F401

# ────────────────────────────────────────────────────────────────────
# 1. Базові шляхи
# ────────────────────────────────────────────────────────────────────
SRC_DIR = Path(__file__).resolve().parent
DATA_DIR = SRC_DIR / "data" / "json_data"
CRAWLER_DIR = SRC_DIR / "crawlers"
SCRIPTS_DIR = SRC_DIR / "scripts"

# ────────────────────────────────────────────────────────────────────
# 2. Допоміжні утиліти
# ────────────────────────────────────────────────────────────────────
def run_local_crawler() -> None:
    """Запускає `local_crawler.py`, якщо json-файли відсутні/неповні."""
    need_run = any(
        not (DATA_DIR / city).exists() or len(list((DATA_DIR / city).iterdir())) < 5
        for city in ("LCHICAGO", "LSAN JOSE", "LPHOENIX")
    )
    if need_run:
        subprocess.run(
            [sys.executable, CRAWLER_DIR / "local_crawler.py"],
            check=True,
        )


def run_best_user_script(n_members: int) -> None:
    """Створює TXT-файли з топ-користувачами."""
    subprocess.run(
        [
            sys.executable,
            "-m", "src.scripts.script",   # ← головна зміна
            "--number", str(n_members),
        ],
        check=True,
    )


# ────────────────────────────────────────────────────────────────────
# 3. Класифікатори-обгортки (однотипні)
# ────────────────────────────────────────────────────────────────────
def run_content(
    train_repo: Dict,
    test_repo: Dict,
    simscores: Dict,
    members: List[str],
) -> None:
    rec = ContentRecommender()
    rec.fit(train_repo["members_events"], train_repo)

    cand_events = list(test_repo["events_info"])
    cand_vecs = rec.transform_events(cand_events, test_repo)

    for m in members:
        rec.score(m, cand_events, cand_vecs, simscores)


def run_location(
    train_repo: Dict,
    test_repo: Dict,
    simscores: Dict,
    members: List[str],
) -> None:
    rec = LocationRecommender()
    rec.fit(train_repo["members_events"], train_repo)

    cand_events = list(test_repo["events_info"])
    for m in members:
        rec.score_candidates(m, cand_events, test_repo, simscores)


def run_group_freq(
    train_repo: Dict,
    test_repo: Dict,
    simscores: Dict,
    members: List[str],
) -> None:
    rec = GroupFrequencyRecommender()
    rec.fit(train_repo["members_events"])

    cand_events = list(test_repo["events_info"])
    for m in members:
        rec.score_candidates(m, cand_events, test_repo, simscores)


# ────────────────────────────────────────────────────────────────────
# 4. Головна функція
# ────────────────────────────────────────────────────────────────────
def main() -> None:
    run_local_crawler()

    argp = argparse.ArgumentParser("Event recommender — evaluation pipeline")
    argp.add_argument("--city", required=True, help="LCHICAGO | LSAN JOSE | LPHOENIX")
    argp.add_argument(
        "--algo",
        nargs="+",
        default=["svm", "rf"],
        help="l2r: svm mlp nb rf (space-separated)",
    )
    argp.add_argument("--members", type=int, default=100, help="Top-N members to test")
    args = argp.parse_args()

    city = args.city
    algo_list = args.algo
    n_members = args.members

    print("Generating files with TOP users …")
    run_best_user_script(n_members)
    print("Done.\n")

    # ── зчитування json ───────────────────────────────────────────
    city_dir = DATA_DIR / city
    group_members, group_events, event_group = load_groups(
        city_dir / "group_members.json",
        city_dir / "group_events.json",
    )
    repo = {
        "events_info": load_events(city_dir / "events_info.json"),
        "members_info": load_members(city_dir / "members_info.json"),
        "members_events": load_rsvps(city_dir / "rsvp_events.json"),
        "group_events": group_events,
        "group_members": group_members,
        "event_group": event_group,
    }

    # ── контейнер для всіх sim-score ──────────────────────────────
    simscores_all: Dict[str, Dict[str, Dict[str, float]]] = defaultdict(
        lambda: defaultdict(dict)
    )

    # ── часові «partition» -и ──────────────────────────────────────
    ts_start, ts_end = 1_262_304_000, 1_388_534_400        # 2010-01-01 .. 2014-01-01
    for part_no, ts in enumerate(sorted(get_timestamps(ts_start, ts_end), reverse=True), 1):
        win_start, win_end = ts - TRAIN_INTERVAL, ts + TRAIN_INTERVAL

        # TOP-користувачів для цього вікна читаємо з готового .txt
        best_file = (
            SCRIPTS_DIR
            / f"{city}_best_users_{win_start}_{win_end}.txt"
        )
        test_members = best_file.read_text(encoding="utf-8").split()[:n_members]

        # train / test репозиторії
        train_repo, test_repo = get_partitioned_repo_wrapper(ts, repo)

        # залишаємо лише тих test-користувачів, що мають історію у train-часі
        test_members = list(set(test_members) & set(train_repo["members_events"]))

        print(f"\n▁▁ Partition #{part_no}: {dt.datetime.utcfromtimestamp(ts)!s} ▔▔")

        # базові рекомендації
        run_content(train_repo, test_repo, simscores_all["content"], test_members)
        run_location(train_repo, test_repo, simscores_all["location"], test_members)
        run_group_freq(train_repo, test_repo, simscores_all["group"], test_members)

        # learning-to-rank
        l2r = LearningToRank()
        l2r.learn(
            simscores=simscores_all,
            test_events=list(test_repo["events_info"]),
            all_members_rsvp=test_repo["members_events"],
            test_members=test_members,
            log_fh=open("results.log", "a", encoding="utf-8"),
            algo_list=algo_list,
            n_members=n_members,
            partition_number=part_no,
        )


if __name__ == "__main__":
    main()
