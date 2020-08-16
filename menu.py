import json
import random
import math

import arcade

import sol_system_generator
import mission
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
        self.draw_hit_box(arcade.color.BLIZZARD_BLUE, 2)
        x = self.center_x
        y = self.center_y + 30
        arcade.draw_text(str(self.name), x, y, arcade.color.WHITE)
        y -= 15
        arcade.draw_text(self.current_mission['name'], x, y, arcade.color.WHITE)


class Map(arcade.View):
    def __init__(self, game_view):
        super().__init__()
        self.game_view = game_view
        self.game_view.map = self
        self.max_orbit = 300
        self.selected_planet = None
        self.current_mission = None
        self.current_planet = None
        self.planet_symbols = None
        self.sun = None
        self.planet_data = None
        self.mission_generator = None
        self.mission_json = {}

        self.alert_symbols = None
        self.alert_texture = arcade.load_texture("Sprites/Planets/symbol/mission_alert.png")

        self.setup()

    def setup(self):
        self.current_mission = None
        self.selected_planet = None
        self.current_planet = None
        self.mission_generator = mission.MissionGenerator()

        self.planet_symbols = arcade.SpriteList()
        self.sun = arcade.Sprite("Sprites/Planets/symbol/sun.png",
                                 center_x=self.game_view.left_view + SCREEN_WIDTH / 2,
                                 center_y=self.game_view.bottom_view + SCREEN_HEIGHT / 2,
                                 scale=0.15)
        with open("Data/sol_system.json") as sol_data:
            sol_json = json.load(sol_data)
            self.planet_data = sol_json
            base_orbit = self.max_orbit / len(sol_json['planets'])
            for planet_d in sol_json['planets']:
                x = self.sun.center_x
                y = self.sun.center_y
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

    def on_show(self):
        self.sun.center_x, self.sun.center_y = self.game_view.left_view+SCREEN_WIDTH/2,\
                                               self.game_view.bottom_view+SCREEN_HEIGHT/2
        for planet in self.planet_symbols:
            planet.fix(self.sun.center_x, self.sun.center_y)

    def on_update(self, delta_time: float):
        self.planet_symbols.on_update(delta_time)
        cxy = (self.game_view.left_view + self.game_view.cursor_screen_pos[0],
               self.game_view.bottom_view + self.game_view.cursor_screen_pos[1])
        self.game_view.cursor.center_x = cxy[0]
        self.game_view.cursor.center_y = cxy[1]

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
                self.selected_planet.draw_mission()
                arcade.draw_text(f"Enter: Launch for {self.selected_planet.name}",
                                 self.game_view.left_view + 10,
                                 self.game_view.bottom_view + SCREEN_HEIGHT - 50,
                                 arcade.color.WHITE)

        arcade.draw_text(f"Esc: close game",
                         self.game_view.left_view + 10,
                         self.game_view.bottom_view + SCREEN_HEIGHT - 25,
                         arcade.color.WHITE)

        if self.selected_planet is not None:
            if self.selected_planet == self.current_planet:
                self.selected_planet.draw_hit_box(arcade.color.RADICAL_RED, 2)
            else:
                self.selected_planet.draw_mission()
                launch = arcade.Sprite("Sprites/Player/Ui/launch.png", 0.2)
                launch.center_x = self.game_view.left_view + (SCREEN_WIDTH/2)
                launch.center_y = self.game_view.bottom_view + 60
                launch.draw()

    def draw(self):
        if self.current_mission is not None:
            self.game_view.on_draw()
            arcade.draw_rectangle_filled(self.game_view.left_view + SCREEN_WIDTH/2,
                                         self.game_view.bottom_view + SCREEN_HEIGHT/2,
                                         SCREEN_WIDTH, SCREEN_HEIGHT, (50, 50, 50, 120))
        self.planet_symbols.draw()

        self.alert_symbols = arcade.SpriteList()
        for planets in self.planet_symbols:
            if planets.current_mission is not None and self.selected_planet != planets:
                alert = arcade.Sprite(center_x=planets.center_x, center_y=planets.center_y + 28, scale=0.15)
                alert.texture = self.alert_texture
                self.alert_symbols.append(alert)
        self.alert_symbols.draw()

        self.sun.draw()

    def on_draw(self):
        arcade.start_render()
        self.draw()
        self.draw_text()

        self.game_view.cursor.draw()

    def on_key_press(self, key: int, modifiers: int):
        if key == arcade.key.ENTER and self.selected_planet is not None and self.selected_planet != self.current_planet:
            self.current_mission = self.selected_planet.current_mission
            self.current_planet = self.selected_planet
            self.game_view.current_mission = self.current_mission
            self.close_up()
        elif key == arcade.key.ESCAPE:
            if self.game_view.player is not None:
                self.game_view.player.clear_upgrades()
            self.reset_map_pos()
            self.window.close()
        elif key == arcade.key.R:
            generator = sol_system_generator.Generator()
            self.game_view.current_mission = None
            self.setup()
        elif self.game_view.current_mission is not None:
            self.save_map_pos()
            self.window.show_view(self.game_view)

    def on_mouse_press(self, x: float, y: float, button: int, modifiers: int):
        if button == arcade.MOUSE_BUTTON_LEFT:
            cxy = (self.game_view.left_view + self.game_view.cursor_screen_pos[0],
                   self.game_view.bottom_view + self.game_view.cursor_screen_pos[1])
            cursor_over = arcade.get_sprites_at_point(cxy, self.planet_symbols)
            if len(cursor_over) > 0:
                if self.selected_planet == cursor_over[0] and self.selected_planet != self.current_planet:
                    self.game_view.current_mission = cursor_over[0].current_mission['key']
                    self.current_planet = cursor_over[0]
                    self.current_mission = self.current_planet.current_mission
                    self.close_up()
                elif self.selected_planet == cursor_over[0]:
                    self.save_map_pos()
                    self.window.show_view(self.game_view)
                self.selected_planet = None
                if cursor_over[0].current_mission is not None:
                    self.selected_planet = cursor_over[0]

    def save_map_pos(self):
        for index, planets in enumerate(self.planet_symbols):
            self.planet_data['planets'][index]['map_symbol']['orbit_pos'] = planets.orbit_pos
        with open("Data/sol_system.json", "w") as file:
            json.dump(self.planet_data, file, indent=4)

    def reset_map_pos(self):
        for index, planets in enumerate(self.planet_symbols):
            self.planet_data['planets'][index]['map_symbol']['orbit_pos'] = -1
        with open("Data/sol_system.json", "w") as file:
            json.dump(self.planet_data, file, indent=4)

    def close_up(self):
        self.save_map_pos()
        self.window.show_view(self.game_view)

    def launch(self):
        pass

    def on_mouse_motion(self, x: float, y: float, dx: float, dy: float):
        self.game_view.cursor_screen_pos = [x, y]


