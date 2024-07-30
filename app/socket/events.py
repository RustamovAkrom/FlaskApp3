from flask_socketio import emit
from app import socketio


@socketio.on("message")
def handle_message(data):
    emit("response", {"data": "Message receved"})