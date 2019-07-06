import json, urllib.parse, http.cookies
http.cookies._is_legal_key = lambda _: True
import requests as _requests
from pypresence import Presence
import time
from os import mkdir, path
from manifest import Manifest

BASE_ROUTE = "https://www.bungie.net/Platform"
ACTIVITY_LOOKUP = BASE_ROUTE + "/Destiny2/{0}/Profile/{1}/Character/{2}/?components=CharacterActivities"
CHARACTER_LOOKUP = BASE_ROUTE + "/Destiny2/{0}/Profile/{1}/?components=Characters"
MEMBERSHIP_ID_LOOKUP = BASE_ROUTE + "/Destiny2/SearchDestinyPlayer/{0}/{1}"

class Setup:
    def __init__(self):
        self.folder_filepath = "./siva_files/"
        self.make_folder()

    def make_folder(self):
        if not os.path.exists(self.folder_filepath):
            os.mkdir(self.folder_filepath)

class Config:
    def __init__(self):
        self.filepath = "./siva_files/config.json"

    def load(self):
        with open(self.filepath, "r") as out:
            config = json.load(out)
        return config

    def save(self, new_config):
        with open(self.filepath, "w+") as out:
            json.dump(new_config, out, indent=4)

class Decoder:
    def __init__(self, headers):
        self._manifest = Manifest(headers)

    def decode_hash(self, hash, definition, language):
        return self._manifest._decode_hash(hash, definition, language)

class Requests:
    def __init__(self, api_token=None):
        self.api_token = api_token
        self.headers = {"X-API-Key": self.api_token}

    def get(self, request):
        _data = _requests.get(urllib.parse.quote(request, safe=':/?&=,.'), headers=self.headers)
        self._requestData = _data.json()
        return self._requestData

def get_last_played_id(membershipType, membershipID, requests):
    url = CHARACTER_LOOKUP.format(membershipType, membershipID)
    character_data = requests.get(url)
    epoch_character_table = {}
    for key, attr in character_data["Response"]["characters"]["data"].items():
        epoch_character_table[convert_datestring_to_epoch(attr["dateLastPlayed"])] = key
    
    for epoch, id in epoch_character_table.items():
        if epoch == max(epoch_character_table.keys()):
            return id

def convert_datestring_to_epoch(datestring):
    datetime_string = datestring.replace("Z", "").replace("T", " ")
    target_timestamp = time.strptime(datetime_string, '%Y-%m-%d %H:%M:%S')
    mktime_epoch = time.mktime(target_timestamp)
    return mktime_epoch + 3382
    
def Main(packaged_data):
    Setup()

    client_id = '596381603522150421'
    RPC = Presence(client_id) 
    RPC.connect()

    Config().save(packaged_data)
    config = Config().load()

    platform_enum_conversion_table = {
        "Playstation": "2",
        "Xbox": "1",
        "BattleNet": "4"
    }

    requests = Requests(config["api_token"])
    decoder = Decoder(requests.headers)

    user_membership_type = platform_enum_conversion_table[config["platform"]]
    user_membership_id = requests.get(MEMBERSHIP_ID_LOOKUP.format(user_membership_type, config["username"]))["Response"][0]["membershipId"]

    while True:
        activity_data = requests.get(
            ACTIVITY_LOOKUP.format(
                user_membership_type, 
                user_membership_id, 
                get_last_played_id(
                    user_membership_type, 
                    user_membership_id,
                    requests
                    )
                )
            )
        activity_hash = activity_data["Response"]["activities"]["data"]["currentActivityHash"]
        activity_data_decoded = decoder.decode_hash(activity_hash, "DestinyActivityDefinition", "en")

        mode_hash = activity_data["Response"]["activities"]["data"]["currentActivityModeHash"]
        mode_data = decoder.decode_hash(mode_hash, "DestinyActivityModeDefinition", "en")

        timer = convert_datestring_to_epoch(activity_data["Response"]["activities"]["data"]["dateActivityStarted"])

        # Default Arguments
        details, state = "In Orbit", "In Orbit"
        party_size = [1,1]
        picture, timer = "in_orbit", time.time()

        if mode_data != None:
            details = mode_data["displayProperties"]["name"]
            state = activity_data_decoded["displayProperties"].get("name", "In Orbit")
            picture = activity_data_decoded["displayProperties"]["name"].lower().replace(" ", "_")
            remove_list = [",", "(", ")"]
            for char in remove_list:
                picture = picture.replace(char, "")

            if activity_data_decoded["isPvP"]:
                details = "Crucible, " + mode_data["displayProperties"]["name"]
                picture = "crucible"

        swap_conversion_table = {
            "the_menagerie:_the_menagerie_heroic": "the_menagerie",
            "zero_hour_heroic": "zero_hour",
            "landing_zone": "mercury",
            "leviathan:_normal": "leviathan",
            "leviathan:_prestige": "leviathan",
            "the_reckoning:_tier_i": "the_reckoning",
            "the_reckoning:_tier_ii": "the_reckoning",
            "the_reckoning:_tier_iii": "the_reckoning",
            "last_wish:_level_55": "last_wish",
            "crown_of_sorrow:_normal": "crown_of_sorrows"
        }

        user_conversion_table = {
            "Last Wish: Level 55": "Last Wish",
            "The Menagerie: The Menagerie (Heroic)": "The Menagerie: (Heroic)",
            "Landing Zone": "Mercury"

        }

        RPC.update(
            state=user_conversion_table.get(state, state), details=details,
            large_image=swap_conversion_table.get(picture, picture),
            small_image="destiny2_logo", small_text="Destiny 2",
            start=timer
        )
        time.sleep(30)