class UpgradeMenu(arcade.View):

    def __init__(self, game_view):
        super().__init__()
        with open("Data/upgrade_data.json") as upgrade_file:
            upgrade_json = json.load(upgrade_file)
            self.static_abilities = upgrade_json['static_abilities']
            self.base_static_upgrade = upgrade_json['base_static']
            self.base_active_upgrade = upgrade_json['base_active']

        self.bonus_range = (
            (0.1, 0.15), (0.16, 0.21), (0.22, 0.27)
        )
        self.bane_range = (
            (0.03, 0.08), (0.09, 0.14), (0.15, 0.2)
        )
        self.game_view = game_view
        self.upgrades = []
        self.shown_upgrades = []
        self.selected_upgrade = None
        self.saved_upgrade = {}

        self.mouse_pos = (0.0, 0.0)

    def on_show(self):
        self.selected_upgrade = None
        self.setup_upgrades()
        self.game_view.left_view = 0
        self.game_view.bottom_view = 0
        arcade.set_viewport(self.game_view.left_view, self.game_view.left_view + SCREEN_WIDTH,
                            self.game_view.bottom_view, self.game_view.bottom_view + SCREEN_HEIGHT)

    def on_draw(self):
        arcade.start_render()
        self.game_view.on_draw()
        self.game_view.map.draw()
        for index, upgrades in enumerate(self.shown_upgrades):
            x = SCREEN_WIDTH - 150
            y = SCREEN_HEIGHT//2 + index * 100
            if x - 75 < self.mouse_pos[0] < x + 75 and y - 37.5 < self.mouse_pos[1] < y + 37.5 \
                    or self.selected_upgrade is upgrades:
                self.selected_upgrade = upgrades
                arcade.draw_rectangle_filled(x, y, 150, 75, arcade.color.ALLOY_ORANGE)
                arcade.draw_text(upgrades['name'], x, y + 20, arcade.color.WHITE, anchor_x="center")
                arcade.draw_text(f"{upgrades['bonus_name']}: {int(upgrades['bonus'] * 100)}%", x, y,
                                 arcade.color.WHITE, anchor_x="center")
                arcade.draw_text(f"{upgrades['bane_name']}: {int(upgrades['bane'] * 100)}%", x, y - 25,
                                 arcade.color.WHITE, anchor_x="center")
            else:
                arcade.draw_rectangle_filled(x, y, 150, 75, GUN_METAL)
                arcade.draw_text(upgrades['name'], x, y + 20, arcade.color.WHITE, anchor_x="center")
                arcade.draw_text("bonus: " + upgrades['bonus_name'], x, y, arcade.color.WHITE, anchor_x="center")
                arcade.draw_text("bane: " + upgrades['bane_name'], x, y - 25, arcade.color.WHITE, anchor_x="center")
        self.game_view.cursor.center_x = self.game_view.cursor_screen_pos[0]
        self.game_view.cursor.center_y = self.game_view.cursor_screen_pos[1]
        self.game_view.cursor.draw()

    def on_update(self, delta_time: float):
        self.game_view.map.on_update(delta_time)

    def setup_upgrades(self):
        self.upgrades = []
        self.shown_upgrades = []
        upgrade_variables = list(self.game_view.player.upgrade_mod)
        for upgrade in self.game_view.player.passive_upgrades:
            if upgrade['level'] < 3:
                new_upgrade = dict(upgrade)
                new_upgrade['level'] += 1
                new_upgrade['prev_upgrade'] = upgrade
                random_points = random.random()
                bonus_points = self.bonus_range[upgrade['level']]
                bane_points = self.bane_range[upgrade['level']]
                new_upgrade['bonus'] = round(bonus_points[0] + (bonus_points[1] - bonus_points[0]) * random_points, 2)
                new_upgrade['bane'] = round(bane_points[0] + (bane_points[1] - bane_points[0]) * random_points, 2)
                broken = new_upgrade['name'].split(" ")
                first_half = broken[0]
                second_half = broken[1]
                if new_upgrade['level'] == 2:
                    new_upgrade['name'] = first_half + " " + second_half + " MK II"
                else:
                    new_upgrade['name'] = first_half + " " + second_half + " MK III"

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
            new_upgrade['bonus'] = round(bonus_points[0] + (bonus_points[1] - bonus_points[0]) * random_points, 2)
            new_upgrade['bane'] = round(bane_points[0] + (bane_points[1] - bane_points[0]) * random_points, 2)
            first_half = ""
            second_half = ""
            for naming in self.static_abilities:
                if naming['name'] == new_upgrade['bane_name']:
                    first_half = naming['negative']
                elif naming['name'] == new_upgrade['bonus_name']:
                    second_half = naming['positive']

                if first_half != "" and second_half != "":
                    break

            new_upgrade['name'] = first_half + " " + second_half + " MK I"
            self.upgrades.append(new_upgrade)

        for i in range(3):
            pick_i = random.randrange(0, len(self.upgrades))
            self.shown_upgrades.append(self.upgrades[pick_i])
            self.upgrades.remove(self.upgrades[pick_i])

    def on_key_press(self, key: int, modifiers: int):
        if key == arcade.key.ESCAPE:
            self.game_view.player.clear_upgrades()
            arcade.close_window()
        elif key == arcade.key.Z:
            self.window.show_view(self.game_view)
        elif arcade.key.KEY_1 <= key <= arcade.key.KEY_3:
            self.selected_upgrade = self.shown_upgrades[key - 49]
        elif key == arcade.key.ENTER and self.selected_upgrade is not None:
            if self.selected_upgrade['prev_upgrade'] != {}:
                self.game_view.player.passive_upgrades.remove(self.selected_upgrade['prev_upgrade'])
            self.game_view.player.setup_upgrades(self.selected_upgrade)
            with open('Data/current_upgrade_data.json', 'w') as upgrade_data:
                json.dump(self.game_view.player.passive_upgrades, upgrade_data, indent=4)
            self.game_view.current_mission = -1
            self.game_view.open_clean_map()

    def on_mouse_motion(self, x: float, y: float, dx: float, dy: float):
        self.mouse_pos = (x, y)
        self.game_view.cursor_screen_pos = self.mouse_pos
