import math
import time
import json

import arcade

import game_data.bullet as bullet
import game_data.ui as ui
import game_data.vector as vector


class Player(arcade.Sprite):

    def __init__(self, ship_type, holder, m_speed, g_damp):
        super().__init__()

        # Data for the ship type.
        self.ship_type = ship_type
        self.thruster_array = ship_type['thruster array']

        # Data for the different bullets.
        self.bullet_type = {
             "type": "Standard",
             "scale": 0.05,
             "texture": "game_data/Sprites/Player/bullets/standard.png",
             "speed": 420,
             "age": 2,
             "damage": 4,
             "hit_box": [[-20.0, 40.0], [-20.0, -40.0], [0.0, -60.0], [0.0, -70.0], [40.0, -80.0], [100.0, -80.0],
                         [120.0, -70.0], [140.0, -60.0], [150.0, -50.0], [160.0, -30.0], [160.0, 30.0], [150.0, 50.0],
                         [140.0, 60.0], [120.0, 70.0], [100.0, 80.0], [40.0, 80.0], [0.0, 70.0], [0.0, 60.0],
                         [-10.0, 50.0]]}

        # Debug / switches
        self.show_hit_box = False
        self.alt = True

        # audio
        file_name = "game_data/Music/shot.wav"
        self.shot_audio = arcade.Sound(file_name, streaming=True)

        # Delay for bullets when pausing.
        self.pause_delay = 0

        # When to spawn enemies
        self.start = 0

        # Whether the player has been hit.
        self.hit = False

        # Upgrades
        self.activated_upgrades = [None, None, None]
        self.start_time = 0
        self.ability_active = False
        self.stored_data = {
            "bonus": "",
            "prev_bonus_value": 0,
            "bane": "",
            "prev_bane_value": 0,
            "duration": 0
        }

        self.passive_upgrades = []
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

        # Base stats for upgrades.
        self.base_max_health = ship_type['health']

        self.base_time_heal = 15

        self.base_heal_rate = 1.5

        self.base_cool_speed = 0.01

        self.base_damage = ship_type['damage']

        self.base_thruster_force = ship_type['thruster force']

        self.base_delay = ship_type['delay']

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
        self.gravity_weakener = g_damp

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
        self.max_speed = m_speed
        self.thruster_force = self.base_thruster_force
        self.turning_thruster_force = 330000
        self.thrusters_output = {'l': 0, 'lc': 0, 'rc': 0, 'r': 0}
        self.weight = ship_type['weight']
        self.thruster_force_vector = [0.0, 0.0]
        self.forward_force = 0
        self.acceleration = [0.0, 0.0]
        self.velocity = [0.0, 0.0]
        self.speed = 0

        # Variables for turning
        self.correcting = False
        self.turn_key = False
        self.turning_force = 0
        self.turning_acceleration = 0
        self.angle_velocity = 0
        self.distance_to_turning = 30
        self.angular_inertia = (1 / 2) * self.weight * (ship_type['width'] ** 2)
        self.correction = 0.33

        # variables for mouse angle
        self.target_angle = 0
        self.mouse_pos_xy = [0.0, 0.0]
        self.previous_mouse_pos = [0.0, 0.0, 0.0]
        self.target_distance = 0
        self.mouse_moved = False

        # Parent Variables
        self.texture = arcade.load_texture(ship_type['texture'])
        self.scale = 0.1

        # Sprite showing where the player is aiming.
        self.true_aim = arcade.Sprite("game_data/Sprites/Player/Ui/true_aim_light.png", scale=0.1,
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
                      (-125, -185), (-145, -185), (-145, -155), (-135, -155), (-135, -135), (-125, -135),
                      (-125, -105), (-85, -105), (-85, -75), (-115, -75), (-115, -55), (-125, -55), (-125, -35),
                      (-135, -35), (-135, -25), (-75, -25), (-75, -15), (-105, -15), (-105, -5))
        self.points = point_list

        # The amount of scrap.
        self.scrap = 0

    def reset(self):
        """
        Resets the player so a new object does not need to be created.
        """

        # Delay for bullets when pausing.
        self.pause_delay = 0

        # When to spawn enemies
        self.start = 0

        # Whether the player has been hit.
        self.hit = False

        # Upgrades.
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
        self.read_upgrades()

        # Health variables.
        self.num_segments = 5
        self.health_segment = self.max_health / self.num_segments
        self.last_damage = 0
        self.dead = False

        # Gravity_variables.
        self.gravity_influences = []
        self.gravity_acceleration = [0.0, 0.0]

        # Ui.
        self.collision_warning = False

        # Variables for gun overheating.
        self.heat_level = 0
        self.cool_speed = self.base_cool_speed
        self.heat_speed = 0
        self.over_heating = False
        self.heat_damage = 1

        # Variables for movement.
        self.speed_limit = True
        self.thrusters_output = {'l': 0, 'lc': 0, 'rc': 0, 'r': 0}
        self.forward_force = 0
        self.acceleration = [0.0, 0.0]
        self.velocity = [0.0, 0.0]

        # Variables for turning.
        self.correcting = False
        self.turn_key = False
        self.turning_force = 0
        self.turning_acceleration = 0
        self.angle_velocity = 0

        # Mouse variables.
        self.target_angle = 0
        self.mouse_pos_xy = [0.0, 0.0]
        self.previous_mouse_pos = [0.0, 0.0, 0.0]
        self.target_distance = 0
        self.mouse_moved = False

        # Shooting variables.
        self.shooting = False
        self.delay = self.base_delay
        self.bullets = arcade.SpriteList()
        self.last_shot = 0

        # Enemy Pointer Variables
        self.enemy_handler = None
        self.enemy_pointers = arcade.SpriteList()

        # Position.
        self.center_x = 0
        self.center_y = 0
        self.angle = 0

        # Hit box.
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
                      (-125, -185), (-145, -185), (-145, -155), (-135, -155), (-135, -135), (-125, -135),
                      (-125, -105), (-85, -105), (-85, -75), (-115, -75), (-115, -55), (-125, -55), (-125, -35),
                      (-135, -35), (-135, -25), (-75, -25), (-75, -15), (-105, -15), (-105, -5))
        self.points = point_list

    def on_update(self, delta_time: float = 1 / 60):

        # If an active ability is in use, and the duration is up then resole the active ability.
        if self.ability_active and self.start_time:
            if self.start_time + self.stored_data['duration'] < time.time():
                self.resolve_active()

        # Heal the player.
        self.heal(delta_time)

        # If not using the mouse apply correction.
        if not self.alt:
            self.apply_correction()

        # Find the acceleration vector and turning speeds, then apply them, then move.
        self.calculate_acceleration_vectors()
        self.apply_acceleration()
        self.move(delta_time)

        # If the player is over heating, then stop the player shooting.
        if self.over_heating:
            self.shooting = False

        # update the bullets, and shoot if the player is not over heating
        # and the time has been long enough from last shot
        self.bullets.on_update(delta_time)
        if self.shooting and self.last_shot + self.delay < time.time() and self.heat_level < 1:

            # Shoot and heat up the player.
            self.shoot()
            self.last_shot = time.time()
            self.heat_speed = (self.base_damage / 100) * (1 - self.upgrade_mod['heat_speed'])
            self.heat_level += self.heat_speed

            # The higher the heat the greater the damage.
            self.heat_damage = 1 + self.heat_level

            # If the player's heat is too high, stop them from shooting and damage them.
            if self.heat_level >= 1:
                self.heat_level = 1
                self.over_heating = True
                self.health -= self.health_segment
        elif self.heat_level > self.cool_speed and not self.shooting:
            # If the player is cooling down, rather than shooting.
            self.heat_level -= self.cool_speed
            self.heat_damage = 1
        elif not self.shooting:
            # If the player is not shooting and have finished cooling down.
            self.heat_damage = 1
            self.heat_level = 0
            self.over_heating = False

        # update the pointers and find the total damage.
        self.enemy_pointers.on_update(delta_time)
        self.total_damage = (self.base_damage * self.heat_damage) * (1 + self.upgrade_mod['damage'])

    def after_update(self):
        # Update after other functions in the main.
        if self.alt:
            self.mouse_angle()

    def draw(self):
        # Draw.
        if not self.dead:
            self.ui.under_draw()
            self.enemy_pointers.draw()
            self.bullets.draw()
        super().draw()
        if not self.dead:
            if self.alt:
                self.true_aim.draw()

            self.ui.draw()
        
    """
    Physics Movement Methods
    """

    def calculate_acceleration_vectors(self):
        """
        Using kinematic equations, vector addition, rotation matrix, and torque equations.

        This function calculates the force and torque each thruster applies to player as linear and angular acceleration
        """
        total_vector = [0, 0]
        total_torque = 0
        # For each thruster calculate.
        for thruster in self.thruster_array:
            # Torque
            dot = (thruster['direction_v'][0] * thruster['position'][0] +
                   thruster['direction_v'][1] * thruster['position'][1])

            # find the angle between the vectors using the total magnitude and the dot product.
            vec_angle = math.acos(dot / thruster['distance'])

            # Force Vector
            normal_force = -(self.thruster_force * math.cos(vec_angle))
            total_vector[0] += thruster['direction_v'][0]\
                               * self.thrusters_output[thruster['alignment']] * normal_force * thruster['output']
            total_vector[1] += thruster['direction_v'][1]\
                               * self.thrusters_output[thruster['alignment']] * normal_force * thruster['output']

            # Rotation Force.
            tangential_force = (self.thruster_force * math.sin(vec_angle) * thruster['output'])
            torque = (thruster['distance'] * tangential_force * self.thrusters_output[thruster['alignment']])

            if 'r' in thruster['alignment']:
                total_torque -= torque
            else:
                total_torque += torque

        # Use a rotation matrix  to rotate the total force vector
        prev_x = total_vector[0]
        rad_angle = math.radians(self.angle)
        total_vector[0] = (prev_x * math.cos(rad_angle) - total_vector[1] * math.sin(rad_angle))
        total_vector[1] = (prev_x * math.sin(rad_angle) + total_vector[1] * math.sin(rad_angle))

        self.thruster_force_vector = total_vector

        self.acceleration = [total_vector[0] / self.weight, total_vector[1] / self.weight]

        # If there is torque, then calculate the angular acceleration.
        if total_torque != 0:
            acceleration = math.degrees(total_torque / self.angular_inertia)
        else:
            acceleration = 0

        self.turning_acceleration = acceleration

    def apply_correction(self):
        """
        If the player is using A and D to turn this method finds the direction and force the player's turning thrusters
        exert to slow down the crafts turning. This correction is not as powerful as what the player can do.
        """

        if not self.turn_key:
            correction_acceleration = 0
            total_vector = [0, 0]

            # First as with the calculations in self.calculate_acceleration_vectors() The torque
            # is calculated.
            for thruster in self.thruster_array:
                dot = (thruster['direction_v'][0] * thruster['position'][0] +
                       thruster['direction_v'][1] * thruster['position'][1])

                vec_angle = math.acos(dot / thruster['distance'])

                torque = (thruster['distance'] * self.thruster_force * self.thrusters_output[thruster['alignment']]
                          * thruster['output'] * math.sin(vec_angle))
                if 'r' in thruster['alignment']:
                    correction_acceleration -= torque
                else:
                    correction_acceleration += torque

            # The torque is then converted to angular acceleration
            correction_acceleration = math.degrees(correction_acceleration/self.angular_inertia)

            # If the turning velocity is greater than this correction than slow the ship down.
            if self.angle_velocity > 2 * correction_acceleration:
                self.thrusters_output['r'] = self.correction
                self.thrusters_output['l'] = 0
            elif self.angle_velocity < 2 * -correction_acceleration:
                self.thrusters_output['l'] = self.correction
                self.thrusters_output['r'] = 0
            else:
                self.angle_velocity = 0
                self.thrusters_output['r'] = 0
                self.thrusters_output['l'] = 0

    def apply_acceleration(self):
        # If the player is using A and D to turn apply turning acceleration.
        if not self.alt:
            self.angle_velocity += self.turning_acceleration

        # Apply the calculated acceleration vector.
        self.velocity[0] += self.acceleration[0]
        self.velocity[1] += self.acceleration[1]

        # If the player has moved apply gravity to them.
        if self.start > 1:
            self.velocity[0] += self.gravity_acceleration[0] * self.gravity_weakener
            self.velocity[1] += self.gravity_acceleration[1] * self.gravity_weakener

    def move(self, delta_time):
        # Move the player based on their angular and liner velocity.
        self.angle += self.angle_velocity * delta_time
        if self.angle > 360:
            self.angle -= 360
        elif self.angle < 0:
            self.angle += 360

        # Cap the player's speed otherwise the game becomes unmanageable.
        if self.speed_limit:
            self.speed = math.sqrt(self.velocity[0]**2 + self.velocity[1]**2)
            if self.speed > self.max_speed:
                self.velocity[0] = (self.velocity[0]/self.speed) * self.max_speed
                self.velocity[1] = (self.velocity[1]/self.speed) * self.max_speed
                self.speed = self.max_speed

        self.center_x += self.velocity[0] * delta_time
        self.center_y += self.velocity[1] * delta_time

    """
    Other Methods
    """

    def add_scrap(self):
        # Record scrap that is collected.
        self.holder.player_scrap += 1

    def apply_upgrades(self):
        """
        This method takes the calculated upgrade bonuses and applies them to the various variables they affect.
        """

        # calculate new Max health and how much this heals the player.
        self.max_health = self.base_max_health * (1 + self.upgrade_mod['max_health'])
        gain = self.max_health - self.base_max_health
        self.health_segment = self.max_health / self.num_segments
        self.health += gain
        if self.health > self.max_health:
            self.health = self.max_health

        # apply all other upgrades that are not applied at the time of use like damage.
        self.time_heal = self.base_time_heal * (1 - self.upgrade_mod['time_heal'])
        self.heal_rate = self.base_heal_rate * (1 + self.upgrade_mod['heal_rate'])
        self.cool_speed = self.base_cool_speed * (1 + self.upgrade_mod['cool_speed'])
        self.thruster_force = self.base_thruster_force * (1 + self.upgrade_mod['thruster_force'])
        self.delay = self.base_delay * (1 - self.upgrade_mod['shoot_delay'])

    def clean_upgrades(self):
        # reset the upgrade modifiers to nothing
        for mods in self.upgrade_mod:
            self.upgrade_mod[mods] = 0

        # Then reapply the bonuses supplied by upgrades.
        for upgrades in self.passive_upgrades:
            self.upgrade_mod[upgrades["bonus_name"]] += upgrades['bonus']
            self.upgrade_mod[upgrades['bane_name']] -= upgrades['bane']

    def setup_upgrades(self, input_upgrade=None):
        # Add a new upgrade if supplied then manage the upgrades.
        if input_upgrade is not None:
            self.passive_upgrades.append(input_upgrade)

        self.clean_upgrades()
        self.apply_upgrades()

    def do_active(self, key):
        """
        This method creates the temporary bonus to the player's upgrades in a major way.

        :param key: which key is pressed, 1, 2, or 3.
        """

        # If a key was supplied, store the previous bonuses and banes of the upgrade before the active upgrade is
        # applied. Then apply the active upgrade and setup the new upgrades.
        if self.activated_upgrades[key] is not None:
            ability = self.activated_upgrades[key]
            self.stored_data['bonus'] = ability['bonus_name']
            self.stored_data['prev_bonus_value'] = self.upgrade_mod[ability['bonus_name']]
            self.stored_data['bane'] = ability['bane_name']
            self.stored_data['prev_bane_value'] = self.upgrade_mod[ability['bane_name']]
            self.stored_data['duration'] = ability['duration']

            self.upgrade_mod[ability['bonus_name']] = ability['bonus']
            self.upgrade_mod[ability['bane_name']] = - ability['bane']

            self.apply_upgrades()

            # record when the ability starts to know how long it has run for.
            self.start_time = time.time()
            self.ability_active = True

    def resolve_active(self):
        # Once the duration has ended, reset the affected abilities, and apply the new upgrade values.
        self.start_time = 0
        self.ability_active = False

        self.upgrade_mod[self.stored_data['bonus']] = self.stored_data['prev_bonus_value']
        self.upgrade_mod[self.stored_data['bane']] = self.stored_data['prev_bane_value']

        self.apply_upgrades()

    def heal(self, delta_time):
        """
        Manages the player's segmented healing and checks if they are alive or dead.
        """
        if self.health > 0:
            # If the player is alive
            if self.health > self.max_health:
                # Ensure their health is not greater than its max.
                self.health = self.max_health
                self.current_segment = 5
            elif self.health <= self.health_segment * (self.current_segment-1):
                # check if their health segment is correct.
                self.current_segment -= 1
            if time.time() > self.last_damage + self.time_heal and self.health < self.max_health:
                # If they should be healing than heal based of their upgradeable heal rate variable.
                if self.health < self.current_segment * self.health_segment:
                    self.health += self.heal_rate * delta_time
                if self.health > self.health_segment * (self.current_segment+1):
                    self.health = self.health_segment * (self.current_segment+1)
        else:
            # If the player is dead, kill them and clean their upgrades.
            self.health = 0
            self.dead = True
            self.clear_upgrades()

    def shoot(self):
        # Shoot a bullet and play the shooting audio.
        self.shot_audio.play(volume=0.2)
        self.bullet_type['damage'] = self.total_damage
        shot = bullet.Bullet([self.center_x, self.center_y], self.angle, self.velocity, self.bullet_type)
        self.bullets.append(shot)

    def clear_upgrades(self):
        # Reset the current_upgrade_data.json file.
        with open('game_data/Data/current_upgrade_data.json', 'w') as file:
            self.passive_upgrades = []
            self.activated_upgrades = [None, None, None]
            final = {'passive': self.passive_upgrades, 'active': self.activated_upgrades}
            json.dump(final, file, indent=4)

    def read_upgrades(self):
        # Read the upgrades file and Save them seperated into passive and active upgrades.
        with open('game_data/Data/current_upgrade_data.json') as upgrade_file:
            upgrade_json = json.load(upgrade_file)
            self.passive_upgrades = upgrade_json['passive']
            self.activated_upgrades = upgrade_json['active']
        self.setup_upgrades()

    def dump_upgrades(self):
        # Save all of the upgrade the player has.
        with open('game_data/Data/current_upgrade_data.json', 'w') as file:
            final = {'passive': self.passive_upgrades, 'active': self.activated_upgrades}
            json.dump(final, file, indent=4)

    def mouse_angle(self):
        """
        This method finds the angle from the player to the mouse and the fastest way to rotate towards it.
        It then finds a correct turning velocity to turn towards it.
        """

        # Find the mouses pos and find the angle towards it.
        mouse_pos = (self.holder.left_view + self.mouse_pos_xy[0],
                     self.holder.bottom_view + self.mouse_pos_xy[1])
        self_pos = (self.center_x, self.center_y)
        self.target_distance = vector.find_distance(mouse_pos, self_pos)
        if self.mouse_moved:
            angle = vector.find_angle(mouse_pos, self_pos)
            self.target_angle = angle
            self.mouse_moved = False

        # find the best direction to turn and make the players angular velocity in that direction.
        angle_diff = vector.calc_small_difference(self.target_angle, self.angle)
        direction = vector.calc_direction(self.target_angle, self.angle)
        difference = self.target_distance - self.previous_mouse_pos[2]
        self.angle_velocity = direction * angle_diff * 2.5

        # Find the position of the true aim marker that shows where the player is aimming.
        self.previous_mouse_pos[2] += difference / 30
        self.true_aim.center_x = self.center_x + (math.cos(math.radians(self.angle)) * self.previous_mouse_pos[2])
        self.true_aim.center_y = self.center_y + (math.sin(math.radians(self.angle)) * self.previous_mouse_pos[2])

    """
    Key Press methods
    """

    def key_down(self, key):
        # Only check the players key presses if they are alive.
        if not self.dead:
            if key == arcade.key.W:
                # If they press W than turn "on" their center thrusters.
                self.thrusters_output['lc'] = 1.0
                self.thrusters_output['rc'] = 1.0
            elif key == arcade.key.A:
                # If they press A than turn "on" their left thrusters and "off" their right thrusters.
                self.thrusters_output['l'] = 1.0
                self.thrusters_output['r'] = 0.0

                # Mark that they are pressing a turning key and stop calculating correction.
                self.turn_key = True
                self.correcting = False
            elif key == arcade.key.D:
                # If they press D than turn "on" their right thrusters and "off" their left thrusters.
                self.thrusters_output['r'] = 1.0
                self.thrusters_output['l'] = 0.0

                # Mark that they are pressing a turning key and stop calculating correction.
                self.turn_key = True
                self.correcting = False

            # Run the do active ability for keys 1, 2, and 3.
            if arcade.key.KEY_1 <= key <= arcade.key.KEY_3 and not self.ability_active:
                self.do_active(key-arcade.key.KEY_1)

            # Shoot.
            elif key == arcade.key.SPACE:
                self.shooting = True

            # Turn the Minimap on and off.
            elif key == arcade.key.TAB and not self.show_hit_box:
                self.show_hit_box = True
            elif key == arcade.key.TAB:
                self.show_hit_box = False

            # Turn using the mouse to aim on and off.
            elif key == arcade.key.LALT and not self.alt:
                self.alt = True
            elif key == arcade.key.LALT:
                self.alt = False

    def key_up(self, key):
        # Only check the players key presses if they are alive.
        if not self.dead:
            if key == arcade.key.W:
                # If the player lets go of W, stop the center thrusters.
                self.thrusters_output['lc'] = 0.0
                self.thrusters_output['rc'] = 0.0
            elif key == arcade.key.A and self.thrusters_output['r'] != 1.0:
                # If the player releases A and they where not turning right than stop the turning thrusters.
                self.thrusters_output['l'] = 0.0
                self.thrusters_output['r'] = 0.0
                self.turn_key = False
            elif key == arcade.key.D and self.thrusters_output['l'] != 1.0:
                # If the player releases D and they where not turning Left than stop the turning thrusters.
                self.thrusters_output['r'] = 0.0
                self.thrusters_output['l'] = 0.0
                self.turn_key = False
            elif key == arcade.key.SPACE:
                # If the player lets go of SPACE than stop shooting.
                self.shooting = False

    def on_mouse_movement(self, x, y):
        # If the player is aiming at the mouse than save the new mouse position.
        if self.alt and not self.dead:
            self.mouse_pos_xy = [x, y]
            self.mouse_angle()
            self.mouse_moved = True

    def on_mouse_press(self, button):
        # If the player is not dead record the mouse presses.
        if not self.dead:
            if button == arcade.MOUSE_BUTTON_LEFT and not self.over_heating:
                # If they can shoot and they press the Left Button than shoot.
                self.shooting = True
            elif button == arcade.MOUSE_BUTTON_RIGHT:
                # If they press the Right Button than accelerate the player.
                for output in self.thrusters_output:
                    self.thrusters_output[output] = 1.0

    def on_mouse_release(self, button):
        # If the player is not dead record the mouse presses.
        if not self.dead:
            if button == arcade.MOUSE_BUTTON_LEFT:
                # If the player release the Left Button, stop them shooting.
                self.shooting = False
            elif button == arcade.MOUSE_BUTTON_RIGHT:
                # If the player releases the Right Button, stop their thrusters
                for output in self.thrusters_output:
                    self.thrusters_output[output] = 0.0
