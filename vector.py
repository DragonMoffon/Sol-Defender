import math


def find_angle(vector1, vector2):
    dx = vector1[0] - vector2[0]
    dy = vector1[1] - vector2[1]
    rad_angle = math.atan2(dy, dx)
    if rad_angle < 0:
        rad_angle += 2 * math.pi
    angle = math.degrees(rad_angle)

    return angle


def find_distance(v1, v2):
    dx = v1[0] - v2[0]
    dy = v1[1] - v2[1]

    distance = math.sqrt(dx ** 2 + dy ** 2)
    return distance
