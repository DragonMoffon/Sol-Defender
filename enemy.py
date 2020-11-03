import math
import random
import time
import PIL

import arcade

import bullet
import ui
import vector


class Cluster(arcade.Sprite):

    def __init__(self, handler, target):
        super().__init__()
        point_list = (0.0, 0.1), (0.1, 0.0), (0.0, 0.0)

        self.set_hit_box(point_list)
        self.num_enemies = 0
        self.speed = random.randint(80, 100)

        self.center_x = 0
        self.center_y = 0

        self.handler = handler
        if target != self.handler.planet_data:
            self.target = target
        else:
            self.target = None

        self.spawned = False

        self.point = ui.Pointer()
        self.point.holder = self.handler.player
        self.point.target = self
        self.handler.player.enemy_pointers.append(self.point)

        self.distance = 0
        self.p_distance = 0

    def spawn_enemies(self, delta_time):
        p_d = self.handler.player.center_x, self.handler.player.center_y
        s_d = self.center_x, self.center_y
        if self.target is not None:
            t_d = self.target.center_x, self.target.center_y
            angle = math.radians(vector.find_angle(t_d, s_d))
            self.distance = vector.find_distance(t_d, s_d)
            d_x = math.cos(angle) * self.speed * delta_time
            d_y = math.sin(angle) * self.speed * delta_time
            self.center_x += d_x
            self.center_y += d_y
        else:
            self.distance = vector.find_distance(p_d, s_d)

        self.p_distance = vector.find_distance(p_d, s_d)
        self.spawn()

    def spawn(self):
        p_d = self.handler.player.center_x, self.handler.player.center_y
        s_d = self.center_x, self.center_y
        if self.distance < arcade.get_display_size()[0] or self.p_distance < arcade.get_display_size()[0]:
            planet_pos = (self.handler.planet_data.center_x, self.handler.planet_data.center_y)
            half_planet = self.handler.planet_data.width / 2
            r_angle_to_cluster = math.radians(vector.find_angle((self.center_x, self.center_y), planet_pos))
            distance_to_planet = (vector.find_distance((self.center_x, self.center_y), planet_pos)
                                  - half_planet)

            for i in range(self.num_enemies):
                enemy_type = random.randrange(0, len(self.handler.basic_types))
                bullet_type = self.handler.bullet_types[self.handler.basic_types[enemy_type]["shoot_type"]]
                enemy = Enemy(self.handler.basic_types[enemy_type], bullet_type)
                enemy.setup(self.handler, s_d, self)

                enemy.center_x = self.handler.planet_data.center_x
                enemy.center_y = self.handler.planet_data.center_y

                random_angle = random.uniform(-0.0872665, 0.0872665)
                enemy.center_x += math.cos(r_angle_to_cluster + random_angle) * (half_planet + distance_to_planet
                                                                                 + random.randint(-100, 100))
                enemy.center_y += math.sin(r_angle_to_cluster + random_angle) * (half_planet + distance_to_planet
                                                                                 + random.randint(-100, 100))
                self.handler.enemy_sprites.append(enemy)
            self.point.remove_from_sprite_lists()
            self.spawned = True

    def slaughter(self):
        self.spawned = True
        self.point.kill()
        self.num_enemies = 0


