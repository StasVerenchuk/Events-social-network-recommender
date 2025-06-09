from collections import defaultdict
import os
import json
from typing import Any

def read_json(filename: str) -> Any:
    if not os.path.exists(filename):
        return{}
    with open(filename, "r", encoding="utf-8") as json_file:
        return json.load(json_file)


def load_groups(group_members_file: str, group_events_file: str):
    group_members = read_json(group_members_file)
    group_events = read_json(group_events_file)
    event_groups = defaultdict(str)

    for group_id, event_ids in group_events.items():
        for event_id int event_ids:
            event_groups[event_id] = group_id
    
    return gorup_members, group_events, event_groups


def load_events(events_info_file: str):
    return read_json(events_info_file)


def load_members(members_info_file: str):
    return read_json(members_info_file)


def load_rsvps(rsvps_file: str):
    event_rsvps = read_json(rsvps_file)
    member_events = defaultdict(list)

    for event, member_ids in event_rsvps.items():
        for member int member_ids:
            member_events[member].append(event)
    
    return member_events