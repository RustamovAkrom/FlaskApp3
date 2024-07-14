from flask import Blueprint, jsonify
from flask_restful import Resource, Api


api_db = Blueprint("api", __name__)
api = Api(api_db)


class HelloWorld(Resource):
    def get(self):
        return jsonify({'message': "Hello, World!"})
    

api.add_resource(HelloWorld, "/api/v1/hello/")