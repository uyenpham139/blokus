import socket
import pickle
import struct
import select

class Network:
    def __init__(self, server_ip, port):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server = server_ip
        self.port = port
        self.client_id = None

    def connect(self):
        """ Connects to server and gets a unique client ID """
        try:
            self.client.connect((self.server, self.port))
            initial_data = self.receive_data(blocking=True)
            if initial_data and initial_data.get("action") == "assign_id":
                self.client_id = initial_data.get("client_id")
                return self.client_id
            else:
                print("Failed to get client ID from server.")
                return None
        except Exception as e:
            print(f"Connection failed: {e}")
            return None

    def get_client_id(self):
        return self.client_id

    def send(self, data):
        """ Sends data to the server (non-blocking) """
        try:
            msg = pickle.dumps(data)
            self.client.sendall(struct.pack('>I', len(msg)) + msg)
        except socket.error as e:
            print(f"Send failed: {e}")

    def receive_data(self, blocking=True):
        """
        Receives data from the server.
        Can be set to blocking (waits for data) or non-blocking (returns None if no data).
        """
        if not blocking:
            ready, _, _ = select.select([self.client], [], [], 0.01) # 10ms timeout
            if not ready:
                return None
        
        try:
            raw_msglen = self.recvall(4)
            if not raw_msglen:
                return None
            msglen = struct.unpack('>I', raw_msglen)[0]
            data = self.recvall(msglen)
            return pickle.loads(data)
        except BlockingIOError:
            return None
        except socket.error as e:
            print(f"Receive data error: {e}")
            return None

    def recvall(self, n):
        """ Helper function to receive n bytes or return None if EOF is hit """
        data = b''
        while len(data) < n:
            packet = self.client.recv(n - len(data))
            if not packet:
                return None
            data += packet
        return data

    def disconnect(self):
        try:
            self.client.close()
        except socket.error as e:
            print(e)