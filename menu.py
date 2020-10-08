import json
import random
import math
import time

import arcade

import sol_system_generator
import mission
import font
import stars
import ui

SCREEN_WIDTH, SCREEN_HEIGHT = arcade.get_display_size()
GUN_METAL = 50, 59, 63


class MapSymbol(arcade.Sprite):
    def __init__(self, x, y, base_distance, data):
        super().__init__(f"Sprites/Planets/symbol/{data['subset']}/{data['type']}.png", 0.15)
        self.data = data
        self.name = data['name']
        self.current_mission = None
        if data['orbit_pos'] < 0:
            self.orbit_pos = random.randrange(0, 360)
        else:
            self.orbit_pos = data['orbit_pos']
        self.base_orbit = base_distance
        self.orbit = data['orbit']
        self.speed = data['speed']
        self.sun_x = x
        self.sun_y = y
        rad_angle = math.radians(self.orbit_pos)
        self.center_x = self.sun_x + (math.cos(rad_angle) * (self.base_orbit * self.orbit))
        self.center_y = self.sun_y + (math.sin(rad_angle) * (self.base_orbit * self.orbit))

    def on_update(self, delta_time: float = 1/60):
        self.orbit_pos += self.speed * self.orbit * delta_time
        rad_angle = math.radians(self.orbit_pos)
        self.center_x = self.sun_x + (math.cos(rad_angle) * (self.base_orbit * self.orbit))
        self.center_y = self.sun_y + (math.sin(rad_angle) * (self.base_orbit * self.orbit))

    def fix(self, x, y):
        self.sun_x = x
        self.sun_y = y

    def draw_mission(self):
        pass


