from typing import Dict, List, Literal

import numpy as np
from sklearn.neighbors import KernelDensity


class LocationRecommender:
    """KDE-рекомендації за геолокацією користувача та його минулих подій."""

    def __init__(
        self,
        kernel: str | Literal["gaussian", "tophat", "epanechnikov"] = "gaussian",
        bandwidth: float | str = "scott",          # ←  зміна: 'scott' замість None
    ) -> None:
        self.kernel = kernel
        self.bandwidth = bandwidth
        self.training_vecs: Dict[str, np.ndarray] = {}

    # ------------------------------------------------------------------ #
    # 1. Навчання: збір (lat, lon) усіх відвіданих користувачем подій
    # ------------------------------------------------------------------ #
    def fit(
        self,
        train_events: Dict[str, List[str]],
        repo: Dict[str, Dict],
    ) -> None:
        """Формує матриці [n_events × 2] для кожного користувача."""
        events_info = repo["events_info"]
        members_info = repo["members_info"]

        for member_id, event_ids in train_events.items():
            coords = [
                (members_info[member_id]["lat"], members_info[member_id]["lon"]),
                *[
                    (events_info[e_id]["lat"], events_info[e_id]["lon"])
                    for e_id in event_ids
                ],
            ]
            self.training_vecs[member_id] = np.asarray(coords)

    # ------------------------------------------------------------------ #
    # 2. Інференс: оцінка правдоподібності KDE для candidate-подій
    # ------------------------------------------------------------------ #
    def score_candidates(
        self,
        member_id: str,
        candidate_events: List[str],
        repo: Dict[str, Dict],
        sim_scores: Dict[str, Dict[str, float]],
    ) -> None:
        """Записує KDE-score у sim_scores[member_id][event_id]."""
        if member_id not in self.training_vecs:
            # нема історії – нічим навчати розподіл
            return

        member_coords = self.training_vecs[member_id]
        kde = KernelDensity(kernel=self.kernel, bandwidth=self.bandwidth).fit(
            member_coords
        )

        events_info = repo["events_info"]
        user_dict = sim_scores.setdefault(member_id, {})

        for e_id in candidate_events:
            lat, lon = events_info[e_id]["lat"], events_info[e_id]["lon"]
            # KDE повертає log-density → перетворюємо в density через exp
            user_dict[e_id] = float(
                np.exp(kde.score_samples([[lat, lon]])[0])
            )
