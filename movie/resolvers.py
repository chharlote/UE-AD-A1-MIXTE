import json
from graphql import GraphQLError


def movies(_, info):
    with open('{}/data/movies.json'.format("."), "r") as file:
        movies = json.load(file)
        return movies['movies']


def movie_with_id(_,info,_id):
    with open('{}/data/movies.json'.format("."), "r") as file:
        movies = json.load(file)
        for movie in movies['movies']:
            if movie['id'] == _id:
                return movie
        raise GraphQLError(f"No movie with id '{_id}'.")


# def update_movie_rate(_, info, _id, _rate):
#     with open("./data/movies.json", "r") as rfile:
#         movies = json.load(rfile)
#
#     for movie in movies["movies"]:
#         if movie["id"] == _id:
#             movie["rating"] = _rate
#
#             with open("./data/movies.json", "w") as wfile:
#                 json.dump(movies, wfile)
#
#             return movie
#
#     raise GraphQLError(f"No movie with id '{_id}'.")

def update_movie(_, info, _id, _title=None, _director=None, _rating=None):
    updates = {}
    if _title is not None:
        updates["title"] = _title
    if _director is not None:
        updates["director"] = _director
    if _rating is not None:
        updates["rating"] = _rating

    if not updates:
        raise GraphQLError("At least one movie attribute must be provided.")

    with open("./data/movies.json", "r") as rfile:
        movies = json.load(rfile)

    for movie in movies["movies"]:
        if movie["id"] == _id:
            movie.update(updates)

            with open("./data/movies.json", "w") as wfile:
                json.dump(movies, wfile)

            return movie

    raise GraphQLError(f"No movie with id '{_id}'.")

def resolve_actors_in_movie(movie, info):
    with open('{}/data/actors.json'.format("."), "r") as file:
        actors = json.load(file)
        result = [actor for actor in actors['actors'] if movie['id'] in actor['films']]
        return result

def create_movie(_, info, _id, _title, _director, _rating):
    newmovies = {}
    newmovie = {}
    with open('{}/data/movies.json'.format("."), "r") as rfile:
        movies = json.load(rfile)
        for id in movies['movies']:
            if id['id'] == _id:
                raise GraphQLError(f"The movie with id '{_id}' already exists.")
        newmovie = {
            "id": _id,
            "title": _title,
            "director": _director,
            "rating": _rating
        }
        movies['movies'].append(newmovie)
        newmovies = movies
    with open('{}/data/movies.json'.format("."), "w") as wfile:
        json.dump(newmovies, wfile)
    return newmovie

def delete_movie(_, info, _id):
    with open("./data/movies.json", "r") as rfile:
        movies = json.load(rfile)

    for movie in movies["movies"]:
        if movie["id"] == _id:
            movies["movies"].remove(movie)

            with open("./data/movies.json", "w") as wfile:
                json.dump(movies, wfile)

            return movie

    raise GraphQLError(f"No movie with id '{_id}'.")