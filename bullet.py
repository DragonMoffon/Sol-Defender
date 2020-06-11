import math
import time

import arcade


class Bullet(arcade.Sprite):

    def __init__(self, pos, angle, velocity):
        super().__init__()
        # parent variables
        self.texture = arcade.load_texture("Sprites/circle_white.png")
        self.scale = 0.01
        self.spawn_away = 0

        # variables for bullets
        self.velocity = [0.0, 0.0]
        self.speed = 500
        self.life = 0
        self.max_age = 2
        self.spawn(pos, angle, velocity)

    def spawn(self, pos, angle, velocity):
        angle_rad = math.radians(angle)

        self.center_x = pos[0] + math.cos(angle_rad) * self.spawn_away
        self.center_y = pos[1] + math.sin(angle_rad) * self.spawn_away
        self.angle = angle

        self.velocity[0] = velocity[0] + (math.cos(angle_rad) * self.speed)
        self.velocity[1] = velocity[1] + (math.sin(angle_rad) * self.speed)
        self.life = time.time() + self.max_age

    def on_update(self, delta_time: float = 1 / 60):
        self.center_x += self.velocity[0] * delta_time
        self.center_y += self.velocity[1] * delta_time
        if time.time() > self.life:
            self.remove_from_sprite_lists()
            del self
