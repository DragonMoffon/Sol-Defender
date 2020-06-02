import arcade
import time
import math
import random

import vector
import bullet
import pointer


class EnemyHandler:
    """
    The EnemyHandler class holds all of the data values necessary for the enemies to act. it is also responsible for
    creating waves and updating enemies
    """

    def __init__(self):
        # The player object. This allows the enemies to get its position.
        self.player = None

        # The sprite list that holds all of the enemy sprites
        self.enemy_sprites = None

        # A simplified variable that represents the difficulty of the wave. currently just how many enemies there are.
        self.num_enemies = 5
        self.wave = 0

    def setup(self):
        """
        this sets up the enemy waves. It will be separated into a setup for each type of wave
        (each mission has a different type)
        """
        self.wave += 1
        self.enemy_sprites = arcade.SpriteList()
        for i in range(self.num_enemies):
            enemy = Enemy()
            enemy.setup(self)
            self.enemy_sprites.append(enemy)

    def draw(self):
        """
        draws all of the enemy sprites
        """
        for enemy in self.enemy_sprites:
            enemy.draw()

    def on_update(self, delta_time: float = 1 / 60):
        """
        updates all of the enemies
        """
        self.enemy_sprites.on_update(delta_time)
        if len(self.enemy_sprites) == 0:
            self.setup()


