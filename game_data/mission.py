import json
import random
import copy as c

import game_data.space as space
import game_data.enemy_handler as enemy_handler


class MissionGenerator:

    def __init__(self):
        with open('game_data/Data/sol_system.json') as planet_file:
            planet_json = json.load(planet_file)
            self.planets = planet_json['planets']
            self.companies = planet_json['companies']

        with open("game_data/Data/enemy_types.json") as enemy_file:
            enemy_json = json.load(enemy_file)
            self.all_enemies = enemy_json['basic_types']
            self.all_bosses = enemy_json['boss_types']

        with open("game_data/Data/mission_data.json") as mission_file:
            mission_json = json.load(mission_file)
            self.mission_json = mission_json['planet_x']

        self.missions = {}
        self.selected_missions = {}
        self.dump_missions = {
                            "planet_x": self.mission_json
                            }

        self.num_missions = 3
        self.generate()

    def reload_dictionaries(self):
        with open('game_data/Data/sol_system.json') as planet_file:
            planet_json = json.load(planet_file)
            self.planets = planet_json['planets']
            self.companies = planet_json['companies']

        with open("game_data/Data/enemy_types.json") as enemy_file:
            enemy_json = json.load(enemy_file)
            self.all_enemies = enemy_json['basic_types']
            self.all_bosses = enemy_json['boss_types']

        with open("game_data/Data/mission_data.json") as mission_file:
            mission_json = json.load(mission_file)
            self.mission_json = mission_json['planet_x']

    def generate(self):
        self.missions = {}
        self.selected_missions = {}
        self.dump_missions = {
                            "planet_x": self.mission_json
                            }
        self.dump()

        self.generate_selection()

    def generate_selection(self):
        for companies in self.companies.values():
            all_planets = list(companies['planets'])
            all_planets.append(companies['home_planet'])
            self.missions[companies['type']] = {}
            for planet in all_planets:
                self.generate_mission(companies, planet)

        self.select()
        self.dump()

    def generate_mission(self, company, planet):
        mission = c.deepcopy(self.mission_json)
        mission['stages'] = 1
        mission['types'] = random.choice(company['missions'])
        mission['company'] = company['name']
        enemy_picks = random.sample(self.all_enemies, random.randrange(1, len(self.all_enemies)))
        for enemies in enemy_picks:
            mission['possible_enemies'].append(enemies['type'])

        boss_picks = random.sample(self.all_bosses, random.randrange(1, len(self.all_bosses)))
        for bosses in boss_picks:
            mission['possible_bosses'].append(bosses['type'])

        mission['name'] = f"{mission['types']} {planet}"
        mission['planet_data'] = self.planets[planet]
        mission['reward'] = random.randint(55, 85)
        self.missions[company['type']][mission['name']] = mission

    def select(self):
        picked_planets = []
        if self.num_missions < 5:
            companies = random.sample(self.companies.keys(), self.num_missions)
        else:
            companies = list(self.companies.keys())
            companies.append(random.choice(list(self.companies.keys())))
        mission = {}
        for company in companies:
            picking = True
            while picking:
                copy_cat = c.copy(self.missions[company])
                for missions in copy_cat.values():
                    if missions['planet_data']['name'] in picked_planets:
                        self.missions[company].pop(missions['name'])
                if len(self.missions[company]):
                    mission = random.choice(list(self.missions[company].values()))
                    picked_planets.append(mission['planet_data']['name'])
                    picking = False
                else:
                    print('one less mission')
                    picking = False

            if mission != {}:
                self.selected_missions[mission['planet_data']['name']] = mission

    def dump(self):
        self.dump_missions['missions'] = self.selected_missions
        with open("game_data/Data/mission_data.json", "w") as mission_data:
            json.dump(self.dump_missions, mission_data, indent=4)


class Mission:

    def __init__(self, game_window):
        self.game_window = game_window
        self.level_data = None

        self.enemy_handler = None
        self.curr_planet = None
        self.target_object = None
        self.asteroids = None

        self.base_mission_data = {
            'name': '',
            'company': '',
            'planet': '',
            'reward': 0,
            'reputation': 0,
            'enemies_killed': 0,
            'total_enemy': 0,
            'scrap_identify': 0,
            'scrap_collect': 0,
            'missions_completed': 0
        }
        self.current_mission_data = None

        self.reputation_mod = 1

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
        with open("game_data/Data/enemy_types.json") as enemy_file:
            enemy_types = json.load(enemy_file)
            basic_enemies = enemy_types['basic_types']
            boss_enemies = enemy_types['boss_types']

        if self.game_window.solar_system is None:
            self.game_window.solar_system = space.SolarSystem(setup=True)
        else:
            self.curr_planet = self.game_window.solar_system.get_planet(self.level_data['planet_data'])
        self.curr_planet = space.Planet(self.game_window, self.level_data['planet_data'])
        self.level_data['planet'] = self.curr_planet
        self.target_object = None
        for satellite in self.curr_planet.satellites:
            if satellite.type == self.level_data['company']:
                self.target_object = satellite
                break
        if self.target_object is None:
            raise TypeError("This Planet Doesn't Have the Satellite Your Looking for")

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
                                                        self.level_data, self.target_object)

        # give the enemy_handler the player
        self.enemy_handler.player = self.game_window.player
        self.enemy_handler.assign_player_health()

        # player pointer
        self.game_window.player.enemy_handler = self.enemy_handler

        self.current_mission_data['name'] = self.level_data['name']
        self.current_mission_data['planet'] = self.curr_planet.name
        self.current_mission_data['reward'] = self.level_data['reward']
        self.current_mission_data['company'] = self.level_data['company']

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
            if self.target_object.health <= 0:
                self.game_window.player.dead = True

        if self.enemy_handler is not None and self.enemy_handler.enemy_sprites is not None\
                and not self.game_window.wormhole:
            self.enemy_handler.on_update(delta_time)

    def add_mission_data(self):
        company = self.game_window.map.companies[self.current_mission_data['company']]

        self.base_mission_data['total_enemy'] = self.current_mission_data['total_enemy']
        self.base_mission_data['missions_completed'] += 1
        self.current_mission_data['missions_completed'] += 1
        self.current_mission_data['reputation'] = round(random.randrange(25, 35) * self.reputation_mod)
        self.game_window.player_credit += self.current_mission_data['reward']
        company['reputation'] += self.current_mission_data['reputation']
        if company['reputation'] > 250:
            company['reputation'] = 250
        if (company['reputation'] - (company['reputation'] % 50))/50 > \
                self.game_window.map.company_rep[company['name']]:
            self.game_window.map.company_rep[company['name']] += 1
            self.game_window.map.rewards(company['name'])
        self.game_window.map.save_map_pos()
