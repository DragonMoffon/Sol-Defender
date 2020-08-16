import math
import time
import json

import arcade

import bullet
import ui
import vector


class Player(arcade.Sprite):

    def __init__(self, holder):

        super().__init__()

        self.bullet_type = {
             "type": "Standard",
             "scale": 0.05,
             "texture": "Sprites/Player/bullets/standard.png",
             "speed": 420,
             "age": 2,
             "damage": 4,
             "hit_box": [[-20.0, 40.0], [-20.0, -40.0], [0.0, -60.0], [0.0, -70.0], [40.0, -80.0], [100.0, -80.0],
                         [120.0, -70.0], [140.0, -60.0], [150.0, -50.0], [160.0, -30.0], [160.0, 30.0], [150.0, 50.0],
                         [140.0, 60.0], [120.0, 70.0], [100.0, 80.0], [40.0, 80.0], [0.0, 70.0], [0.0, 60.0],
                         [-10.0, 50.0]]}
        # Debug / switches
        self.show_hit_box = False
        self.alt = False

        # audio
        file_name = "Music/shot.wav"
        self.shot_audio = arcade.Sound(file_name, streaming=True)

        self.pause_delay = 0

        self.start = 0

        self.hit = False

        # Upgrades
        self.passive_upgrades = []
        self.activated_upgrades = []
        self.upgrade_mod = {
            "max_health": 0,
            "time_heal": 0,
            "heal_rate": 0,
            "cool_speed": 0,
            "heat_speed": 0,
            "damage": 0,
            "thruster_force": 0,
            "shoot_delay": 0
        }

        self.base_max_health = 100

        self.base_time_heal = 15

        self.base_heal_rate = 1.5

        self.base_cool_speed = 0.01

        self.base_damage = 4

        self.base_thruster_force = 750000

        self.base_delay = 0.125

        # health Variables
        self.max_health = self.base_max_health
        self.health = self.max_health
        self.num_segments = 5
        self.health_segment = self.max_health / self.num_segments
        self.current_segment = 5
        self.last_damage = 0
        self.time_heal = self.base_time_heal
        self.heal_rate = self.base_heal_rate
        self.dead = False

        # Gravity_variables
        self.gravity_handler = None
        self.gravity_influences = []
        self.gravity_acceleration = [0.0, 0.0]
        self.gravity_weakener = 0

        # Ui
        self.holder = holder
        self.ui = ui.PlayerUi(self, self.holder)
        self.holder.gravity_handler.set_gravity_object(self)
        self.collision_warning = False

        # variables for gun overheating
        self.heat_level = 0
        self.cool_speed = self.base_cool_speed
        self.heat_speed = 0
        self.over_heating = False
        self.heat_damage = 1

        # damage
        self.total_damage = 0

        # Variables for movement
        self.speed_limit = True
        self.thruster_force = 750000
        self.turning_thruster_force = 330000
        self.thrusters_output = [0.0, 0.0]
        self.weight = 450000
        self.forward_force = 0
        self.acceleration = [0.0, 0.0]
        self.velocity = [0.0, 0.0]

        # Variables for turning
        self.correcting = False
        self.turn_key = False
        self.turning_force = 0
        self.turning_acceleration = 0
        self.angle_velocity = 0
        self.distance_to_turning = 30
        self.angular_inertia = (1 / 12) * self.weight * (64.5 ** 2)
        self.correction = 0.33

        self.target_angle = 0
        self.mouse_pos_xy = [0.0, 0.0]
        self.previous_mouse_pos = [0.0, 0.0, 0.0]
        self.target_distance = 0
        self.mouse_moved = False

        # Parent Variables
        self.texture = arcade.load_texture("Sprites/Player/Ships/Saber Solo.png")
        self.scale = 0.1

        self.true_aim = arcade.Sprite("Sprites/Player/Ui/true_aim_light.png", scale=0.1,
                                      center_x=self.center_x, center_y=self.center_y)

        # shooting variables
        self.shooting = False
        self.delay = self.base_delay
        self.bullets = arcade.SpriteList()
        self.last_shot = 0

        # Enemy Pointer Variables
        self.enemy_handler = None
        self.enemy_pointers = arcade.SpriteList()

        # hit box
        self.hit_box = ((-145, -5), (-145, 5), (-105, 5), (-105, 15), (-75, 15), (-75, 25), (-135, 25), (-135, 35),
                        (-125, 35), (-125, 55), (-115, 55), (-115, 75), (-85, 75), (-85, 105), (-125, 105), (-125, 135),
                        (-135, 135), (-135, 155), (-145, 155), (-145, 185), (-125, 185), (-125, 195), (-165, 195),
                        (-165, 205), (-135, 205), (-135, 215), (-35, 215), (-35, 205), (25, 205), (25, 195), (85, 195),
                        (85, 185), (125, 185), (125, 175), (135, 175), (135, 165), (145, 165), (145, 155), (155, 155),
                        (155, 135), (165, 135), (165, 55), (115, 55), (115, 45), (65, 45), (65, 35), (75, 35), (75, 15),
                        (85, 15), (85, -15), (75, -15), (75, -35), (65, -35), (65, -45), (115, -45), (115, -55),
                        (165, -55), (165, -135), (155, -135), (155, -155), (145, -155), (145, -165), (135, -165),
                        (135, -175), (125, -175), (125, -185), (85, -185), (85, -195), (25, -195), (25, -205),
                        (-35, -205), (-35, -215), (-135, -215), (-135, -205), (-165, -205), (-165, -195), (-125, -195),
                        (-125, -185), (-145, -185), (-145, -155), (-135, -155), (-135, -135), (-125, -135),
                        (-125, -105), (-85, -105), (-85, -75), (-115, -75), (-115, -55), (-125, -55), (-125, -35),
                        (-135, -35), (-135, -25), (-75, -25), (-75, -15), (-105, -15), (-105, -5))

    """
    arcade.Sprite Methods
    """

    def on_update(self, delta_time: float = 1 / 60):
        self.heal(delta_time)
        self.apply_correction()
        self.calculate_thruster_force()
        self.calculate_turning_acceleration()
        self.calculate_acceleration()
        self.apply_acceleration()
        self.move(delta_time)

        if self.over_heating:
            self.shooting = False

        self.bullets.on_update(delta_time)
        if self.shooting and self.last_shot + self.delay < time.time() and self.heat_level < 1:
            self.shoot()
            self.last_shot = time.time()
            self.heat_speed = (self.base_damage / 100) * (1 - self.upgrade_mod['heat_speed'])
            self.heat_level += self.heat_speed
            self.heat_damage = 1 + self.heat_level
            if self.heat_level >= 1:
                self.heat_level = 1
                self.over_heating = True
        elif self.heat_level > self.cool_speed and not self.shooting:
            self.heat_level -= self.cool_speed
            self.heat_damage = 1
        elif not self.shooting:
            self.heat_damage = 1
            self.heat_level = 0
            self.over_heating = False

        self.enemy_pointers.on_update(delta_time)
        self.total_damage = (self.base_damage * self.heat_damage) * (1 + self.upgrade_mod['damage'])

    def after_update(self):
        if self.alt:
            self.mouse_angle()

    def draw(self):
        self.ui.under_draw()
        self.enemy_pointers.draw()
        self.bullets.draw()
        super().draw()
        if self.alt:
            self.true_aim.draw()
        for index, mods in enumerate(self.upgrade_mod):
            if self.upgrade_mod[mods] != 0:
                x = self.holder.left_view + 25
                y = self.holder.bottom_view + 250 + index * 25
                arcade.draw_text(f"{mods}: {self.upgrade_mod[mods]}", x, y, arcade.color.WHITE)
        if self.show_hit_box:
            arcade.draw_text(str(self.current_segment),
                             self.center_x, self.center_y + 60,
                             arcade.color.WHITE)

            arcade.draw_circle_outline(self.center_x, self.center_y, 480, arcade.color.GREEN)
            arcade.draw_circle_outline(self.center_x, self.center_y, 330, arcade.color.GREEN)
            arcade.draw_circle_outline(self.center_x, self.center_y, 285, arcade.color.ORANGE)
            arcade.draw_circle_outline(self.center_x, self.center_y, 75, arcade.color.RADICAL_RED)

            self.draw_hit_box()
            for shot in self.bullets:
                arcade.draw_line(shot.center_x, shot.center_y,
                                 shot.velocity[0] + shot.center_x, shot.velocity[1] + shot.center_y,
                                 arcade.color.CYBER_YELLOW)
            """
            self.draw_hit_box(color=arcade.color.LIME_GREEN)
            """
            arcade.draw_line(self.center_x, self.center_y,
                             self.center_x + self.velocity[0], self.center_y + self.velocity[1],
                             arcade.color.CYBER_YELLOW)

        self.ui.draw()
        
    """
    Physics Movement Methods
    """

    def apply_correction(self):
        if not self.turn_key:
            if self.angle_velocity > self.correction:
                self.thrusters_output[0] = -self.correction
            elif self.angle_velocity < -self.correction:
                self.thrusters_output[0] = self.correction
            else:
                self.angle_velocity = 0
                self.thrusters_output[0] = 0

        """if not self.turn_key and 0 < self.angle_velocity <= self.turning_acceleration\
                or self.turning_acceleration < self.angle_velocity < 0:
            self.thrusters_output[0] = 0
            self.angle_velocity = 0
        elif not self.turn_key and not self.correcting:
            needed_acceleration = math.radians((-self.angle_velocity)/250)
            self.thrusters_output[0] = self.calculate_thruster_output(needed_acceleration)
            self.correcting = True"""

    def calculate_thruster_output(self, needed_acceleration):
        turning_torque = needed_acceleration * self.angular_inertia
        turning_force = turning_torque / self.distance_to_turning
        return turning_force / self.turning_thruster_force

    def calculate_thruster_force(self):
        self.turning_force = self.turning_thruster_force * self.thrusters_output[0]
        if self.thrusters_output[0] < -self.correction and self.angle_velocity > 0 and self.turn_key:
            self.turning_force *= 1.5
        elif self.thrusters_output[0] > self.correction and self.angle_velocity < 0 and self.turn_key:
            self.turning_force *= 1.5
        self.forward_force = self.thrusters_output[1] * self.thruster_force * 4

    def calculate_acceleration(self):
        angle_rad = math.radians(self.angle)
        acceleration = self.forward_force / self.weight
        dx = round(math.cos(angle_rad) * acceleration, 2)
        dy = round(math.sin(angle_rad) * acceleration, 2)
        self.acceleration = [dx, dy]

    def calculate_turning_acceleration(self):
        turning_torque = self.distance_to_turning * self.turning_force
        if turning_torque != 0:
            acceleration = math.degrees(turning_torque / self.angular_inertia)
        else:
            acceleration = 0
        self.turning_acceleration = acceleration

    def apply_acceleration(self):
        if not self.alt:
            self.angle_velocity += self.turning_acceleration
        self.velocity[0] += self.acceleration[0]
        self.velocity[1] += self.acceleration[1]

        if self.start > 1:
            self.velocity[0] += self.gravity_acceleration[0] * self.gravity_weakener
            self.velocity[1] += self.gravity_acceleration[1] * self.gravity_weakener

    def move(self, delta_time):
        self.angle += self.angle_velocity * delta_time
        if self.angle > 360:
            self.angle -= 360
        elif self.angle < 0:
            self.angle += 360
        if self.speed_limit:
            speed_limit = 2500
            speed = math.sqrt(self.velocity[0]**2 + self.velocity[1]**2)
            if speed > speed_limit:
                self.velocity[0] = (self.velocity[0]/speed) * speed_limit
                self.velocity[1] = (self.velocity[1]/speed) * speed_limit

        self.center_x += self.velocity[0] * delta_time
        self.center_y += self.velocity[1] * delta_time

    """
    Other Methods
    """
    def setup_upgrades(self, input_upgrade=None):
        if input_upgrade is not None:
            self.passive_upgrades.append(input_upgrade)
        for mods in self.upgrade_mod:
            self.upgrade_mod[mods] = 0

        for upgrades in self.passive_upgrades:
            self.upgrade_mod[upgrades["bonus_name"]] += upgrades['bonus']
            self.upgrade_mod[upgrades['bane_name']] -= upgrades['bane']

        self.max_health = self.base_max_health * (1 + self.upgrade_mod['max_health'])
        gain = self.max_health - self.base_max_health
        self.health_segment = self.max_health / self.num_segments
        self.health += gain
        if self.health > self.max_health:
            self.health = self.max_health
        self.time_heal = self.base_time_heal * (1 - self.upgrade_mod['time_heal'])
        self.heal_rate = self.base_heal_rate * (1 + self.upgrade_mod['heal_rate'])
        self.cool_speed = self.base_cool_speed * (1 + self.upgrade_mod['cool_speed'])
        self.thruster_force = self.base_thruster_force * (1 + self.upgrade_mod['thruster_force'])
        self.delay = self.base_delay * (1 - self.upgrade_mod['shoot_delay'])

    def heal(self, delta_time):
        if self.health > self.max_health:
            self.health = self.max_health
            self.current_segment = 5
        elif self.health <= 0:
            self.health = 0
            self.dead = True
            self.clear_upgrades()
        elif self.health <= self.health_segment * (self.current_segment-1):
            self.current_segment -= 1
        if time.time() > self.last_damage + self.time_heal and self.health < self.max_health:
            if self.health < self.current_segment * self.health_segment:
                self.health += self.heal_rate * delta_time
            if self.health > self.health_segment * (self.current_segment+1):
                self.health = self.health_segment * (self.current_segment+1)

    def shoot(self):
        self.shot_audio.play(volume=0.1)
        self.bullet_type['damage'] = self.total_damage
        shot = bullet.Bullet([self.center_x, self.center_y], self.angle, self.velocity, self.bullet_type)
        self.gravity_handler.set_gravity_object(shot)
        self.bullets.append(shot)

    def clear_upgrades(self):
        with open('Data/current_upgrade_data.json', 'w') as file:
            self.passive_upgrades = []
            json.dump(self.passive_upgrades, file)

    def read_upgrades(self):
        with open('Data/current_upgrade_data.json') as upgrade_file:
            self.passive_upgrades = json.load(upgrade_file)
        self.setup_upgrades()

    def mouse_angle(self):
        mouse_pos = (self.holder.left_view + self.mouse_pos_xy[0],
                     self.holder.bottom_view + self.mouse_pos_xy[1])
        self_pos = (self.center_x, self.center_y)
        self.target_distance = vector.find_distance(mouse_pos, self_pos)
        if self.mouse_moved:
            angle = vector.find_angle(mouse_pos, self_pos)
            self.target_angle = angle
            self.mouse_moved = False

        angle_diff = vector.calc_small_difference(self.target_angle, self.angle)
        direction = vector.calc_direction(self.target_angle, self.angle)
        difference = self.target_distance - self.previous_mouse_pos[2]
        self.angle_velocity = direction * angle_diff * 10
        self.previous_mouse_pos[2] += difference / 30
        self.true_aim.center_x = self.center_x + (math.cos(math.radians(self.angle)) * self.previous_mouse_pos[2])
        self.true_aim.center_y = self.center_y + (math.sin(math.radians(self.angle)) * self.previous_mouse_pos[2])

    """
    Key Press methods
    """

    def key_down(self, key):

        if key == arcade.key.W:
            self.thrusters_output[1] = 1.0
        elif key == arcade.key.A:
            self.thrusters_output[0] = 1.0
            self.turn_key = True
            self.correcting = False
        elif key == arcade.key.D:
            self.thrusters_output[0] = -1.0
            self.turn_key = True
            self.correcting = False

        elif key == arcade.key.V:
            self.angle = 180
        elif key == arcade.key.B:
            self.angle = 90
        elif key == arcade.key.N:
            self.angle = 45

        elif key == arcade.key.SPACE:
            self.shooting = True

        elif key == arcade.key.TAB and not self.show_hit_box:
            self.show_hit_box = True
        elif key == arcade.key.TAB:
            self.show_hit_box = False

        elif key == arcade.key.LALT and not self.alt:
            self.alt = True
        elif key == arcade.key.LALT:
            self.alt = False

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

    def on_mouse_movement(self, x, y):
        if self.alt:
            self.mouse_pos_xy = [x, y]
            self.mouse_angle()
            self.mouse_moved = True

    def on_mouse_press(self, button):
        if button == arcade.MOUSE_BUTTON_LEFT and not self.over_heating:
            self.shooting = True
        elif button == arcade.MOUSE_BUTTON_RIGHT:
            self.thrusters_output[1] = 1.0

    def on_mouse_release(self, button):
        if button == arcade.MOUSE_BUTTON_LEFT:
            self.shooting = False
        elif button == arcade.MOUSE_BUTTON_RIGHT:
            self.thrusters_output[1] = 0.0