class Enemy(arcade.Sprite):
    """
    The Enemy class is used by the enemy handler in each wave. their movement works just like the
    players, however they have decision trees on whether to turn left or right or when to move forward.
    """

    def __init__(self):
        super().__init__()
        self.max_velocity = 153
        self.final_velocity = 0
        self.final_angle = 0

        # Parent variables for drawing.
        self.texture = arcade.load_texture("Enemy Solo.png")
        self.scale = 0.1

        # checks if the enemy should be trying to
        self.handler = None
        self.target_distance = 0
        self.target_angle = 0
        self.angular_momentum_max = 0

        # variables for both forward thrust and turning thrust
        self.weight = 525054
        self.thruster_force = 300000

        # variables for turning
        self.turning_distance = 28
        self.angular_inertia = (1 / 12) * self.weight * (49.5 ** 2)
        self.turn_thrust_percent = 0.0
        self.angular_force = 0
        self.angular_acceleration = 0
        self.angular_velocity = 0

        # shooting variables
        self.shooting = False
        self.bullets = arcade.SpriteList()
        self.last_shot = 0
        self.shoot_delay = 0.1
        self.next_shot = 0

    def draw(self):
        self.bullets.draw()
        super().draw()

    def on_update(self, delta_time: float = 1 / 60):
        """
        runs all functions necessary each update
        """
        self.target_distance = vector.find_distance((self.center_x,self.center_y),
                                                    (self.handler.player.center_x, self.handler.player.center_y))
        if self.target_distance <= 300:
            self.calc_turn()
            if self.shooting and self.last_shot + self.shoot_delay < time.time():
                self.last_shot = time.time()
                self.shoot()
        self.check_contact()
        self.calc_turning_acceleration()
        self.apply_acceleration_velocity(delta_time)
        self.bullets.on_update(delta_time)
        self.if_hit_player()

    def shoot(self):
        shot = bullet.Bullet([self.center_x,self.center_y], self.angle, self.velocity)
        shot.texture = arcade.load_texture("circle red.png")
        self.bullets.append(shot)

    def setup(self, handler):
        """
        sets up the enemy in relation to the player. it also gives the enemy the handler for easier access to variables
        """
        self.handler = handler
        self.angle = random.randint(0, 360)
        screen = arcade.get_display_size()
        close = True
        while close:
            self.center_x = handler.player.center_x + random.randint(-(screen[0] // 2) + 30, (screen[0] // 2) - 29)
            self.center_y = handler.player.center_y + random.randint(-(screen[1] // 2) + 30, (screen[1] // 2) - 29)
            self.target_distance = vector.find_distance((self.center_x, self.center_y),
                                                        (self.handler.player.center_x, self.handler.player.center_y))
            if self.target_distance > 300:
                close = False

        point = pointer.Pointer()
        point.holder = self.handler.player
        point.target = self
        self.handler.player.enemy_pointers.append(point)

    def calc_turn(self):
        """
        calculates the direction the enemy must turn as well as whether they must be decelerating or accelerating.
        """
        target = self.handler.player
        pos_T = (target.center_x, target.center_y)
        pos_S = (self.center_x, self.center_y)
        self.target_angle = vector.find_angle(pos_T, pos_S)
        direction = self.calc_direction()
        if round(self.target_angle) != self.angle:
            self.angle += direction
        if self.target_angle - 5 < self.angle < self.target_angle + 5:
            self.shooting = True
        '''
        difference = self.calc_difference()
        print(self.angular_velocity)
        if self.target_angle - 1 < self.angle < self.target_angle + 1 and self.angular_velocity < 0.25:
            self.turn_thrust_percent = 0.0
        elif difference[0] < 300 or difference[1] < 300:
            self.turn_thrust_percent = direction
            if difference[0] < 50 and self.angular_velocity < 0.25:
                self.turn_thrust_percent = 0.0
            if difference[0] < 50 and self.angular_velocity > -0.25:
                self.turn_thrust_percent = 0.0
        elif direction == 1 and self.angular_velocity < self.max_velocity:
            self.turn_thrust_percent = 1.0
        elif direction == -1 and self.angular_velocity > -self.max_velocity:
            self.turn_thrust_percent = -1.0
            '''

    def calc_difference(self):
        difference_left = self.target_angle - self.angle
        difference_right = self.angle + (360 - self.target_angle)
        if difference_left < 0:
            difference_left += 360
        if difference_right > 360:
            difference_right -= 360

        return difference_left, difference_right

    def calc_direction(self):
        direction = 0
        difference = self.calc_difference()
        difference_left = difference[0]
        difference_right = difference[1]
        # print("left:", difference_left, ":", "right:", difference_right)
        if difference_left < difference_right:
            direction = 1
        elif difference_right < difference_left:
            direction = -1
        return direction

    def calc_turning_acceleration(self):
        """
        calculates the amount of force the thruster is outputting and the acceleration in a direction
        """
        self.angular_force = self.thruster_force * self.turn_thrust_percent
        turning_torque = self.turning_distance * self.angular_force
        if turning_torque != 0:
            self.angular_acceleration = turning_torque / self.angular_inertia
        else:
            self.angular_acceleration = 0

    def apply_acceleration_velocity(self, delta_time):
        """
        applies the acceleration and the velocity. the velocity applied to the angle is * by delta_time to convert it
        from degree per second to degrees per frame
        """
        self.angular_velocity += math.degrees(self.angular_acceleration)
        self.angle += self.angular_velocity * delta_time
        if self.angle > 360:
            self.angle -= 360
        elif self.angle < 0:
            self.angle += 360

        self.find_final_angle(delta_time)

    def find_final_angle(self, delta_time):
        deceleration = math.degrees(self.angular_acceleration)
        velocity = self.angular_velocity
        if deceleration > 0: deceleration *= -1
        if velocity > 0: velocity *= -1

        if deceleration == 0: time_to_0 = 0.6
        else: time_to_0 = (velocity / deceleration) * delta_time

        self.final_angle = self.angle + (0.5 * (self.angular_velocity * delta_time) * time_to_0)
        """
            debug print statements
            print(velocity, ":", deceleration)
            print(time_to_0)
            print(self.final_angle, ":", self.target_angle)
        """

    def check_contact(self):
        hits = arcade.check_for_collision_with_list(self, self.handler.player.bullets)
        if len(hits) > 0:
            self.handler.player.score += 1
            for pointer in self.handler.player.enemy_pointers:
                if pointer.target == self:
                    pointer.remove_from_sprite_lists()
                    del pointer
            self.remove_from_sprite_lists()
            for hit in hits:
                hit.remove_from_sprite_lists()
                del hit
            del self

    def if_hit_player(self):
        hits = arcade.check_for_collision_with_list(self.handler.player, self.bullets)
        if len(hits) > 0:
            self.handler.player.hit = True
            self.handler.player.deaths += 1
            for hit in hits:
                hit.remove_from_sprite_lists()
                del hit
