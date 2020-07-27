import math
import random
import time
import PIL
import json

import arcade

import bullet
import ui
import vector


class EnemyHandler:
    """
    The EnemyHandler class holds all of the data values necessary for the enemies to act. it is also responsible for
    creating waves and updating enemies
    """

    def __init__(self, game_window, basic_types: list = None, boss_types: list = None):

        # Enemy type Json file reading.
        self.basic_types = basic_types
        self.boss_types = boss_types
        if basic_types is None or boss_types is None:
            file = "Data/enemy_types.json"
            self.enemy_types = {}
            with open(file) as json_file:
                self.enemy_types = json.load(json_file)
            if basic_types is None:
                self.basic_types = self.enemy_types["basic_types"]
            if boss_types is None:
                self.boss_types = self.enemy_types["boss_types"]

        file = "Data/bullet_types.json"
        self.bullet_types = []
        self.boss_bullet_types = []
        with open(file) as json_file:
            bullets = json.load(json_file)
            self.bullet_types = bullets["enemy"]
            self.boss_bullet_types = bullets['boss']

        # Enemy Based UI Elements
        self.boss_ui = ui.BossUi(game_window)

        self.game_window = game_window

        # The player object. This allows the enemies to get its position.
        self.player = None

        # The sprite list that holds all of the enemy sprites
        self.enemy_sprites = None

        # clusters for when there are more than 10 enemies
        self.clusters = []
        self.min_count_in_clusters = 5
        self.max_count_in_clusters = 10
        self.total_count_in_clusters = 0
        self.cluster_count = 1

        # the current wave, plus which stage of difficulty
        self.wave = 0
        self.stage = 1
        self.boss_wave = False

        # The number of enemies and the starting number.
        self.starting_num_enemies = 2
        self.num_enemies = 0

        # the difficulty and whether the difficulty changes
        self.difficulty = 0
        self.average_difficulty = 0
        self.stay_same = False

        # the wave times for difficulties
        self.wave_times = []
        self.average_time = 0
        self.current_wave_time = 0

        # player health for enemy waves
        self.last_player_health = 0

    def assign_player_health(self):
        """
        This method is Just to ensure no bugs arise.
        """
        if self.player is not None:
            loss = self.last_player_health - self.player.health
            self.last_player_health = self.player.health
            return loss
        else:
            return None

    def calc_wave(self):

        """
        using variables calculated based on the how the player is doing
         the number of enemies is based of a difficult equation.
        """
        loss = self.assign_player_health()
        if loss > 0:
            loss_factor = 1/loss
        else:
            loss_factor = 0

        if len(self.wave_times) > 0:
            time_factor = self.average_time / self.wave_times[-1]
        #    print(f"Average Time = {self.average_time}. Last Time = {self.wave_times[-1]}")
        else:
            time_factor = 0

        base = 1.05
        last_difficulty = self.difficulty
        if last_difficulty > 0:
            modifier = round((loss_factor + time_factor + (last_difficulty-base))*(self.stage/20), 2)
        #    print(
        #        f"difficulty = base[{base}] + (loss factor[{loss_factor}] + time factor[{time_factor}]"
        #        f" + last difficulty[{last_difficulty - base}])*(stage[{self.stage / 20}]). ")
            self.average_difficulty = round(((last_difficulty - base) + modifier) / 2, 2)
        else:
            modifier = 0
        self.difficulty = round(base + modifier, 2)
        prev_num_enemies = self.num_enemies
        self.num_enemies = round(self.starting_num_enemies * ((self.difficulty + self.average_difficulty) ** self.wave))

        if self.num_enemies < self.starting_num_enemies:
            self.num_enemies = self.starting_num_enemies

        if self.num_enemies < prev_num_enemies:
            self.num_enemies = prev_num_enemies

        print("difficulty =", self.difficulty, "average difficulty =", round(self.average_difficulty + base, 2),
              "- Number of enemies =", self.num_enemies)

    def do_wave_time(self):
        """
        All steps based on record keeping the time a player takes to complete a mission
        """
        if self.current_wave_time > 0:
            self.wave_times.append(time.time() - self.current_wave_time)
            total = 0
            for times in self.wave_times:
                total += times
            self.average_time = total/len(self.wave_times)
        self.current_wave_time = time.time()

    def setup_wave(self):
        """
        The method called to set up the next wave.
        """
        self.boss_ui.clear()
        if self.boss_wave:
            self.stage += 1
            self.do_wave_time()
            self.calc_wave()
            self.setup_boss()
            self.boss_ui.setup(self.enemy_sprites)
            self.boss_wave = False
        else:
            self.wave += 1
            self.do_wave_time()
            self.calc_wave()
            self.setup_enemies()
            if self.wave % 5 == 0:
                self.boss_wave = True

        print("Stage:", self.stage, "Wave:", self.wave)

    def setup_enemies(self):
        self.enemy_sprites = arcade.SpriteList()

        if self.num_enemies >= self.max_count_in_clusters:
            self.cluster()
        else:
            for i in range(self.num_enemies):
                enemy_type = random.randrange(0, len(self.basic_types))
                bullet_type = self.bullet_types[self.basic_types[enemy_type]["shoot_type"]]
                enemy = Enemy(self.basic_types[enemy_type], bullet_type)
                enemy.setup(self)
                self.enemy_sprites.append(enemy)

    def setup_boss(self):
        self.enemy_sprites = arcade.SpriteList()
        boss_type = self.boss_types[random.randrange(0, len(self.boss_types))]
        bullets = boss_type['shoot_type']
        bullet_type = self.boss_bullet_types[bullets]
        enemy = Enemy(boss_type, bullet_type)
        enemy.setup(self)
        self.enemy_sprites.append(enemy)

    def cluster(self):
        screen_x, screen_y = arcade.get_display_size()
        self.clusters = []
        remaining = self.num_enemies % self.min_count_in_clusters
        if not remaining:
            num_clusters = int(self.num_enemies / self.min_count_in_clusters)
        else:
            num_clusters = int((self.num_enemies - remaining) / self.min_count_in_clusters)
        for i in range(num_clusters):
            cluster = Cluster(self)
            cluster.num_enemies = self.min_count_in_clusters + remaining
            remaining = 0
            close = True
            while close:
                cluster.center_x = self.player.center_x + random.randint(-3 * screen_x, 3 * screen_x + 1)
                cluster.center_y = self.player.center_y + random.randint(-3 * screen_x, 3 * screen_x + 1)
                distance = vector.find_distance((cluster.center_x, cluster.center_y),
                                                (self.player.center_x, self.player.center_y))
                if distance > 1.5 * screen_x:
                    close = False
            self.clusters.append(cluster)

    def draw(self):
        """
        draws all of the enemy sprites
        """
        for enemy in self.enemy_sprites:
            enemy.draw()

        for cluster in self.clusters:
            arcade.draw_text(str(cluster.num_enemies), cluster.center_x, cluster.center_y, arcade.color.WHITE)

        if self.wave % 5 == 1:
            arcade.draw_text(str(self.stage), self.player.center_x, self.player.center_y - 30, arcade.color.WHITE)

        self.boss_ui.draw()

    def on_update(self, delta_time: float = 1 / 60):
        """
        updates all of the enemies
        """
        self.enemy_sprites.on_update(delta_time)
        if len(self.clusters) != 0:
            for clusters in self.clusters:
                if not clusters.spawned:
                    clusters.spawn_enemies()

        self.total_count_in_clusters = 0
        for clusters in self.clusters:
            self.total_count_in_clusters += clusters.num_enemies

        if len(self.enemy_sprites) == 0 and self.total_count_in_clusters <= 0:
            self.setup_wave()

    def pause_delay(self, pause_delay):
        for bodies in self.enemy_sprites:
            for shots in bodies.bullets:
                shots.pause_delay += pause_delay