class Enemy(arcade.Sprite):
    """
    The Enemy class is used by the enemy handler in each wave. their movement works on a set of rules that
    calculate how they should move every update.
    """

    def __init__(self, type_data: dict, bullet_type: dict):
        super().__init__()

        # type
        self.type_data = type_data
        self.type = type_data['type']
        self.super_type = type_data['super_type']

        # checks if the enemy is in range of player
        self.handler = None
        self.target = None
        self.cluster = None
        self.fix = False

        # gravity variables
        self.gravity_handler = None
        self.gravity_acceleration = [0.0, 0.0]
        self.weight = 549054

        # movement
        self.turning_speed = 100
        self.velocity = [0.0, 0.0]

        # shooting variables
        self.firing = False
        self.bullet_type = bullet_type
        self.bullets = arcade.SpriteList()
        self.last_shot = 0
        self.shoot_delay = 0.1
        self.shoot_delay_range = type_data['shoot_delay']
        self.next_shot = 0
        self.num_shots = type_data['num_shots']
        self.start_angle = type_data['start_angle']
        self.angle_mod = type_data['angle_mod']

        self.shot_sound = arcade.Sound("Music/Enemy Shot.wav")
        self.shot_panning = -1
        self.shot_volume = 0

        # rapid shooting variables
        self.shots_this_firing = 0
        self.next_shot_rapid = 0
        self.shot_gap = 0.15

        # shooting variable to fix bug
        self.first_shot = False

        # sprites
        self.textures = []
        self.scale = 0.1
        self.get_sprites(type_data['image_file'])
        self.health = type_data['health']
        self.full_health = self.health
        if len(self.textures) - 1:
            self.health_segment = self.health / (len(self.textures) - 1)
        else:
            self.health_segment = 1
        self.frame = 1

        # gravity variables
        self.gravity_handler = None
        self.gravity_acceleration = [0.0, 0.0]

        # algorithm variables
        self.target = [0.0, 0.0]
        self.target_speed = 0
        self.target_acceleration = 0
        self.target_velocity = [0.0, 0.0]

        self.target_angle = 0
        self.angle_to_target = 0
        self.direction = 0
        self.difference = [0.0, 0.0]

        self.speed = 0

        self.target_distance = 0

        # Movement Rules
        self.rule_1_effect = [0.0, 0.0]
        self.rule_2_effect = [0.0, 0.0]
        self.rule_3_effect = [0.0, 0.0]
        self.rule_4_effect = [0.0, 0.0]
        self.rule_5_effect = [0.0, 0.0]
        self.rule_effects = [self.rule_1_effect, self.rule_2_effect, self.rule_4_effect,
                             self.rule_5_effect]

        self.do_rule = 0

        self.rule_1_priority = type_data['rules'][0]
        self.rule_2_priority = type_data['rules'][1]
        self.rule_3_priority = type_data['rules'][2]
        self.rule_4_priority = type_data['rules'][3]
        self.rule_5_priority = type_data['rules'][4]
        # Ability Variables
        try:
            self.abilities = type_data['abilities']
            self.active_ability = None
            self.active_frames = []
            self.ability_frames = []
            for frames in type_data['ability_frames']:
                frame_list = []
                self.get_sprites(frames, frame_list)
                self.ability_frames.append(frame_list)

            self.cool_down = 0
            self.cool_down_delay = 4
            self.start_time = 0
            self.duration = 0

        except KeyError:
            self.abilities = None
            self.active_ability = None
            self.active_frames = None
            self.ability_frames = None
            self.start_time = 0
            self.duration = 0

        self.thruster = None

    def setup(self, handler, x_y_pos: tuple = None, cluster: Cluster = None):
        """
        sets up the enemy in relation to the player. it also gives the enemy the handler for easier access to variables
        """
        self.cluster = cluster

        self.thruster = ui.EnemyExhaust(handler.game_window, self)

        if x_y_pos is None:
            x_y_pos = handler.player.center_x, handler.player.center_y

        self.handler = handler
        self.angle = random.randint(0, 360)

        self.set_hit_box(points=self.type_data['point_list'])

        handler.game_window.gravity_handler.set_gravity_object(self)

        if self.cluster is not None:
            pass
        else:
            rad_angle = round(random.uniform(0.0, 2 * math.pi), 2)
            self.center_x = x_y_pos[0] + math.cos(rad_angle) + random.randint(320, 600)
            self.center_y = x_y_pos[1] + math.sin(rad_angle) + random.randint(320, 600)

        point = ui.Pointer()
        point.holder = self.handler.player
        point.target = self

        self.target = self.handler.player
        self.target.enemy_pointers.append(point)
        self.velocity[0] = self.target.velocity[0]
        self.velocity[1] = self.target.velocity[1]

    def get_sprites(self, image_file, list_to_append: list = None):
        """
        Gets all of the hurt sprites for the enemy
        """
        image = PIL.Image.open(image_file)
        num_frames = image.size[1] // image.size[0]
        x = image.size[0]
        y = image.size[1] / num_frames
        for i in range(num_frames):
            texture = arcade.load_texture(image_file, 0, y * i, x, y)
            if list_to_append is None:
                self.textures.append(texture)
            else:
                list_to_append.append(texture)
        if list_to_append is None:
            self.texture = self.textures[0]

    def draw(self):
        """
        Draws the enemy sprite and bullets, as well as debug information
        """
        # self.thruster.on_draw()

        if self.firing:
            self.draw_hit_box(arcade.color.RADICAL_RED)

        if self.handler.player.show_hit_box:
            self.draw_hit_box(arcade.color.WHITE)

            for shot in self.bullets:
                arcade.draw_line(shot.center_x, shot.center_y,
                                 shot.velocity[0] + shot.center_x, shot.velocity[1] + shot.center_y,
                                 arcade.color.CYBER_YELLOW)

            string = str(self.health)
            arcade.draw_text(string, self.center_x, self.center_y - self.width, arcade.color.WHITE)

            arcade.draw_line(self.center_x + self.rule_1_effect[0] * 20, self.center_y + self.rule_1_effect[1] * 20,
                             self.center_x, self.center_y,
                             arcade.color.RADICAL_RED)
            arcade.draw_line(self.center_x + self.rule_2_effect[0] * 20, self.center_y + self.rule_2_effect[1] * 20,
                             self.center_x, self.center_y,
                             arcade.color.OCEAN_BOAT_BLUE)
            arcade.draw_line(self.center_x + self.rule_3_effect[0] * 20, self.center_y + self.rule_3_effect[1] * 20,
                             self.center_x, self.center_y,
                             arcade.color.WHITE_SMOKE)
            arcade.draw_line(self.center_x, self.center_y,
                             self.center_x + self.rule_4_effect[0] * 20, self.center_y + self.rule_4_effect[1] * 20,
                             arcade.color.LIME_GREEN)
            arcade.draw_line(self.center_x, self.center_y,
                             self.center_x + self.rule_5_effect[0] * 20, self.center_y + self.rule_5_effect[1] * 20,
                             arcade.color.ALLOY_ORANGE)
            arcade.draw_line(self.center_x + self.velocity[0], self.center_y + self.velocity[1],
                             self.center_x, self.center_y,
                             arcade.color.CYBER_YELLOW)
        self.bullets.draw()
        super().draw()

    def on_update(self, delta_time: float = 1 / 60):
        """
        Every update run different methods for the enemy and its algorithms.
        """

        if self.health <= 0:
            self.kill()

        # check contact
        self.check_contact()
        self.if_hit_player()

        # fix the enemies angle to be in the range 0 - 360
        self.fix_angle()

        # calculate different variables needed for the rules
        self.calculate_movement()

        # turn towards the player
        self.turn(delta_time)

        # gravity
        self.velocity[0] += self.gravity_acceleration[0]
        self.velocity[1] += self.gravity_acceleration[1]

        # run a counter to check when to do some of the rules, then calculate the rules and the resultant velocity
        self.do_rule += 1 * delta_time
        self.rules()

        # apply velocity
        self.center_x += self.velocity[0] * delta_time
        self.center_y += self.velocity[1] * delta_time

        # abilities
        if self.abilities is not None:
            self.ability_rules()

        # shooting
        if self.active_ability is None:
            self.shoot_rule()
            if self.firing:
                self.shoot()
        self.bullets.on_update(delta_time)

    def turn(self, delta_time):
        """
        turn the enemy to face the player.
        """
        if self.direction == -1:
            small_difference = self.difference[1]
        else:
            small_difference = self.difference[0]

        if self.turning_speed * delta_time < small_difference:
            self.angle += self.turning_speed * delta_time * self.direction
        else:
            self.angle += small_difference * self.direction

    def fix_angle(self):
        """
        for ease of calculating difference, fix the angle of the enemy sprite.
        """
        if self.angle > 360:
            self.angle -= 360
        elif self.angle < 0:
            self.angle += 360

        self.radians = math.radians(self.angle)

    def drop_scrap(self):
        if self.super_type != "boss":
            num = random.randrange(0, 4)
            for scrap in range(num):
                x_y = (self.center_x + random.randrange(-15, 16), self.center_y + random.randrange(-15, 16))
                drop = vector.Scrap(self.handler.player, self.handler, x_y)
                self.handler.scrap_list.append(drop)
            self.handler.count_dropped_scrap(num)

    def kill(self):

        self.handler.count_enemy_death()
        self.drop_scrap()

        for point in self.handler.player.enemy_pointers:
            if point.target == self:
                point.kill()

        if self.cluster is not None:
            self.cluster.num_enemies -= 1

        self.remove_from_sprite_lists()
        del self

    """
    Methods for different contact. Either being hit or hitting the player.
    """

    def check_contact(self):
        """
        Check to see if the player or an ally hits the enemy.
        """
        hits = arcade.check_for_collision_with_list(self, self.handler.player.bullets)
        for enemy in self.handler.enemy_sprites:
            if enemy != self and type(enemy) != vector.AnimatedTempSprite:
                e_hits = arcade.check_for_collision_with_list(self, enemy.bullets)
                if len(e_hits) > 0:
                    for hit in e_hits:
                        hits.append(hit)
        if len(hits) > 0:
            hit_copy = hits
            for index, hit in enumerate(hit_copy):
                hits[index].kill()
                self.health -= hit.damage
                if self.health <= self.full_health - (self.frame * self.health_segment) and not self.health < 0:
                    self.texture = self.textures[self.frame]
                    self.frame += 1
                if self.health <= 0:
                    death = vector.AnimatedTempSprite("Sprites/Enemies/enemy explosions.png",
                                                      (self.center_x, self.center_y))
                    self.handler.enemy_sprites.append(death)
                    self.kill()

    def if_hit_player(self):
        """
        check if the enemy hits the player
        """
        hits = arcade.check_for_collision_with_list(self.target, self.bullets)
        if len(hits) > 0:
            self.target.health -= self.bullet_type['damage']
            self.target.last_damage = time.time()
            file = "Music/player_damage.wav"
            sound = arcade.Sound(file)
            sound.play(volume=0.1)

            if self.target.health < 0:
                self.target.health = 0
            if self.target.health <= 0:
                self.target.dead = True

            self.target.hit = True
            for hit in hits:
                hit.kill()

    """
    Methods for calculating the different rules.
    """

    def calculate_movement(self):
        """
        calculates the variables needed for the algorithms.
        """
        # get the angle towards the player
        target = self.target
        self_pos = (self.center_x, self.center_y)
        target_pos = (target.center_x, target.center_y)
        self.target_angle = vector.find_angle(target_pos, self_pos)

        # find the difference and the direction
        self.difference = vector.calc_difference(self.target_angle, self.angle)
        self.direction = vector.calc_direction(self.target_angle, self.angle)

        self.target_velocity = target.velocity
        self.target_speed = math.sqrt(target.velocity[0] ** 2 + target.velocity[1] ** 2)
        if self.handler.player.forward_force / self.handler.player.weight > self.target_acceleration:
            self.target_acceleration = self.handler.player.forward_force / self.handler.player.weight

        # distance to player
        self.target_distance = vector.find_distance(self_pos, target_pos)

        # self speed
        self.speed = vector.find_distance((0.0, 0.0), self.velocity)

        diff_panning = self_pos[0] - target_pos[0]
        s_width = arcade.get_display_size()[0]
        if abs(diff_panning) < s_width:
            self.shot_panning = diff_panning / (s_width * 2)
        else:
            self.shot_panning = 0

        if self.target_distance < s_width:
            self.shot_volume = 0.12 - self.target_distance / (s_width * 12)
        else:
            self.shot_volume = 0

    def rules(self):
        """
        all of the enemy rules for movement.
        """
        self.rule_1_effect = self.rule1()
        if self.do_rule > 0.1:
            self.do_rule = 0
            if self.rule_2_priority:
                self.rule_2_effect = self.rule2()
            if self.rule_3_priority:
                self.rule_3_effect = self.rule3()
            if self.rule_4_priority:
                self.rule_4_effect = self.rule4()
            if self.rule_5_priority:
                self.rule_5_effect = self.rule5()

        self.rule_effects = [self.rule_1_effect, self.rule_2_effect, self.rule_3_effect,
                             self.rule_4_effect, self.rule_5_effect]

        final = [0.0, 0.0]
        final[0] = self.rule_1_effect[0] \
                   + self.rule_2_effect[0] \
                   + self.rule_3_effect[0] \
                   + self.rule_4_effect[0] \
                   + self.rule_5_effect[0]
        final[1] = self.rule_1_effect[1] \
                   + self.rule_2_effect[1] \
                   + self.rule_3_effect[1] \
                   + self.rule_4_effect[1] \
                   + self.rule_5_effect[1]

        self.velocity[0] += final[0]
        self.velocity[1] += final[1]

        """speed_limit = self.target_speed + 200
        speed = math.sqrt(self.velocity[0] ** 2 + self.velocity[1] ** 2)
        if speed > speed_limit:
            self.velocity[0] = (self.velocity[0] / speed) * speed_limit
            self.velocity[1] = (self.velocity[1] / speed) * speed_limit"""

    def ability_rules(self):
        if self.active_ability is None:
            for frames, ability in enumerate(self.abilities):
                if ability == 'invisibility':
                    self.invisibility_rule(frames)
                elif ability == 'mob':
                    self.mob_rule()

                if self.active_ability is not None:
                    break

        if self.active_ability == 'invisibility':
            self.invisibility_rule()
        elif self.active_ability == 'mob':
            self.mob_rule()

    """
    The Shooting Methods
    """

    def shoot_rule(self):
        if not self.firing and self.last_shot + self.shoot_delay < time.time():
            if self.difference[0] < 20 or self.difference[1] < 20 and self.target_distance < 750:
                self.firing = True
                for neighbor in self.handler.enemy_sprites:
                    distance_to_neighbor = vector.find_distance((self.center_x, self.center_y),
                                                                (neighbor.center_x, neighbor.center_y))
                    if neighbor != self:
                        if distance_to_neighbor < self.target_distance + 200:
                            angle_to_neighbor = vector.find_angle((neighbor.center_x, neighbor.center_y),
                                                                  (self.center_x, self.center_y))
                            difference = vector.calc_difference(angle_to_neighbor, self.angle)
                            if difference[0] < 45 or difference[1] < 45:
                                self.firing = False

                        if self.firing is False:
                            self.last_shot = time.time()
                            self.shoot_delay = random.randrange(self.shoot_delay_range[0], self.shoot_delay_range[1])
                            break

    def shoot(self):
        if self.firing and time.time() > self.next_shot:
            angle = self.angle + self.start_angle + (self.angle_mod * self.shots_this_firing)
            shot = bullet.Bullet([self.center_x, self.center_y], angle, self.velocity, self.bullet_type)
            self.bullets.append(shot)
            self.shots_this_firing += 1
            self.shot_sound.play(self.shot_volume, self.shot_panning)
            self.next_shot = time.time() + self.shot_gap

            if self.shots_this_firing >= self.num_shots:
                self.firing = False
                self.shots_this_firing = 0
                self.next_shot = 0
                self.last_shot = time.time()
                self.shoot_delay = random.randrange(self.shoot_delay_range[0], self.shoot_delay_range[1])

    """
    The Movement Rules:
    Rule One: Move Towards the player but stay 300 pixels away.
    Rule Two: Avoid being in front of allies, and do not crash into each other.
    Rule Three: Attempt to slow down or speed up to match the players velocity.
    Rule Four: Avoid being in front of the player.
    Rule Five: Move Away from Gravity
    """

    def rule1(self):
        """
        Rule One: Move Towards the player but stay 300 pixels away.
        """
        distance = self.target_distance
        rad_angle = math.radians(self.target_angle)
        if distance > 480:
            x = math.cos(rad_angle) * self.target_acceleration + 0.4
            y = math.sin(rad_angle) * self.target_acceleration + 0.4
        elif distance > 330:
            x = math.cos(rad_angle) * self.target_acceleration
            y = math.sin(rad_angle) * self.target_acceleration
        elif distance < 285:
            x = math.cos(rad_angle) * -2.5
            y = math.sin(rad_angle) * -2.5
        elif distance < 75:
            x = math.cos(rad_angle) * -4
            y = math.sin(rad_angle) * -4
        else:
            x = 0
            y = 0
        result = [x * self.rule_1_priority, y * self.rule_1_priority]
        return result

    def rule2(self):
        """
        Rule Two: Avoid being in front of allies, and do not crash into each other.
        """
        x = 0
        y = 0
        total = 0
        for neighbor in self.handler.enemy_sprites:
            if neighbor != self:
                distance = vector.find_distance((self.center_x, self.center_y), (neighbor.center_x, neighbor.center_y))
                if distance < 250:
                    total += 1

                    angle_neighbor = vector.find_angle((self.center_x, self.center_y),
                                                       (neighbor.center_x, neighbor.center_y))
                    difference_neighbor = vector.calc_difference(neighbor.angle, angle_neighbor)
                    direction = 0
                    move = 0
                    if difference_neighbor[0] < 45 and difference_neighbor[0] < difference_neighbor[1]:
                        direction = neighbor.angle - 90
                        move = (45 - difference_neighbor[0])
                    if difference_neighbor[1] < 45 and difference_neighbor[1] < difference_neighbor[0]:
                        direction = neighbor.angle + 90
                        move = (45 - difference_neighbor[1])
                    if direction:
                        rad_difference = math.radians(direction)
                        x += math.cos(rad_difference) * move
                        y += math.sin(rad_difference) * move
                    else:
                        x += (self.center_x - neighbor.center_x)
                        y += (self.center_y - neighbor.center_y)

        if total:
            x /= total
            y /= total
        result = [x * self.rule_2_priority * 0.05, y * self.rule_2_priority * 0.05]
        return result

    def rule3(self):
        """
        Rule Three: Attempt to slow down or speed up to match the players velocity
        """
        result = [0.0, 0.0]
        if self.target_distance < 1920 and abs(self.speed - self.target_speed) > 250:
            result[0] = (self.target_velocity[0] - self.velocity[0]) / 4
            result[1] = (self.target_velocity[1] - self.velocity[1]) / 4
        elif self.target_distance < 1920:
            result[0] = (self.target_velocity[0] - self.velocity[0]) / 8
            result[1] = (self.target_velocity[1] - self.velocity[1]) / 8

        return [result[0] * 0.05 * self.rule_3_priority, result[1] * 0.05 * self.rule_3_priority]

    def rule4(self):
        """
        Rule Four: Avoid being in front of the player.
        """
        player = self.handler.player
        angle_to_self = vector.find_angle((self.center_x, self.center_y),
                                          (player.center_x, player.center_y))
        difference = vector.calc_difference(player.angle, angle_to_self)
        direction = 0
        move = 0
        if difference[0] < 45 and difference[0] < difference[1]:
            direction = player.angle - 90
            move = (45 - difference[0])
        if difference[1] < 45 and difference[1] < difference[0]:
            direction = player.angle + 90
            move = (45 - difference[1])
        x, y = 0, 0
        if direction:
            rad_difference = math.radians(direction)
            x = math.cos(rad_difference) * move
            y = math.sin(rad_difference) * move
        result = [x * self.rule_4_priority * 0.05, y * self.rule_4_priority * 0.05]
        return result

    def rule5(self):
        """
        Rule Five: avoid planets
        """
        x = 0
        y = 0
        total = 0
        for influence in self.gravity_handler.gravity_influences:
            distance = vector.find_distance((self.center_x, self.center_y),
                                            (influence.center_x, influence.center_y)) - (influence.width / 2)
            if 0 < distance < 2500:

                total += 1
                neg_direction = math.radians(vector.find_angle((self.center_x, self.center_y),
                                                               (influence.center_x, influence.center_y)))

                neg_x = math.cos(neg_direction) * distance
                neg_y = math.sin(neg_direction) * distance

                x += neg_x / 2500
                y += neg_y / 2500

                if x < 0:
                    x = -1 - x
                else:
                    x = 1 - x

                if y < 0:
                    y = -1 - y
                else:
                    y = 1 - y

                x *= 3
                y *= 3

        if total:
            x /= total
            y /= total

        result = [x * self.rule_5_priority, y * self.rule_5_priority]
        return result

    """
    Ability Rules:
        Note:
            A Spacecraft can have multiple abilities but only on will be active at a time
            When doing abilities the order in which they are sorted in the json file changes there priority
            if the ability takes any frames of animation they go in a second list in the same order
    Invisibility: for a set amount of time based on the difficulty of the enemy,
                  change the frame to a perfect black frame. Also change their rules to strongly dodge attacks
                  and try move away from the player

    """

    def invisibility_rule(self, frames=None):
        if self.active_ability is None:
            do_rule = False
            if time.time() > self.cool_down and self.target_distance > 330:
                do_rule = True
            if do_rule:
                self.active_ability = 'invisibility'
                self.active_frames = self.ability_frames[frames]
                self.start_time = time.time()
                self.duration = 3 * self.handler.difficulty
                self.texture = self.active_frames[0]
                self.rule_4_priority = 2.0

                for point in self.handler.player.enemy_pointers:
                    if point.target == self:
                        point.remove_from_sprite_lists()
                        del point
        elif time.time() > self.start_time + self.duration:
            self.active_ability = None
            self.active_frames = []

            self.texture = self.textures[self.frame]
            self.rule_4_priority = self.type_data['rules'][3]

            self.start_time = 0
            self.duration = 0

            self.cool_down = time.time() + self.cool_down_delay

            point = ui.Pointer()
            point.holder = self.handler.player
            point.target = self
            self.handler.player.enemy_pointers.append(point)

    def mob_rule(self):
        if self.active_ability is None:
            pass
        elif time.time() > self.start_time + self.duration:
            pass
