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
import main
import vector

SCREEN_WIDTH, SCREEN_HEIGHT = arcade.get_display_size()
GUN_METAL = 50, 59, 63


class TitleScreen(arcade.View):

    def __init__(self, game_window):
        super().__init__()
        self.game_view = main.GameWindow()
        self.game_window = game_window

        self.state = 0

        self.stars = stars.StarField(self.game_view, False)
        angle = random.uniform(0, 2 * math.pi)
        self.velocity = [math.cos(angle) * 5, math.sin(angle) * 5]

        self.title = arcade.Sprite("Sprites/Sol Defender Title.png")
        self.title.center_x = SCREEN_WIDTH/2
        self.title.center_y = SCREEN_HEIGHT - 200

        self.button_data = [
            {'tex': 'Sprites/start.png', 'x': SCREEN_WIDTH/2, 'y': SCREEN_HEIGHT - 400,
             'action': 'launch', 'change': 0, 'state': 0,  'scale': 1},
            {'tex': 'Sprites/control.png', 'x': SCREEN_WIDTH/2, 'y': SCREEN_HEIGHT - 500,
             'action': 'change', 'change': 1, 'state': 0, 'scale': 1},
            {'tex': 'Sprites/back.png', 'x': 200, 'y': 40,
             'action': 'change', 'change': 0, 'state': 1, 'scale': 0.5}
        ]
        self.button_lists = [arcade.SpriteList(), arcade.SpriteList()]
        for button in self.button_data:
            sprite = arcade.Sprite(button['tex'], scale=button['scale'],
                                   center_x=button['x'], center_y=button['y'])
            sprite.change_x = self.button_data.index(button)
            self.button_lists[button['state']].append(sprite)

        self.text_data = [
            {'text': "Aim: Mouse", 'x': SCREEN_WIDTH/2, 'y': SCREEN_HEIGHT - 400,
             'state': 1, 'scale': 1},
            {'text': "Shoot: Space or Left MB", 'x': SCREEN_WIDTH/2, 'y': SCREEN_HEIGHT - 420,
             'state': 1, 'scale': 1},
            {'text': "Forward: W or Right MB", 'x': SCREEN_WIDTH/2, 'y': SCREEN_HEIGHT - 440,
             'state': 1, 'scale': 1},
            {'text': "Active Abilities: Keys 1 2 and 3", 'x': SCREEN_WIDTH/2, 'y': SCREEN_HEIGHT - 460,
             'state': 1, 'scale': 1},
            {'text': "Objective: Kill everything", 'x': SCREEN_WIDTH/2, 'y': SCREEN_HEIGHT - 480,
             'state': 1, 'scale': 1},
        ]
        self.text_lists = [arcade.SpriteList(), arcade.SpriteList()]
        for text in self.text_data:
            text_list = font.LetterList(text['text'], text['x'], text['y'], text['scale'], mid_x=True)
            self.text_lists[text['state']].extend(text_list)

        self.actions = {'launch': self.launch, 'change': self.switch_state}

    def switch_state(self, state):
        self.state = state

    def launch(self, state=0):
        self.game_view.do_planet_sprites()
        mini_map = Map(self.game_view)
        self.game_window.show_view(mini_map)

    def on_update(self, delta_time: float):
        self.stars.on_update(self.velocity)

    def on_draw(self):
        arcade.start_render()

        self.stars.draw()

        self.button_lists[self.state].draw()

        self.text_lists[self.state].draw()

        self.title.draw()

        self.game_view.cursor.draw()

    def on_mouse_motion(self, x: float, y: float, dx: float, dy: float):
        self.game_view.cursor.center_x = x
        self.game_view.cursor.center_y = y

    def on_mouse_press(self, x: float, y: float, button: int, modifiers: int):
        if button == arcade.MOUSE_BUTTON_LEFT:
            clicked = arcade.get_sprites_at_point((x, y), self.button_lists[self.state])
            if len(clicked):
                data = self.button_data[clicked[-1].change_x]
                action = self.actions[data['action']]
                action(data['change'])

    def on_key_press(self, key: int, modifiers: int):
        if key == arcade.key.ENTER:
            self.launch(0)
        elif key == arcade.key.ESCAPE or key == arcade.key.X:
            self.window.close()

    def on_show(self):
        intro = arcade.Sound("Music/Intro Jingle.wav")
        intro.play(vector.VOLUME)


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
        self.ship_tab = None

        self.active_upgrade = None
        self.do_active = False
        self.reward_handler = RewardHandler(self, self.game_view, self.game_view.player)

        self.setup()

    def setup(self, upgrades=False):
        self.current_mission = None
        self.selected_planet = None
        self.current_planet = None
        # generator = sol_system_generator.Generator(self.game_view)

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

            if self.mission_generator is None:
                self.mission_generator = mission.MissionGenerator()
            else:
                self.mission_generator.reload_dictionaries()
                self.mission_generator.generate()

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
            m_data = (None, None)
            for missions in self.mission_json['missions'].values():
                if missions['company'] == companies['name']:
                    if m_data[0] is not None:
                        m_data = (m_data[0], missions)
                    else:
                        m_data = (missions, None)
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

        self.reward_handler.do_all_rewards()

        if self.game_view.player is not None:
            self.ship_tab = ui.ShipTab(self.game_view.player.passive_upgrades, self.game_view, self)

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
                        if slides.mission_data[0] is not None:
                            for planets in self.planet_symbols:
                                if planets.name == slides.planet_data[slides.state]['name']:
                                    self.selected_planet = planets
                                    break
                else:
                    slides.mouse_over(False)
                    if self.selected_planet is not None and slides.mission_data[0] is not None and not slides.selected:
                        if slides.planet_data[slides.state]['name'] == self.selected_planet.name:
                            self.selected_planet = None

            self.upgrade_tab.check(self.upgrade_tab.collides_with_point(cxy))

            self.company_slides.update_animation(delta_time)
            self.upgrade_tab.update_animation(delta_time)

            if self.ship_tab is not None:
                self.ship_tab.mouse_over(self.ship_tab.collides_with_point(cxy))
        else:
            self.active_upgrade.check(cxy)

        reputation = 0
        for comp in self.companies.values():
            reputation += comp['reputation']
            if reputation >= 500:
                generator = sol_system_generator.Generator(self.game_view)
                break

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
            pass
            slides.draw()

        self.upgrade_tab.draw()
        if self.ship_tab is not None:
            self.ship_tab.update_animation()
            self.ship_tab.draw()

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
            self.upgrade_tab.on_mouse_press(cxy[0], cxy[1])
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
            print("odd")
            self.active_upgrade = ui.ActiveUpgrade(self.companies[company_name], self)
            self.do_active = True
            self.active_upgrade.slide = 1
        else:
            print("even")
            self.reward_handler.reward(company)

    def on_mouse_motion(self, x: float, y: float, dx: float, dy: float):
        self.game_view.cursor_screen_pos = [x, y]


