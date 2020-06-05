import math
import time

import arcade

import bullet


class Player(arcade.Sprite):

    def __init__(self):

        super().__init__()

        self.hit = False
        self.health = 100
        self.dead = False
        self.show_hitbox = False

        # The Seven Stats
        self.damage = 4

        # Variables for movement
        self.thruster_force = 330000
        self.thrusters_output = [0.0, 0.0]
        self.weight = 549054
        self.forward_force = 0
        self.acceleration = [0.0, 0.0]
        self.velocity = [0.0, 0.0]

        # Variables for turning
        self.turn_key = False
        self.turning_force = 0
        self.turning_acceleration = 0
        self.angle_velocity = 0
        self.distance_to_turning = 30
        self.angular_inertia = (1 / 12) * self.weight * (64.5 ** 2)
        self.correction = 0.33

        # Parent Variables
        self.texture = arcade.load_texture("Sprites/Saber Solo.png")
        self.scale = 0.1

        # shooting variables
        self.shooting = False
        self.delay = 0.1
        self.bullets = arcade.SpriteList()
        self.last_shot = 0

        # Enemy Pointer Variables
        self.enemy_handler = None
        self.enemy_pointers = arcade.SpriteList()

        # hit box
        point_list = ((-145, -5), (-145, 5), (-105, 5), (-105, 15), (-75, 15), (-75, 25), (-135, 25), (-135, 35),
                      (-125, 35), (-125, 55), (-115, 55), (-115, 75), (-85, 75), (-85, 105), (-125, 105), (-125, 135),
                      (-135, 135), (-135, 155), (-145, 155), (-145, 185), (-125, 185), (-125, 195), (-165, 195),
                      (-165, 205), (-135, 205), (-135, 215), (-35, 215), (-35, 205), (25, 205), (25, 195), (85, 195),
                      (85, 185), (125, 185), (125, 175), (135, 175), (135, 165), (145, 165), (145, 155), (155, 155),
                      (155, 135), (165, 135), (165, 55), (115, 55), (115, 45), (65, 45), (65, 35), (75, 35), (75, 15),
                      (85, 15), (85, -15), (75, -15), (75, -35), (65, -35), (65, -45), (115, -45), (115, -55),
                      (165, -55), (165, -135), (155, -135), (155, -155), (145, -155), (145, -165), (135, -165),
                      (135, -175), (125, -175), (125, -185), (85, -185), (85, -195), (25, -195), (25, -205),
                      (-35, -205), (-35, -215), (-135, -215), (-135, -205), (-165, -205), (-165, -195), (-125, -195),
                      (-125, -185), (-145, -185), (-145, -155), (-135, -155), (-135, -135), (-125, -135), (-125, -105),
                      (-85, -105), (-85, -75), (-115, -75), (-115, -55), (-125, -55), (-125, -35), (-135, -35),
                      (-135, -25), (-75, -25), (-75, -15), (-105, -15), (-105, -5))

        self.set_hit_box(point_list)

    def apply_correction(self):
        if not self.turn_key:
            if self.angle_velocity < -0.3:
                self.thrusters_output[0] = self.correction
            elif self.angle_velocity > 0.3:
                self.thrusters_output[0] = -self.correction
            else:
                self.angle_velocity = 0
                self.thrusters_output[0] = 0.0

    def calculate_thruster_force(self):
        self.turning_force = self.thruster_force * self.thrusters_output[0]
        self.forward_force = self.thrusters_output[1] * self.thruster_force * 4

    def calculate_acceleration(self):
        turning_torque = self.distance_to_turning * self.turning_force
        if turning_torque != 0:
            self.turning_acceleration = math.degrees(turning_torque / self.angular_inertia)
        else:
            self.turning_acceleration = 0
        angle_rad = math.radians(self.angle)
        acceleration = self.forward_force / self.weight
        dx = round(math.cos(angle_rad) * acceleration, 2)
        dy = round(math.sin(angle_rad) * acceleration, 2)
        self.acceleration = [dx, dy]

    def apply_acceleration(self):
        self.angle_velocity += self.turning_acceleration
        self.velocity[0] += self.acceleration[0]
        self.velocity[1] += self.acceleration[1]

    def move(self, delta_time):
        self.angle += self.angle_velocity * delta_time
        if self.angle > 360:
            self.angle -= 360
        elif self.angle < 0:
            self.angle += 360
        self.center_x += self.velocity[0] * delta_time
        self.center_y += self.velocity[1] * delta_time

    def on_update(self, delta_time: float = 1 / 60):
        self.calculate_thruster_force()
        self.calculate_acceleration()
        self.apply_acceleration()
        self.move(delta_time)
        self.apply_correction()

        self.bullets.on_update(delta_time)
        if self.shooting and self.last_shot + self.delay < time.time():
            self.shoot()
            self.last_shot = time.time()

        self.enemy_pointers.on_update(delta_time)

    def shoot(self):
        shot = bullet.Bullet([self.center_x, self.center_y], self.angle, self.velocity)
        self.bullets.append(shot)

    def draw(self):
        self.enemy_pointers.draw()
        self.bullets.draw()
        super().draw()
        if self.show_hitbox:
            self.draw_hit_box(color=arcade.color.LIME_GREEN)

    def key_down(self, key):
        if key == arcade.key.W:
            self.thrusters_output[1] = 1.0
        elif key == arcade.key.A:
            self.thrusters_output[0] = 1.0
            self.turn_key = True
        elif key == arcade.key.D:
            self.thrusters_output[0] = -1.0
            self.turn_key = True
        elif key == arcade.key.SPACE:
            self.shooting = True
        elif key == arcade.key.TAB and not self.show_hitbox:
            self.show_hitbox = True
        elif key == arcade.key.TAB and self.show_hitbox:
            self.show_hitbox = False

    def key_up(self, key):
        if key == arcade.key.W:
            self.thrusters_output[1] = 0.0
        elif key == arcade.key.A and self.thrusters_output[0] != -1.0:
            self.thrusters_output[0] = 0.0
            self.turn_key = False
        elif key == arcade.key.D and self.thrusters_output[0] != 1.0:
            self.thrusters_output[0] = 0.0
            self.turn_key = False
        elif key == arcade.key.SPACE:
            self.shooting = False
