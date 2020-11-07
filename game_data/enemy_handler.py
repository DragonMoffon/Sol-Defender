import math
import random
import json

import arcade

import game_data.ui as ui
import game_data.vector as vector
import game_data.font as font
import game_data.enemy as _

MAX_ENEMIES = 90


class EnemyHandler:
    """
    The EnemyHandler class holds all of the data values necessary for the enemies to act. it is also responsible for
    creating waves and updating enemies
    """

    def __init__(self, game_window, mission_handler,
                 basic_types: list = None, boss_types: list = None,
                 mission_data: dict = None, target_object=None):
        # Enemy type Json file reading.
        self.basic_types = basic_types
        self.boss_types = boss_types

        file = "game_data/Data/bullet_types.json"
        self.bullet_types = []
        self.boss_bullet_types = []
        with open(file) as json_file:
            bullets = json.load(json_file)
            self.bullet_types = bullets["enemy"]
            self.boss_bullet_types = bullets['boss']

        self.game_window = game_window
        self.mission_handler = mission_handler
        self.target_object = target_object
        if self.target_object is None:
            self.target_object = self.mission_handler.curr_planet

        self.level_data = mission_data
        self.planet_data = mission_data['planet']

        # The player object. This allows the enemies to get its position.
        self.player = None

        self.scrap_list = arcade.SpriteList()

        # The sprite list that holds all of the enemy sprites
        self.enemy_sprites = None

        # engagement time.
        self.engagement = 0

        # The number of enemies and the starting number.
        self.starting_num_enemies = 12
        self.num_enemies = 0

        # the difficulty and whether the difficulty changes
        self.base_difficulty = self.game_window.prev_difficulty
        self.difficulty = 0
        self.average_difficulty = 0
        self.stay_same = False

        # player health for enemy waves
        self.last_player_health = 0

        self.time_to_spawn = None

        # clusters for when there are more than 10 enemies
        self.clusters = []
        self.min_count_in_clusters = 4
        self.max_count_in_clusters = 8
        self.total_count_in_clusters = 0
        self.cluster_count = 1

        # the current wave, plus which stage of difficulty
        self.wave = 0
        self.stage = 1
        self.num_stages = mission_data['stages']
        self.boss_wave = False

        # the wave times for difficulties
        self.wave_times = []
        self.average_time = 0
        self.current_wave_time = 0

    def reset(self):
        self.slaughter()

        # The sprite list that holds all of the enemy sprites
        self.enemy_sprites = None

        # The SpriteList that holds all the scrap
        self.scrap_list = arcade.SpriteList()

        # clusters for when there are more than 10 enemies
        self.clusters = []
        self.total_count_in_clusters = 0
        self.cluster_count = 1

        # the current wave, plus which stage of difficulty
        self.wave = 0
        self.stage = 1
        self.boss_wave = False

        # The number of enemies and the starting number.
        self.num_enemies = 0

        # the difficulty and whether the difficulty changes
        self.base_difficulty = self.game_window.prev_difficulty
        self.difficulty = 0
        self.average_difficulty = 0

        # the wave times for difficulties
        self.wave_times = []
        self.average_time = 0
        self.current_wave_time = 0

        # player health for enemy waves
        self.last_player_health = 0

    def slaughter(self):
        if self.enemy_sprites is not None:
            safe_copy = self.enemy_sprites
            for enemy in safe_copy:
                enemy.kill()

        if self.clusters is not None:
            for clusters in self.clusters:
                clusters.slaughter()

    def calc_wave(self):

        """
        using variables calculated based on the how the player is doing
         the number of enemies is based of a difficult equation.
        """
        loss = self.assign_player_health()
        if loss > 0:
            loss_factor = 1 / loss
        else:
            loss_factor = 0

        if len(self.wave_times) > 0:
            time_factor = self.average_time / self.wave_times[-1]
        #    print(f"Average Time = {self.average_time}. Last Time = {self.wave_times[-1]}")
        else:
            time_factor = 0

        base = self.base_difficulty
        last_difficulty = self.difficulty
        print(" loss factor:", loss_factor, "time factor:", time_factor, "base:", base)
        if last_difficulty > 0:
            modifier = round((loss_factor + time_factor + (last_difficulty - base)) * (self.stage / 20), 2)
            #    print(
            #        f"difficulty = base[{base}] + (loss factor[{loss_factor}] + time factor[{time_factor}]"
            #        f" + last difficulty[{last_difficulty - base}])*(stage[{self.stage / 20}]). ")
            self.average_difficulty = round(((last_difficulty - base) + modifier) / 2, 2)
        else:
            modifier = 0
        self.difficulty = round(base + modifier, 2)
        prev_num_enemies = self.num_enemies
        self.num_enemies = round(self.starting_num_enemies * ((self.difficulty + self.average_difficulty) ** self.wave))

        if self.num_enemies > MAX_ENEMIES:
            self.num_enemies = MAX_ENEMIES

        if self.num_enemies < self.starting_num_enemies:
            self.num_enemies = self.starting_num_enemies

        if self.num_enemies < prev_num_enemies:
            self.num_enemies = prev_num_enemies

        print("difficulty =", self.difficulty, "average difficulty =", round(self.average_difficulty + base, 2),
              "- Number of enemies =", self.num_enemies)

    def setup_wave(self):
        """
        The method called to set up the next wave.
        """
        if self.boss_wave:
            self.stage += 1
            self.do_wave_time()
            self.calc_wave()
            self.setup_boss()
            self.boss_wave = False
        else:
            if self.stage > self.num_stages:
                self.game_window.prev_difficulty = self.difficulty
                self.mission_handler.add_mission_data()
                self.game_window.wormhole_update(0)
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
        self.cluster()

    def setup_boss(self):
        self.enemy_sprites = arcade.SpriteList()
        boss_type = random.choice(self.boss_types)
        bullets = boss_type['shoot_type']
        bullet_type = self.boss_bullet_types[bullets]
        enemy = _.Enemy(boss_type, bullet_type)
        enemy.setup(self, self.player)
        self.enemy_sprites.append(enemy)

    def cluster(self):
        if self.num_enemies >= self.max_count_in_clusters:
            check = self.max_count_in_clusters
            smallest = self.max_count_in_clusters
            not_found = True
            while not_found:
                if self.num_enemies % check < self.num_enemies % smallest:
                    smallest = check
                if self.num_enemies % check == 0 or check <= self.min_count_in_clusters:
                    not_found = False
                else:
                    check -= 1

            remaining = self.num_enemies % smallest
            num_clusters = int((self.num_enemies - remaining) / smallest)
            amount = smallest
        else:
            remaining = 0
            num_clusters = 1
            amount = self.num_enemies

        screen_x, screen_y = arcade.get_display_size()
        self.clusters = []
        angle_to_object = None
        distance_to_object = 0
        if self.target_object != self.planet_data:
            angle_to_object = vector.find_angle((self.target_object.center_x, self.target_object.center_y),
                                                (self.planet_data.center_x, self.planet_data.center_y))
            distance_to_object = vector.find_distance((self.planet_data.center_x, self.planet_data.center_y),
                                                      (self.target_object.center_x, self.target_object.center_y))

        for i in range(num_clusters):
            cluster = _.Cluster(self, self.target_object)
            cluster.num_enemies = amount

            if angle_to_object is None:
                angle = round(random.uniform(0.0, 2 * math.pi), 2)
                cluster.center_x = self.planet_data.center_x + (math.cos(angle) *
                                                                (self.planet_data.width +
                                                                random.randint(screen_x * 3, screen_x * 6)))
                cluster.center_y = self.planet_data.center_y + (math.sin(angle) *
                                                                (self.planet_data.width +
                                                                random.randint(screen_x * 3, screen_x * 6)))
            else:
                angle = math.radians(angle_to_object + random.randint(-6, 7))
                distance = distance_to_object + random.randint(screen_x * 3, screen_x * 6)
                if distance < self.planet_data.width / 2 + 1000:
                    distance = self.planet_data.width / 2 + 1000 + random.randint(50, 500)
                cluster.center_x = self.planet_data.center_x + (math.cos(angle) * distance)
                cluster.center_y = self.planet_data.center_y + (math.sin(angle) * distance)

            self.clusters.append(cluster)

        if remaining:
            for cluster in self.clusters:
                cluster.num_enemies += 1
                remaining -= 1
                if remaining <= 0:
                    break

    def draw(self):
        """
        draws all of the enemy sprites
        """
        self.scrap_list.draw()

        if self.time_to_spawn is not None:
            self.time_to_spawn.draw()

        for enemy in self.enemy_sprites:
            enemy.draw()

    def on_update(self, delta_time: float = 1 / 60):
        """
        updates all of the enemies
        """
        self.scrap_list.update()
        self.enemy_sprites.on_update(delta_time)
        if len(self.clusters) != 0:
            for clusters in self.clusters:
                if not clusters.spawned:
                    clusters.spawn_enemies(delta_time)

        self.total_count_in_clusters = 0
        time_to_spawn = None
        for clusters in self.clusters:
            self.total_count_in_clusters += clusters.num_enemies
            if not clusters.spawned:
                distance = vector.find_distance((clusters.center_x, clusters.center_y),
                                                (self.target_object.center_x, self.target_object.center_y)) \
                           - arcade.get_display_size()[0]
                speed = clusters.speed

                t = distance / speed
                if time_to_spawn is None or t < time_to_spawn:
                    time_to_spawn = t

        if time_to_spawn is not None:
            self.time_to_spawn = font.LetterList("Time Until Threat Arrival: " + str(round(time_to_spawn)) + "s",
                                                 self.game_window.left_view + arcade.get_display_size()[0] / 2,
                                                 self.game_window.bottom_view + arcade.get_display_size()[1] - 50,
                                                 mid_x=True)
        else:
            self.time_to_spawn = None

        if len(self.enemy_sprites):
            self.engagement += delta_time

        if len(self.enemy_sprites) == 0 and self.total_count_in_clusters <= 0:
            self.setup_wave()

        self.do_enemy_targets()

    """Parent Methods"""

    def do_enemy_targets(self):
        player_targets = 0
        for enemies in self.enemy_sprites:
            distance = vector.find_distance((self.player.center_x, self.player.center_y),
                                            (enemies.center_x, enemies.center_y))
            if distance < ui.SCREEN_WIDTH * 3 and player_targets < self.max_count_in_clusters:
                enemies.target = self.player
                player_targets += 1
            else:
                enemies.target = self.target_object

    def assign_player_health(self):
        """
        This method is Just to ensure no bugs arise.
        """
        if self.player is not None:
            loss = self.last_player_health - self.player.current_segment
            self.last_player_health = self.player.current_segment
            return loss
        else:
            return None

    def do_wave_time(self):
        """
        All steps based on record keeping the time a player takes to complete a mission
        """
        if self.engagement > 0:
            self.wave_times.append(self.engagement)
            total = 0
            for times in self.wave_times:
                total += times
            self.average_time = total / len(self.wave_times)
            print("prev_time", self.engagement, end="")
        self.engagement = 0

    def pause_delay(self, pause_delay):
        if self.enemy_sprites is not None:
            for bodies in self.enemy_sprites:
                for shots in bodies.bullets:
                    shots.pause_delay += pause_delay

    def count_enemy_death(self):
        self.mission_handler.current_mission_data['enemies_killed'] += 1
        self.mission_handler.current_mission_data['total_enemy'] += 1

    def count_dropped_scrap(self, scrap_count):
        self.mission_handler.current_mission_data['scrap_identify'] += scrap_count

    def count_collect_scrap(self):
        self.mission_handler.current_mission_data['scrap_collect'] += 1
