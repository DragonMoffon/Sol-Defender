import random
import json
import math

# The weight and radius of earth for planets to be based off.
EARTH_WEIGHT = 5.972 * 10 ** 24
EARTH_RADIUS = 6000000

# The weight and radius of the moon for satellites to be based off.
MOON_WEIGHT = 7.35 * 10 ** 22
MOON_RADIUS = 1737100

# json file paths for concise code.
SOL_DATA = "game_data/Data/sol_generation_data.json"
SOL_SYSTEM = "game_data/Data/sol_system.json"

# json file paths for planet and satellite sprites.
PLANET_BASE = "game_data/Sprites/Planets/"
SATELLITE_BASE = "game_data/Sprites/Satellites/"

# sets for faster searching for planet checking.
HABITABLE = {"earth", "desert", "ocean"}
GAS = {"giant", "dwarf", "helium", "ice", "hot"}
COLONISABLE = {"silicate", "carbon", "ice"}
MINERAL = {"carbon", "lava", "iron", "silicate"}


class Generator:
    """
    The Generator Class generates all planets and companies in the Sol System.
    """

    def __init__(self, game_view):
        self.game_view = game_view

        # The number of planets that are possible.
        self.num_sections = 8

        # The current number of planets.
        self.num_planets = 0

        # All planets generated.
        self.planets = []

        # Lists for each Planet per class for company generation.
        self.planets_in_classes = {
            "colonised": [],
            "gas": [],
            "mineral": [],
        }

        # planet and moon subsets for naming, and texture path finding.
        self.planet_subsets = ("exo", "gas")
        self.moon_types = ("white", "red", "green")

        # Open sol_generation_data.json to find the empty planet and satellite dictionaries.
        self.companies = {}
        with open(SOL_DATA) as sol_file:
            self.sol_data = json.load(sol_file)
            self.basic_planet = self.sol_data['basic_planet']
            self.basic_satellite = self.sol_data['basic_satellite']

        # generate sol system and delete self.
        self.generate()
        del self

    def generate(self):
        # set variables again in case recalled.
        self.num_planets = 0
        self.planets = []
        self.planets_in_classes = {
            "colonised": [],
            "gas": [],
            "mineral": [],
        }
        self.companies = {}

        # try create a planet equal to self.num section, starting at 1.
        for cycle in range(1, self.num_sections + 1):
            self.cycle(cycle)

        # clean the dictionaries and dump to sol_system.json.
        self.clean_up()

    def cycle(self, curr_position):
        # generate a planet and if it is not None, add to the planets list.
        planet = self.generate_planet(curr_position)
        if planet is not None:
            self.planets.append(planet)

    def generate_planet(self, curr_position):
        # Generate the planet data.

        # pick whether the planet is an exo or gas planet.
        pick_subset = random.randrange(0, len(self.planet_subsets))
        subset = self.planet_subsets[pick_subset]
        type_picks = []

        # randomly pick the planet's typex
        for types in self.sol_data[subset]:
            test = self.sol_data[subset][types]

            # test if the type is possible in the planet's orbit position.
            if test['orbit'][0] <= curr_position <= test['orbit'][1]:
                for add in range(test['rarity']):
                    type_picks.append(types)

        planet_pick = random.choice(type_picks)

        # generate the planet's data.
        return self.generate_planet_data(curr_position, subset, planet_pick)

    def generate_planet_data(self, curr_position, subset, planet_type):
        # If the planet type is not null.
        if planet_type != 'null':
            # Copy the basic planet empty dict.
            planet = dict(self.basic_planet)

            # Find the data on the specific planet type.
            planet_data = self.sol_data[subset][planet_type]

            # Set the planet's data.
            planet['satellites'] = []

            # Create a dictionary for the map symbol within the orbit pos.
            planet['map_symbol'] = {'orbit_pos': -1}
            planet['type'] = planet_type
            planet['subset'] = subset
            planet['tex'] = random.randrange(0, len(self.game_view.planet_sprites[subset][planet_type]))

            # Check what type the planet is against the previously created sets for company generation.
            if planet['type'] in HABITABLE:
                planet['colonised'] = True
                self.planets_in_classes['colonised'].append(planet)
            elif planet['type'] in MINERAL:
                self.planets_in_classes['mineral'].append(planet)
            elif planet['type'] in GAS:
                self.planets_in_classes['gas'].append(planet)

            # Randomly choose the stats of the planet depending on supplied data and based on earth.
            rand_stats = random.random()
            weight = (planet_data['weight'][0] +
                      (planet_data['weight'][1] - planet_data['weight'][0])
                      * rand_stats) * EARTH_WEIGHT
            radius = (planet_data['size'][0]
                      + (planet_data['size'][1] - planet_data['size'][0])
                      * rand_stats) * EARTH_RADIUS
            planet['weight'] = round(weight, 2)
            planet['radius'] = round(radius, 2)

            # Find the texture location for the planet.
            planet['texture'] = PLANET_BASE + f"{subset}/{planet_type}.png"

            # Create more data for the map symbol of the planet.
            planet['map_symbol']['orbit'] = curr_position
            planet['map_symbol']['speed'] = round(random.uniform(0.5, 2.6), 2)

            # Find it's position, gas planets are placed further away from the 0, 0 orgin point.
            if subset == "exo":
                planet['x_pos'] = random.randint(3000, 7500)
                planet['y_pos'] = random.randint(3000, 7500)
            else:
                planet['x_pos'] = random.randint(4500, 9000)
                planet['y_pos'] = random.randint(4500, 9000)
            return planet
        return None

    def setup_satellites(self):
        # Create satellites both moons and company satellites.
        for planet in self.planets:

            # Change the possible amount of moons depending on subset, with gas giants getting more
            if planet['subset'] == "exo":
                min_satellites = (planet['map_symbol']['orbit'] - 6)
                max_satellites = planet['map_symbol']['orbit'] - 2
            else:
                min_satellites = (planet['map_symbol']['orbit'] - 5)
                max_satellites = planet['map_symbol']['orbit'] + random.randint(-3, 1)

            if min_satellites < 0:
                min_satellites = 0
            if max_satellites < 0:
                max_satellites = 0

            # A list of all the types of satellites, both moon and company.
            all_satellites = []
            num_satellites = random.randint(min_satellites, max_satellites)
            while len(all_satellites) < num_satellites:
                all_satellites.append("moon")

            for companies in self.companies.values():
                if planet['name'] in companies['planets'] or planet['name'] in companies['home_planet']:
                    all_satellites.append(companies['type'])

            # Shuffle the satellites so their orbits are random.
            random.shuffle(all_satellites)

            previous_orbit = 0
            # create the data for each satellite.
            for index, satellites in enumerate(all_satellites):
                # Create a copy of the empty satellite dict.
                satellite = dict(self.basic_satellite)

                # Create the orbit of the satellite, so that they are all suffiently spaced from each other.
                satellite['orbit'] = previous_orbit + 1200 + (index * random.randint(350, 450))
                if not previous_orbit:
                    satellite['orbit'] += 800
                previous_orbit = satellite['orbit']

                # Choose a random speed for the satellite.
                satellite['speed'] = round(random.uniform(0.05, 0.45), 2)

                # If the satellite is a moon, give it all the data needed for gravity calculations.
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

                # Find the texture location of the satellite and add it to the satellites of the planet.
                satellite['texture'] = SATELLITE_BASE + f"{satellite['subset']}/{satellite['type']}.png"
                planet['satellites'].append(satellite)

    def clean_up(self):
        # If there are less than 6 planets recreate the Sol System.
        if len(self.planets) < 6:
            self.generate()
        else:
            # A check to see if there are any habitable worlds.
            habitable_worlds = 0

            # Line all of the planets up and give them a a same based on their position.
            for index, planet in enumerate(self.planets):
                # sets the map symbols orbit to the order of the planets.
                planet['map_symbol']['orbit'] = index + 1

                # A simple function that takes the index position plus one and uses it to find the Roman numeral value.
                values = (9, 5, 4, 1)
                symbols = ("IX", "V", "IV", "I")
                value = 0
                num = index + 1
                while num > 0:
                    for _ in range(num // values[value]):
                        planet['name'] += symbols[value]
                        num -= values[value]
                    value += 1

                # If the planet is habitable increase the habitable world check by one.
                if planet['subset'] == 'exo' and planet['type'] in HABITABLE:
                    habitable_worlds += 1

            # If no habitable worlds were generated, create one in orbit 2 of the Sol System.
            if not habitable_worlds:
                self.planets[1] = self.generate_planet_data(2, 'exo', random.choice(tuple(HABITABLE)))
                self.planets[1]['name'] = "sol II"
                habitable_worlds += 1

            # Check if any of the planets are colonisable, if they are randomly choose if they are colonised.
            for planet in self.planets:
                if planet['type'] in COLONISABLE and planet['subset'] == 'exo':
                    colonised = random.random()
                    if colonised >= (8 - habitable_worlds) / 10:
                        planet['colonised'] = True
                        habitable_worlds += 1
                        if planet in self.planets_in_classes['mineral']:
                            self.planets_in_classes['mineral'].remove(planet)
                            self.planets_in_classes['colonised'].append(planet)

            # setup companies and satellites then load the data to sol_system.json.
            self.company()
            self.setup_satellites()
            self.load()

    def company(self):
        # open the company generation json file and get all data from it.
        self.planets_in_classes['all'] = self.planets
        with open("game_data/Data/company_generation_data.json") as company_file:
            company_json = json.load(company_file)
            pos_companies = company_json['companies']
            bonuses = company_json['bonus']
            upgrades = company_json['upgrade']

        # the self.companies dict holds all the final data.
        self.companies = {}

        # The list of picked companies. randomly select three.
        picked_companies = random.sample(pos_companies.keys(), 3)

        # if the government company was chosen choose three more until the government is not included.
        while 'government' in picked_companies:
            picked_companies = random.sample(pos_companies.keys(), 3)

        # add the government back in.
        picked_companies.append('government')

        # make a company dict for each picked company/
        for companies in picked_companies:
            # Create the company dict and choose the company home planet.
            company = {'bonus': None, 'upgrade': None,
                       'home_planet': random.choice(self.planets_in_classes['colonised'])['name'],
                       'planets': [], 'missions': []}

            # If there are possible bonuses and upgrades for the company, generate it's data.
            if len(bonuses[companies]) and len(upgrades[companies]):
                # Randomly generate the companies bonuses, and upgrades.
                # Then remove those options from all other companies.
                company['bonus'] = random.choice(bonuses[companies])
                company['upgrade'] = random.choice(upgrades[companies])
                for other_companies in pos_companies:
                    if other_companies != companies:
                        if company['bonus'] in bonuses[other_companies]:
                            bonuses[other_companies].remove(company['bonus'])
                        if company['upgrade'] in upgrades[other_companies]:
                            upgrades[other_companies].remove(company['upgrade'])

                # Supply the types of missions the company offers.
                company['missions'] = pos_companies[companies]['missions']

                # Calculates the total number of company satellites, and the possible planets.
                num_satellites = math.ceil(len(self.planets) / 3)
                planet_quick = pos_companies[companies]['planets']
                pick_planets = []
                for classes in planet_quick:
                    pick_planets.extend(self.planets_in_classes[classes])

                # Randomly selects a planet for a satellite depending on the num_satellites value.
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

                    # Adds the picked planet to the companies planet list.
                    if planet_pick:
                        pick_planets.remove(planet_pick_full)
                        company['planets'].append(planet_pick)
                    else:
                        break

                # sets the name and type to the type of planet.
                company['type'] = companies
                company['name'] = companies
                company['reputation'] = 0
                self.companies[companies] = company
            else:
                # If the planet cannot generate a unique upgrade and special ability do not generate it.
                break

        # print the data for the company.
        for company in self.companies.values():
            print(f"{company['type']}, Home World: {company['home_planet']} \n"
                  f"      Planets of Operation: {company['planets']} \n"
                  f"      Specialities: {company['bonus']} : {company['upgrade']}")

    def load(self):
        # the final solar system dictionary.
        final = {}

        # Print the name of the planet, then add it to the final dict.
        for planet in self.planets:
            print(f"{planet['name']} : {planet['subset']} : {planet['type']}", end="")
            if planet['colonised']:
                print(" : Colonised")
            else:
                print("")
            final[planet['name']] = planet

        # Add companies to the sol_system data the load it to sol_system.json.
        with open(SOL_SYSTEM, "w") as sol_system:
            json_load = {'planets': final, 'companies': self.companies}
            json.dump(json_load, sol_system, indent=4)
