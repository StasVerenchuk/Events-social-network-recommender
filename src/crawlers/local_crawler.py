from collections import defaultdict
from pathlib import Path
import json 
import logging
import os

import pandas as pd

logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s', level=logging.INFO)

OUTPUT_DIR = "data/json_data"

cities = ["CHICAGO", "PHOENIX", "SAN JOSE"]
default_loc = {
    "CHICAGO":{
        "lat":41.8781,
        "lon":-87.6298
    },
    "PHOENIX":{
        "lat":33.4484,
        "lon":-112.0740
    },
    "SAN JOSE":{
        "lat":37.3382,
        "lon":-121.8863
    }
}

city_groups_dict = defaultdict(lambda: [])
groups_city_dict = defaultdict(lambda: "")
group_events_dict = defaultdict(lambda: defaultdict(lambda: []))
group_members_dict = defaultdict(lambda: defaultdict(lambda: []))
member_groups_dict = defaultdict(lambda: "")
event_groups_dict = defaultdict(lambda: "")
rsvp_event_members_dict = defaultdict(lambda: defaultdict(lambda: []))
members_info_dict = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: 0.0)))
events_info_dict = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: 0.0)))
location_lat_lon_dict = defaultdict(lambda: defaultdict(lambda: 0.0))


def main():
    logging.info("Start get_groups_from_cities() function")
    get_groups_from_cities(cities)
    logging.info("End get_groups_from_cities()_ function")
    logging.info("--------------------------------------")

    logging.info("Start get_events_from_groups() function")
    get_events_from_groups()
    logging.info("End get_events_from_groups()_ function")
    logging.info("--------------------------------------")

    logging.info("Start get_members_from_groups() function")
    get_members_from_groups()
    logging.info("End get_members_from_groups()_ function")
    logging.info("--------------------------------------")

    logging.info("Start get_rsvp_from_events() function")
    get_rsvp_from_events()
    logging.info("End get_rsvp_from_events()_ function")
    logging.info("--------------------------------------")

    logging.info("Start get_member_info() function")
    get_member_info()
    logging.info("End get_member_info()_ function")
    logging.info("--------------------------------------")

    logging.info("Start get_event_info() function")
    get_event_info()
    logging.info("End get_evnet_info()_ function")


def create_json_file(dictionary, filename):
    json_representation = json.dumps(dictionary)
    with open(filename, "w", encoding="utf-8") as f:
        f.write(json_representation)

    
def get_groups_from_cities(cities):
    global city_groups_dict, groups_city_dict

    city_data = pd.read_csv("data/groups.csv")

    city_list = list(city_data.region)
    group_list = list(city_data.group_id)

    for i in range(len(city_list)):
        city_groups_dict[str(city_list[i])].append(str(group_list[i]))
        groups_city_dict[str(group_list[i])] = (str(city_list[i]))
        


def get_events_from_groups():
    global group_events_dict, groups_city_dict, event_groups_dict

    group_events_data = pd.read_csv("data/group_events.csv")

    group_ids = list(group_events_data.group_id)
    event_ids = list(group_events_data.event_id)

    for i in range(len(group_ids)):
        # group_events_dict[groups_city_dict[str(group_ids[i])]][str(group_ids[i])].append(str(event_ids[i]))
        # event_groups_dict[str(event_ids[i])] = str(group_ids[i])
        group_id = str(group_ids[i])
        event_id = str(event_ids[i])
        city = groups_city_dict[group_id]
        group_events_dict[city][group_id].append(event_id)
        event_groups_dict[event_id] = group_id

    for city in group_events_dict:
        city_path = os.path.join(OUTPUT_DIR, f"L{city}")
        if not os.path.isdir(city_path):
            os.makedirs(city_path)
        output_file = os.path.join(city_path, "group_events.json")
        create_json_file(group_events_dict[city], output_file)


def get_members_from_groups():
    global group_members_dict, groups_city_dict, member_groups_dict

    group_members_data = pd.read_csv("data/group_users.csv")

    group_ids = list(group_members_data.group_id)
    member_ids = list(group_members_data.user_id)

    for i in range(len(group_ids)):
        group_id = str(group_ids[i])
        member_id = str(member_ids[i])
        city = groups_city_dict[group_id]
        group_members_dict[city][group_id].append(member_id)
        member_groups_dict[member_id] = group_id

    for city in group_members_dict:
        city_path = os.path.join(OUTPUT_DIR, f"L{city}")
        if not os.path.isdir(city_path):
            os.makedirs(city_path)
        output_file = os.path.join(city_path, "group_members.json")
        create_json_file(group_members_dict[city], output_file)