class RewardHandler:

    def __init__(self, map_menu, game_window, player):
        self.map = map_menu
        self.game = game_window
        self.player = player

        self.current_company = None
        self.rep_level = 0

        self.rewards = {"more_available_missions": self.more_available_missions,
                        "more_reputation_gained": self.more_reputation_gained,
                        "more_available_upgrades": self.more_available_upgrades,
                        "max_speed": self.max_speed,
                        "better_overall_negatives": self.better_overall_negatives,
                        "better_overall_upgrades": self.better_overall_upgrades,
                        "cheaper_upgrades": self.cheaper_upgrades,
                        "more_scrap_value": self.more_scrap_value,
                        "less_gravity": self.less_gravity}
        self.current_reward = None

    def do_all_rewards(self):

        self.map.upgrade_generator.num_upgrades = 3

        self.map.mission_generator.num_missions = 3

        self.map.upgrade_generator.bane_modifier = 1
        self.map.upgrade_generator.all_modifier = 1
        self.map.upgrade_generator.cost_modifier = 1

        self.map.upgrade_tab.sell_bonus = 0.85

        self.game.mission.reputation_mod = 1

        self.game.player_max_speed = 95309
        self.game.player_gravity_dampening = 1

        for company in self.map.companies.values():
            self.reward(company)

    def reward(self, company):
        self.current_company = company

        rep = math.floor(company['reputation'] / 50)
        if company['reputation'] == 250:
            rep = 4

        if rep > 3:
            self.rep_level = 0
        elif rep > 1:
            self.rep_level = 1

        if rep:
            self.calc_reward()
            self.apply_reward()

        self.current_company = None
        self.rep_level = 0

    def calc_reward(self):
        self.current_reward = self.rewards[self.current_company['bonus']]

    def apply_reward(self):
        self.current_reward()

    def more_available_missions(self):
        # change variable in mission generator and leave the rest to it.
        # Change a variable in the mission generator that says how many missions to create.
        #
        # In the mission generator create a number of missions equal to this variable.
        # when it is greater than the number of companies make two for one of the companies.
        # In the map menu tell that company's upgrade slide to turn on the flip-flop switching.
        if self.rep_level:
            self.map.mission_generator.num_missions = 4
        else:
            self.map.mission_generator.num_missions = 5

    def more_reputation_gained(self):
        # change variable in mission generator and leave the rest to it.
        # change a variable in the mission generator that is multiplied onto the end of the reputation number.
        if self.rep_level:
            self.game.mission.reputation_mod = 1.10
        else:
            self.game.mission.reputation_mod = 1.25

    def more_available_upgrades(self):
        # change variable in upgrade generator and leave the rest to it.
        # Change a variable in the upgrade generator that says how many upgrades to make.
        # In the map menu tell the upgrade slide how many upgrades to create.
        # The upgrade slide then changes texture to match the one necessary for the number of upgrades.
        if self.rep_level:
            self.map.upgrade_generator.num_upgrades = 4
        else:
            self.map.upgrade_generator.num_upgrades = 5

    def max_speed(self):
        # change variable in Main Game for player and leave the rest to it.
        # change a variable in the main game so when it sets up the player it multiplies the player's max speed by
        # this new variable.
        if self.rep_level:
            self.game.player_max_speed = 2500 * 1.05
        else:
            self.game.player_max_speed = 2500 * 1.15

    def better_overall_negatives(self):
        # change variable in upgrade generator and leave the rest to it.
        # change a variable in the upgrade generator that multiplies with the bane modifier.
        if self.rep_level:
            self.map.upgrade_generator.bane_modifier = 1 - 0.5
        else:
            self.map.upgrade_generator.bane_modifier = 1 - 0.15

    def better_overall_upgrades(self):
        # change variable in upgrade generator and leave the rest to it.
        # change a variable in the upgrade generator that multiplies with the bonus and bane modifier.
        if self.rep_level:
            self.map.upgrade_generator.all_modifier = 1 + 0.5
        else:
            self.map.upgrade_generator.all_modifier = 1 + 0.15

    def cheaper_upgrades(self):
        if self.rep_level:
            self.map.upgrade_generator.cost_modifier = 1 - 0.5
        else:
            self.map.upgrade_generator.cost_modifier = 1 - 0.15

    def more_scrap_value(self):
        # change variable in map menu and leave the rest to it.
        # changes a variable in the map menu that increases the sell price of scrap.
        if self.rep_level:
            self.map.upgrade_tab.sell_bonus = 0.95
        else:
            self.map.upgrade_tab.sell_bonus = 1.10

    def less_gravity(self):
        # change a variable in the main game to affect the player and leave the rest to it.
        # change a variable in the main game that means when the player is set up the affect of gravity on them is
        # diminished.
        if self.rep_level:
            self.game.player_gravity_dampening = 1 - 0.5
        else:
            self.game.player_gravity_dampening = 1 - 0.15


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

        self.num_upgrades = 3
        self.bane_modifier = 1
        self.cost_modifier = 1
        self.all_modifier = 1

        self.bonus_upgrades = {}

    def setup_upgrades(self):
        self.bonus_upgrades = {}
        for companies in self.game_view.map.companies.values():
            self.bonus_upgrades[companies['upgrade']] = companies

        self.upgrades = []
        self.shown_upgrades = ()
        upgrade_variables = list(self.game_view.player.upgrade_mod)
        for upgrade in self.game_view.player.passive_upgrades:
            if upgrade['level'] < 3:
                new_upgrade = dict(upgrade)
                new_upgrade['level'] += 1
                new_upgrade['prev_upgrade'] = upgrade
                random_points = random.random()
                bonus_points = self.bonus_range[upgrade['level']]
                bane_points = self.bane_range[upgrade['level']]
                cost_points = self.cost_range[upgrade['level']]
                bonus = (bonus_points[0] + (bonus_points[1] - bonus_points[0]) * random_points)
                bane = bane_points[0] + (bane_points[1] - bane_points[0]) * random_points
                new_upgrade['bonus'] = round(bonus * self.all_modifier, 2)
                new_upgrade['bane'] = round(bane * self.all_modifier * self.bane_modifier, 2)
                if new_upgrade['bonus_name'] in self.bonus_upgrades:
                    bonus = 1 - (self.bonus_upgrades[new_upgrade['bonus_name']]['reputation'] / 250) * 0.25
                else:
                    bonus = 1

                cost = (cost_points[0] + (cost_points[1] - cost_points[0]) * random_points) * bonus
                new_upgrade['cost'] = round(cost * self.cost_modifier)
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
            bonus = (bonus_points[0] + (bonus_points[1] - bonus_points[0]) * random_points)
            bane = bane_points[0] + (bane_points[1] - bane_points[0]) * random_points
            new_upgrade['bonus'] = round(bonus * self.all_modifier, 2)
            new_upgrade['bane'] = round(bane * self.all_modifier * self.bane_modifier, 2)
            if new_upgrade['bonus_name'] in self.bonus_upgrades:
                bonus = 1 - (self.bonus_upgrades[new_upgrade['bonus_name']]['reputation'] / 250) * 0.25
            else:
                bonus = 1

            cost = (cost_points[0] + (cost_points[1] - cost_points[0]) * random_points) * bonus
            new_upgrade['cost'] = round(cost * self.cost_modifier)
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

        self.shown_upgrades = tuple(random.sample(self.upgrades, self.num_upgrades))
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
