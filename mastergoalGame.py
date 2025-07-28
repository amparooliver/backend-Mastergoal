import time
from ball import Ball
from player import Player
from position import Position

# Global constants
NUM_GOALS = 2 #Number of goals to win
#NUM_TURNS = 40

class MastergoalGame:
    """Clase principal que maneja el estado del juego y las reglas."""
    # Constantes para equipos
    LEFT = "LEFT"
    RIGHT = "RIGHT"
    
    # Dimensiones del tablero
    ROWS = 15
    COLS = 11
    
    def __init__(self, level=1, max_turns=None, play_with_timer=False, timer_duration=None):
        """Inicializa el juego con el nivel especificado."""
        self.level = level
        self.left_goals = 0
        self.right_goals = 0
        self.current_team = self.LEFT  # Equipo blanco comienza
        self.players = []  # Lista de todos los jugadores
        self.ball = None  # La pelota
        self.last_possession_team = None  # Último equipo que tuvo posesión
        self.passes_count = 0  # Contador de pases en el turno actual
        self.turn_count = 0  # Contador de turnos
        self.skip_next_turn = False  # Flag para saltarse el siguiente turno (nivel 3)
        self.max_turns = max_turns  # None = sin límite de turnos

        # Timer logic
        self.play_with_timer = play_with_timer
        self.timer_duration = timer_duration  # seconds
        self.turn_start_time = None  # Will be set at the start of each turn

        # Inicializa el juego según el nivel
        self.setup_game(level)

        # Set timer for the very first turn
        if self.play_with_timer:
            self.turn_start_time = time.time()
    
    def setup_game(self, level):
        """Configura el juego según el nivel especificado."""
        self.players = []
        
        # Configuración según nivel
        if level == 1:
            # Nivel 1: 1 jugador por equipo - sin arquero
            self.players.append(Player(Position(4, 5), self.LEFT, 1))
            self.players.append(Player(Position(10, 5), self.RIGHT, 1))
            self.ball = Ball(Position(7, 5))    
        elif level == 2:
            # Nivel 2: 2 jugadores por equipo - sin arquero
            self.players.append(Player(Position(4, 5), self.LEFT, 1))
            self.players.append(Player(Position(2, 5), self.LEFT, 2))
            self.players.append(Player(Position(10, 5), self.RIGHT, 1))
            self.players.append(Player(Position(12, 5), self.RIGHT, 2))
            self.ball = Ball(Position(7, 5))      
        elif level == 3:
            # Jugadores blancos
            self.players.append(Player(Position(3, 5), self.LEFT, 1, True))  # Arquero
            self.players.append(Player(Position(4, 3), self.LEFT, 2))
            self.players.append(Player(Position(4, 7), self.LEFT, 3))
            self.players.append(Player(Position(6, 2), self.LEFT, 4))
            self.players.append(Player(Position(6, 8), self.LEFT, 5))
            # Jugadores rojos
            self.players.append(Player(Position(11, 5), self.RIGHT, 1, True))  # Arquero
            self.players.append(Player(Position(10, 3), self.RIGHT, 2))
            self.players.append(Player(Position(10, 7), self.RIGHT, 3))
            self.players.append(Player(Position(8, 2), self.RIGHT, 4))
            self.players.append(Player(Position(8, 8), self.RIGHT, 5))
            self.ball = Ball(Position(7, 5))

    
    def reset_after_goal(self):
        """Reinicia las posiciones después de un gol."""
        # Reinicia las posiciones según el nivel
        self.setup_game(self.level)
        # El equipo que recibió el gol comienza
        self.current_team = self.RIGHT if self.left_goals > self.right_goals else self.LEFT
        self.passes_count = 0
        self.last_possession_team = None
    
    def is_goal_LEFT(self, position):
        """Verifica si la posición es un gol para el equipo blanco."""
        return position.row == 14 and 3 <= position.col <= 7
    
    def is_goal_RIGHT(self, position):
        """Verifica si la posición es un gol para el equipo rojo."""
        return position.row == 0 and 3 <= position.col <= 7
    
    def is_out_of_bounds(self, position):
        """Verifica si la posición está fuera de límites."""
        # Casillas en la fila 0 y 14 fuera del arco
        if position.row == 0 and not (3 <= position.col <= 7):
            return True
        if position.row == 14 and not (3 <= position.col <= 7):
            return True
        # Fuera del tablero
        return position.row < 0 or position.row >= self.ROWS or position.col < 0 or position.col >= self.COLS
    
    def is_forbidden_corner(self, position, team):
        """Verifica si la posición es una esquina prohibida para el equipo."""
        if team == self.LEFT:
            return (position.row == 1 and position.col == 0) or (position.row == 1 and position.col == 10)
        else:  # RIGHT
            return (position.row == 13 and position.col == 0) or (position.row == 13 and position.col == 10)
    
    def is_in_big_area(self, position, team):
        """Verifica si la posición está en el área grande del equipo."""
        if team == self.LEFT:
            return 1 <= position.row <= 4 and 1 <= position.col <= 9
        else:  # RIGHT
            return 10 <= position.row <= 13 and 1 <= position.col <= 9
    
    def is_in_small_area(self, position, team):
        """Verifica si la posición está en el área chica del equipo."""
        if team == self.LEFT:
            return 1 <= position.row <= 2 and 2 <= position.col <= 8
        else:  # RIGHT
            return 12 <= position.row <= 13 and 2 <= position.col <= 8
    
    def is_special_tile(self, position, team):
        """Verifica si la posición es una casilla especial para el equipo."""
        if self.level < 3:
            return False  
        if team == self.LEFT:
            # Corners del equipo rojo
            if (position.row == 13 and position.col == 0) or (position.row == 13 and position.col == 10):
                return True
            # Frente al arco rojo
            if position.row == 13 and 3 <= position.col <= 7:
                return True
        else:  # RIGHT
            # Corners del equipo blanco
            if (position.row == 1 and position.col == 0) or (position.row == 1 and position.col == 10):
                return True
            # Frente al arco blanco
            if position.row == 1 and 3 <= position.col <= 7:
                return True         
        return False
    
    def is_neutral_tile(self, position):
        """Verifica si la posición es una casilla neutra."""
        if self.level == 1:
            return False     
        LEFT_adjacent = 0
        RIGHT_adjacent = 0
        for player in self.players:
            if player.position.is_adjacent(position):
                if player.team == self.LEFT:
                    LEFT_adjacent += 1
                else:
                    RIGHT_adjacent += 1           
        return LEFT_adjacent > 0 and RIGHT_adjacent > 0 and LEFT_adjacent == RIGHT_adjacent
    
    def is_ball_in_neutral_state(self):
        """Verifica si la pelota está en estado neutral (igual número de jugadores adyacentes de cada equipo)."""
        return self.is_neutral_tile(self.ball.position)

    def is_player_in_ball_neutral_state(self, player_position):
        """Verifica si un jugador está participando en el estado neutral de la pelota."""
        if not self.is_ball_in_neutral_state():
            return False
        return player_position.is_adjacent(self.ball.position)
        
    def get_player_at(self, position):
        """Devuelve el jugador en la posición dada o None si no hay ninguno."""
        for player in self.players:
            if player.position == position:
                return player
        return None
    
    def get_team_players(self, team):
        """Devuelve una lista de jugadores del equipo especificado."""
        return [player for player in self.players if player.team == team]
    
    def get_goalkeeper(self, team):
        """Devuelve el arquero del equipo o None si no hay."""
        for player in self.players:
            if player.team == team and player.is_goalkeeper:
                return player
        return None
    
    def get_goalkeeper_arms(self, team):
        """Devuelve las posiciones válidas de los brazos del arquero."""
        goalkeeper = self.get_goalkeeper(team)
        if not goalkeeper or not self.is_in_big_area(goalkeeper.position, team):
            return []  
        arms = []
        # Brazos horizontales del arquero
        left_arm = Position(goalkeeper.position.row, goalkeeper.position.col - 1)
        right_arm = Position(goalkeeper.position.row, goalkeeper.position.col + 1)
        # Solo agregar brazos que estén dentro del área grande
        if not self.is_out_of_bounds(left_arm) and self.is_in_big_area(left_arm, team):
            arms.append(left_arm)
        if not self.is_out_of_bounds(right_arm) and self.is_in_big_area(right_arm, team):
            arms.append(right_arm)
        return arms
    
    def get_legal_player_moves(self, player_position):
        """Devuelve todas las posiciones legales a las que un jugador puede moverse."""
        legal_moves = []
        player = self.get_player_at(player_position)
        if not player or player.team != self.current_team:
            return []
        # Verificar si el jugador está en el estado neutral de la pelota
        is_in_ball_neutral_state = self.is_player_in_ball_neutral_state(player_position)
            
        for dr in [-2, -1, 0, 1, 2]:
            for dc in [-2, -1, 0, 1, 2]:
                if dr == 0 and dc == 0:
                    continue
                if abs(dr) > 2 or abs(dc) > 2:
                    continue
                if not (dr == 0 or dc == 0 or abs(dr) == abs(dc)):
                    continue

                new_position = Position(player_position.row + dr, player_position.col + dc)
                
                if self.is_out_of_bounds(new_position):
                    continue
                if self.is_forbidden_corner(new_position, player.team):
                    continue
                if self.get_player_at(new_position) is not None:
                    continue
                if new_position == self.ball.position:
                    continue
                if self.is_goal_LEFT(new_position) or self.is_goal_RIGHT(new_position):
                    continue  # No puede entrar al área de gol
                
                # No puede posicionarse en las casillas de brazos del arquero (CHEQUEA PARA EL ARQUEROE ESTO?)
                if self.level == 3 and not player.is_goalkeeper:
                    # Verificar brazos de ambos equipos
                    LEFT_arms = self.get_goalkeeper_arms(self.LEFT)
                    RIGHT_arms = self.get_goalkeeper_arms(self.RIGHT)
                    if new_position in LEFT_arms or new_position in RIGHT_arms:
                        continue
                
                # LÓGICA ESPECIAL PARA ARQUERO EN NIVEL 3
                if self.level == 3 and player.is_goalkeeper:
                    # Si el arquero se mueve a una posición dentro de su área grande,
                    # debe verificar que tenga espacio para al menos un brazo válido
                    if self.is_in_big_area(new_position, player.team):
                        # Verificar que en la nueva posición tenga espacio para sus brazos
                        potential_left_arm = Position(new_position.row, new_position.col - 1)
                        potential_right_arm = Position(new_position.row, new_position.col + 1)
                        
                        # Contar cuántos brazos válidos tendría en la nueva posición
                        valid_arms = 0
                        
                        # Verificar brazo izquierdo (solo si está dentro del área grande)
                        if (not self.is_out_of_bounds(potential_left_arm) and 
                            self.is_in_big_area(potential_left_arm, player.team) and
                            self.get_player_at(potential_left_arm) is None and
                            potential_left_arm != self.ball.position):
                            valid_arms += 1
                        
                        # Verificar brazo derecho (solo si está dentro del área grande)
                        if (not self.is_out_of_bounds(potential_right_arm) and 
                            self.is_in_big_area(potential_right_arm, player.team) and
                            self.get_player_at(potential_right_arm) is None and
                            potential_right_arm != self.ball.position):
                            valid_arms += 1
                        
                        # El arquero necesita al menos un brazo válido para moverse dentro del área
                        if valid_arms == 0:
                            continue
                    # Si se mueve fuera del área grande, se convierte en jugador normal
                    # y no hay restricciones adicionales

                # Si el jugador está en estado neutral de la pelota, 
                # solo puede moverse a posiciones que sigan siendo adyacentes a la pelota
                if is_in_ball_neutral_state:
                    if not new_position.is_adjacent(self.ball.position):
                        continue  # Debe mantenerse adyacente a la pelota en estado neutral  

                # Verifica si pasa por encima de la pelota o de otro jugador
                # Los jugadores pueden saltar sobre los brazos del arquero a la sgte casilla
                direction = player_position.direction_to(new_position)
                steps = new_position.distance(player_position)
                path_blocked = False
                for step in range(1, steps):
                    intermediate = player_position.position_in_direction(direction, step)
                    if intermediate == self.ball.position:
                        path_blocked = True
                        break
                    # Verificar si hay un jugador que no sea un brazo de arquero
                    player_at_intermediate = self.get_player_at(intermediate)
                    if player_at_intermediate is not None:
                        path_blocked = True
                        break
                
                if not path_blocked:
                    legal_moves.append(new_position)
      
        return legal_moves

    def get_legal_ball_kicks(self, from_position):
        """Devuelve todas las posiciones legales a las que la pelota puede ser pateada."""
        legal_kicks = []
        
        if self.ball.position != from_position:
            return []
            
        # Verificar si hay un jugador del equipo actual adyacente a la pelota
        kicker = None
        for player in self.get_team_players(self.current_team):
            if player.position.is_adjacent(self.ball.position):
                kicker = player
                break
                
        if kicker is None:
            return []
            
        # La pelota puede moverse 1-4 casillas en línea recta
        for direction in [(0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1), (-1, 0), (-1, 1)]:
            for distance in range(1, 5):
                new_position = self.ball.position.position_in_direction(direction, distance)
                
                # Verificar fuera de límites (permitir entrar a arco)
                if self.is_out_of_bounds(new_position) and not (self.is_goal_LEFT(new_position) or self.is_goal_RIGHT(new_position)):
                    break
                
                # No puede patear a su propio córner
                if self.is_forbidden_corner(new_position, kicker.team):
                    continue
                
                # No puede terminar en su propia área grande (salvo gol)
                if self.is_in_big_area(new_position, kicker.team) and not (self.is_goal_LEFT(new_position) or self.is_goal_RIGHT(new_position)):
                    continue
                
                # No puede patear a su propio arco (autogol)
                if (kicker.team == self.LEFT and self.is_goal_RIGHT(new_position)) or \
                (kicker.team == self.RIGHT and self.is_goal_LEFT(new_position)):
                    continue  # No permitir autogoles
                
                # ⚽ SOLO en nivel 3: chequeo arquero y brazos
                if self.level == 3:
                    goalkeeper_blocks = False
                    # No pasar sobre cuerpo del arquero
                    for d in range(1, distance + 1):
                        pos = self.ball.position.position_in_direction(direction, d)
                        player_at_pos = self.get_player_at(pos)
                        if player_at_pos and player_at_pos.is_goalkeeper:
                            goalkeeper_blocks = True
                            break
                    
                    if goalkeeper_blocks:
                        continue  # Pasa sobre arquero => no es válido
                    
                    # Chequeamos brazos del arquero
                    opponent_team = self.RIGHT if self.current_team == self.LEFT else self.LEFT
                    opponent_gk = self.get_goalkeeper(opponent_team)
                    if opponent_gk and self.is_in_big_area(opponent_gk.position, opponent_team):
                        arms = self.get_goalkeeper_arms(opponent_team)
                        for d in range(1, distance + 1):
                            pos = self.ball.position.position_in_direction(direction, d)
                            if pos in arms:
                                goalkeeper_blocks = True
                                break
                        
                        if goalkeeper_blocks:
                            continue  # Pasa sobre brazo => no es válido

                # No puede terminar en casilla ocupada
                if self.get_player_at(new_position) is not None:
                    continue

                # RESTRICCIÓN DE PASES MODIFICADA
                # Si ya se han realizado 3 pases, no permitir otro pase
                is_pass = False
                if self.level >= 2:  # Solo en niveles 2 y 3 hay pases
                    for teammate in self.get_team_players(self.current_team):
                        if teammate.position != kicker.position and teammate.position.is_adjacent(new_position):
                            is_pass = True
                            break
                
                if self.passes_count >= 3 and is_pass:
                    continue  # Ya se hicieron 3 pases, no permitir otro pase
                
                # MODIFICACIÓN: Puede patearse la pelota a posición adyacente a sí mismo solo si también es adyacente a un compañero (pase)
                if new_position.is_adjacent(kicker.position):
                    # En nivel 1, nunca puede patear adyacente a sí mismo
                    if self.level == 1:
                        continue
                    # En niveles 2 y 3, solo puede hacerlo si es un pase (hay compañero adyacente)
                    elif self.level >= 2:
                        has_teammate_adjacent = False
                        for teammate in self.get_team_players(self.current_team):
                            if teammate.position != kicker.position and teammate.position.is_adjacent(new_position):
                                has_teammate_adjacent = True
                                break
                        if not has_teammate_adjacent:
                            continue  # No hay compañero adyacente, no puede patear ahí

                # Niveles 1: no puede quedar adyacente a oponente (excepto jugada de gol)
                if self.level == 1:
                    opponent_team = self.RIGHT if self.current_team == self.LEFT else self.LEFT
                    adjacent_to_opponent = False
                    for opponent in self.get_team_players(opponent_team):
                        if new_position.is_adjacent(opponent.position):
                            adjacent_to_opponent = True
                            break
                    if adjacent_to_opponent:
                        # Sólo permitido si es gol
                        if not (self.is_goal_LEFT(new_position) or self.is_goal_RIGHT(new_position)):
                            continue

                # Nivel 2 y 3: chequeo de casilla neutra en destino
                if self.level in (2, 3):
                    LEFT_adjacent = 0
                    RIGHT_adjacent = 0
                    for player in self.players:
                        if player.position.is_adjacent(new_position):
                            if player.team == self.LEFT:
                                LEFT_adjacent += 1
                            else:
                                RIGHT_adjacent += 1
                    if LEFT_adjacent + RIGHT_adjacent > 0:
                        if LEFT_adjacent != RIGHT_adjacent:
                            # Hay mayoría, veamos de quién es
                            if (self.current_team == self.LEFT and RIGHT_adjacent > LEFT_adjacent) or \
                            (self.current_team == self.RIGHT and LEFT_adjacent > RIGHT_adjacent):
                                continue  # No puedes patear a un lugar dominado por el oponente

                # Si pasa todos los chequeos, es un pateo legal
                legal_kicks.append(new_position)

        return legal_kicks

    def can_pass(self, to_position):
        """Verifica si la pelota puede ser pasada a la posición dada."""
        if self.level == 1:
            return False  # No se permiten pases en nivel 1
        if self.passes_count >= 3:
            return False  # No se permiten más de 3 pases

        # Debe haber un jugador del mismo equipo adyacente (que no sea el que patea)
        kicker = None
        for player in self.get_team_players(self.current_team):
            if player.position.is_adjacent(self.ball.position):
                kicker = player
                break
                
        if kicker is None:
            return False

        # Buscar otro jugador del mismo equipo que reciba el pase
        for player in self.get_team_players(self.current_team):
            if player.position.is_adjacent(to_position) and player.position != kicker.position:
                return True
                
        return False

    def execute_move(self, player_position, new_position):
        """Ejecuta el movimiento de un jugador."""
        player = self.get_player_at(player_position)
        
        if not player or player.team != self.current_team:
            return False
            
        if new_position not in self.get_legal_player_moves(player_position):
            return False
            
        player.move_to(new_position)
        
        # Si el jugador está adyacente a la pelota, debe patear
        # PERO solo si la pelota NO está en estado neutral
        if new_position.is_adjacent(self.ball.position) and not self.is_ball_in_neutral_state():
            self.last_possession_team = player.team
            return True  # Jugador debe patear ahora
        else:
            # Cambiar de turno si no hay un pase obligatorio
            self.end_turn()
            return True
            
        return False
    
    def execute_kick(self, new_ball_position):
        """Ejecuta un pateo de la pelota."""
        if new_ball_position not in self.get_legal_ball_kicks(self.ball.position):
            return False
            
        # Verificar si es un gol
        if self.is_goal_LEFT(new_ball_position):
            self.left_goals += 1
            self.reset_after_goal()
            return True
            
        if self.is_goal_RIGHT(new_ball_position):
            self.right_goals += 1
            self.reset_after_goal()
            return True
            
        # Mover la pelota
        self.ball.move_to(new_ball_position)
        
        # Verificar si es una casilla especial (nivel 3)
        if self.level == 3 and self.is_special_tile(new_ball_position, self.current_team):
            self.skip_next_turn = True
        
        # Verificar si es un pase verificando si hay un jugador del mismo equipo adyacente
        # que pueda recibir la pelota (diferente al que pateó)
        is_pass = False
        
        # Primero identificamos quién pateó
        kicker = None
        for player in self.get_team_players(self.current_team):
            if player.position.is_adjacent(self.ball.position) and self.ball.position != new_ball_position:
                kicker = player
                break
        
        # Luego verificamos si hay un receptor de pase
        if self.level >= 2:  # Solo en niveles 2 y 3 hay pases
            for teammate in self.get_team_players(self.current_team):
                if teammate != kicker and teammate.position.is_adjacent(new_ball_position):
                    is_pass = True
                    break
        
        if is_pass and self.passes_count < 3 and not self.is_neutral_tile(self.ball.position):
            self.passes_count += 1
            # NO cambiar de turno, sigue siendo el mismo equipo
            return True
        else:
            # Si no es un pase, o ya se hicieron 3 pases, o es un neutral tile ,cambiar de turno
            self.end_turn()
            return True

    def end_turn(self):
        """Finaliza el turno actual y cambia al siguiente equipo."""
        self.turn_count += 1
        self.passes_count = 0  # Reiniciar el contador de pases al cambiar de turno
        
        # Set turn start time if timer is enabled
        if self.play_with_timer:
            self.turn_start_time = time.time()

        # Cambiar al siguiente equipo
        self.current_team = self.RIGHT if self.current_team == self.LEFT else self.LEFT
        
        # Verificar si se debe saltar el siguiente turno
        if self.skip_next_turn:
            self.skip_next_turn = False
            self.end_turn()  # Saltar el turno
            
    def get_game_state(self):
        """Devuelve un diccionario con el estado actual del juego."""
        return {
            'level': self.level,
            'left_goals': self.left_goals,
            'right_goals': self.right_goals,
            'current_team': self.current_team,
            'ball_position': (self.ball.position.row, self.ball.position.col),
            'players': [(p.team, p.player_id, p.position.row, p.position.col, p.is_goalkeeper) for p in self.players],
            'passes_count': self.passes_count,
            'turn_count': self.turn_count,
            'skip_next_turn': self.skip_next_turn,
            'play_with_timer': self.play_with_timer,
            'timer_duration': self.timer_duration,
            'turn_start_time': self.turn_start_time,
        }
    
    def get_winner(self):
        """Devuelve el equipo ganador o None si el juego no ha terminado."""
        if self.left_goals >= NUM_GOALS:
            return self.LEFT
        if self.right_goals >= NUM_GOALS:
            return self.RIGHT
        return None
    
    def is_game_over(self):
        """Devuelve 1 si gano blanco, -1 si gano rojo, 0.1 si es empate (por maximo de turnos), 0 si continua"""
        if self.left_goals >= NUM_GOALS:
            return 1
        if self.right_goals >= NUM_GOALS:
            return -1
        if self.max_turns is not None and self.turn_count >= self.max_turns:
            return 0.1
        return 0
    
    def get_legal_moves(self):
        """Devuelve todas las jugadas legales para el equipo actual."""
        legal_moves = []
        
        # Si un jugador está adyacente a la pelota, debe patearla (a menos que la pelota esté en estado neutral)
        for player in self.get_team_players(self.current_team):
            if player.position.is_adjacent(self.ball.position) and not self.is_ball_in_neutral_state():
                kicks = self.get_legal_ball_kicks(self.ball.position)
                return [('kick', self.ball.position, kick) for kick in kicks]
        
        # Si no, puede mover cualquier jugador
        for player in self.get_team_players(self.current_team):
            moves = self.get_legal_player_moves(player.position)
            legal_moves.extend([('move', player.position, move) for move in moves])
            
        return legal_moves