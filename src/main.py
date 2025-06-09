import argparse
import time
import datetime
from collections import defaultdict

from content_recommender import ContentRecommender
from preprocessing import load_events, load_members, load_rsvps
from partition import get_timestamps, get_partitioned_repo_wrapper
from measurements import evaluate_recommendation

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--events", required=True)
    parser.add_argument("--members", required=True)
    parser.add_argument("--rsvps", required=True)
    parser.add_argument("--members_count", type=int, default=50)
    args = parser.parse_args()

    events_info = load_events(args.events)
    members_info = load_members(args.members)
    rsvps_info = load_rsvps(args.rsvps)

    repo = {
        "events_info": events_info,
        "members_info": members_info,
        "members_evetns" : members_events
    }

    simscores = defaultdict(lambda: defaultdict(float))
    interval = int((364 / 2) * 24 * 60 * 60)
    timestamps = get_timestamps(1262304000, 1388534400, interval)

    recommender = ContentRecommender()

    for t in timestamps:
        training_repo, test_repo = get_partitioned_repo_wrapper(t, repo, interval)
        test_members = list(test_repo["members_events"].keys())[:args.members_count]
        potential_events = list(test_repo["events_info"].keys())

        recommender.train(training_repo["members_events"], training_repo)
        test_vecs = recommender.get_test_events_with_description(test_repo, potential_events)

        for member in test_members:
            recommender.test(member, potential_events, test_vecs, simscores)

        print(f"[Done] Completed partition for timestamp: {dattime.datetime.fromtimestamp(t)}")

    accuracy = evaluate_recommender(simscores, repo["members_events"])
    for member_id, acc in accuracy.items():
        print(f"Member {member_id}: Accuracy = {acc.average():.2f}%")


if __name__ == "__main__":
    main()