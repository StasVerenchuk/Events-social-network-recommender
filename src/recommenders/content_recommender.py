from collections import defaultdict

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class ContentRecommender:
    def __init__(self):
        self.word_tfidf = TfidfVectorizer(
            ngram_range = (1, 1,),
            analyzer = "word",
            sublinear_tf=True,
            max_df = 0.5,
            stop_words = "english",
            norm = "l2"
        )


    def get_test_events_with_description(self, repo, potential_events):
        events_info = repo["events_info"]
        test_events = np.array([
            events_info[event_id]["description"]
            for event_id in potential_events
            if "description" in events_info[event_id] and events_info[event_id]["description"]
        ])

        test_events_vecs = self.word_tfidf.transform(test_events)
        return test_events_vecs


    def train(self, training_events_dict, info_repo):
        events_info = info_repo["events_info"]
        self.training_vecs = {}

        training_events = np.array([
            events_info[event_id]["description"]
            for user_id in training_events_dict
            for event_id in training_events_dict[user_id]
            if "description" in events_info[event_id] and events_info[event_id]["description"]
        ])

        self.word_tfidf.fit(training_events)

        for user_id in training_events_dict:
            training_event = ""
            for event_id in training_events_dict[user_id]:
                if "description" in events_info[event_id] and events_info[event_id]["description"]:
                    training_event += events_info[event_id]["description"] + " "

            training_vec = self.word_tfidf.transform(np.array([training_event]))
            self.training_vecs[user_id] = training_vec


    def test(self, member_id, potential_events, test_events_vecs, simscores):
        member_vec = self.training_vecs.get(member_id)
        if member_vec is None:
            return

        similarity_scores = cosine_similarity(member_vec, test_events_vecs).flatten()
        for i in range(len(potential_events)):
            simscores[member_id][potential_events[i]] = similarity_scores[i]
