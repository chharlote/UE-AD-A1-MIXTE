from ariadne import graphql_sync, make_executable_schema, load_schema_from_path, ObjectType, QueryType, MutationType
from flask import Flask, request, jsonify, make_response
from pathlib import Path
from ..utils import sigterm  # handle sigterm signal

from . import resolvers as r

PORT = 3201
HOST = '0.0.0.0'

app = Flask(__name__)
BASE_DIR = Path(__file__).resolve().parent

type_defs = load_schema_from_path(BASE_DIR / 'booking.graphql')
query = QueryType()
mutation = MutationType()
user_booking = ObjectType('UserBooking')
booking_date = ObjectType('BookingDate')

query.set_field('bookings', r.bookings)

mutation.set_field('add_booking', r.add_booking)
mutation.set_field('delete_booking', r.delete_booking)
mutation.set_field('delete_user_bookings', r.delete_user_bookings)

schema = make_executable_schema(type_defs, query, mutation, user_booking, booking_date)


@app.route("/", methods=['GET'])
def home():
    return make_response("<h1 style='color:blue'>Welcome to the Booking service!</h1>", 200)


@app.route('/graphql', methods=['POST'])
def graphql_server():
    data = request.get_json()
    success, result = graphql_sync(
        schema,
        data,
        context_value=request,
        debug=app.debug
    )
    status_code = 200 if success else 400
    return jsonify(result), status_code


if __name__ == "__main__":
    print("Server running in port %s" % (PORT))
    app.run(host=HOST, port=PORT)