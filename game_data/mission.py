import json
import random
import copy as c

import game_data.space as space
import game_data.enemy_handler as enemy_handler

# Mission Generator.
#       This creates the missions each time the player finishes a mission and launches the game.
#
# Mission.
#       This Class handles the aspects of the game around missions, it creates the planet, enemy handler, and keeps
#       handles the json storage systems for missions.


class MissionGenerator:

    def __init__(self):

        # Load data for companies and planets from sol_system.json.
        with open('game_data/Data/sol_system.json') as planet_file:
            planet_json = json.load(planet_file)
            self.planets = planet_json['planets']
            self.companies = planet_json['companies']

        # Load data about the enemy types from enemy_types.json.
        with open("game_data/Data/enemy_types.json") as enemy_file:
            enemy_json = json.load(enemy_file)
            self.all_enemies = enemy_json['basic_types']
            self.all_bosses = enemy_json['boss_types']

        # Load an empty mission dictionary.
        with open("game_data/Data/mission_data.json") as mission_file:
            mission_json = json.load(mission_file)
            self.mission_json = mission_json['planet_x']

        self.missions = {}
        self.selected_missions = {}
        self.dump_missions = {
                            "planet_x": self.mission_json
                            }

        # The number of missions to generate. Is modified by the reward handler in menu.py.
        self.num_missions = 3
        self.generate()

    def reload_dictionaries(self):
        """
        This function reloads all of the data read from the .json files in case the Sol System was recreated.
        """

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
        # for the companies in the sol system, generate a mission for each planet they have a satellite on.
        for companies in self.companies.values():
            # get a list of all planets they have a satellite on.
            all_planets = list(companies['planets'])
            all_planets.append(companies['home_planet'])

            # add an empty dictionary to the missions dictionary with the company type as the key.
            self.missions[companies['type']] = {}

            # generate a mission for each planet.
            for planet in all_planets:
                self.generate_mission(companies, planet)

        # select a number of missions equal to self.num_missions and save them to mission_data.json
        self.select()
        self.dump()

    def generate_mission(self, company, planet):
        """
        Generate a mission based of the input company and planet.
        This mission has a random selection of possible enemies and bosses.

        :param company: The company which requests this mission
        :param planet: The planet that the mission takes place at.
        """

        # create a copy of the empty mission dictionary. Then fill it with the necessary data.
        mission = c.deepcopy(self.mission_json)

        # the number of sets of 5 waves that occur. always 1.
        mission['stages'] = 1

        # The type of mission it is based on the company. always visual.
        mission['types'] = random.choice(company['missions'])

        # The input company.
        mission['company'] = company['name']

        # The randomly picked possible enemies and bosses.
        enemy_picks = random.sample(self.all_enemies, random.randrange(1, len(self.all_enemies)))
        for enemies in enemy_picks:
            mission['possible_enemies'].append(enemies['type'])

        boss_picks = random.sample(self.all_bosses, random.randrange(1, len(self.all_bosses)))
        for bosses in boss_picks:
            mission['possible_bosses'].append(bosses['type'])

        # Final data, including the rewards.
        mission['name'] = f"{mission['types']} {planet}"
        mission['planet_data'] = self.planets[planet]
        mission['reward'] = random.randint(55, 85)

        # Add the mission to the previously created empty dictionary.
        self.missions[company['type']][mission['name']] = mission

    def select(self):
        """
        Randomly selects a number of the generated missions equal to the number of missions.
        """

        if self.num_missions < 5:
            # if the number of missions is less than 5
            # pick a random selection of companies equal to the num of missions.
            companies = random.sample(self.companies.keys(), self.num_missions)
        else:
            # If there is 5 or more missions, add all companies and then add one again randomly.
            companies = list(self.companies.keys())
            companies.append(random.choice(list(self.companies.keys())))

        # the dictionary that holds the randomly selected mission for each company.
        mission = {}

        # the list of picked planets that have missions.
        picked_planets = []

        # for each company randomly chosen, pick one of the randomly created missions that is on a mission that
        # has no mission yet.
        for company in companies:
            picking = True
            while picking:
                copy_cat = c.copy(self.missions[company])
                # remove all missions that are on planets that are already picked.
                for missions in copy_cat.values():
                    if missions['planet_data']['name'] in picked_planets:
                        self.missions[company].pop(missions['name'])

                # if there are any missions left choose one to be the mission for this company, then add the missions
                # planet to the picked planet list.
                if len(self.missions[company]):
                    mission = random.choice(list(self.missions[company].values()))
                    picked_planets.append(mission['planet_data']['name'])
                    picking = False
                else:
                    picking = False

            # if the mission is not an empty mission append it to selected missions.
            if mission != {}:
                self.selected_missions[mission['planet_data']['name']] = mission

    def dump(self):
        # dump the mission data to mission_data.json.
        self.dump_missions['missions'] = self.selected_missions
        with open("game_data/Data/mission_data.json", "w") as mission_data:
            json.dump(self.dump_missions, mission_data, indent=4)


