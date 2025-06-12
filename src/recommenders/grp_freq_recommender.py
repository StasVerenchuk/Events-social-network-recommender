from typing import Dict, List, Set


class GroupFrequencyRecommender:
    """
    Оцінює «близькість» події користувачу як частку вже відвіданих
    ним подій усередині тієї ж групи.
    """

    def __init__(self) -> None:
        # member_id → set(event_id)
        self.user_history: Dict[str, Set[str]] = {}

    # ------------------------------------------------------------------ #
    # 1. «Навчання» – просто запамʼятати історію участі
    # ------------------------------------------------------------------ #
    def fit(
        self,
        member_events: Dict[str, List[str]],
    ) -> None:
        self.user_history = {
            m_id: set(evt_ids) for m_id, evt_ids in member_events.items()
        }

    # ------------------------------------------------------------------ #
    # 2. Інференс – рахунок для кожної candidate-події
    # ------------------------------------------------------------------ #
    def score_candidates(
        self,
        member_id: str,
        candidate_events: List[str],
        repo: Dict[str, Dict],
        sim_scores: Dict[str, Dict[str, float]],
    ) -> None:
        """
        Записує score = |відвідано у цій групі| / |усіх відвіданих|
        у словник sim_scores[member_id][event_id].
        """
        user_events = self.user_history.get(member_id, set())
        if not user_events:                         # ⬅ якщо історії нема – ігноруємо
            return

        # зручні посилання
        event_to_group: Dict[str, str] = repo["event_group"]
        group_to_events: Dict[str, List[str]] = repo["group_events"]

        user_scores = sim_scores.setdefault(member_id, {})

        for event_id in candidate_events:
            group_id = event_to_group.get(event_id)
            if not group_id:
                user_scores[event_id] = 0.0
                continue

            group_events = set(group_to_events[group_id])
            overlap = user_events & group_events

            score = len(overlap) / len(user_events)
            user_scores[event_id] = float(score)
