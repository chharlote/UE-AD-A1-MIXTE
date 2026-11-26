import json
from pathlib import Path
import requests
from flask import g
from graphql import GraphQLError
from pymongo import MongoClient
from ..utils.jwt import token_required

BASE_DIR = Path(__file__).resolve().parent
BOOKINGS_FILE = BASE_DIR / "databases" / "bookings.json"

MOVIE_SERVICE_URL = "http://127.0.0.1:3001/graphql"
SCHEDULE_SERVICE_URL = "http://127.0.0.1:3202"

client = MongoClient("mongodb://root:example@mongo:27017/")
db = client["bookings"]
bookings_collection = db["bookings"]

if bookings_collection.count_documents({}) == 0:
    with open(BOOKINGS_FILE, "r") as jsf:
        bookings_data = json.load(jsf)["bookings"]
        if bookings_data:
            bookings_collection.insert_many(bookings_data)


def verify_movie(movie_id: str, auth_header: str | None) -> None:
    headers = {"Authorization": auth_header} if auth_header else {}
    query = """
    query($id: String!) {
        movie_with_id(_id: $id) {
            id
        }
    }
    """
    try:
        res = requests.post(
            MOVIE_SERVICE_URL,
            json={"query": query, "variables": {"id": movie_id}},
            headers=headers,
        )
        payload = res.json()
        if res.status_code != 200 or payload.get("errors") or not payload.get("data", {}).get("movie_with_id"):
            raise GraphQLError("Movie not found")
    except GraphQLError:
        raise
    except requests.exceptions.RequestException as e:
        raise GraphQLError(f"Movie service unavailable: {str(e)}")


def verify_schedule(date: str, movie_id: str) -> None:
    try:
        res = requests.get(f"{SCHEDULE_SERVICE_URL}/timesbydate", params={"date": date})
        if res.status_code != 200:
            raise GraphQLError("No schedule found for this date")
        schedule = res.json()
        if str(movie_id) not in [str(m) for m in schedule.get("movies", [])]:
            raise GraphQLError("Movie is not scheduled on this date")
    except GraphQLError:
        raise
    except requests.exceptions.RequestException as e:
        raise GraphQLError(f"Schedule service unavailable: {str(e)}")


@token_required()
def bookings(_, info):
    if g.admin:
        return list(bookings_collection.find({}, {"_id": 0}))

    user_b = bookings_collection.find_one({"userid": g.user_id}, {"_id": 0})
    if user_b:
        return [user_b]
    return [{"userid": g.user_id, "dates": []}]


@token_required()
def add_booking(_, info, _movie_id, _date):
    if not _movie_id:
        raise GraphQLError("Missing movie_id")
    if not _date:
        raise GraphQLError("Missing date")

    movie_id = str(_movie_id)
    date = str(_date)
    auth_header = info.context.headers.get("Authorization") if info.context else None

    verify_movie(movie_id, auth_header)
    verify_schedule(date, movie_id)

    user_b = bookings_collection.find_one({"userid": g.user_id})
    if user_b:
        for d in user_b.get("dates", []):
            if d["date"] == date:
                if movie_id in d["movies"]:
                    return {"message": "Already booked"}
                bookings_collection.update_one(
                    {"userid": g.user_id, "dates.date": date},
                    {"$push": {"dates.$.movies": movie_id}}
                )
                return {"message": "Booking added"}

        bookings_collection.update_one(
            {"userid": g.user_id},
            {"$push": {"dates": {"date": date, "movies": [movie_id]}}}
        )
        return {"message": "Booking added"}

    bookings_collection.insert_one({
        "userid": g.user_id,
        "dates": [{"date": date, "movies": [movie_id]}],
    })
    return {"message": "Booking added"}


@token_required()
def delete_booking(_, info, _movie_id, _date):
    if not _movie_id:
        raise GraphQLError("Missing movie_id")
    if not _date:
        raise GraphQLError("Missing date")

    movie_id = str(_movie_id)
    date = str(_date)

    user_b = bookings_collection.find_one({"userid": g.user_id})
    if not user_b:
        raise GraphQLError("No bookings found for this user")

    for d in user_b.get("dates", []):
        if d["date"] == date and movie_id in d["movies"]:
            bookings_collection.update_one(
                {"userid": g.user_id, "dates.date": date},
                {"$pull": {"dates.$.movies": movie_id}}
            )
            # Remove the date entry if no movies remain on that date
            bookings_collection.update_one(
                {"userid": g.user_id},
                {"$pull": {"dates": {"date": date, "movies": {"$size": 0}}}}
            )
            return {"message": "Booking deleted"}

    raise GraphQLError("Booking not found for this date or movie")


@token_required(admin_req=True)
def delete_user_bookings(_, info, _user_id):
    result = bookings_collection.delete_one({"userid": str(_user_id)})
    if result.deleted_count == 0:
        raise GraphQLError("No bookings found for this user")
    return {"message": f"All bookings deleted for user {_user_id}"}