class Mission:

    def __init__(self, game_window):
        self.game_window = game_window
        self.level_data = None

        # The objects the Mission class handles when in game.
        self.enemy_handler = None
        self.curr_planet = None
        self.target_object = None

        # the base mission data dictionary used on the mission end card.
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

        # the modifier that changes how much reputation the player gains from a mission.
        # changed by the reward handler in menu.py
        self.reputation_mod = 1

    def reload(self):
        # resets the mission.
        if self.enemy_handler is not None:
            self.enemy_handler.reset()

    def mission_setup(self, level_data: dict = None):
        # sets up the mission from the data loaded from level_data.
        self.level_data = level_data
        self.current_mission_data = dict(self.base_mission_data)

        self.enemy_handler = None
        self.curr_planet = None

        # If level_data is supplied, setup the mission.
        if level_data is not None:
            self.setup()

    def setup(self):
        # From enemy_types.json load all enemy types.
        with open("game_data/Data/enemy_types.json") as enemy_file:
            enemy_types = json.load(enemy_file)
            basic_enemies = enemy_types['basic_types']
            boss_enemies = enemy_types['boss_types']

        # Create the current missions planet from supplied data.
        self.curr_planet = space.Planet(self.game_window, self.level_data['planet_data'])
        self.level_data['planet'] = self.curr_planet
        self.target_object = None

        # find the satellite of the mission's company.
        for satellite in self.curr_planet.satellites:
            if satellite.type == self.level_data['company']:
                self.target_object = satellite
                break
        if self.target_object is None:
            # If the satellite does not exist then there has been a generation error.
            raise TypeError("This Planet Doesn't Have the Satellite Your Looking for")

        # find the enemy types that are used in this mission for the enemy_handler.
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

        # give the current mission data the information needed for the mission end card.
        self.current_mission_data['name'] = self.level_data['name']
        self.current_mission_data['planet'] = self.curr_planet.name
        self.current_mission_data['reward'] = self.level_data['reward']
        self.current_mission_data['company'] = self.level_data['company']

    def check_setup(self):
        # check to see if the player is moving, this is to ensure enemies only spawn once the player has moved.
        if self.game_window.player.start == 1:
            self.enemy_handler.setup_wave()
            self.game_window.player.start = 2

    def draw(self):
        # the basic draw functions, however if there are any objects that equal None do not draw them.
        if self.curr_planet is not None:
            self.curr_planet.draw()

        if self.enemy_handler is not None and self.enemy_handler.enemy_sprites is not None:
            self.enemy_handler.draw()

    def on_update(self, delta_time: float = 1/60):
        # Update all objects that are not None.
        if self.curr_planet is not None:
            self.curr_planet.on_update(delta_time)
            if self.target_object.health <= 0:
                self.game_window.player.dead = True

        if self.enemy_handler is not None and self.enemy_handler.enemy_sprites is not None\
                and not self.game_window.wormhole:
            self.enemy_handler.on_update(delta_time)

    def add_mission_data(self):
        # Do a final modification of self.current_mission_data for the end card.

        company = self.game_window.map.companies[self.current_mission_data['company']]

        # add the total number of enemies killed to base mission data so it stays between missions.
        self.base_mission_data['total_enemy'] = self.current_mission_data['total_enemy']

        # record that a mission is complete to the base mission data so it stays between missions.
        self.base_mission_data['missions_completed'] += 1
        self.current_mission_data['missions_completed'] += 1

        # give the player a reputation reward, to the company of the mission.
        self.current_mission_data['reputation'] = round(random.randrange(25, 35) * self.reputation_mod)
        self.game_window.player_credit += self.current_mission_data['reward']
        company['reputation'] += self.current_mission_data['reputation']
        if company['reputation'] > 250:
            company['reputation'] = 250
        elif (company['reputation'] - (company['reputation'] % 50))/50 > \
                self.game_window.map.company_rep[company['name']]:
            # If the company has reached a new reputation level then reward the player.
            self.game_window.map.company_rep[company['name']] += 1
            self.game_window.map.rewards(company['name'])

        # save data in the map.
        self.game_window.map.save_map_pos()
