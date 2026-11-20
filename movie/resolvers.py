import json
import uuid
from pathlib import Path
from graphql import GraphQLError


BASE_DIR = Path(__file__).resolve().parent
MOVIES_FILE = BASE_DIR / "data" / "movies.json"
ACTORS_FILE = BASE_DIR / "data" / "actors.json"

def read_movies():
    with MOVIES_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def write_movies(data):
    with MOVIES_FILE.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False)



def movies(_, info, _director=None, _title=None, _min_rating=None):
    result = read_movies()["movies"]

    if _director:
        result = [
            movie for movie in result
            if _director.lower() in movie["director"].lower()
        ]

    if _title:
        result = [
            movie for movie in result
            if _title.lower() in movie["title"].lower()
        ]

    if _min_rating is not None:
        result = [
            movie for movie in result
            if float(movie["rating"]) >= float(_min_rating)
        ]

    return result

def movie_with_id(_, info, _id):
    for movie in read_movies()["movies"]:
        if str(movie["id"]) == str(_id):
            return movie

    raise GraphQLError(f"No movie with id '{_id}'.")

def create_movie(_, info, _title, _director, _rating):
    data = read_movies()

    if not _title:
        raise GraphQLError("Missing title.")
    if not _director:
        raise GraphQLError("Missing director.")
    if _rating is None:
        raise GraphQLError("Missing rating.")

    new_id = str(uuid.uuid4())

    new_movie = {
            "id": new_id,
            "title": _title,
            "director": _director,
            "rating": _rating
        }

    data["movies"].append(new_movie)
    write_movies(data)
    return new_movie


def update_movie(_, info, _id, _title=None, _director=None, _rating=None):
    data = read_movies()
    updates = {}
    if _title is not None:
        updates["title"] = _title
    if _director is not None:
        updates["director"] = _director
    if _rating is not None:
        updates["rating"] = _rating

    if not updates:
        raise GraphQLError("At least one movie attribute must be provided.")

    for movie in data["movies"]:
        if movie["id"] == _id:
            movie.update(updates)
            write_movies(data)
            return movie

    raise GraphQLError(f"No movie with id '{_id}'.")


def delete_movie(_, info, _id):
    data = read_movies()

    for movie in data["movies"]:
        if movie["id"] == _id:
            data["movies"].remove(movie)
            write_movies(data)
            return movie
    raise GraphQLError(f"No movie with id '{_id}'.")

def resolve_actors_in_movie(movie, info):
    with open('{}/data/actors.json'.format("."), "r") as file:
        actors = json.load(file)
        result = [actor for actor in actors['actors'] if movie['id'] in actor['films']]
        return result
