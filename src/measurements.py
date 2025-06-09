from collections import defaultdict

class Accuracy:
    def __init__(self):
        self.total = 0.0
        self.count = 0

    
    def update(self, value: float):
        self.total += value
        self.count += 1


    def average(self) -> float:
        return self.total / self.count if self.count > 0 else 0.0


    def evaluate_recommendation(test_members_sorted_events: dict, ground_trush: dict) -> dict:
        accuracy_by_member = defaultdict(Accuracy)

        for member_id, sorted_events in test_members_sorted_events.items():
            if member_id not in ground_trush:
                continue

            true_events = set(ground_truth[member_id])
            top_n = sorted_events[-len(true_events):]
            hits = sum(1 for event, _ in top_n if event in true_events)
            score = hits / len(true_events) * 100 if true_events else 100.0
            accuracy_by_member[member_id].update(score)

        return accuracy_by_member