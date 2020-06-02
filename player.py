import arcade
import math
import time

import bullet
import pointer


class Player(arcade.Sprite):

    def __init__(self):

        super().__init__()
        self.hit = False
        self.score = 0
        self.deaths = 0

        # Variables for movement
        self.thruster_force = 330000
        self.thrusters_output = [0.0,0.0]
        self.weight = 549054
        self.forward_force = 0
        self.acceleration = [0.0,0.0]
        self.velocity = [0.0,0.0]

        # Variables for turning
        self.turn_key = False
        self.turning_force = 0
        self.turning_acceleration = 0
        self.angle_velocity = 0
        self.distance_to_turning = 30
        self.angular_inertia = (1/12)*self.weight*(64.5**2)
        self.correction = 0.33

        # Parent Variables
        self.texture = arcade.load_texture("Saber Solo.png")
        self.scale = 0.1

        # shooting variables
        self.shooting = False
        self.delay = 0.1
        self.bullets = arcade.SpriteList()
        self.last_shot = 0

        # Enemy Pointer Variables
        self.enemy_handler = None
        self.enemy_pointers = arcade.SpriteList()

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
        self.turning_force = self.thruster_force*self.thrusters_output[0]
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
        self.acceleration = [dx,dy]

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

    def on_update(self, delta_time: float = 1/60):
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
        shot = bullet.Bullet([self.center_x,self.center_y], self.angle, self.velocity)
        self.bullets.append(shot)

    def draw(self):
        self.enemy_pointers.draw()
        self.bullets.draw()
        super().draw()

    def key_down(self,key):
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
