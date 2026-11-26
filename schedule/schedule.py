from flask import Flask, render_template, request, jsonify, make_response, send_from_directory
import json
import requests
from jwt import token_required
from flask_swagger_ui import get_swaggerui_blueprint
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport
from gql.transport.exceptions import TransportQueryError, TransportServerError
from pymongo import MongoClient, ReturnDocument

app = Flask(__name__)

PORT = 3202
HOST = '0.0.0.0'
MOVIE_GRAPHQL_URL ="http://movie:3001/graphql"

# SWAGGER
SWAGGER_URL = "/docs"
API_URL = "/openapi.yaml"

swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={"app_name": "Schedule Service API"}
)
app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

# MONGODB
client = MongoClient("mongodb://root:example@mongo:27017/")
db = client["schedule"]
schedule_collection = db["schedule"]

if schedule_collection.count_documents({}) == 0:
    with open('./databases/times.json', "r") as jsf:
        schedule_data = json.load(jsf)["schedule"]
        schedule_collection.insert_many(schedule_data)


def verify_movie(movie_id: str) -> tuple[bool, int, str]:
    authorization = request.headers.get("Authorization")
    headers = {"Content-Type": "application/json"}
    if authorization:
        headers["Authorization"] = authorization

    transport = RequestsHTTPTransport(
        url=MOVIE_GRAPHQL_URL,
        headers=headers,
        use_json=True,
        timeout=10,
    )
    client = Client(transport=transport)

    query = gql("""
        query GetMovieById($id: String!) {
            movie_with_id(_id: $id) {
                id
            }
        }
    """)

    try:
        result = client.execute(query, variable_values={"id": str(movie_id)})
        movie = result.get("movie_with_id")

        if movie is not None and movie.get("id"):
            return True, 200, ""

        return False, 404, "Movie not found"

    except TransportServerError as e:
        if e.code == 401:
            return False, 401, "Invalid or missing Authorization token"
        return False, e.code or 502, f"Movie service returned an error: {str(e)}"

    except TransportQueryError as e:
        return False, 400, f"GraphQL query error: {str(e)}"

    except requests.exceptions.RequestException as e:
        return False, 503, f"Movie service unavailable: {str(e)}"
@app.route("/", methods=['GET'])
def home():
   return "<h1 style='color:blue'>Welcome to the Showtime service!</h1>"

@app.route("/openapi.yaml", methods=["GET"])
def openapi_spec():
    return send_from_directory(".", "schedule.yaml", mimetype="application/yaml")


@app.route("/times", methods=['GET'])
@token_required()
def get_schedule():
    schedules = list(schedule_collection.find({}, {"_id": 0}))
    return make_response(jsonify(schedules), 200)

@app.route("/timesbydate", methods=['GET'])
@token_required()
def get_time_bydate():
    req = request.args
    if not req or "date" not in req:
        return make_response(jsonify({"error": "Missing date parameter"}), 400)

    schedule = schedule_collection.find_one({"date": req["date"]}, {"_id": 0})
    if not schedule:
        return make_response(jsonify({"error": "No schedule found for this date"}), 404)
    return make_response(jsonify(schedule), 200)

@app.route("/times/", methods=['POST'])
@token_required(admin_req=True)
def add_schedule():
    req = request.get_json()
    if not req:
        return make_response(jsonify({"error": "Invalid or missing JSON payload"}), 400)
    if not req["date"]:
        return make_response(jsonify({"error": "Missing date"}), 400)
    if not req["movies"]:
        return make_response(jsonify({"error": "Missing movies"}), 400)
    new_date = req['date']
    new_movies = req['movies']

    missing_movies = []
    for movie_id in new_movies:
        is_valid, status_code, error_message = verify_movie(movie_id)
        if not is_valid:
            missing_movies.append(movie_id)

    if missing_movies:
        return make_response(jsonify({"error": "The following movies are not found", "movies": missing_movies}), 404)

    if schedule_collection.find_one({"date": new_date}):
        return make_response(jsonify({"error": "This date already exists"}), 409)

    new_schedule = {
        "date": new_date,
        "movies": new_movies
    }
    schedule_collection.insert_one(new_schedule)
    return make_response(
        jsonify({
            "message": "Schedule added",
            "schedule": {"date": new_date, "movies": new_movies}
        }),
        201
    )

@app.route('/times/<date>/movies', methods=['POST'])
@token_required(admin_req=True)
def add_movie_to_schedule(date):
    data = request.get_json()
    if not data or 'movies' not in data:
        return make_response(jsonify({"error": "No movies provided"}), 400)

    new_movies = data['movies']
    target_schedule = schedule_collection.find_one({"date": str(date)}, {"_id": 0})
    if not target_schedule:
        return make_response(jsonify({"error": "Date not found"}), 404)

    missing_movies = []
    for movie_id in new_movies:
        is_valid, status_code, error_message = verify_movie(movie_id)
        if not is_valid:
            missing_movies.append(movie_id)
    if missing_movies:
        return make_response(jsonify({"error": "The following movies are not found", "movies": missing_movies}), 404)


    already_existing_movies = []
    for movie_id in new_movies:
        if movie_id in target_schedule["movies"]:
            already_existing_movies.append(movie_id)
    if already_existing_movies:
        return make_response(
            jsonify({
                "error": "The following movies are already scheduled for this date",
                "movies": already_existing_movies
            }),
            409
        )

    updated_schedule = schedule_collection.find_one_and_update(
        {"date": str(date)},
        {"$push": {"movies": {"$each": new_movies}}},
        projection={"_id": 0},
        return_document=ReturnDocument.AFTER
    )

    return make_response(
        jsonify({
            "message": "Movies added successfully",
            "schedule": updated_schedule
        }),
        200
    )

@app.route('/times/<date>/<movie_id>', methods=['DELETE'])
@token_required(admin_req=True)
def delete_movie_from_schedule(date, movie_id):
    target_schedule = schedule_collection.find_one({"date": str(date)}, {"_id": 0})
    if not target_schedule:
        return make_response(jsonify({"error": "Date not found"}), 404)

    if movie_id not in target_schedule["movies"]:
        return make_response(
            jsonify({
                "message": "The movie is not scheduled for this date",
                "movie_id": movie_id
            }),
            404
        )
    updated_schedule = schedule_collection.find_one_and_update(
        {"date": str(date)},
        {"$pull": {"movies": movie_id}},
        projection={"_id": 0},
        return_document=ReturnDocument.AFTER
    )

    return make_response(
        jsonify({
            "message": "Movie deleted successfully",
            "movie_id_deleted": movie_id,
            "new_schedule": updated_schedule
        }),
        200
    )

@app.route('/times/<date>', methods=['DELETE'])
@token_required(admin_req=True)
def delete_schedule(date):
    result = schedule_collection.delete_one({"date": str(date)})
    if result.deleted_count == 0:
        return make_response(jsonify({"error": "Schedule not found"}), 404)

    return make_response(
        jsonify({
            "message": "Schedule deleted successfully",
            "date": date,
        }),
        200
    )



if __name__ == "__main__":
   print("Server running in port %s"%(PORT))
   app.run(host=HOST, port=PORT)
