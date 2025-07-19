from flask import Flask, request, jsonify
from flask_cors import CORS
from mastergoalGame import MastergoalGame
from position import Position

app = Flask(__name__)
CORS(app)

# Global game instance
game = None

@app.route('/start_game', methods=['POST'])
def start_game():
    global game
    data = request.json
    level = data.get("level", 2)
    game = MastergoalGame(level=level)
    return jsonify({"message": "Game started", "state": game.get_game_state()})


@app.route('/move', methods=['POST'])
def move():
    global game
    if game is None:
        return jsonify({"error": "Game not started"}), 400

    data = request.json
    move_type = data.get('type')
    from_row, from_col = data.get('from') # ALREADY RECEI VED CORRECTLY
    to_row, to_col = data.get('to') # ALREADY RECEI VED CORRECTLY

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


@app.route('/state', methods=['GET'])
def get_state():
    global game
    if game is None:
        return jsonify({"error": "Game not started"}), 400
    return jsonify(game.get_game_state())


@app.route('/legal_moves', methods=['GET'])
def get_legal_moves():
    global game
    if game is None:
        return jsonify({"error": "Game not started"}), 400
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


@app.route('/restart', methods=['POST'])
def restart_game():
    global game
    if game is None:
        return jsonify({"error": "Game not started"}), 400
    game.setup_game(game.level)
    game.turn_count = 0
    game.left_goals = 0
    game.right_goals = 0
    return jsonify({'message': 'Game restarted', 'state': game.get_game_state()})


if __name__ == '__main__':
    app.run(debug=True)