class Map(arcade.View):
    def __init__(self, game_view, upgrades_todo=False):
        super().__init__()
        self.game_view = game_view
        self.game_view.map = self
        self.max_orbit = 300
        self.selected_planet = None
        self.current_mission = None
        self.current_planet = None
        self.planet_symbols = None
        self.companies = None
        self.sun = None
        self.planet_data = None
        self.sol_data = None
        self.mission_generator = None
        self.mission_json = {}

        self.alert_symbols = None
        self.alert_texture = arcade.load_texture("Sprites/Planets/symbol/mission_alert.png")
        self.mission_sprite = arcade.Sprite("Sprites/Ui/current_mission.png", 0.15)
        self.selected_sprite = arcade.Sprite("Sprites/Ui/selected_planet.png", 0.15)
        self.launch_sprite = arcade.Sprite("Sprites/Player/Ui/launch.png", 0.2)

        self.company_slides = None
        self.company_slide_dict = None
        self.current_slide = None
        self.company_rep = {}

        self.upgrade_tab = None
        self.upgrades = []
        self.current_upgrade = None
        self.upgrades_todo = upgrades_todo
        self.upgrade_generator = UpgradesGenerator(self.game_view)

        self.active_upgrade = None
        self.do_active = False

        self.setup()

    def setup(self, upgrades=False):
        self.current_mission = None
        self.selected_planet = None
        self.current_planet = None
        # generator = sol_system_generator.Generator(self.game_view)
        if self.mission_generator is None:
            self.mission_generator = mission.MissionGenerator()
        else:
            self.mission_generator.reload_dictionaries()
            self.mission_generator.generate()

        self.planet_symbols = arcade.SpriteList()
        self.sun = arcade.Sprite("Sprites/Planets/symbol/sun.png",
                                 center_x=self.game_view.left_view + SCREEN_WIDTH / 2,
                                 center_y=self.game_view.bottom_view + SCREEN_HEIGHT / 2,
                                 scale=0.15)
        with open("Data/sol_system.json") as sol_data:
            sol_json = json.load(sol_data)
            self.sol_data = sol_json
            self.planet_data = sol_json['planets']
            self.companies = sol_json['companies']
            base_orbit = self.max_orbit / len(self.planet_data)
            x = self.sun.center_x
            y = self.sun.center_y
            for planet_d in self.planet_data.values():
                data = dict(planet_d['map_symbol'])
                data['name'] = planet_d['name']
                data['type'] = planet_d['type']
                data['subset'] = planet_d['subset']
                planet = MapSymbol(x, y, base_orbit, data)

                with open("Data/mission_data.json") as mission_data:
                    self.mission_json = json.load(mission_data)
                    if data['name'] in self.mission_json['missions']:
                        planet.current_mission = self.mission_json['missions'][data['name']]
                        self.mission_json['missions'][data['name']]['planet_data'] = planet_d

                with open("Data/mission_data.json", "w") as mission_dump:
                    json.dump(self.mission_json, mission_dump, indent=4)
                self.planet_symbols.append(planet)

        self.company_slides = arcade.SpriteList()
        self.company_slide_dict = {}
        self.company_rep = {}
        s_x = self.game_view.left_view + SCREEN_WIDTH - 65
        s_y = self.game_view.bottom_view + SCREEN_HEIGHT - 210
        for companies in self.companies.values():
            m_data = None
            for missions in self.mission_json['missions'].values():
                if missions['company'] == companies['name']:
                    m_data = missions
            slide = ui.CompanyTab(s_x, s_y, companies, m_data, self)
            self.company_slides.append(slide)
            self.company_slide_dict[companies['name']] = slide
            s_y -= 100

            rep = (companies['reputation'] - (companies['reputation'] % 50))/50
            self.company_rep[companies['name']] = rep

        if upgrades:
            self.upgrades = self.upgrade_generator.setup_upgrades()
        else:
            self.upgrades = (None, None, None)
        self.upgrade_tab = ui.UpgradeTab(self, self.upgrades)

        self.launch_sprite.center_x = self.game_view.left_view + (SCREEN_WIDTH / 2)
        self.launch_sprite.center_y = self.game_view.bottom_view + 60

    def on_show(self):
        self.sun.center_x, self.sun.center_y = self.game_view.left_view+SCREEN_WIDTH/2,\
                                               self.game_view.bottom_view+SCREEN_HEIGHT/2
        for planet in self.planet_symbols:
            planet.fix(self.sun.center_x, self.sun.center_y)

        for slides in self.company_slides:
            slides.update_position()

        self.upgrade_tab.update_position()

        if self.current_slide is not None:
            self.current_slide.slide = 1
            self.current_slide.start_t = time.time() * 1000
            self.current_slide.b = 0

    def on_update(self, delta_time: float):
        self.planet_symbols.on_update(delta_time)
        cxy = (self.game_view.left_view + self.game_view.cursor_screen_pos[0],
               self.game_view.bottom_view + self.game_view.cursor_screen_pos[1])
        self.game_view.cursor.center_x = cxy[0]
        self.game_view.cursor.center_y = cxy[1]

        if not self.do_active:
            check = arcade.get_sprites_at_point(cxy, self.company_slides)
            for slides in self.company_slides:
                if len(check) and check[-1] == slides:
                    if self.current_slide is None or self.current_slide == slides:
                        slides.mouse_over(True)
                        self.current_slide = slides
                        if slides.mission_data is not None:
                            for planets in self.planet_symbols:
                                if planets.name == slides.planet_data['name']:
                                    self.selected_planet = planets
                                    break
                else:
                    slides.mouse_over(False)
                    if self.selected_planet is not None and slides.mission_data is not None and not slides.selected:
                        if slides.planet_data['name'] == self.selected_planet.name:
                            self.selected_planet = None

            self.upgrade_tab.check(self.upgrade_tab.collides_with_point(cxy))

            self.company_slides.update_animation(delta_time)
            self.upgrade_tab.update_animation(delta_time)
        else:
            self.active_upgrade.check(cxy)

    def draw_text(self):
        if self.game_view.current_mission is not None:
            arcade.draw_text(f"R: restart {self.current_mission['name']}",
                             self.game_view.left_view + 10,
                             self.game_view.bottom_view + SCREEN_HEIGHT - 50,
                             arcade.color.WHITE)

            arcade.draw_text(f"Any: Close 'mini map'",
                             self.game_view.left_view + 10,
                             self.game_view.bottom_view + SCREEN_HEIGHT - 75,
                             arcade.color.WHITE)

            if self.selected_planet is not None and self.current_planet != self.selected_planet:
                arcade.draw_text(f"Enter: Launch for {self.selected_planet.name}",
                                 self.game_view.left_view + 10,
                                 self.game_view.bottom_view + SCREEN_HEIGHT - 100,
                                 arcade.color.WHITE)
        else:
            if self.selected_planet is not None:
                arcade.draw_text(f"Enter: Launch for {self.selected_planet.name}",
                                 self.game_view.left_view + 10,
                                 self.game_view.bottom_view + SCREEN_HEIGHT - 50,
                                 arcade.color.WHITE)

        arcade.draw_text(f"X: close game",
                         self.game_view.left_view + 10,
                         self.game_view.bottom_view + SCREEN_HEIGHT - 25,
                         arcade.color.WHITE)

    def draw(self):
        if self.current_mission is not None:
            self.game_view.on_draw()
            arcade.draw_rectangle_filled(self.game_view.left_view + SCREEN_WIDTH/2,
                                         self.game_view.bottom_view + SCREEN_HEIGHT/2,
                                         SCREEN_WIDTH, SCREEN_HEIGHT, (50, 50, 50, 120))
        self.planet_symbols.draw()

        self.alert_symbols = arcade.SpriteList()
        for planets in self.planet_symbols:
            if planets.current_mission is not None \
                    and self.selected_planet != planets and self.current_planet != planets:
                alert = arcade.Sprite(center_x=planets.center_x, center_y=planets.center_y + 28, scale=0.15)
                alert.texture = self.alert_texture
                self.alert_symbols.append(alert)
        self.alert_symbols.draw()

        if self.selected_planet is not None and self.selected_planet != self.current_planet:
            self.launch_sprite.draw()
            self.selected_sprite.center_x = self.selected_planet.center_x
            self.selected_sprite.center_y = self.selected_planet.center_y
            self.selected_sprite.draw()
        if self.current_planet is not None:
            self.mission_sprite.center_x = self.current_planet.center_x
            self.mission_sprite.center_y = self.current_planet.center_y
            self.mission_sprite.draw()

        for slides in self.company_slides:
            slides.draw()

        self.upgrade_tab.draw()

        self.sun.draw()

        if self.do_active and self.active_upgrade is not None:
            arcade.draw_rectangle_filled(self.game_view.left_view + SCREEN_WIDTH/2,
                                         self.game_view.bottom_view + SCREEN_HEIGHT/2,
                                         SCREEN_WIDTH+100, SCREEN_HEIGHT+100, (90, 90, 90, 90))
            if not self.active_upgrade.start_t:
                self.active_upgrade.start_t = time.time() * 1000
            self.active_upgrade.update_animation()
            self.active_upgrade.draw()

    def on_draw(self):
        arcade.start_render()
        self.draw()
        self.draw_text()

        self.game_view.cursor.draw()

    def on_key_press(self, key: int, modifiers: int):
        if self.do_active:
            self.active_upgrade.trigger()
        if key == arcade.key.ENTER and self.selected_planet is not None and self.selected_planet != self.current_planet:
            self.current_mission = self.selected_planet.current_mission
            self.current_planet = self.selected_planet
            self.game_view.current_mission = self.current_mission
            self.close_up()
        elif key == arcade.key.X:
            if self.game_view.player is not None:
                self.game_view.player.clear_upgrades()
            self.reset_map_pos()
            self.window.close()
        elif key == arcade.key.R:
            generator = sol_system_generator.Generator(self.game_view)
            self.game_view.current_mission = None
            self.setup()
        elif key == arcade.key.M:
            self.current_mission = None
            self.game_view.current_mission = None
            self.save_map_pos()
            self.setup()
            with open("Data/mission_data.json") as mission_data:
                self.mission_json = json.load(mission_data)
                for planet in self.planet_symbols:
                    if planet.name in self.mission_json['missions']:
                        self.mission_json['missions'][planet.name]['planet_data'] = \
                            self.planet_data[planet.name]
                        planet.current_mission = self.mission_json['missions'][planet.name]

                    else:
                        planet.current_mission = None

        elif self.game_view.current_mission is not None:
            self.save_map_pos()
            self.window.show_view(self.game_view)

    def on_mouse_press(self, x: float, y: float, button: int, modifiers: int):
        if self.do_active:
            self.active_upgrade.trigger()

        if button == arcade.MOUSE_BUTTON_LEFT and not self.do_active:
            cxy = (self.game_view.left_view + self.game_view.cursor_screen_pos[0],
                   self.game_view.bottom_view + self.game_view.cursor_screen_pos[1])
            if self.upgrade_tab.selected_upgrade:
                self.upgrade_tab.on_mouse_press()
            if self.launch_sprite.collides_with_point((cxy[0], cxy[1])) and \
                    self.selected_planet is not None and self.selected_planet != self.current_planet:
                self.current_planet = self.selected_planet
                self.current_mission = self.current_planet.current_mission
                self.game_view.current_mission = self.current_mission
                self.close_up()
            else:
                cursor_over = arcade.get_sprites_at_point(cxy, self.planet_symbols)
                if len(cursor_over) > 0:
                    if self.selected_planet == cursor_over[0] and self.selected_planet != self.current_planet:
                        self.current_planet = cursor_over[0]
                        self.current_mission = self.current_planet.current_mission
                        self.game_view.current_mission = self.current_mission
                        self.close_up()
                    elif self.selected_planet == cursor_over[0]:
                        self.save_map_pos()
                        self.window.show_view(self.game_view)
                    if self.selected_planet is not None:
                        self.company_slide_dict[self.selected_planet.current_mission['company']].selected = False
                    self.selected_planet = None
                    if cursor_over[0].current_mission is not None:
                        self.selected_planet = cursor_over[0]
                        self.company_slide_dict[self.selected_planet.current_mission['company']].selected = True
                        self.current_slide = self.company_slide_dict[self.selected_planet.current_mission['company']]
                else:
                    self.selected_planet = None
                    if self.current_slide is not None:
                        self.current_slide.selected = False
                        self.current_slide = None

    def save_map_pos(self):
        for planets in self.planet_symbols:
            self.sol_data['planets'][planets.name]['map_symbol']['orbit_pos'] = planets.orbit_pos
        with open("Data/sol_system.json", "w") as file:
            json.dump(self.sol_data, file, indent=4)

    def reset_map_pos(self):
        for planets in self.planet_symbols:
            self.sol_data['planets'][planets.name]['map_symbol']['orbit_pos'] = -1
        with open("Data/sol_system.json", "w") as file:
            json.dump(self.sol_data, file, indent=4)

    def close_up(self):
        self.save_map_pos()
        self.game_view.setup()
        self.window.show_view(self.game_view)

    def rewards(self, company_name):
        company = self.companies[company_name]
        if self.company_rep[company_name] % 2:
            self.active_upgrade = ui.ActiveUpgrade(self.companies[company_name], self)
            self.do_active = True
            self.active_upgrade.slide = 1
        else:
            print('not implemented \n'
                  + font.DONKEY)

    def on_mouse_motion(self, x: float, y: float, dx: float, dy: float):
        self.game_view.cursor_screen_pos = [x, y]


