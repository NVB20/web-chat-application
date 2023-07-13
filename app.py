from flask import Flask, session, request
from flask_socketio import SocketIO, join_room, send, leave_room  
from view import view
from room_manager import rooms, SCECRET_KEY
from mongo import insert_messages, delete_collection
from handle_time import time_now

app = Flask(__name__)
app.config["SECRET_KEY"] = SCECRET_KEY
socketio = SocketIO(app)
app.register_blueprint(view, url_perfix="")

# Dictionary to track client disconnections
disconnect_flags = {}


#save here messages in db
@socketio.on("message")
def message(data):
    room = session.get("room")
    
    if room not in rooms:
        return 
    
    content = {"name": session.get("name"), 
               "message": data["data"],
               "time": time_now()
               }
    send(content, to=room)
    rooms[room]["messages"].append(content)
    
    insert_messages(content, room)
    print(f"{session.get('name')} said: {data['data']}")


@socketio.on("connect") 
def connect(auth):
    room = session.get("room")
    name = session.get("name")
    
    if not room or not name:
        return
    if room not in rooms:
        leave_room(room)
        return
    
    join_room(room)
    send({"name": name, "message": "has enterd the room"}, to=room)
    rooms[room]["members"] += 1
    print(f"{name} joined room {room}")  


@socketio.on("disconnect")
def disconnect():
    room = session.get("room")
    name = session.get("name", False)
    
    print("socket emitted here")
    
    if room in rooms:
        rooms[room]['members'] -= 1
        if rooms[room]['members'] <= 0:
            del rooms[room]
            delete_collection(room)
            print("delted room from lists")
    
    send({"name": name, "message": "has left the room"}, to=room, name=name)
    print(f"{name} has left the room {room}")


if __name__ == "__main__":
    socketio.run(app=app, debug=True)
    
        
    