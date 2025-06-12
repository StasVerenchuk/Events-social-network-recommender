import json
from collections import defaultdict
from pathlib import Path
from typing import Any, DefaultDict, Dict, List, Tuple


def read_json(path: Path) -> Dict[str, Any]:
    """Зчитує файл JSON, повертає порожній словник, якщо файл не існує
    або містить невалідний JSON."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        # можна залогувати помилку, якщо треба
        return {}


def load_groups(
    group_members_path: Path,
    group_events_path: Path,
) -> Tuple[
    Dict[str, List[str]],
    Dict[str, List[str]],
    Dict[str, str],
]:
    """Повертає:
    1) group_members   – {group_id: [member_id, …]}
    2) group_events    – {group_id: [event_id,  …]}
    3) event_to_group  – {event_id: group_id} (зворотна відповідність)
    """
    group_members: Dict[str, List[str]] = read_json(group_members_path)
    group_events: Dict[str, List[str]] = read_json(group_events_path)

    event_to_group: Dict[str, str] = {
        event_id: group_id
        for group_id, event_ids in group_events.items()
        for event_id in event_ids
    }

    return group_members, group_events, event_to_group


def load_events(events_info_path: Path) -> Dict[str, Any]:
    """Зчитує інформацію про події."""
    return read_json(events_info_path)


def load_members(members_info_path: Path) -> Dict[str, Any]:
    """Зчитує координати / профілі користувачів."""
    return read_json(members_info_path)


def load_rsvps(rsvp_path: Path) -> Dict[str, List[str]]:
    """
    Перетворює структуру {event_id: [member_id, …]}
    на {member_id: [event_id, …]}
    """
    event_to_members: Dict[str, List[str]] = read_json(rsvp_path)

    member_to_events: DefaultDict[str, List[str]] = defaultdict(list)
    for event_id, member_ids in event_to_members.items():
        for member_id in member_ids:
            member_to_events[member_id].append(event_id)

    return member_to_events


# приклад використання
# if __name__ == "__main__":
#     DATA_DIR = Path("data/json_data/LCHICAGO")

#     groups = load_groups(
#         DATA_DIR / "group_members.json",
#         DATA_DIR / "group_events.json",
#     )
#     events_info = load_events(DATA_DIR / "events_info.json")
#     members_info = load_members(DATA_DIR / "members_info.json")
#     member_events = load_rsvps(DATA_DIR / "rsvp_events.json")