class Cluster:

    def __init__(self, handler):
        self.num_enemies = 0

        self.center_x = 0
        self.center_y = 0

        self.handler = handler
        self.spawned = False

        self.point = ui.Pointer()
        self.point.holder = self.handler.player
        self.point.target = self
        self.handler.player.enemy_pointers.append(self.point)

    def spawn_enemies(self):
        t_d = self.handler.player.center_x, self.handler.player.center_y
        s_d = self.center_x, self.center_y
        distance = vector.find_distance(t_d, s_d)
        if distance < arcade.get_display_size()[0]:
            for i in range(self.num_enemies):
                enemy_type = random.randrange(0, len(self.handler.basic_types))
                bullet_type = self.handler.bullet_types[self.handler.basic_types[enemy_type]["shoot_type"]]
                enemy = Enemy(self.handler.basic_types[enemy_type], bullet_type)
                enemy.setup(self.handler, s_d)
                enemy.cluster = self
                self.handler.enemy_sprites.append(enemy)
            self.point.remove_from_sprite_lists()
            self.spawned = True


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
        self.difficulty = type_data['difficulty_value']

        # checks if the enemy is in range of player
        self.handler = None
        self.cluster = None

        # gravity variables
        self.gravity_handler = None
        self.gravity_acceleration = [0.0, 0.0]
        self.weight = 549054

        # movement
        self.turning_speed = 100
        self.velocity = [0.0, 0.0]

        # shooting variables
        self.shooting = False
        self.firing = False
        self.bullet_type = bullet_type
        self.bullets = arcade.SpriteList()
        self.last_shot = 0
        self.shoot_delay = 0.1
        self.shoot_delay_range = type_data['shoot_delay']
        self.next_shot = 0

        # rapid shooting variables
        self.shots_this_firing = 0
        self.next_shot_rapid = 0
        self.shot_gap = 0.15

        # shooting variable to fix bug
        self.first_shot = False

        # sprites
        self.textures = []
        self.scale = 0.15
        self.get_sprites(type_data['image_file'])
        self.health = type_data['health']
        self.full_health = self.health
        self.health_segment = self.health / (len(self.textures)-1)
        self.frame = 1

        # hit box
        self.hit_box = type_data['point_list']

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

        self.target_distance = 0

        # Movement Rules
        self.rule_1_effect = [0.0, 0.0]
        self.rule_2_effect = [0.0, 0.0]
        self.rule_3_effect = [0.0, 0.0]
        self.rule_4_effect = [0.0, 0.0]

        self.do_rule = 0

        self.rule_1_priority = type_data['rules'][0]
        self.rule_2_priority = type_data['rules'][1]
        self.rule_3_priority = type_data['rules'][2]
        self.rule_4_priority = type_data['rules'][3]

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

    def setup(self, handler, x_y_pos: tuple = None):
        """
        sets up the enemy in relation to the player. it also gives the enemy the handler for easier access to variables
        """
        if x_y_pos is None:
            x_y_pos = handler.player.center_x, handler.player.center_y

        self.handler = handler
        self.angle = random.randint(0, 360)

        handler.game_window.gravity_handler.set_gravity_object(self)

        screen = arcade.get_display_size()
        close = True
        while close:
            self.center_x = x_y_pos[0] + random.randint(-(screen[0] // 2) + 30, (screen[0] // 2) - 29)
            self.center_y = x_y_pos[1] + random.randint(-(screen[1] // 2) + 30, (screen[1] // 2) - 29)
            self.target_distance = vector.find_distance((self.center_x, self.center_y),
                                                        (self.handler.player.center_x, self.handler.player.center_y))
            if self.target_distance > 300:
                close = False

        point = ui.Pointer()
        point.holder = self.handler.player
        point.target = self
        self.handler.player.enemy_pointers.append(point)

    def get_sprites(self, image_file, list_to_append: list = None):
        """
        Gets all of the hurt sprites for the enemy
        """
        image = PIL.Image.open(image_file)
        num_frames = image.size[1]//image.size[0]
        x = image.size[0]
        y = image.size[1]/num_frames
        for i in range(num_frames):
            texture = arcade.load_texture(image_file, 0, y*i, x, y)
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
        if self.shooting:
            self.draw_hit_box(arcade.color.RADICAL_RED)

        if self.handler.player.show_hit_box:

            for shot in self.bullets:
                arcade.draw_line(shot.center_x, shot.center_y,
                                 shot.velocity[0] + shot.center_x, shot.velocity[1] + shot.center_y,
                                 arcade.color.CYBER_YELLOW)

            string = str(self.health)
            arcade.draw_text(string, self.center_x, self.center_y - self.width, arcade.color.WHITE)

            arcade.draw_line(self.center_x + self.rule_1_effect[0]*20, self.center_y + self.rule_1_effect[1]*20,
                             self.center_x, self.center_y,
                             arcade.color.RADICAL_RED)
            arcade.draw_line(self.center_x + self.rule_2_effect[0]*20, self.center_y + self.rule_2_effect[1]*20,
                             self.center_x, self.center_y,
                             arcade.color.OCEAN_BOAT_BLUE)
            arcade.draw_line(self.center_x + self.rule_3_effect[0]*20, self.center_y + self.rule_3_effect[1]*20,
                             self.center_x, self.center_y,
                             arcade.color.WHITE_SMOKE)
            arcade.draw_line(self.center_x, self.center_y,
                             self.center_x+self.rule_4_effect[0] * 20, self.center_y+self.rule_4_effect[1] * 20,
                             arcade.color.LIME_GREEN)
            arcade.draw_line(self.center_x + self.velocity[0], self.center_y + self.velocity[1],
                             self.center_x, self.center_y,
                             arcade.color.CYBER_YELLOW)
        self.bullets.draw()
        super().draw()

    def on_update(self, delta_time: float = 1/60):
        """
        Every update run different methods for the enemy and its algorithms.
        """

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
        self.do_rule += 1*delta_time
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
        self.bullets.on_update()

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

    def kill(self):

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
            if enemy != self:
                e_hits = arcade.check_for_collision_with_list(self, enemy.bullets)
                if len(e_hits) > 0:
                    for hit in e_hits:
                        hits.append(hit)
        if len(hits) > 0:
            hits[0].kill()
            self.health -= self.handler.player.damage
            if self.health <= self.full_health - (self.frame * self.health_segment) and not self.health < 0:
                self.texture = self.textures[self.frame]
                self.frame += 1
            if self.health <= 0:
                self.kill()

    def if_hit_player(self):
        """
        check if the enemy hits the player
        """
        hits = arcade.check_for_collision_with_list(self.handler.player, self.bullets)
        if len(hits) > 0:
            self.handler.player.health -= self.bullet_type['damage']
            if self.handler.player.health < 0:
                self.handler.player.health = 0
            if self.handler.player.health <= 0:
                self.handler.player.dead = True
            self.handler.player.hit = True
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
        target = self.handler.player
        self_pos = (self.center_x, self.center_y)
        target_pos = (target.center_x, target.center_y)
        self.target_angle = vector.find_angle(target_pos, self_pos)

        # find the difference and the direction
        self.difference = vector.calc_difference(self.target_angle, self.angle)
        self.direction = vector.calc_direction(self.target_angle, self.angle)

        self.target_velocity = target.velocity
        self.target_speed = math.sqrt(target.velocity[0]**2 + target.velocity[1]**2)
        self.target_acceleration = target.forward_force / target.weight

        # distance to player
        dx = self_pos[0] - target_pos[0]
        dy = self_pos[1] - target_pos[1]
        self.target_distance = math.sqrt(dx**2 + dy**2)

    def shoot_rule(self):
        if not self.firing:
            self.shooting = False
            if self.last_shot + self.shoot_delay < time.time():
                if self.type_data['shoot_type'] == 0:
                    self.standard_rule()
                elif self.type_data['shoot_type'] == 1:
                    self.rapid_rule()
                elif self.type_data['shoot_type'] == 2:
                    self.blast_rule()
                elif self.type_data['shoot_type'] == 3:
                    self.spread_rule()
                elif self.type_data['shoot_type'] == 4:
                    self.circle_rule()
                else:
                    self.standard_rule()
                self.last_shot = time.time()
                self.shoot_delay = random.randrange(self.shoot_delay_range[0], self.shoot_delay_range[1])

        if self.type_data['shoot_type'] == 1:
            self.rapid_shoot()
        elif self.shooting:
            self.standard_shoot()

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
            if self.rule_3_priority:
                self.rule_4_effect = self.rule4()
        final = [0.0, 0.0]
        final[0] = self.rule_1_effect[0] + self.rule_2_effect[0] + self.rule_3_effect[0] + self.rule_4_effect[0]
        final[1] = self.rule_1_effect[1] + self.rule_2_effect[1] + self.rule_3_effect[1] + self.rule_4_effect[1]

        self.velocity[0] += final[0]
        self.velocity[1] += final[1]

        speed_limit = self.target_speed + 200
        speed = math.sqrt(self.velocity[0] ** 2 + self.velocity[1]**2)
        if speed > speed_limit:
            self.velocity[0] = (self.velocity[0] / speed) * speed_limit
            self.velocity[1] = (self.velocity[1] / speed) * speed_limit

    def ability_rules(self):
        if self.active_ability is None:
            for frames, ability in enumerate(self.abilities):
                if self.active_ability is None:
                    if ability == 'invisibility':
                        self.invisibility_rule(frames)

        if self.active_ability == 'invisibility':
            self.invisibility_rule()

    """
    The Shooting Rules
    (0) Standard: Fires a single medium damage bullet where they are facing
    (1) Rapid: Fires multiple low damage bullets where they are facing 
    (2) Blast: Fires one large slow high damage bullet where they are facing
    (3) Spread: Fires 3-5 short range high damage bullets in a spread from -45 to 5 degrees from where they are facing
    (4) Circle: Fires 6 - 10 medium damage bullets evenly spread 360 degrees around them
    """

    def standard_rule(self):
        """
        Calculates if the enemy should shoot.
        """
        if self.difference[0] < 30 or self.difference[1] < 30 and self.target_distance < 800:
            self.shooting = True
            for neighbor in self.handler.enemy_sprites:
                distance_to_neighbor = vector.find_distance((self.center_x, self.center_y),
                                                            (neighbor.center_x, neighbor.center_y))
                if neighbor != self:
                    if distance_to_neighbor < self.target_distance:
                        angle_to_neighbor = vector.find_angle((neighbor.center_x, neighbor.center_y),
                                                              (self.center_x, self.center_y))
                        difference = vector.calc_difference(angle_to_neighbor, self.angle)
                        if difference[0] < 30 or difference[1] < 30:
                            self.shooting = False

                    if self.shooting is False:
                        break  
                        
    def standard_shoot(self):
        """
        shoots a bullets.
        """
        shot = bullet.Bullet([self.center_x, self.center_y], self.angle, self.velocity, self.bullet_type)
        self.bullets.append(shot)

    def rapid_rule(self):
        if not self.firing:
            if self.difference[0] < 20 or self.difference[1] < 20 and self.target_distance < 750:
                self.firing = True
                for neighbor in self.handler.enemy_sprites:
                    distance_to_neighbor = vector.find_distance((self.center_x, self.center_y),
                                                                (neighbor.center_x, neighbor.center_y))
                    if neighbor != self:
                        if distance_to_neighbor < self.target_distance:
                            angle_to_neighbor = vector.find_angle((neighbor.center_x, neighbor.center_y),
                                                                  (self.center_x, self.center_y))
                            difference = vector.calc_difference(angle_to_neighbor, self.angle)
                            if difference[0] < 45 or difference[1] < 45:
                                self.firing = False

                        if self.firing is False:
                            break

    def rapid_shoot(self):
        if self.firing and time.time() > self.next_shot_rapid:
            self.standard_shoot()
            self.shots_this_firing += 1
            self.next_shot_rapid = time.time() + self.shot_gap

            if self.shots_this_firing >= 5:
                self.firing = False
                self.shots_this_firing = 0
                self.last_shot = time.time()
                self.shoot_delay = random.randrange(self.shoot_delay_range[0], self.shoot_delay_range[1])

    def blast_rule(self):
        pass

    def spread_rule(self):
        pass

    def circle_rule(self):
        pass

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
            x = math.cos(rad_angle) * 2.8
            y = math.sin(rad_angle) * 2.8
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
                if distance < 100:
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
        if self.target_distance < 700:
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
        pass

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
                self.duration = 3 * (self.difficulty * self.handler.difficulty)
                self.texture = self.active_frames[0]
                self.rule_4_priority = 2.0

                for point in self.handler.player.enemy_pointers:
                    if point.target == self:
                        point.remove_from_sprite_lists()
                        del point
        else:
            if time.time() > self.start_time + self.duration:
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


if __name__ == "__main__":
    with open('Data/enemy_types.json') as enemy_file:
        enemies = json.load(enemy_file)
        for enemy_types in enemies['basic_types']:
            for feature in enemy_types:
                print(feature + ":", enemy_types[feature])
            print("")
