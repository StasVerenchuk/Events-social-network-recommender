from collections import defaultdict
from typing import Any

def filter_events_info(events_info: dict, start: int, end: int) -> dict:
    return {
        e: data for e, data in events_info.items()
        if start <= data["time"] <= end
    }


def get_intersection(a: list, b: list) -> list:
    b_set = set(b)
    return [x for x in a if x in b_set]


def get_partitioned_repo(repo: dict, start_time: int, end_time: int) -> dict:
    events_info = repo["events_info"]
    events_info_in_range = filter_events_info(events_info, start_time, end_time)

    member_events_in_range = {}
    all_event_ids_in_range = list(events_info_in_range.keys())

    for member, event_ids in repo["members_events"].items():
        filtered = get_intersection(all_event_ids_in_range, event_ids)
        if filtered:
            member_events_in_range[member] = filtered

    return {
        "events_info": events_info_in_range,
        "members_events": defaultdict(list, member_events_in_range),
    }


def get_partitioned_repo_wrapper(timestamp: int, repo: dict, interval: int) -> tuple:
    return {
        get_partitioned_repo(repo, timestamp - interval, timestamp),
        get partitioned_repo(repo, timestamp, timestamp + interval)
    }


def get_timestamps(start_time: int, end_time: int, interval: int) -> list:
    return list(range(start_time + interval, end_time - interval, interval))