class UpgradesGenerator:

    def __init__(self, game_view):
        with open("Data/upgrade_data.json") as upgrade_file:
            upgrade_json = json.load(upgrade_file)
            self.static_abilities = upgrade_json['static_abilities']
            self.base_static_upgrade = upgrade_json['base_static']

        self.bonus_range = (
            (0.1, 0.15), (0.16, 0.21), (0.22, 0.27)
        )
        self.bane_range = (
            (0.03, 0.08), (0.09, 0.14), (0.15, 0.2)
        )
        self.cost_range = (
            (45, 65), (70, 90), (95, 115)
        )

        self.upgrades = []
        self.shown_upgrades = []
        self.saved_upgrade = {}

        self.game_view = game_view

        self.bonus_upgrades = {}

    def setup_upgrades(self):
        self.bonus_upgrades = {}
        for companies in self.game_view.map.companies.values():
            self.saved_upgrade[companies['upgrade']] = companies['name']

        self.upgrades = []
        self.shown_upgrades = ()
        upgrade_variables = list(self.game_view.player.upgrade_mod)
        print(upgrade_variables)
        for upgrade in self.game_view.player.passive_upgrades:
            if upgrade['level'] < 3:
                print(upgrade_variables)
                print(upgrade['bonus_name'])
                new_upgrade = dict(upgrade)
                new_upgrade['level'] += 1
                new_upgrade['prev_upgrade'] = upgrade
                random_points = random.random()
                bonus_points = self.bonus_range[upgrade['level']]
                bane_points = self.bane_range[upgrade['level']]
                cost_points = self.cost_range[upgrade['level']]
                new_upgrade['bonus'] = round(bonus_points[0] + (bonus_points[1] - bonus_points[0]) * random_points, 2)
                new_upgrade['bane'] = round(bane_points[0] + (bane_points[1] - bane_points[0]) * random_points, 2)
                if new_upgrade['bonus'] in self.bonus_upgrades:
                    bonus = 1 - (self.bonus_upgrades[new_upgrade['bonus']]['reputation'] / 250) * 0.25
                else:
                    bonus = 1
                new_upgrade['cost'] = round(cost_points[0] + (cost_points[1] - cost_points[0]) * random_points) * bonus
                broken = new_upgrade['name'].split(" ")
                first_half = broken[0]
                second_half = broken[1]
                if new_upgrade['level'] == 2:
                    new_upgrade['name'] = first_half + " " + second_half + " MK_II"
                else:
                    new_upgrade['name'] = first_half + " " + second_half + " MK_III"

                upgrade_variables.remove(new_upgrade['bonus_name'])
                self.upgrades.append(new_upgrade)

        for upgrade_variable in upgrade_variables:
            new_upgrade = dict(self.base_static_upgrade)
            new_upgrade['bonus_name'] = upgrade_variable
            while new_upgrade['bane_name'] == "":
                pick = random.randrange(0, len(self.static_abilities))
                if self.static_abilities[pick]['name'] != new_upgrade['bonus_name']:
                    new_upgrade['bane_name'] = self.static_abilities[pick]['name']
            random_points = random.random()
            bonus_points = self.bonus_range[0]
            bane_points = self.bane_range[0]
            cost_points = self.cost_range[0]
            new_upgrade['bonus'] = round(bonus_points[0] + (bonus_points[1] - bonus_points[0]) * random_points, 2)
            new_upgrade['bane'] = round(bane_points[0] + (bane_points[1] - bane_points[0]) * random_points, 2)
            new_upgrade['cost'] = round(cost_points[0] + (cost_points[1] - cost_points[0]) * random_points)
            first_half = ""
            second_half = ""
            for naming in self.static_abilities:
                if naming['name'] == new_upgrade['bane_name']:
                    first_half = naming['negative']
                elif naming['name'] == new_upgrade['bonus_name']:
                    second_half = naming['positive']

                if first_half != "" and second_half != "":
                    break

            new_upgrade['name'] = first_half + " " + second_half + " MK_I"
            self.upgrades.append(new_upgrade)

        self.shown_upgrades = tuple(random.sample(self.upgrades, 3))
        return self.shown_upgrades


