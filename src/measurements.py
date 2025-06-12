from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Tuple


@dataclass
class Accuracy:
    """Накопичує середній відсоток точності рекомендацій."""
    percentage_sum: float = 0.0
    count: int = 0
    average: float = field(init=False, default=0.0)

    def update(self, recommendation_accuracy: float) -> None:
        self.percentage_sum += recommendation_accuracy
        self.count += 1
        self.average = self.percentage_sum / self.count

    def __str__(self) -> str:
        return f"{self.average:.2f} %"


# member_id → Accuracy
member_feature_accuracy: Dict[str, Accuracy] = defaultdict(Accuracy)


def recommendation_measurement(
    test_members_sorted_events: Dict[str, List[Tuple[str, float]]],
    all_members_rsvpd_events: Dict[str, List[str]],
    test_members: List[str],
) -> None:
    """
    Оцінює точність рекомендацій:
    - test_members_sorted_events: {member_id: [(event_id, score), …]} (відсортовано за score)
    - all_members_rsvpd_events:  {member_id: [event_id, …]}  (факт «yes» RSVP)
    - test_members:              список member_id, для яких міряємо точність
    """
    for member_id in test_members:
        accuracy = member_feature_accuracy[member_id]

        # Скільки подій користувач реально відвідав у тестовому інтервалі
        rsvpd_events = all_members_rsvpd_events.get(member_id, [])
        union_size = len(rsvpd_events)

        # Топ-N рекомендацій, де N = |RSVP|
        top_events = test_members_sorted_events.get(member_id, [])[-union_size:]

        # Перетин рекомендованих подій i фактичних RSVP
        intersection = sum(event_id in rsvpd_events for event_id, _ in top_events)

        recommendation_accuracy = (
            100.0 if union_size == 0 else intersection / union_size * 100.0
        )

        accuracy.update(recommendation_accuracy)

        print(
            f"Member {member_id:>8}: "
            f"last accuracy = {recommendation_accuracy:.2f} %, "
            f"cumulative average = {accuracy}"
        )
