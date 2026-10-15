import requests
from pymongo import MongoClient


class LOLDatabase:
    def __init__(self, config) -> None:
        self.config = config
        self.myclient = MongoClient(
            self.config["host"],
            username=self.config["username"],
            password=self.config["password"],
        )
        self.loldb = self.myclient["lol_database"]
        self.user = self.loldb["users"]
        self.matches = self.loldb["matches"]
        if self.matches.find_one() is None:
            self.match_index = 0
        else:
            # get last index of match
            self.match_index = self.matches.find().sort("_id", -1)[0]["_id"] + 1
        print(self.match_index)
        if self.user.find_one() is None:
            self.user_index = 0
        else:
            # get last index of user
            self.user_index = self.user.find().sort("_id", -1)[0]["_id"] + 1
        print(self.user_index)

    def reset_user(self):
        # reset all win lost elo
        for user in self.user.find():
            self.user.update_one(
                {"_id": user["_id"]},
                {
                    "$set": {
                        "win": 0,
                        "lose": 0,
                        "total": 0,
                        "elo": 1000,
                    }
                },
            )

    def remove_all_match(self):
        self.matches.delete_many({})

    def get_user(self, name: str):
        return self.user.find_one({"name": name})

    def get_match(self, match_id: int):
        return self.matches.find_one({"match_id": match_id})

    def get_all_match(self):
        return self.matches.find()

    def get_last_match_index(self):
        return self.match_index - 1

    def get_all_user(self):
        # get all user from database and sort by elo
        user_list = []
        for user in self.user.find():
            user_list.append(user)
        user_list.sort(key=lambda x: x["elo"], reverse=True)
        return user_list

    def get_all_user_name(self):
        # get all user name
        user_list = []
        for user in self.user.find():
            user_list.append(user["name"])
        return user_list

    def add_user(self, name: str):
        if self.get_user(name) is None:
            self.user.insert_one(
                {
                    "_id": self.user_index,
                    "name": name,
                    "win": 0,
                    "lose": 0,
                    "total": 0,
                    "elo": 1000,
                }
            )
            self.user_index += 1
        return self.get_user(name)

    def update_user(self, name: str, win: int, lose: int, elo: int):
        user = self.get_user(name)
        self.user.update_one(
            {"_id": user["_id"]},
            {
                "$set": {
                    "win": win,
                    "lose": lose,
                    "total": win + lose,
                    "elo": elo,
                }
            },
        )

    def add_match(self, team1, team2, win):
        self.matches.insert_one(
            {
                "_id": self.match_index,
                "team1": team1,
                "team2": team2,
                "win": win,
            }
        )
        self.match_index += 1

    def delete_all_user(self):
        self.user.delete_many({})

    def remove_last_match(self):
        self.matches.delete_one({"_id": self.match_index - 1})


if __name__ == "__main__":
    db = LOLDatabase()
    print(db.matches.find().sort("_id", -1)[0]["_id"] + 1)
