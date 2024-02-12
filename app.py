from flask import Flask, jsonify, request, session
from flask_pymongo import PyMongo
from flask_pymongo import ObjectId
from flask_socketio import SocketIO, join_room, leave_room, send

app = Flask(__name__)
app.config["MONGO_URI"] = "mongodb+srv://shreynagda:shrey0308@cluster0.zxdkj5v.mongodb.net/quiz?retryWrites=true&w=majority"
mongo = PyMongo(app)
# app.config['SECRET_KEY'] = 'varad'
socketio = SocketIO(app, cors_allowed_origins="*")

db = mongo.db

#Home Route
@app.route("/", methods=['GET'])
def home():
    return jsonify("Database connected!")

#Rooms GET 
@app.route("/api/rooms", methods=['GET'])
def get_room():
    temp_list=[]
    for item in db.rooms.find():
        item['_id'] = str(item['_id'])
        temp_list.append(item)
    return jsonify(temp_list)

#Rooms Create POST
@app.route("/api/rooms", methods=['POST'])
def post_rooms():
    room_code = request.json["room_code"]
    room_name = request.json["room_name"]
    print(db.rooms.find())
    if len(list(db.rooms.find({"room_code": room_code, "room_name": room_name}))) <= 0:
        _id = db.rooms.insert_one(request.json)
        return jsonify({'id' : str(_id.inserted_id)})
    else:
        return jsonify("The room name or code is in use, try another one")

#Rooms Update PUT
@app.route("/api/rooms", methods=['PUT'])
def put_rooms():
    # _id = request.json['_id']
    _id = request.json['_id']
    del request.json["_id"]
    data = request.json
    print(data)
    db.rooms.find_one_and_update({'_id': ObjectId(_id)}, {'$set': data})
    return jsonify("update")

#Rooms DELETE
@app.route("/api/rooms", methods=['DELETE'])
def del_rooms():
    return jsonify("")

#Scores inside a room
@app.route("/api/rooms/scores/<room_code>", methods=['GET'])
def get_scores(room_code):
    score_data = []
    players = db.rooms.find_one({"room_code": room_code})['players']
    print(players)
    if len(players) > 0:
        for i in players:
            score_data.append({
                'id': i['id'],
                'score': i['score']
            })
        return jsonify(score_data)
    else:
        jsonify("Invalid room code")


#Player joining a room
@app.route("/api/rooms/join", methods=['PUT'])
def addPlayer():
    room_code = request.json['room_code']
    player = request.json['player']
    players = db.rooms.find_one({"room_code": room_code})['players']
    max_players = db.rooms.find_one({"room_code": room_code})['max_players']
    if(len(players) + 1 >= max_players):
        return jsonify("Maximum players reached")
    player['id'] = str(len(players)+1)
    for i in players:
        if i['name'] == player['name']:
            return jsonify("Player name already in use! Try Another")
    players.append(player)
    db.rooms.find_one_and_update({"room_code": room_code}, {'$set':{"players": players}})
    socketio.emit("join", {"name": player['name'], "room_code": room_code})
    return jsonify({"players": players})
#Update Score
@app.route("/api/game/score", methods=['POST'])
def updateScore():
    return jsonify()

#Checking Answer and update score
@app.route("/api/game/answer", methods=['POST'])
def checkAnswer():
    option = request.json["option"]
    player_id = request.json["id"]
    room_code = request.json["room_code"]
    question_index = request.json['index']
    player_index = 0
    room = dict(db.rooms.find_one({"room_code": room_code}))
    questions = room["questions"]
    players = room["players"]
    player = None
    for i in players:
        if i['id'] == player_id:
            player_index = players.index(i)
            player = i
    if(questions[question_index]['correct_option'] == option):
        player['score'] = player['score'] + 1
        players[player_index] = player
        db.rooms.find_one_and_update({"room_code": room_code}, {'$set': {"players": players}})
    return jsonify("Scores updated!")

@socketio.on("connect")
def connect():
    print("Client connected!")

@socketio.on("mycustom")
def mycustom(data):
    print(data)

@socketio.on("join")
def on_join(data):
    room_code = data['room_code']
    name = data['name']
    join_room(room_code)
    send(f"{name} has entered the room {room_code}", to=room_code)
    print(f"{name} has entered the room {room_code}")


#Driver Code    
if __name__ == "__main__":
    socketio.run(app, debug=True, port=5001)
