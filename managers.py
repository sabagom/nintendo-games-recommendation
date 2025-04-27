import pymongo
import bcrypt
import ast
import pandas as pd
import random
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class LoginManager:

    def __init__(self) -> None:
        # MongoDB connection
        self.client = pymongo.MongoClient("mongodb://localhost:27017/")
        self.db = self.client["project"]
        self.collection = self.db["users"]
    #    self.salt = b"$2b$12$ezgTynDsK3pzF8SStLuAPO"  # TODO: if not working, generate a new salt
        self.salt = b"$2a$12$YR4kY/E6UvzBIyFdC3U8Ku"
    def register_user(self, username: str, password: str) -> None:
        if not username or not password :
            raise ValueError("Username and password are required.")
        if len(username) < 3 or len(password) < 3:
            raise ValueError("Username and password must be at least 3 characters.")
        if self.collection.find_one({"username": username}):
            raise ValueError(f"User already exists: {username}.")
        
        hashedPassword = bcrypt.hashpw(password,self.salt.decode('utf-8'))
        new_object = {"username":username, "password": hashedPassword, "rented_games":[]}
        self.collection.insert_one(new_object)

    def login_user(self, username: str, password: str) -> object:
        hashedPassword = bcrypt.hashpw(password,self.salt.decode('utf-8'))
        user = self.collection.find_one({"username": username, "password": hashedPassword})
        if not user:
            raise ValueError(f"Invalid username or password")
        else:
            print(f"Logged in successfully as: {username}")
            return user



class DBManager:

    def __init__(self) -> None:
        # MongoDB connection
        self.client = pymongo.MongoClient("mongodb://localhost:27017/")
        self.db = self.client["project"]
        self.user_collection = self.db["users"]
        self.game_collection = self.db["games"]

    def load_csv(self) -> None:

        df = pd.read_csv("NintendoGames.csv", encoding="utf-8")
        df["genres"] = df["genres"].apply(ast.literal_eval)
        df["is_rented"] = False
        #Add games
        records = df.to_dict(orient="records")
        for record in records:
            self.game_collection.update_one(
                {"title": record["title"]},
                {"$set": record},
                upsert=True
            )

    def recommend_games_by_genre(self, user: dict) -> str:
        user_document = self.user_collection.find_one({'_id': user['_id']})
        if user_document and 'rented_games' in user_document:
            rented_games = user_document['rented_games']
        if not rented_games:
            return "No games rented"
        genre_counts = {}
        for game in rented_games:
            genres = game["genres"]
            for genre in genres:
                genre_counts[genre] = genre_counts.get(genre, 0) + 1
        chosen_genre = random.choices(list(genre_counts.keys()), weights=genre_counts.values())[0]
        rented_game_titles = [game['title'] for game in rented_games]
        recommended_games = self.game_collection.find({"genres": chosen_genre, "title": {"$nin": rented_game_titles}}).limit(5)
        return "\n".join(game["title"] for game in recommended_games)

    def recommend_games_by_name(self, user: dict) -> str:
        user_document = self.user_collection.find_one({'_id': user['_id']})
        if user_document and 'rented_games' in user_document:
            rented_games = user_document['rented_games']
        if not rented_games:
            return "No games rented"
        # Extract titles of games rented by the user
        rented_titles = [game['title'] for game in rented_games]
        chosen_game = random.choice(rented_games)
        chosen_title = chosen_game["title"]
        all_titles = [game['title'] for game in self.game_collection.find()]
        all_titles.append(chosen_title)
        # Filter out titles that are in the user's rented games list
        filtered_titles = [title for title in all_titles if title not in rented_titles]
        filtered_titles.append(chosen_title)
        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform(filtered_titles)
        chosen_index = filtered_titles.index(chosen_title)
        chosen_vector = tfidf_matrix[chosen_index]
        cosine_similarities = cosine_similarity(chosen_vector, tfidf_matrix).flatten()
        related_indices = cosine_similarities.argsort()[:-7:-1]
        recommended_titles = [filtered_titles[idx] for idx in related_indices if idx != chosen_index]
        return "\n".join(recommended_titles)

    def rent_game(self, user: dict, game_title: str) -> str:
        game = self.game_collection.find_one({"title": game_title}) 
        if not game:
            return f"{game_title} not found"
        if not game.get("is_rented", False):
            self.game_collection.update_one({"title": game_title}, {"$set": {"is_rented": True}})
            self.user_collection.update_one({'_id': user['_id']}, {'$addToSet': {'rented_games': game}})
            return f"{game_title} rented successfully"
        return f"{game_title} is already rented"

    def return_game(self, user: dict, game_title: str) -> str:
        user_document = self.user_collection.find_one({'_id': user['_id']})
        if user_document and 'rented_games' in user_document:
            rented_games = user_document['rented_games']
        for game in rented_games:
            if game.get("title") == game_title:
                self.game_collection.update_one({"title": game_title}, {"$set": {"is_rented": False}})
                self.user_collection.update_one({'_id': user['_id']}, {'$pull': {'rented_games': {'title': game_title}}})
                return f"{game_title} returned successfully"
        return f"{game_title} was not rented by you"
