# Blokus
A Python implementation of the Mattel game Blokus, featuring a menu system and a smart AI opponent.

## Features
- **Game Menu:** A full menu system to navigate the game.
- **Multiple Game Modes:**
    - **Player vs. AI:** Play against an artificial intelligence with selectable difficulty.
    - **Player vs. Player:** Hot-seat multiplayer for two people.
- **AI Opponent:**
    - The AI uses the **Alpha-Beta Pruning** algorithm to make strategic decisions.
    - **Two Difficulty Levels:**
        - **Easy:** The AI searches at a shallow depth (depth=1), making it faster but less challenging.
        - **Hard:** The AI searches deeper into the game tree (depth=2), providing a tougher challenge.
    - The AI's heuristic evaluates moves based on both the score and control of strategic corners on the board.
- **Save & Continue:** The game automatically saves after every turn. You can resume your last game from the main menu using the "Continue" button.

## Requirements
- Python 3.x
- Numpy
- Pygame

You can install the dependencies with pip:
```bash
pip install numpy pygame
```
*Note: An older version of the AI used TensorFlow. If you wish to experiment with the Reinforcement Learning AI, you will also need to install it (`pip install tensorflow`).*

## How to Run
1. Navigate to the root directory of the project.
2. Run the main script:
   ```bash
   python3 blokus.py
   ```
3. Use the menu to select a game mode and start playing.

## Game Rules
The official rules are included in `blokus-rules.pdf`. A summary is as follows:
1. Each player chooses a color.
2. The first piece played by each player must cover a corner square on the board.
3. Every subsequent piece played must touch at least one corner of one of the player's own pieces. Pieces of the same color can **only** touch at the corners.
4. Pieces of different colors can touch at any side or corner.
5. The game ends when no player can make another move.
6. Scoring is based on the number of squares on the pieces you *couldn't* place. The player with the highest score (fewest negative points) wins. A bonus is awarded for placing all pieces.