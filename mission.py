import json
import random
import copy as c

import space
import enemy_handler


class MissionGenerator:

    def __init__(self):
        with open('Data/sol_system.json') as planet_file:
            self.planets = json.load(planet_file)['planets']

        with open("Data/enemy_types.json") as enemy_file:
            enemy_json = json.load(enemy_file)
            self.all_enemies = enemy_json['basic_types']
            self.all_bosses = enemy_json['boss_types']

        with open("Data/mission_data.json") as mission_file:
            mission_json = json.load(mission_file)
            self.mission_json = mission_json['planet_x']

        self.missions = []
        self.selected_missions = {}
        self.dump_missions = {
                            "planet_x": self.mission_json
                            }

        self.generate_selection()

    def generate_selection(self):
        for gen_num in range(9):
            self.generate_mission()

        self.select()
        self.dump()

    def generate_mission(self):
        mission = c.deepcopy(self.mission_json)
        mission['stages'] = random.randrange(1, 4)
        for enemies in self.all_enemies:
            pick = random.random()
            if pick > 0.5:
                mission['possible_enemies'].append(enemies['type'])
        if len(mission['possible_enemies']) == 0:
            for enemies in self.all_enemies:
                mission['possible_enemies'].append(enemies['type'])

        for bosses in self.all_bosses:
            pick = random.random()
            if pick > 0.5:
                mission['possible_bosses'].append(bosses['type'])
        if len(mission['possible_bosses']) == 0:
            for bosses in self.all_bosses:
                mission['possible_bosses'].append(bosses['type'])
        mission['name'] = "defend "
        self.missions.append(mission)

    def select(self):
        picked_planets = random.sample(self.planets, 3)
        picked_missions = random.sample(self.missions, 3)
        random.shuffle(picked_missions)

        key = 1
        for index, planet in enumerate(picked_planets):
            mission = picked_missions[index]
            mission['name'] += planet['name']
            mission['key'] = key
            mission['reward'] = round(planet['weight']/(5.972 * 10 ** 24) * (mission['stages'] * 4))**2
            key += 1
            self.selected_missions[f"{planet['name']}"] = mission

    def dump(self):
        self.dump_missions['missions'] = self.selected_missions
        with open("Data/mission_data.json", "w") as mission_data:
            json.dump(self.dump_missions, mission_data, indent=4)


class Mission:

    def __init__(self, game_window):
        self.game_window = game_window
        self.level_data = None

        self.enemy_handler = None
        self.curr_planet = None
        self.asteroids = None

        self.base_mission_data = {
            'name': '',
            'planet': '',
            'reward': 0,
            'enemies_killed': 0,
            'total_enemy': 0,
            'scrap_identify': 0,
            'scrap_collect': 0,
            'missions_completed': 0
        }
        self.current_mission_data = None

    def reload(self):
        if self.enemy_handler is not None:
            self.enemy_handler.reset()

    def mission_setup(self, level_data: dict = None):
        self.level_data = level_data
        self.current_mission_data = dict(self.base_mission_data)

        self.enemy_handler = None
        self.curr_planet = None
        self.asteroids = None

        if level_data is not None:
            self.setup()

    def setup(self):
        with open("Data/enemy_types.json") as enemy_file:
            enemy_types = json.load(enemy_file)
            basic_enemies = enemy_types['basic_types']
            boss_enemies = enemy_types['boss_types']

        """
        TO SETUP:
        Asteroid Json file and setup within mission.
        """
        if self.game_window.solar_system is None:
            self.game_window.solar_system = space.SolarSystem(setup=True)
        else:
            self.curr_planet = self.game_window.solar_system.get_planet(self.level_data['planet_data'])
        self.curr_planet = space.Planet(self.game_window, self.level_data['planet_data'])
        self.level_data['planet'] = self.curr_planet

        mission_enemies = []
        for enemies in basic_enemies:
            for pos_enemies in self.level_data['possible_enemies']:
                if enemies['type'] == pos_enemies:
                    mission_enemies.append(enemies)
                    break

        mission_bosses = []
        for bosses in boss_enemies:
            for pos_bosses in self.level_data['possible_bosses']:
                if bosses['type'] == pos_bosses:
                    mission_bosses.append(bosses)
                    break

        self.enemy_handler = enemy_handler.EnemyHandler(self.game_window, self,
                                                        mission_enemies, mission_bosses,
                                                        self.level_data)

        # give the enemy_handler the player
        self.enemy_handler.player = self.game_window.player
        self.enemy_handler.assign_player_health()

        # player pointer
        self.game_window.player.enemy_handler = self.enemy_handler

        self.current_mission_data['name'] = self.level_data['name']
        self.current_mission_data['planet'] = self.curr_planet.name
        self.current_mission_data['reward'] = self.level_data['reward']

    def check_setup(self):
        if self.game_window.player.start == 1:
            self.enemy_handler.setup_wave()
            self.game_window.player.start = 2

    def draw(self):
        if self.asteroids is not None:
            self.asteroids.draw()

        if self.curr_planet is not None:
            self.curr_planet.draw()

        if self.enemy_handler is not None and self.enemy_handler.enemy_sprites is not None:
            self.enemy_handler.draw()

    def on_update(self, delta_time: float = 1/60):
        if self.asteroids is not None:
            self.asteroids.on_update(delta_time)

        if self.curr_planet is not None:
            self.curr_planet.on_update(delta_time)

        if self.enemy_handler is not None and self.enemy_handler.enemy_sprites is not None\
                and not self.game_window.wormhole:
            self.enemy_handler.on_update(delta_time)

    def add_mission_data(self):
        self.base_mission_data['total_enemy'] = self.current_mission_data['total_enemy']
        self.base_mission_data['missions_completed'] += 1
        self.current_mission_data['missions_completed'] += 1
        self.game_window.player_credit += self.current_mission_data['reward']
