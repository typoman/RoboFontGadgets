import math

def distance(p1: tuple, p2: tuple):
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])
