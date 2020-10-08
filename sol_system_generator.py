import random
import json
import math

EARTH_WEIGHT = 5.972 * 10 ** 24
EARTH_RADIUS = 6000000

MOON_WEIGHT = 7.35 * 10 ** 22
MOON_RADIUS = 1737100

SOL_DATA = "Data/sol_generation_data.json"
SOL_SYSTEM = "Data/sol_system.json"

PLANET_BASE = "Sprites/Planets/"
SATELLITE_BASE = "Sprites/Satellites/"

HABITABLE = {"earth", "desert", "ocean"}
GAS = {"giant", "dwarf", "helium", "ice", "hot"}
COLONISABLE = {"silicate", "carbon", "ice"}
MINERAL = {"carbon", "lava", "iron", "silicate"}


class Generator:

    def __init__(self, game_view):
        self.game_view = game_view
        self.num_sections = 8
        self.num_planets = 0
        self.planets = []
        self.planets_in_classes = {
            "colonised": [],
            "gas": [],
            "mineral": [],
        }
        self.planet_subsets = ("exo", "gas")
        self.moon_types = ("white", "red", "green")
        self.companies = {}
        with open(SOL_DATA) as sol_file:
            self.sol_data = json.load(sol_file)
            self.basic_planet = self.sol_data['basic_planet']
            self.basic_satellite = self.sol_data['basic_satellite']
        self.generate()
        del self

    def generate(self):
        self.num_planets = 0
        self.planets = []
        self.planets_in_classes = {
            "colonised": [],
            "gas": [],
            "mineral": [],
        }
        self.companies = {}
        for cycle in range(1, self.num_sections + 1):
            self.cycle(cycle)
        self.clean_up()

    def cycle(self, curr_position):
        planet = self.generate_planet(curr_position)
        if planet is not None:
            self.planets.append(planet)

    def generate_planet_data(self, curr_position, subset, planet_type):
        if planet_type != 'null':
            planet = dict(self.basic_planet)
            planet_data = self.sol_data[subset][planet_type]
            planet['satellites'] = []
            planet['map_symbol'] = {'orbit_pos': -1}
            planet['type'] = planet_type
            planet['subset'] = subset
            planet['tex'] = random.randrange(0, len(self.game_view.planet_sprites[subset][planet_type]))
            if planet['type'] in HABITABLE:
                planet['colonised'] = True
                self.planets_in_classes['colonised'].append(planet)
            elif planet['type'] in MINERAL:
                self.planets_in_classes['mineral'].append(planet)
            elif planet['type'] in GAS:
                self.planets_in_classes['gas'].append(planet)
            # print(curr_position, ":", subset, ":", planet_type)
            rand_stats = random.random()
            weight = (planet_data['weight'][0] +
                      (planet_data['weight'][1] - planet_data['weight'][0])
                      * rand_stats) * EARTH_WEIGHT
            radius = (planet_data['size'][0]
                      + (planet_data['size'][1] - planet_data['size'][0])
                      * rand_stats) * EARTH_RADIUS
            planet['weight'] = round(weight, 2)
            planet['radius'] = round(radius, 2)
            # print(planet['weight'], ":", planet['radius'], ":", round(rand_stats, 2))
            planet['texture'] = PLANET_BASE + f"{subset}/{planet_type}.png"
            planet['map_symbol']['orbit'] = curr_position
            planet['map_symbol']['speed'] = round(random.uniform(0.5, 2.6), 2)
            if subset == "exo":
                planet['x_pos'] = random.randint(3000, 7500)
                planet['y_pos'] = random.randint(3000, 7500)
            else:
                planet['x_pos'] = random.randint(4500, 9000)
                planet['y_pos'] = random.randint(4500, 9000)
            return planet
        return None

    def generate_planet(self, curr_position):
        pick_subset = random.randrange(0, len(self.planet_subsets))
        subset = self.planet_subsets[pick_subset]
        type_picks = []
        for types in self.sol_data[subset]:
            test = self.sol_data[subset][types]
            if test['orbit'][0] <= curr_position <= test['orbit'][1]:
                for add in range(test['rarity']):
                    type_picks.append(types)
        random.shuffle(type_picks)
        planet_pick = random.randrange(0, len(type_picks))
        planet_type = type_picks[planet_pick]
        return self.generate_planet_data(curr_position, subset, planet_type)

    def setup_satellites(self):
        for planet in self.planets:
            if planet['subset'] == "exo":
                min_satellites = (planet['map_symbol']['orbit'] - 6)
                max_satellites = planet['map_symbol']['orbit'] - 2
            else:
                min_satellites = (planet['map_symbol']['orbit'] - 5)
                max_satellites = planet['map_symbol']['orbit'] + random.randint(-1, 3)

            if min_satellites < 0:
                min_satellites = 0
            if max_satellites < 0:
                max_satellites = 0

            all_satellites = []
            num_satellites = random.randint(min_satellites, max_satellites)
            while len(all_satellites) < num_satellites:
                all_satellites.append("moon")

            for companies in self.companies.values():
                if planet['name'] in companies['planets'] or planet['name'] in companies['home_planet']:
                    all_satellites.append(companies['type'])

            random.shuffle(all_satellites)

            previous_orbit = 0
            for index, satellites in enumerate(all_satellites):
                satellite = dict(self.basic_satellite)
                satellite['orbit'] = previous_orbit + 1200 + (index * random.randint(350, 450))
                if not previous_orbit:
                    satellite['orbit'] += 800
                previous_orbit = satellite['orbit']
                satellite['speed'] = round(random.uniform(0.05, 0.45), 2)
                if satellites == "moon":
                    satellite['subset'] = 'moon'
                    pick = random.choice(self.moon_types)
                    satellite['type'] = pick
                    satellite['gravity'] = True
                    rand_stats = random.random()
                    satellite['weight'] = MOON_WEIGHT * round(0.75 + (8 - 0.75) * rand_stats, 2)
                    satellite['radius'] = MOON_RADIUS * round(0.8 + (6 - 0.8) * rand_stats, 2)
                else:
                    satellite['subset'] = 'station'
                    satellite['type'] = satellites

                satellite['texture'] = SATELLITE_BASE + f"{satellite['subset']}/{satellite['type']}.png"
                planet['satellites'].append(satellite)

    def clean_up(self):
        if len(self.planets) < 6:
            self.generate()
        else:
            habitable_worlds = 0
            for index, planet in enumerate(self.planets):
                planet['map_symbol']['orbit'] = index + 1
                values = (9, 5, 4, 1)
                symbols = ("IX", "V", "IV", "I")
                value = 0
                num = index + 1
                while num > 0:
                    for _ in range(num // values[value]):
                        planet['name'] += symbols[value]
                        num -= values[value]
                    value += 1
                if planet['subset'] == 'exo' and planet['type'] in HABITABLE:
                    habitable_worlds += 1

            if not habitable_worlds:
                self.planets[1] = self.generate_planet_data(2, 'exo', random.choice(tuple(HABITABLE)))
                self.planets[1]['name'] = "sol II"
                habitable_worlds += 1

            for planet in self.planets:
                if planet['type'] in COLONISABLE and planet['subset'] == 'exo':
                    colonised = random.random()
                    if colonised >= (8 - habitable_worlds) / 10:
                        planet['colonised'] = True
                        habitable_worlds += 1
                        if planet in self.planets_in_classes['mineral']:
                            self.planets_in_classes['mineral'].remove(planet)
                            self.planets_in_classes['colonised'].append(planet)
            self.company()
            self.setup_satellites()
            self.load()

    def load(self):
        final = {}
        for planet in self.planets:
            print(f"{planet['name']} : {planet['subset']} : {planet['type']}", end="")
            if planet['colonised']:
                print(" : Colonised")
            else:
                print("")
            final[planet['name']] = planet

        with open(SOL_SYSTEM, "w") as sol_system:
            json_load = {'planets': final, 'companies': self.companies}
            json.dump(json_load, sol_system, indent=4)

    def company(self):
        self.planets_in_classes['all'] = self.planets
        with open("Data/company_generation_data.json") as company_file:
            company_json = json.load(company_file)
            pos_companies = company_json['companies']
            bonuses = company_json['bonus']
            upgrades = company_json['upgrade']

        self.companies = {}
        picked_companies = ['government']
        while 'government' in picked_companies:
            picked_companies = random.sample(pos_companies.keys(), 3)
        picked_companies.append('government')

        for companies in picked_companies:
            company = {'bonus': None, 'upgrade': None,
                       'home_planet': random.choice(self.planets_in_classes['colonised'])['name'],
                       'planets': [], 'missions': []}
            if len(bonuses[companies]) and len(upgrades[companies]):
                company['bonus'] = random.choice(bonuses[companies])
                company['upgrade'] = random.choice(upgrades[companies])
                company['missions'] = pos_companies[companies]['missions']
                for other_companies in pos_companies:
                    if other_companies != companies:
                        if company['bonus'] in bonuses[other_companies]:
                            bonuses[other_companies].remove(company['bonus'])
                        if company['upgrade'] in upgrades[other_companies]:
                            upgrades[other_companies].remove(company['upgrade'])

                num_satellites = math.ceil(len(self.planets) / 3)
                planet_quick = pos_companies[companies]['planets']
                pick_planets = []
                for classes in planet_quick:
                    pick_planets.extend(self.planets_in_classes[classes])

                for satellite in range(num_satellites):
                    planet_pick_full = {}
                    planet_pick = 0
                    while not planet_pick:
                        if len(pick_planets):
                            planet_pick_full = pick_planets[random.randrange(0, len(pick_planets))]
                            if planet_pick_full['name'] != company['home_planet']:
                                planet_pick = planet_pick_full['name']
                            else:
                                pick_planets.remove(planet_pick_full)
                        else:
                            break

                    if planet_pick:
                        pick_planets.remove(planet_pick_full)
                        company['planets'].append(planet_pick)
                    else:
                        break

                company['type'] = companies
                company['name'] = companies
                company['reputation'] = 0
                self.companies[companies] = company
            else:
                print(f"{companies} Cant Be Special Today")
                break

        for company in self.companies.values():
            print(f"{company['type']}, Home World: {company['home_planet']} \n"
                  f"      Planets of Operation: {company['planets']} \n"
                  f"      Specialities: {company['bonus']} : {company['upgrade']}")
