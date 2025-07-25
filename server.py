from flask import Flask, request, jsonify
from flask_cors import CORS
from mastergoalGame import MastergoalGame
from position import Position

app = Flask(__name__)

# Configure CORS properly
CORS(app, 
     origins=["https://mastergoal.onrender.com", "http://localhost:5173"],  # Add your frontend domains
     methods=["GET", "POST", "OPTIONS"],
     allow_headers=["Content-Type", "Authorization"])

# Global game instance
game = None

@app.route('/', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "message": "MasterGoal API is running"})

@app.route('/start_game', methods=['POST'])
def start_game():
    global game
    try:
        data = request.json
        level = data.get("level", 2)
        game = MastergoalGame(level=level)
        return jsonify({"message": "Game started", "state": game.get_game_state()})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/move', methods=['POST'])
def move():
    global game
    if game is None:
        return jsonify({"error": "Game not started"}), 400

    try:
        data = request.json
        move_type = data.get('type')
        from_row, from_col = data.get('from') # ALREADY RECEIVED CORRECTLY
        to_row, to_col = data.get('to') # ALREADY RECEIVED CORRECTLY

        from_pos = Position(from_row, from_col)
        to_pos = Position(to_row, to_col)

        if move_type == 'move':
            success = game.execute_move(from_pos, to_pos)
        elif move_type == 'kick':
            success = game.execute_kick(to_pos)
        else:
            return jsonify({'success': False, 'error': 'Invalid move type'}), 400

        return jsonify({
            'success': success,
            'game_over': game.is_game_over(),
            'winner': game.get_winner(),
            'state': game.get_game_state()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/state', methods=['GET'])
def get_state():
    global game
    if game is None:
        return jsonify({"error": "Game not started"}), 400
    try:
        return jsonify(game.get_game_state())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/legal_moves', methods=['GET'])
def get_legal_moves():
    global game
    if game is None:
        return jsonify({"error": "Game not started"}), 400
    try:
        legal_moves = game.get_legal_moves()
        moves_serialized = [
            {
                "type": move_type,
                "from": [from_pos.row, from_pos.col],
                "to": [to_pos.row, to_pos.col]
            }
            for move_type, from_pos, to_pos in legal_moves
        ]
        return jsonify(moves_serialized)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/restart', methods=['POST'])
def restart_game():
    global game
    if game is None:
        return jsonify({"error": "Game not started"}), 400
    try:
        game.setup_game(game.level)
        game.turn_count = 0
        game.left_goals = 0
        game.right_goals = 0
        return jsonify({'message': 'Game restarted', 'state': game.get_game_state()})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Handle preflight OPTIONS requests
@app.before_request
def handle_preflight():
    if request.method == "OPTIONS":
        response = jsonify()
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add('Access-Control-Allow-Headers', "*")
        response.headers.add('Access-Control-Allow-Methods', "*")
        return response

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)