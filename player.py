class Player:
    """Representa un jugador en el juego."""
    def __init__(self, position, team, player_id, is_goalkeeper=False):
        self.position = position
        self.team = team  # 'LEFT' o 'RIGHT'
        self.player_id = player_id
        self.is_goalkeeper = is_goalkeeper
    
    def __str__(self):
        return f"{self.team} Player {self.player_id} at {self.position}"
    
    def move_to(self, new_position):
        """Mueve el jugador a una nueva posición."""
        self.position = new_position

