import math


def calc_difference(target_angle, start_angle):
    difference_left = target_angle - start_angle
    difference_right = start_angle + (360 - target_angle)
    if difference_left < 0:
        difference_left += 360
    if difference_right > 360:
        difference_right -= 360

    return difference_left, difference_right


def calc_direction(target_angle, start_angle):
    direction = 0
    difference = calc_difference(target_angle, start_angle)
    difference_left = difference[0]
    difference_right = difference[1]
    # print("left:", difference_left, ":", "right:", difference_right)
    if difference_left < difference_right:
        direction = 1
    elif difference_right < difference_left:
        direction = -1
    return direction


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
