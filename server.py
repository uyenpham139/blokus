import socket
import threading
import pickle
import struct
import constants
import time

HOST = '0.0.0.0'
PORT = constants.DEFAULT_PORT

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

server.settimeout(1.0)

server.bind((HOST, PORT))
server.listen()

print(f"Lobby Server started on {HOST}:{PORT}...")

# --- New Server Structure ---
client_connections = {} # {conn: {"client_id": int, "room_id": int}}
rooms = {} # {room_id: GameRoom object}
next_client_id = 1
next_room_id = 1

class GameRoom:
    """ Manages a single game room and its state """
    def __init__(self, name, host_conn, host_id, room_id):
        self.id = room_id
        self.name = name
        self.status = "WAITING" # WAITING, PLAYING
        self.max_players = 4
        
        self.clients = {host_id: host_conn} # {client_id: conn}
        self.player_info = {
            host_id: {"name": f"Player {host_id}", "is_ready": False, "is_host": True}
        }
        
        # Game state moves inside the room
        self.game_state = {
            "board": None, # Will be set on game start
            "turn": 1,
            "last_move": None
        }

    def add_player(self, conn, client_id):
        if len(self.clients) >= self.max_players:
            return False # Room is full
            
        self.clients[client_id] = conn
        self.player_info[client_id] = {"name": f"Player {client_id}", "is_ready": False, "is_host": False}
        return True

    def remove_player(self, client_id):
        if client_id in self.clients:
            del self.clients[client_id]
        if client_id in self.player_info:
            del self.player_info[client_id]
        
        # If host leaves, all players must leave
        if not self.player_info or all(not p['is_host'] for p in self.player_info.values()):
            return "DISBAND" # Signal to disband room
        
        return "OK"

    def set_player_ready(self, client_id, is_ready):
        if client_id in self.player_info:
            self.player_info[client_id]["is_ready"] = is_ready

    def get_info(self):
        """ Returns serializable info for the lobby """
        return {
            "id": self.id,
            "name": self.name,
            "player_count": len(self.clients),
            "max_players": self.max_players,
            "status": self.status,
            "players": self.player_info
        }

    def all_ready(self):
        if len(self.player_info) < self.max_players: # Wait for 4 players
             return False
        return all(p["is_ready"] for p in self.player_info.values())

    def broadcast(self, data):
        """ Send data to ALL clients in this room """
        for conn in list(self.clients.values()): 
            send_data(conn, data)

# --- Helper Functions ---
def send_data(conn, data):
    """ Helper to send pickled data with length header """
    try:
        msg = pickle.dumps(data)
        packed_msg = struct.pack('>I', len(msg)) + msg
        conn.sendall(packed_msg)
    except Exception as e:
        print(f"[Send Error] {e}")

def get_room_list():
    """ Returns a list of all waiting rooms """
    room_list = []
    for room in rooms.values():
        if room.status == "WAITING":
            room_list.append({
                "id": room.id,
                "name": room.name,
                "player_count": len(room.clients),
                "max_players": room.max_players
            })
    return room_list

def handle_client(conn, client_id):
    global rooms, next_room_id
    client_room_id = None
    
    try:
        while True:
            raw_msglen = conn.recv(4)
            if not raw_msglen: break
            msglen = struct.unpack('>I', raw_msglen)[0]
            
            data = b''
            while len(data) < msglen:
                packet = conn.recv(msglen - len(data))
                if not packet: break
                data += packet
            
            if not data: break
            
            payload = pickle.loads(data)
            action = payload.get("action")

            if action == "get_room_list":
                send_data(conn, {"action": "room_list", "rooms": get_room_list()})
            
            elif action == "create_room":
                room_name = payload.get("name", f"Room {next_room_id}")
                new_room = GameRoom(room_name, conn, client_id, next_room_id)
                rooms[next_room_id] = new_room
                client_connections[conn]["room_id"] = next_room_id
                client_room_id = next_room_id
                next_room_id += 1
                
                print(f"Client {client_id} created room '{room_name}' (ID: {new_room.id})")
                send_data(conn, {"action": "room_joined", "room_info": new_room.get_info()})

            elif action == "join_room":
                room_id = payload.get("room_id")
                if room_id in rooms and rooms[room_id].status == "WAITING":
                    room = rooms[room_id]
                    if room.add_player(conn, client_id):
                        client_connections[conn]["room_id"] = room_id
                        client_room_id = room_id
                        print(f"Client {client_id} joined room ID: {room_id}")
                        # Send confirmation to new player
                        send_data(conn, {"action": "room_joined", "room_info": room.get_info()})
                        # Broadcast update to everyone else
                        room.broadcast({"action": "room_update", "room_info": room.get_info()})
                    else:
                        send_data(conn, {"action": "error", "message": "Room is full or in-game."})
                else:
                    send_data(conn, {"action": "error", "message": "Room not found."})

            elif action == "set_ready":
                if client_room_id and client_room_id in rooms:
                    room = rooms[client_room_id]
                    room.set_player_ready(client_id, payload.get("is_ready", False))
                    room.broadcast({"action": "room_update", "room_info": room.get_info()})

            elif action == "start_game":
                if client_room_id and client_room_id in rooms:
                    room = rooms[client_room_id]
                    if room.player_info[client_id]["is_host"] and room.all_ready():
                        print(f"Starting game for room {room.id}")
                        room.status = "PLAYING"
                        # Broadcast start signal
                        room.broadcast({"action": "game_start", "game_state": room.game_state})
                    else:
                        send_data(conn, {"action": "error", "message": "You are not host or not all players are ready."})
            
            elif action == "game_move":
                if client_room_id and client_room_id in rooms:
                    room = rooms[client_room_id]
                    if room.status == "PLAYING":
                        room.broadcast({"action": "game_move_broadcast", "move_data": payload.get("move_data")})

    except Exception as e:
        print(f"Client {client_id} Error: {e}")
    
    # --- Client Disconnect Cleanup ---
    print(f"Client {client_id} disconnected.")
    if conn in client_connections:
        client_room_id = client_connections[conn].get("room_id")
        if client_room_id and client_room_id in rooms:
            room = rooms[client_room_id]
            result = room.remove_player(client_id)
            if result == "DISBAND" or len(room.clients) == 0:
                print(f"Disbanding room {room.id} (host left or empty)")
                room.broadcast({"action": "room_disbanded"})
                del rooms[client_room_id]
            else:
                room.broadcast({"action": "room_update", "room_info": room.get_info()})
        
        del client_connections[conn]
    conn.close()

# --- Main Accept Loop ---
try:
    while True:
        try:
            conn, addr = server.accept()
            print(f"New connection from: {addr}")
            
            client_connections[conn] = {"client_id": next_client_id, "room_id": None}
            send_data(conn, {"action": "assign_id", "client_id": next_client_id})
            
            thread = threading.Thread(target=handle_client, args=(conn, next_client_id))
            thread.start()
            
            next_client_id += 1
        except socket.timeout:
            continue
except KeyboardInterrupt:
    print("\nServer stopping...")
finally:
    server.close()
    print("Server closed.")