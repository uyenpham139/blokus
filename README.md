# Installation
```
pip install numpy
```

# How to play
## PvP Mode
This mode requires 4 players connected to the same LAN network (e.g., connected to the same Wi-Fi). One player will be the Host, and the other three are Guests.

1. For the Host (Player 1)

Follow these steps in order:

**Step 1: Find Your IP Address**

- Open a terminal or Command Prompt.

- Run the command: `ipconfig`

- Look for your IPv4 Address. It will look something like 192.168.88.150.

- Give this IP address to the 3 other players. They will need it to connect.

**Step 2: Start the Server**

- In the same terminal (or a new one), run:

	```bash
	python server.py
	```
- Keep this terminal open. It is the game server.

**Step 3: Start Your Game**

- Open a new, separate terminal.

- Run the game client:

	```bash
	python blokus.py
	```
- When the panel pops up, type `127.0.0.1` into the "Server IP" input. (This tells your game client to connect to the server running on your own machine).

- Wait for the other players to join.

2. For the Other Players (Guests 2, 3, & 4)

- Make sure you are on the same LAN/Wi-Fi as the Host.

- Get the Host's IPv4 address (e.g., 192.168.88.150) from them.

- Open a terminal and run the game:

	```bash
	python blokus.py
	```

- Click the "4 Player (Online)" button.

- In the "Connect to Server" panel, type the Host's IP address (the one they gave you).

- Click "Connect" to join the lobby.