def get_rsvp_from_events():
    global event_groups_dict, groups_city_dict, rsvp_event_members_dict
    response_list = []
    member_list = []
    event_list = []

    for i in range(1, 18):
        file_path = Path("data") / f"rsvps_{i}.csv"
        rsvp_data = pd.read_csv(file_path)

        response_list.extend(rsvp_data["response"])
        member_list.extend(rsvp_data["user_id"])
        event_list.extend(rsvp_data["event_id"])

    for response, member_id, event_id in zip(response_list, member_list, event_list):
        if response == "yes":
            event_id_str = str(event_id)
            member_id_str = str(member_id)
            group_id = event_groups_dict.get(event_id_str)

            if group_id:
                city = groups_city_dict.get(group_id)
                if city:
                    rsvp_event_members_dict[city][event_id_str].append(member_id_str)

    for city, city_rsvp_data in rsvp_event_members_dict.items():
        city_dir = Path("data/json_data") / f"L{city}"
        city_dir.mkdir(parents=True, exist_ok=True)
        output_path = city_dir / "rsvp_events.json"
        create_json_file(city_rsvp_data, output_path)


def get_member_info():
    global groups_city_dict, members_info_dict, member_groups_dict
    member_list = []
    latitude_list = []
    longitude_list = []

    for i in range(1, 8):
        file_path = Path("data") / f"users_{i}.csv"
        user_data = pd.read_csv(file_path)
        
        member_list.extend(user_data["user_id"])
        latitude_list.extend(user_data["latitude"])
        longitude_list.extend(user_data["longitude"])

    for member_id, lat, lon in zip(member_list, latitude_list, longitude_list):
        member_id_str = str(member_id)
        group_id = member_groups_dict.get(member_id_str)

        if group_id:
            city = groups_city_dict.get(group_id)
            if city:
                members_info_dict[city][member_id_str]["lat"] = float(lat)
                members_info_dict[city][member_id_str]["lon"] = float(lon)

    for city, city_members in members_info_dict.items():
        city_dir = Path("data/json_data") / f"L{city}"
        city_dir.mkdir(parents=True, exist_ok=True)
        output_path = city_dir / "members_info.json"
        create_json_file(city_members, output_path)


def get_event_info():
    global events_info_dict, groups_city_dict, event_groups_dict, location_lat_lon_dict

    event_list = []
    location_list = []
    event_time_list = []
    description_list = []

    file_path = Path("data") / f"locations.csv"
    location_data = pd.read_csv(file_path)
    location_id = location_data["location_id"]
    latitude = location_data["latitude"]
    longitude = location_data["longitude"]

    for loc_id, lat, lon in zip(location_id, latitude, longitude):
        if pd.notnull(loc_id):
            location_lat_lon_dict[loc_id]["lat"] = lat
            location_lat_lon_dict[loc_id]["lon"] = lon

    for i in range(1, 25):
        file_path = Path("data") / f"events_{i}.csv"
        event_data = pd.read_csv(file_path)

        event_list.extend(event_data["event_id"])
        location_list.extend(event_data["location_id"])
        event_time_list.extend(event_data["time"])
        description_list.extend(event_data["fee_price"])

    for event_id, loc_id, evt_time, desc in zip(event_list, location_list, event_time_list, description_list):
        event_id_str = str(event_id)
        group_id = event_groups_dict.get(event_id_str)

        if not group_id:
            continue

        city = groups_city_dict.get(group_id)
        if not city:
            continue

        city_dict = events_info_dict[city][event_id_str]
        city_dict["time"] = int(evt_time)
        
        if pd.isnull(desc):
            city_dict["description"] = ""
        else:
            city_dict["description"] = str(desc)
        
        if pd.isnull(loc_id):
            city_dict["lat"] = default_loc[city]["lat"]
            city_dict["lon"] = default_loc[city]["lon"]
        else:
            city_dict["lat"] = float(location_lat_lon_dict[loc_id]["lat"])
            city_dict["lon"] = float(location_lat_lon_dict[loc_id]["lon"])

    for city, city_event_data in events_info_dict.items():
        city_dir = Path("data/json_data") / f"L{city}"
        city_dir.mkdir(parents=True, exist_ok=True)
        output_path = city_dir / "events_info.json"
        create_json_file(city_event_data, output_path)


if __name__ == "__main__":
    logging.info("------------------ Start Local Crawler ------------------")
    main()
    logging.info("------------------ End Local Crawler ------------------")