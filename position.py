class Position:
    """Representa una posición en el tablero con fila y columna."""
    def __init__(self, row, col):
        self.row = row
        self.col = col
    
    def __eq__(self, other):
        if not isinstance(other, Position):
            return False
        return self.row == other.row and self.col == other.col
    
    def __hash__(self):
        return hash((self.row, self.col))
    
    def __str__(self):
        return f"({self.row}, {self.col})"
    
    def is_adjacent(self, other):
        """Verifica si esta posición es adyacente a otra."""
        return abs(self.row - other.row) <= 1 and abs(self.col - other.col) <= 1 and self != other
    
    def distance(self, other):
        """Calcula la distancia máxima entre esta posición y otra.(distancia de Chebyshev)"""
        return max(abs(self.row - other.row), abs(self.col - other.col))
    
    def min_distance(self, other):
        """Calcula la distancia minima entre esta posición y otra."""
        return min(abs(self.row - other.row), abs(self.col - other.col))
    
    def direction_to(self, other):
        """Devuelve la dirección desde esta posición a otra como (dr, dc)."""
        dr = 0 if self.row == other.row else (1 if other.row > self.row else -1)
        dc = 0 if self.col == other.col else (1 if other.col > self.col else -1)
        return (dr, dc)
    
    def position_in_direction(self, direction, distance=1):
        """Devuelve una nueva posición en la dirección dada a la distancia especificada."""
        dr, dc = direction
        return Position(self.row + dr * distance, self.col + dc * distance)
