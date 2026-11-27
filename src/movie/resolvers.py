import json
import uuid
from pathlib import Path
from graphql import GraphQLError
from pymongo import MongoClient, ReturnDocument
from ..utils.jwt import token_required


BASE_DIR = Path(__file__).resolve().parent
MOVIES_FILE = BASE_DIR / "databases" / "movies.json"
ACTORS_FILE = BASE_DIR / "databases" / "actors.json"

client = MongoClient("mongodb://root:example@mongo:27017/")
db = client["movies"]
movies_collection = db["movies"]
actors_collection = db["actors"]

if movies_collection.count_documents({}) == 0:
    with open(MOVIES_FILE, "r") as jsf:
        movies_data = json.load(jsf)["movies"]
        movies_collection.insert_many(movies_data)

if actors_collection.count_documents({}) == 0:
    with open(ACTORS_FILE, "r") as jsf:
        actors_data = json.load(jsf)["actors"]
        actors_collection.insert_many(actors_data)


@token_required()
def movies(_, info, _id=None, _title=None, _director=None, _min_rating=None):
    query = {}

    if _id is not None:
        query["id"] = str(_id)

    if _title is not None:
        query["title"] = {"$regex": str(_title), "$options": "i"}

    if _director is not None:
        query["director"] = str(_director)

    if _min_rating is not None:
        query["rating"] = {"$gt": float(_min_rating)}

    return list(movies_collection.find(query, {"_id": 0}))


@token_required()
def movie_with_id(_, info, _id):
    movie = movies_collection.find_one({"id": str(_id)}, {"_id": 0})
    if movie is None:
        raise Exception("Movie ID not found")
    return movie


@token_required(admin_req=True)
def create_movie(_, info, _title, _director, _rating):

    if not _title:
        raise GraphQLError("Missing title.")
    if not _director:
        raise GraphQLError("Missing director.")
    if _rating is None:
        raise GraphQLError("Missing rating.")
    if not isinstance(_rating, (int, float)) or not (0 <= _rating <= 10):
        raise GraphQLError("Rating must be a number between 0 and 10.")

    new_id = str(uuid.uuid4())

    new_movie = {
        "id": new_id,
        "title": _title,
        "director": _director,
        "rating": _rating
    }
    movies_collection.insert_one(new_movie.copy())

    return new_movie


@token_required(admin_req=True)
def update_movie(_, info, _id, _title=None, _director=None, _rating=None):
    updates = {}
    if _title is not None:
        updates["title"] = str(_title)
    if _director is not None:
        updates["director"] = str(_director)
    if _rating is not None:
        updates["rating"] = float(_rating)

    if not updates:
        raise GraphQLError("At least one movie attribute must be provided.")

    updated_movie = movies_collection.find_one_and_update(
        {"id": str(_id)},
        {"$set": updates},
        projection={"_id": 0},
        return_document=ReturnDocument.AFTER
    )

    if updated_movie is None:
        raise Exception(f"No movie with id '{_id}'.")

    return updated_movie


@token_required(admin_req=True)
def delete_movie(_, info, _id):
    movie = movies_collection.find_one({"id": str(_id)}, {"_id": 0})
    if movie:
        movies_collection.delete_one({"id": str(_id)})
    else:
        raise Exception(f"No movie with id '{_id}'.")
    return movie


def resolve_actors_in_movie(movie, info):
    with open(ACTORS_FILE.format("."), "r") as file:
        actors = json.load(file)
        result = [actor for actor in actors['actors'] if movie['id'] in actor['films']]
        return result
