class Ball:
    """Representa la pelota en el juego."""
    def __init__(self, position):
        self.position = position
    
    def __str__(self):
        return f"Ball at {self.position}"
    
    def move_to(self, new_position):
        """Mueve la pelota a una nueva posición."""
        self.position = new_position
