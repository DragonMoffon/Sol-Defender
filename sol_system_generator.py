import random
import json

EARTH_WEIGHT = 5.972 * 10 ** 24
EARTH_RADIUS = 6000000

MOON_WEIGHT = 7.35 * 10**22
MOON_RADIUS = 1737100

SOL_DATA = "Data/sol_generation_data.json"
SOL_SYSTEM = "Data/sol_system.json"

PLANET_BASE = "Sprites/Planets/"
SATELLITE_BASE = "Sprites/Satellites/"

HABITABLE = {"earth", "desert", "ocean"}


class Generator:

    def __init__(self):
        self.num_sections = 8
        self.num_planets = 0
        self.planets = []
        self.planet_subsets = ("exo", "gas")
        self.satellite_subsets = ("station", "moon")
        self.station_types = ("research", "research")
        self.moon_types = ("white", "red", "green")
        self.satellite_types = (self.station_types, self.moon_types)
        with open(SOL_DATA) as sol_file:
            self.sol_data = json.load(sol_file)
            self.basic_planet = self.sol_data['basic_planet']
            self.basic_satellite = self.sol_data['basic_satellite']
        self.generate()
        del self

    def generate(self):
        for cycle in range(1, self.num_sections + 1):
            self.cycle(cycle)
        self.clean_up()

    def cycle(self, curr_position):
        planet = self.generate_planet(curr_position)
        if planet is not None:
            self.planets.append(planet)

    def generate_planet_data(self, curr_position, subset,  planet_type):
        if planet_type != 'null':
            planet = dict(self.basic_planet)
            planet_data = self.sol_data[subset][planet_type]
            planet['satellites'] = []
            planet['map_symbol'] = {'orbit_pos': -1}
            planet['type'] = planet_type
            planet['subset'] = subset
            if planet['type'] in HABITABLE:
                planet['colonised'] = True
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
            planet['map_symbol']['speed'] = random.uniform(0.5, 2.6)
            if subset == "exo":
                planet['x_pos'] = random.randint(3000, 7500)
                planet['y_pos'] = random.randint(3000, 7500)
                min_satellites = (curr_position - 6)
                max_satellites = curr_position - 1
                if min_satellites < 0:
                    min_satellites = 0
            else:
                planet['x_pos'] = random.randint(4500, 9000)
                planet['y_pos'] = random.randint(4500, 9000)
                min_satellites = (curr_position - 3)
                max_satellites = curr_position + random.randint(0, 4)
                if min_satellites < 0:
                    min_satellites = 0
            previous_orbit = 0
            for satellites in range(random.randint(min_satellites, max_satellites)):
                satellite = dict(self.basic_satellite)
                satellite['orbit'] = previous_orbit + 1200 + (satellites * random.randint(350, 450))
                previous_orbit = satellite['orbit']
                satellite['speed'] = round(random.uniform(0.25, 3.5), 2)
                pick = random.randint(0, 1)
                satellite['gravity'] = pick
                satellite['subset'] = self.satellite_subsets[pick]
                pick_choice = self.satellite_types[pick]
                satellite['type'] = pick_choice[random.randrange(0, len(pick_choice))]
                satellite['texture'] = SATELLITE_BASE + f"{satellite['subset']}/{satellite['type']}.png"
                if pick:
                    rand_stats = random.random()
                    satellite['weight'] = MOON_WEIGHT * round(0.75 + (8 - 0.75) * rand_stats, 2)
                    satellite['radius'] = MOON_RADIUS * round(0.8 + (6 - 0.8) * rand_stats, 2)
                # print(f"    satellite{satellites + 1}: {satellite['subset']} : {satellite['type']}")
                planet['satellites'].append(satellite)
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

    def clean_up(self):
        if len(self.planets) < 3:
            self.generate()
        else:
            habitable_worlds = 0
            for index, planet in enumerate(self.planets):
                planet['map_symbol']['orbit'] = index + 1
                values = (5, 4, 1)
                symbols = ("V", "IV", "I")
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
                if planet['type'] == "silicate":
                    colonised = random.random()
                    if colonised >= (5 - habitable_worlds) / 10:
                        planet['colonised'] = True
            self.load()

    def load(self):
        for planet in self.planets:
            print(f"{planet['name']} : {planet['subset']} : {planet['type']}")

        with open(SOL_SYSTEM, "w") as sol_system:
            json_load = {'planets': self.planets}
            json.dump(json_load, sol_system, indent=4)
