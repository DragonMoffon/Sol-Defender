import math
from PIL import Image

import arcade


"""
While called vector.py due to its mathematical functions 
vector also holds utility classes that don't have anywhere else to be
"""


class Scrap(arcade.Sprite):

    def __init__(self, player, enemy_handler, x_y):
        super().__init__("Sprites/circles/circle_green.png", 0.2, center_x=x_y[0], center_y=x_y[1])
        self.player = player
        self.enemy_handler = enemy_handler

    def update(self):
        p_vec = (self.player.center_x, self.player.center_y)
        s_vec = (self.center_x, self.center_y)
        distance = find_distance(p_vec, s_vec)
        if distance < 500:
            direction = math.radians(find_angle(p_vec, s_vec))
            acceleration = 0.0006 * self.player.weight / distance
            move_x = math.cos(direction) * acceleration
            move_y = math.sin(direction) * acceleration
            self.center_x += move_x
            self.center_y += move_y
            if distance <= self.width:
                self.scale = ((self.width*distance)/(self.width*self.width)) * 0.2
                if distance < 15:
                    self.enemy_handler.count_collect_scrap()
                    self.player.add_scrap()
                    self.remove_from_sprite_lists()
                    del self


class AnimatedTempSprite(arcade.Sprite):

    def __init__(self, sprite_sheet, pos, animation_speed: int = 12, loops: int = 1):
        super().__init__()

        self.scale = 1
        self.center_x = pos[0]
        self.center_y = pos[1]
        self.loops = loops
        self.frames = []
        self.fps = animation_speed
        self.frame_timer = 0
        self.frame_step = 1 / animation_speed
        self.current_texture = 0
        image = Image.open(sprite_sheet)
        frame_size, sprite_sheet_height = image.size
        if sprite_sheet_height % frame_size != 0:
            raise TypeError("The Frames Must Have Equal Width and Height")
        else:
            num_frames = sprite_sheet_height//frame_size
            for y in range(num_frames):
                texture = arcade.load_texture(sprite_sheet, 0, frame_size * y,
                                              frame_size, frame_size)
                self.frames.append(texture)
            self.texture = self.frames[self.current_texture]

    def on_update(self, delta_time: float = 1/60):
        self.frame_timer += delta_time
        if self.frame_timer >= self.frame_step:
            self.frame_timer -= self.frame_step
            self.current_texture += 1
            if self.current_texture < len(self.frames):
                self.texture = self.frames[self.current_texture]
            else:
                self.loops -= 1
                if self.loops <= 0:
                    self.kill()

    def kill(self):
        self.remove_from_sprite_lists()
        del self


"""
These are all general use mathematical functions based around 2D points(vectors) and angles.
"""


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
