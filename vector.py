"""
These are all general use mathematical functions based around 2D points(vectors) and angles.
"""

import math


def calc_difference(target_angle, start_angle):
    """
    Calculate the Difference between two angles in a clockwise and anti-clockwise direction
    """
    difference_left = target_angle - start_angle
    difference_right = start_angle + (360 - target_angle)
    if difference_left < 0:
        difference_left += 360
    if difference_right > 360:
        difference_right -= 360

    return difference_left, difference_right


def calc_small_difference(target_angle, start_angle):
    """
    Calculate the Difference between two angles in a clockwise and anti-clockwise direction
    """
    difference_left = target_angle - start_angle
    difference_right = start_angle + (360 - target_angle)
    if difference_left < 0:
        difference_left += 360
    if difference_right > 360:
        difference_right -= 360

    if difference_right > difference_left:
        return difference_left
    else:
        return difference_right


def calc_direction(target_angle, start_angle):
    """
    using the difference calculate which direction (clockwise[-1], anti-clockwise[1]) is closest
    """

    direction = 0
    difference = calc_difference(target_angle, start_angle)
    difference_left = difference[0]
    difference_right = difference[1]
    if difference_left < difference_right:
        direction = 1
    elif difference_right < difference_left:
        direction = -1
    return direction


def find_angle(vector1, vector2):
    """
    Find the angle(a.k.a the direction) between two vectors
     with one at each end of the hypotenuse of a right angled triangle.
    """
    dx = vector1[0] - vector2[0]
    dy = vector1[1] - vector2[1]
    rad_angle = math.atan2(dy, dx)
    if rad_angle < 0:
        rad_angle += 2 * math.pi
    angle = math.degrees(rad_angle)

    return angle


def find_distance(v1, v2):
    """
    find the distance(a.k.a magnitude) between two vectors.
    """
    dx = v1[0] - v2[0]
    dy = v1[1] - v2[1]

    distance = math.sqrt(dx ** 2 + dy ** 2)
    return distance
