from collections import defaultdict
from typing import Dict, List

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class ContentRecommender:
    """
    Формує TF-IDF простір за описами подій і обчислює
    подібність (cosine similarity) між користувачем та подіями.
    """

    def __init__(self, ngram_range: tuple[int, int] = (1, 1)) -> None:
        self.vectorizer = TfidfVectorizer(
            ngram_range=ngram_range,
            analyzer="word",
            sublinear_tf=True,
            max_df=0.5,
            stop_words="english",
            norm="l2",
        )
        # member_id -> вектор користувача
        self.training_vecs: Dict[str, np.ndarray] = {}

    # --------------------------------------------------------------------- #
    # 1. Підготовка даних (корпус + вектори користувачів)
    # --------------------------------------------------------------------- #
    @staticmethod
    def _events_to_text(event_ids: List[str], events_info: Dict[str, Dict]) -> str:
        """Об'єднує описи кількох подій в один текст."""
        return " ".join(events_info[e_id]["description"] for e_id in event_ids)

    def fit(self, member_events: Dict[str, List[str]], repo: Dict) -> None:
        """
        Створює словник TF-IDF і вектори користувачів.
        `member_events` ‒ {member_id: [event_id, …]} для train-періоду.
        """
        events_info = repo["events_info"]

        # --- 1) формуємо «корпус» з усіх описів подій ---
        corpus = [
            events_info[event_id]["description"]
            for events in member_events.values()
            for event_id in events
        ]
        self.vectorizer.fit(corpus)

        # --- 2) вектор користувача = сума/конкатенація його подій ---
        for member_id, events in member_events.items():
            text = self._events_to_text(events, events_info)
            self.training_vecs[member_id] = self.vectorizer.transform([text])

    # --------------------------------------------------------------------- #
    # 2. Векторизація кандидат-подій
    # --------------------------------------------------------------------- #
    def transform_events(
        self, event_ids: List[str], repo: Dict
    ) -> np.ndarray:
        """Повертає TF-IDF-матрицю для списку event_id."""
        events_info = repo["events_info"]
        texts = [events_info[e_id]["description"] for e_id in event_ids]
        return self.vectorizer.transform(texts)

    # --------------------------------------------------------------------- #
    # 3. Обчислення score-ів / оновлення словника sim-scores
    # --------------------------------------------------------------------- #
    def score(
        self,
        member_id: str,
        candidate_events: List[str],
        candidate_vecs: np.ndarray,
        sim_scores: Dict[str, Dict[str, float]],
    ) -> None:
        """
        Записує cosine-similarity для кожної події кандидата у `sim_scores`.
        `sim_scores` — зовнішній контейнер {member_id: {event_id: score}}.
        """
        user_vec = self.training_vecs[member_id]          # (1  ×  d)
        scores = cosine_similarity(user_vec, candidate_vecs).flatten()

        user_dict = sim_scores.setdefault(member_id, {})
        for e_id, score in zip(candidate_events, scores):
            user_dict[e_id] = float(score)
