import bisect
from collections import defaultdict
from typing import Dict, List, Tuple

# ──────────────────────────────────────────────────────────────
# 1. Допоміжні утиліти
# ──────────────────────────────────────────────────────────────
SECONDS_PER_DAY = 86_400


def seconds_in_days(days: int) -> int:
    """Повертає кількість секунд у N днях."""
    return days * SECONDS_PER_DAY


# Півроку ≈ 182 дні
TRAIN_INTERVAL = seconds_in_days(182)


# ──────────────────────────────────────────────────────────────
# 2. Генерація «контрольних» timestamp-ів
# ──────────────────────────────────────────────────────────────
def get_timestamps(start: int, end: int) -> List[int]:
    """
    Генерує послідовність timestamp-ів:
    start, start+Δ, start+2Δ, …  <  end-2Δ, де Δ = TRAIN_INTERVAL.
    """
    return list(
        range(start, end - 2 * TRAIN_INTERVAL, TRAIN_INTERVAL)
    )


# ──────────────────────────────────────────────────────────────
# 3. Розбиття сховища (repo) на train / test
# ──────────────────────────────────────────────────────────────
Repo = Dict[str, Dict]  # умовний тип для стислості


def get_partitioned_repo_wrapper(ts: int, repo: Repo) -> Tuple[Repo, Repo]:
    """Обгортка, що формує train- та test-репозиторії навколо `ts`."""
    train_repo = _partition_repo(repo, ts - TRAIN_INTERVAL, ts)
    test_repo = _partition_repo(repo, ts, ts + TRAIN_INTERVAL)
    return train_repo, test_repo


def _partition_repo(repo: Repo, start: int, end: int) -> Repo:
    """
    Витягує підмножини подій, учасників і груп,
    що потрапляють у часовий проміжок [start, end].
    """
    # 1) Події у діапазоні
    events_info_all: Dict[str, Dict] = repo["events_info"]
    events_info = {
        e_id: info
        for e_id, info in events_info_all.items()
        if start <= info["time"] <= end
    }
    event_ids: List[str] = sorted(events_info.keys())

    # 2) Членство користувачів (member → [event_id, …])
    member_events_all: Dict[str, List[str]] = repo["members_events"]
    members_events = {
        m_id: _intersect_sorted(event_ids, evt_list)
        for m_id, evt_list in member_events_all.items()
        if (new := _intersect_sorted(event_ids, evt_list))
    }

    # 3) Події груп (group → [event_id, …])
    group_events_all: Dict[str, List[str]] = repo["group_events"]
    group_events = {
        g_id: _intersect_sorted(event_ids, evt_list)
        for g_id, evt_list in group_events_all.items()
        if (new := _intersect_sorted(event_ids, evt_list))
    }

    # 4) Зворотна відповідність event → group
    event_group_all: Dict[str, str] = repo["event_group"]
    event_group = {
        e_id: event_group_all[e_id]
        for e_id in events_info
        if e_id in event_group_all
    }

    # 5) Інформація про користувачів
    members_info_all: Dict[str, Dict] = repo["members_info"]
    members_info = {
        m_id: members_info_all[m_id] for m_id in members_events
    }

    return {
        "events_info": events_info,
        "members_events": defaultdict(list, members_events),
        "members_info": members_info,
        "group_events": group_events,
        "event_group": event_group,
    }


# ──────────────────────────────────────────────────────────────
# 4. Допоміжні ф-ції
# ──────────────────────────────────────────────────────────────
def get_member_events_dict_in_range(
    repo: Repo, start: int, end: int
) -> Dict[str, List[str]]:
    """Повертає member → [event_id] у заданому діапазоні."""
    return {
        m_id: _filter_events_by_time(repo, evt_ids, start, end)
        for m_id, evt_ids in repo["members_events"].items()
    }


def _filter_events_by_time(
    repo: Repo, events: List[str], start: int, end: int
) -> List[str]:
    events_info = repo["events_info"]
    return [
        e_id
        for e_id in events
        if start <= events_info[e_id]["time"] <= end
    ]


def _intersect_sorted(big: List[str], small: List[str]) -> List[str]:
    """Швидке перетинання: big має бути відсортованим."""
    return [x for x in small if _binary_search(big, x)]


def _binary_search(lst: List[str], item: str) -> bool:
    """Замінено на bisect: O(log n)."""
    idx = bisect.bisect_left(lst, item)
    return idx < len(lst) and lst[idx] == item
