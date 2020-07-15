import math
import time

import arcade


class Bullet(arcade.Sprite):

    def __init__(self, pos, angle, velocity, bullet_type: dict, texture: str = None):
        super().__init__()
        # parent variables
        if texture is not None:
            texture_location = texture
        else:
            texture_location = bullet_type['texture']
        self.texture = arcade.load_texture(texture_location)
        self.scale = bullet_type['scale']
        self.spawn_away = 0
        self.hit_box = bullet_type['hit_box']

        # variables for bullets
        self.velocity = [0.0, 0.0]
        self.speed = bullet_type['speed']
        self.life = 0
        self.max_age = bullet_type['age']
        self.spawn(pos, angle, velocity)
        self.damage = bullet_type['damage']

    def spawn(self, pos, angle, velocity):
        """
        Taking many variables from the parent spawn the bullet and give it velocity
        """
        angle_rad = math.radians(angle)

        self.center_x = pos[0] + math.cos(angle_rad) * self.spawn_away
        self.center_y = pos[1] + math.sin(angle_rad) * self.spawn_away

        self.velocity[0] = velocity[0] + (math.cos(angle_rad) * self.speed)
        self.velocity[1] = velocity[1] + (math.sin(angle_rad) * self.speed)

        self.angle = angle

        self.life = time.time() + self.max_age

    def on_update(self, delta_time: float = 1 / 60):
        """
        Update the bullet and kill it if it's to old.
        """
        self.center_x += self.velocity[0] * delta_time
        self.center_y += self.velocity[1] * delta_time
        if time.time() > self.life:
            self.remove_from_sprite_lists()
            del self