class MissionEndCard(arcade.View):

    def __init__(self, game_view):
        super().__init__()
        self.mission_stats = None
        self.base_strings = {
            'name': '',
            'company': '',
            'planet': 'Planet: ',
            'reward': 'Reward: ',
            'reputation': 'Reputation: ',
            'enemies_killed': 'Threats Eliminated: ',
            'total_enemy': 'Total Eliminated: ',
            'scrap_identify': 'Scrap Identified: ',
            'scrap_collect': 'Scrap Collected: ',
            'missions_completed': 'Missions Completed: '
        }

        self.mission_strings = None
        self.text_strings = []
        self.star_field = None
        self.false_screen_velocity = [0.0, 0.0]
        self.false_screen_acceleration = [0.0, 0.0]
        self.direction = 0
        self.game_view = game_view

    def setup(self, mission_stats):
        self.mission_stats = mission_stats
        self.text_strings = []

        s_x = SCREEN_WIDTH/2 - 250
        s_y = SCREEN_HEIGHT/2 + 140

        self.mission_strings = dict(self.base_strings)
        for string in self.mission_strings:
            string = self.mission_strings[string] + str(self.mission_stats[string])
            text = string.lower()
            self.text_strings.append(font.LetterList(text, s_x, s_y))
            s_y -= 18

    def on_show(self):
        # view
        self.game_view.left_view = 0
        self.game_view.bottom_view = 0
        arcade.set_viewport(self.game_view.left_view,
                            SCREEN_WIDTH + self.game_view.left_view,
                            self.game_view.bottom_view,
                            SCREEN_HEIGHT + self.game_view.bottom_view)

        self.star_field = stars.StarField(self.game_view, False)

        self.direction = math.radians(random.randrange(0, 360))
        d_x = math.cos(self.direction) * 5
        d_y = math.sin(self.direction) * 5
        self.false_screen_velocity = [d_x, d_y]
        self.false_screen_acceleration = [d_x, d_y]

    def on_update(self, delta_time: float):
        if self.false_screen_velocity[0] == 0 or self.false_screen_velocity[1] == 0:
            self.false_screen_velocity[0] = 0.5
            self.false_screen_velocity[0] = 0.5
        if math.sqrt(self.false_screen_velocity[0]**2 + self.false_screen_velocity[1]**2) <= 35:
            self.false_screen_velocity[0] += self.false_screen_acceleration[0] * delta_time
            self.false_screen_velocity[1] += self.false_screen_acceleration[1] * delta_time
        self.star_field.on_update(self.false_screen_velocity)

    def on_draw(self):
        arcade.start_render()
        self.star_field.draw()
        arcade.draw_rectangle_filled(SCREEN_WIDTH/2, SCREEN_HEIGHT/2,
                                     SCREEN_WIDTH + 150, SCREEN_HEIGHT + 150,
                                     (90, 90, 90, 90))
        for text in self.text_strings:
            text.draw()

    def on_key_press(self, symbol: int, modifiers: int):
        self.game_view.open_upgrade_map()

    def on_mouse_press(self, x: float, y: float, button: int, modifiers: int):
        self.game_view.open_upgrade_map()
