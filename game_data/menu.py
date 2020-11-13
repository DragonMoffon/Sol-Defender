import json
import random
import math
import time

import arcade

import game_data.sol_system_generator as sol_system_generator
import game_data.mission as mission
import game_data.font as font
import game_data.stars as stars
import game_data.ui as ui
import game_data.game as game
import game_data.vector as vector

SCREEN_WIDTH, SCREEN_HEIGHT = arcade.get_display_size()


class TitleScreen(arcade.View):
    """
    This is the initial screen the player sees when the game is launched.

    It uses a state system to just show the text needed.

    State 0 is the main screen.

    State 1 is the instructions page.

    State 2 is the ship select page.
    """

    def __init__(self, game_window):
        super().__init__()
        self.game_view = game.GameWindow()
        self.game_window = game_window

        # It sets the cursor to a more visible color.
        self.game_view.cursor.texture = arcade.load_texture("game_data/Sprites/Player/Ui/cross_hair_white.png")

        # The state for each page.
        self.state = 0

        # A StarField so that the background is not plain black.
        self.stars = stars.StarField(self.game_view, False)
        angle = random.uniform(0, 2 * math.pi)
        self.velocity = [math.cos(angle) * 5, math.sin(angle) * 5]

        # The title graphic. Since this is the main screen the title is always visible.
        self.title = arcade.Sprite("game_data/Sprites/Sol Defender Title.png")
        self.title.center_x = SCREEN_WIDTH / 2
        self.title.center_y = SCREEN_HEIGHT - 200

        # This list holds the button data.
        #   Each button contains:
        #       tex: The texture location
        #       x: The center x pos, y: The center y pos.
        #       action: What action the button takes. This is use later in the action handler.
        #       change: This is the input variable that is used in the action handler.
        #       state: This says what state the button is shown on.
        #       scale: The scale of the sprite.
        self.button_data = [
            {'tex': 'game_data/Sprites/shs_start.png', 'x': SCREEN_WIDTH / 2, 'y': SCREEN_HEIGHT - 500,
             'action': 'launch', 'change': 0, 'state': 0, 'scale': 1},
            {'tex': 'game_data/Sprites/shs_help.png', 'x': SCREEN_WIDTH / 2, 'y': SCREEN_HEIGHT - 430,
             'action': 'change', 'change': 1, 'state': 0, 'scale': 1},
            {'tex': 'game_data/Sprites/shs_ships.png', 'x': SCREEN_WIDTH / 2, 'y': SCREEN_HEIGHT - 569,
             'action': 'change', 'change': 2, 'state': 0, 'scale': 1},
            {'tex': 'game_data/Sprites/back.png', 'x': 200, 'y': 40,
             'action': 'change', 'change': 0, 'state': 1, 'scale': 0.5},
            {'tex': 'game_data/Sprites/back.png', 'x': 200, 'y': 40,
             'action': 'change', 'change': 0, 'state': 2, 'scale': 0.5},
            {'tex': 'game_data/Sprites/back_bn.png', 'x': SCREEN_WIDTH / 2 - 150, 'y': SCREEN_HEIGHT - 700,
             'action': 'ship', 'change': -1, 'state': 2, 'scale': 0.25},
            {'tex': 'game_data/Sprites/next_bn.png', 'x': SCREEN_WIDTH / 2 + 150, 'y': SCREEN_HEIGHT - 700,
             'action': 'ship', 'change': 1, 'state': 2, 'scale': 0.25}
        ]
        # There is a list of SpriteLists that hold all the buttons. The index position of the list is used with the
        # self.state variable to show specific buttons.
        self.button_lists = [arcade.SpriteList(), arcade.SpriteList()]

        # For every button in self.button_data create a button sprite.
        for button in self.button_data:
            # This while loop ensure that the button_list has enough sprite lists.
            while len(self.button_lists) - 1 < button['state']:
                self.button_lists.append(arcade.SpriteList())
            sprite = arcade.Sprite(button['tex'], scale=button['scale'],
                                   center_x=button['x'], center_y=button['y'])
            # Set the change_x of the button to be its index for later accessing.
            sprite.change_x = self.button_data.index(button)
            self.button_lists[button['state']].append(sprite)

        # Similar to the button data, this list holds all the text data.
        #   Each sting contains:
        #       tex: The string that will be loaded
        #       x: The center x of the string, y : The center y of the string.
        #       state: The state the text will show in
        #       scale: The scale on which the text will be.
        self.text_data = [
            {'text': "Aim: Mouse", 'x': SCREEN_WIDTH / 2, 'y': SCREEN_HEIGHT - 400,
             'state': 1, 'scale': 1},
            {'text': "Shoot: Space or Left MB", 'x': SCREEN_WIDTH / 2, 'y': SCREEN_HEIGHT - 420,
             'state': 1, 'scale': 1},
            {'text': "Forward: W or Right MB", 'x': SCREEN_WIDTH / 2, 'y': SCREEN_HEIGHT - 440,
             'state': 1, 'scale': 1},
            {'text': "Active Abilities: Keys 1 2 and 3", 'x': SCREEN_WIDTH / 2, 'y': SCREEN_HEIGHT - 460,
             'state': 1, 'scale': 1},
            {'text': "Show map: Tab", 'x': SCREEN_WIDTH / 2, 'y': SCREEN_HEIGHT - 480,
             'state': 1, 'scale': 1},
            {'text': "Objective: Kill everything", 'x': SCREEN_WIDTH / 2, 'y': SCREEN_HEIGHT - 500,
             'state': 1, 'scale': 1},
            {'text': "Select Your Ship", 'x': SCREEN_WIDTH / 2, 'y': SCREEN_HEIGHT - 400,
             'state': 2, 'scale': 1},
            {'text': "Music and Jingles Created By SketchyLogic", 'x': SCREEN_WIDTH / 2, 'y': 35,
             'state': 0, 'scale': 1}
        ]

        # Same as the button list it creates a sprite list for each state.
        self.text_lists = []
        # For each text in text data create a string of text and add it to the specific state SpriteList.
        for text in self.text_data:
            while len(self.text_lists) - 1 < text['state']:
                self.text_lists.append(arcade.SpriteList())
            text_list = font.LetterList(text['text'], text['x'], text['y'], text['scale'], mid_x=True)
            self.text_lists[text['state']].extend(text_list)

        # These variables are specifically for the ship action within the action handler.
        self.ship_type = 0
        self.ships = list(self.game_view.player_ships.keys())
        self.ship_data = self.game_view.player_ships
        self.ship_sprite = arcade.Sprite(self.ship_data[self.ships[self.ship_type]]['texture'], scale=0.2,
                                         center_x=SCREEN_WIDTH / 2, center_y=SCREEN_HEIGHT - 600)
        self.ship_name = font.LetterList(self.ships[self.ship_type], SCREEN_WIDTH / 2, SCREEN_HEIGHT - 430,
                                         mid_x=True)

        # The action dictionary that holds all of the different actions as functions.
        self.actions = {'launch': self.launch, 'change': self.switch_state, 'ship': self.ship}

    def switch_state(self, state=0):
        """
        This method switches the state to the supplied state.

        :param state: The supplied state to switch to.
        """
        self.state = state

    def launch(self, state=0):
        """
        Launches the game and opens the map menu.

        :param state: UNUSED.
        """
        self.game_view.do_planet_sprites()
        self.game_view.cursor.texture = arcade.load_texture("game_data/Sprites/Player/Ui/cross_hair_light.png")
        generator = sol_system_generator.Generator(self.game_view)
        mini_map = Map(self.game_view)
        self.game_window.show_view(mini_map)

    def ship(self, state=0):
        """
        Show which ship the player has selected and change the ship selected in game.

        :param state: whether to increase or decrease the ship type variable.
        """

        # Switch through the different ships.
        if state > 0 and self.ship_type < len(self.ships) - 1:
            self.ship_type += 1
        elif state < 0 and self.ship_type > 0:
            self.ship_type -= 1
        elif state > 0 and self.ship_type == len(self.ships) - 1:
            self.ship_type = 0
        elif state < 0 and self.ship_type == 0:
            self.ship_type = len(self.ships) - 1

        # Change the ship sprites and name.
        self.ship_sprite = arcade.Sprite(self.ship_data[self.ships[self.ship_type]]['texture'], scale=0.2,
                                         center_x=SCREEN_WIDTH / 2, center_y=SCREEN_HEIGHT - 600)
        self.ship_name = font.LetterList(self.ships[self.ship_type], SCREEN_WIDTH / 2, SCREEN_HEIGHT - 430,
                                         mid_x=True)

        # Set the player's ship in game.
        self.game_view.player_ship = self.ships[self.ship_type]

    def on_update(self, delta_time: float):
        # Update the stars so they animate.
        self.stars.on_update(self.velocity)

    def on_draw(self):
        arcade.start_render()

        # Draw the stars.
        self.stars.draw()

        # Draw the buttons and text specific to this state.
        self.button_lists[self.state].draw()

        self.text_lists[self.state].draw()

        # If in state 2, show the ship sprite and name.
        if self.state == 2:
            self.ship_sprite.draw()
            self.ship_name.draw()

        # Draw the title and cursor.
        self.title.draw()

        self.game_view.cursor.draw()

    def on_mouse_motion(self, x: float, y: float, dx: float, dy: float):
        # Set the cursors position.
        self.game_view.cursor.center_x = x
        self.game_view.cursor.center_y = y

    def on_mouse_press(self, x: float, y: float, button: int, modifiers: int):
        # Use the action dictionary and the data of the button to find what action to take.
        if button == arcade.MOUSE_BUTTON_LEFT:
            clicked = arcade.get_sprites_at_point((x, y), self.button_lists[self.state])
            if len(clicked):
                data = self.button_data[clicked[-1].change_x]
                # THIS IS NOT A REAL ERROR. IT IS A MISTAKE WITH PYCHARM #
                self.actions[data['action']](data['change'])

    def on_key_press(self, key: int, modifiers: int):
        """
        Runs different actions when the player presses key.

        Enter runs the game.

        Escape and X both close the game.
        """
        if key == arcade.key.ENTER:
            self.launch(0)
        elif key == arcade.key.ESCAPE or key == arcade.key.X:
            self.window.close()

    def on_show(self):
        # When the game is launched it plays an intro jingle by SketchyLogic.
        intro = arcade.Sound("game_data/Music/Intro Jingle.wav")
        intro.play(vector.VOLUME)


class MapSymbol(arcade.Sprite):
    """
    MapSymbols are used for the planets that orbit the sun. They hold data on missions and on what type of planet they
    are.
    """

    def __init__(self, x, y, base_distance, data):
        super().__init__(f"game_data/Sprites/Planets/symbol/{data['subset']}/{data['type']}.png", 0.15)
        self.data = data
        self.name = data['name']
        self.current_mission = None

        # If it's orbit has not been set randomly give it an orbit.
        if data['orbit_pos'] < 0:
            self.orbit_pos = random.randrange(0, 360)
        else:
            self.orbit_pos = data['orbit_pos']

        # The orbit of the symbol.
        self.base_orbit = base_distance
        self.orbit = data['orbit']
        self.speed = data['speed']

        # Use these variables to position the sprite.
        self.sun_x = x
        self.sun_y = y
        rad_angle = math.radians(self.orbit_pos)
        self.center_x = self.sun_x + (math.cos(rad_angle) * (self.base_orbit * self.orbit))
        self.center_y = self.sun_y + (math.sin(rad_angle) * (self.base_orbit * self.orbit))

    def on_update(self, delta_time: float = 1 / 60):
        # In update, simply add to the angle of the object and find the new position
        self.orbit_pos += (self.speed / self.orbit) * delta_time
        rad_angle = math.radians(self.orbit_pos)
        self.center_x = self.sun_x + (math.cos(rad_angle) * (self.base_orbit * self.orbit))
        self.center_y = self.sun_y + (math.sin(rad_angle) * (self.base_orbit * self.orbit))

    def fix(self, x, y):
        # When the viewport moves the sun x and y will be wrong so this fixes it.
        self.sun_x = x
        self.sun_y = y


class Map(arcade.View):
    """
    The Map holds the missions, the companies, the upgrades, and the Map with all of the planets.
    """

    def __init__(self, game_view, upgrades_todo=False):
        super().__init__()
        # Saves the game view and saves self into the game view.
        self.game_view = game_view
        self.game_view.map = self

        # The maximum orbit of planets
        self.max_orbit = 400

        # The planet symbols and the currently selected planet and the planet with an active mission currently.
        self.selected_planet = None
        self.current_mission = None
        self.current_planet = None
        self.planet_symbols = None

        # Company data, planet data, and solar system data.
        self.companies = None
        self.sun = None
        self.planet_data = None
        self.sol_data = None

        # Mission data.
        self.mission_generator = None
        self.mission_json = {}

        # Sprites for missions and launching.
        self.alert_symbols = None
        self.alert_texture = arcade.load_texture("game_data/Sprites/Planets/symbol/mission_alert.png")
        self.mission_sprite = arcade.Sprite("game_data/Sprites/Ui/current_mission.png", 0.15)
        self.selected_sprite = arcade.Sprite("game_data/Sprites/Ui/selected_planet.png", 0.15)
        self.launch_sprite = arcade.Sprite("game_data/Sprites/Player/Ui/launch.png", 0.2)

        # Company slides from ui.py.
        self.company_slides = None
        self.company_slide_dict = None
        self.current_slide = None
        self.company_rep = {}

        # Upgrade slide from ui.py.
        self.upgrade_tab = None
        self.upgrades = []
        self.current_upgrade = None
        self.upgrades_todo = upgrades_todo
        self.upgrade_generator = UpgradesGenerator(self.game_view)

        # Ship tab showing what upgrades the player has.
        self.ship_tab = None

        # Active upgrade slides and the reward handler.
        self.active_upgrade = None
        self.do_active = False
        self.reward_handler = RewardHandler(self, self.game_view, self.game_view.player)

        self.setup()

    def setup(self, upgrades=False):
        """
        resets variables, creates planet symbols, missions, and upgrades.

        :param upgrades: should upgrades be generated
        """
        self.current_mission = None
        self.selected_planet = None
        self.current_planet = None

        # Creates planet symbols
        self.planet_symbols = arcade.SpriteList()

        # Makes the sun symbols
        self.sun = arcade.Sprite("game_data/Sprites/Planets/symbol/sun.png",
                                 center_x=self.game_view.left_view + SCREEN_WIDTH / 2,
                                 center_y=self.game_view.bottom_view + SCREEN_HEIGHT / 2,
                                 scale=0.15)

        # Open the sol system json file and load the data.
        with open("game_data/Data/sol_system.json") as sol_data:
            sol_json = json.load(sol_data)
            self.sol_data = sol_json
            self.planet_data = sol_json['planets']
            self.companies = sol_json['companies']

            if self.mission_generator is None:
                self.mission_generator = mission.MissionGenerator()
            else:
                self.mission_generator.reload_dictionaries()
                self.mission_generator.generate()

            # Create all of the planet symbols.
            base_orbit = self.max_orbit / len(self.planet_data)
            x = self.sun.center_x
            y = self.sun.center_y
            for planet_d in self.planet_data.values():
                data = dict(planet_d['map_symbol'])
                data['name'] = planet_d['name']
                data['type'] = planet_d['type']
                data['subset'] = planet_d['subset']
                planet = MapSymbol(x, y, base_orbit, data)

                # Sets the planet for each mission and stores the mission in the planet symbols.
                with open("game_data/Data/mission_data.json") as mission_data:
                    self.mission_json = json.load(mission_data)
                    if data['name'] in self.mission_json['missions']:
                        planet.current_mission = self.mission_json['missions'][data['name']]
                        self.mission_json['missions'][data['name']]['planet_data'] = planet_d

                # Save the mission data with the planet data saved.
                with open("game_data/Data/mission_data.json", "w") as mission_dump:
                    json.dump(self.mission_json, mission_dump, indent=4)
                self.planet_symbols.append(planet)

        # Create the company slides.
        self.company_slides = arcade.SpriteList()
        self.company_slide_dict = {}
        self.company_rep = {}

        # Position of the company slides.
        s_x = self.game_view.left_view + SCREEN_WIDTH - 65
        s_y = self.game_view.bottom_view + SCREEN_HEIGHT - 210

        # Find all the mission for each company. Then create the company slides.
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

            # Find the reputation level of the company.
            rep = (companies['reputation'] - (companies['reputation'] % 50)) / 50
            self.company_rep[companies['name']] = rep

        # Generate upgrades if we should.
        if upgrades:
            self.upgrades = self.upgrade_generator.setup_upgrades()
        else:
            self.upgrades = (None, None, None)

        # Create the upgrade tab.
        self.upgrade_tab = ui.UpgradeTab(self, self.upgrades)

        # Position the launch sprite.
        self.launch_sprite.center_x = self.game_view.left_view + (SCREEN_WIDTH / 2)
        self.launch_sprite.center_y = self.game_view.bottom_view + 60

        # Calculate the rewards.
        self.reward_handler.do_all_rewards()

        # Create the ship tab.
        if self.game_view.player is not None:
            self.ship_tab = ui.ShipTab(self.game_view.player.passive_upgrades, self.game_view, self)

    def on_show(self):
        """
        Fix the Planets, the slides, and the upgrade tab.
        """
        self.sun.center_x, self.sun.center_y = self.game_view.left_view + SCREEN_WIDTH / 2, \
                                               self.game_view.bottom_view + SCREEN_HEIGHT / 2
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
        # Update the
        self.planet_symbols.on_update(delta_time)
        cxy = (self.game_view.left_view + self.game_view.cursor_screen_pos[0],
               self.game_view.bottom_view + self.game_view.cursor_screen_pos[1])
        self.game_view.cursor.center_x = cxy[0]
        self.game_view.cursor.center_y = cxy[1]

        # If there isn't an active upgrade currently working.
        if not self.do_active:
            check = arcade.get_sprites_at_point(cxy, self.company_slides)
            # Reverse the order of the company slides so the one that draws on top is selected first.
            slides = self.company_slides[::-1]

            # For every slide check to see if it is being selected. If a slide does get selected break from the cycle.
            for slide in slides:
                if slide.collides_with_point(cxy):
                    if self.current_slide is None or self.current_slide == slide:
                        slide.mouse_over(True)
                        self.current_slide = slide
                        if slide.mission_data[0] is not None:
                            for planets in self.planet_symbols:
                                if planets.name == slide.planet_data[slide.state]['name']:
                                    self.selected_planet = planets
                                    break
                else:
                    slide.mouse_over(False)
                    if self.selected_planet is not None and slide.mission_data[0] is not None and not slide.selected:
                        if slide.planet_data[slide.state]['name'] == self.selected_planet.name:
                            self.selected_planet = None

            # Check if the upgrade tab is being selected.
            self.upgrade_tab.check(self.upgrade_tab.collides_with_point(cxy))

            # Update the animation of the tabs.
            self.company_slides.update_animation(delta_time)
            self.upgrade_tab.update_animation(delta_time)

            # move the ship tab.
            if self.ship_tab is not None:
                self.ship_tab.mouse_over(self.ship_tab.collides_with_point(cxy))
        else:
            # Check with an upgrade tab.
            self.active_upgrade.check(cxy)

        # Do the reputation check to see if the player wins.
        reputation = 0
        for comp in self.companies.values():
            reputation += comp['reputation']
            if reputation >= 500:
                generator = sol_system_generator.Generator(self.game_view)
                title = TitleScreen(self.window)
                self.window.show_view(title)
                break

    def draw_text(self):
        """
        This is the text drawing half of the draw method.
        """
        arcade.draw_text("X: to close game",
                         self.game_view.left_view + 10,
                         self.game_view.bottom_view + SCREEN_HEIGHT - 25,
                         arcade.color.WHITE)

        if self.game_view.current_mission is not None:
            # If there is a current mission
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
                                 self.game_view.bottom_view + SCREEN_HEIGHT - 25,
                                 arcade.color.WHITE)
        else:
            # If there is no current mission
            if self.selected_planet is not None:
                arcade.draw_text(f"Enter: Launch for {self.selected_planet.name}",
                                 self.game_view.left_view + 10,
                                 self.game_view.bottom_view + SCREEN_HEIGHT - 50,
                                 arcade.color.WHITE)

    def draw(self):
        # If the player has opened this map during a mission show the game in the background.
        if self.current_mission is not None:
            self.game_view.on_draw()
            arcade.draw_rectangle_filled(self.game_view.left_view + SCREEN_WIDTH / 2,
                                         self.game_view.bottom_view + SCREEN_HEIGHT / 2,
                                         SCREEN_WIDTH, SCREEN_HEIGHT, (50, 50, 50, 120))

        # Draw all of the planet symbols
        self.planet_symbols.draw()

        # Create and draw a red alert over every planet symbol with a mission.
        self.alert_symbols = arcade.SpriteList()
        for planets in self.planet_symbols:
            if planets.current_mission is not None \
                    and self.selected_planet != planets and self.current_planet != planets:
                alert = arcade.Sprite(center_x=planets.center_x, center_y=planets.center_y + 28, scale=0.15)
                alert.texture = self.alert_texture
                self.alert_symbols.append(alert)
        self.alert_symbols.draw()

        # Show the launch sprite if the player is selecting a mission, and the planet select symbol.
        if self.selected_planet is not None and self.selected_planet != self.current_planet:
            self.launch_sprite.draw()
            self.selected_sprite.center_x = self.selected_planet.center_x
            self.selected_sprite.center_y = self.selected_planet.center_y
            self.selected_sprite.draw()
        # Draw the current planet symbol.
        if self.current_planet is not None:
            self.mission_sprite.center_x = self.current_planet.center_x
            self.mission_sprite.center_y = self.current_planet.center_y
            self.mission_sprite.draw()

        # Draw all of the company slides.
        for slide in self.company_slides:
            slide.draw()

        # Draw the uprade tab and ship tab.
        self.upgrade_tab.draw()
        if self.ship_tab is not None:
            self.ship_tab.update_animation()
            self.ship_tab.draw()

        # Draw the sun
        self.sun.draw()

        # If there is an active upgrade currently show the active upgrade screen and dim the background.
        if self.do_active and self.active_upgrade is not None:
            arcade.draw_rectangle_filled(self.game_view.left_view + SCREEN_WIDTH / 2,
                                         self.game_view.bottom_view + SCREEN_HEIGHT / 2,
                                         SCREEN_WIDTH + 100, SCREEN_HEIGHT + 100, (90, 90, 90, 90))
            if not self.active_upgrade.start_t:
                self.active_upgrade.start_t = time.time() * 1000
            self.active_upgrade.update_animation()
            self.active_upgrade.draw()

    def on_draw(self):
        """
        Run both the draw and draw text methods and then draw the cursor.
        """
        arcade.start_render()
        self.draw()
        self.draw_text()

        self.game_view.cursor.draw()

    def on_key_press(self, key: int, modifiers: int):
        """
        The key press method.
        """

        # If there is an active upgrade do a check.
        if self.do_active:
            self.active_upgrade.trigger()

        if key == arcade.key.ENTER and self.selected_planet is not None and self.selected_planet != self.current_planet:
            # Launch for a selected mission
            self.current_mission = self.selected_planet.current_mission
            self.current_planet = self.selected_planet
            self.game_view.current_mission = self.current_mission
            self.close_up()
        elif key == arcade.key.X:
            # Close the game.
            if self.game_view.player is not None:
                self.game_view.player.clear_upgrades()
            self.reset_map_pos()
            self.window.close()
        elif key == arcade.key.R:
            # Regenerate the solar system.
            generator = sol_system_generator.Generator(self.game_view)
            self.game_view.current_mission = None
            self.setup()
        elif key == arcade.key.M:
            # Recreate the missions.
            self.current_mission = None
            self.game_view.current_mission = None
            self.save_map_pos()
            self.setup()
            with open("game_data/Data/mission_data.json") as mission_data:
                self.mission_json = json.load(mission_data)
                for planet in self.planet_symbols:
                    if planet.name in self.mission_json['missions']:
                        self.mission_json['missions'][planet.name]['planet_data'] = \
                            self.planet_data[planet.name]
                        planet.current_mission = self.mission_json['missions'][planet.name]

                    else:
                        planet.current_mission = None

        elif self.game_view.current_mission is not None:
            # Close the map menu and open the game menu.
            self.save_map_pos()
            self.window.show_view(self.game_view)

    def on_mouse_press(self, x: float, y: float, button: int, modifiers: int):
        # If there is a active upgrade currently do the trigger.
        if self.do_active:
            self.active_upgrade.trigger()

        # If the player presses left check to see if they selected anything.
        if button == arcade.MOUSE_BUTTON_LEFT and not self.do_active:
            cxy = (self.game_view.left_view + self.game_view.cursor_screen_pos[0],
                   self.game_view.bottom_view + self.game_view.cursor_screen_pos[1])

            # Check the upgrade tab.
            self.upgrade_tab.on_mouse_press(cxy[0], cxy[1])

            # Check the launch sprite.
            if self.launch_sprite.collides_with_point((cxy[0], cxy[1])) and \
                    self.selected_planet is not None and self.selected_planet != self.current_planet:
                self.current_planet = self.selected_planet
                self.current_mission = self.current_planet.current_mission
                self.game_view.current_mission = self.current_mission
                self.close_up()
            else:
                # Check if the any planets where selected.
                cursor_over = arcade.get_sprites_at_point(cxy, self.planet_symbols)
                if len(cursor_over) > 0:
                    if self.selected_planet == cursor_over[0] and self.selected_planet != self.current_planet:
                        # If they double click a planet launch.
                        self.current_planet = cursor_over[0]
                        self.current_mission = self.current_planet.current_mission
                        self.game_view.current_mission = self.current_mission
                        self.close_up()
                    elif self.current_planet == cursor_over[0]:
                        # If they have the map open over the game view,
                        # and they click the current planet close the menu.
                        self.save_map_pos()
                        self.window.show_view(self.game_view)

                    # Reset and re-find the selected planet.
                    if self.selected_planet is not None:
                        # If there is a selected planet set the company slide selected to False.
                        self.current_slide.selected = False
                    self.selected_planet = None
                    if cursor_over[0].current_mission is not None:
                        self.selected_planet = cursor_over[0]
                        self.current_slide = self.company_slide_dict[self.selected_planet.current_mission['company']]
                        self.current_slide.selected = True
                else:
                    # If no planet was selected reset all variables.
                    self.selected_planet = None
                    if self.current_slide is not None:
                        self.current_slide.selected = False
                        self.current_slide = None

    def save_map_pos(self):
        """
        Save the position of the map symbols.
        """
        for planets in self.planet_symbols:
            self.sol_data['planets'][planets.name]['map_symbol']['orbit_pos'] = planets.orbit_pos
        with open("game_data/Data/sol_system.json", "w") as file:
            json.dump(self.sol_data, file, indent=4)

    def reset_map_pos(self):
        """
        reset the position of the map symbols.
        """
        for planets in self.planet_symbols:
            self.sol_data['planets'][planets.name]['map_symbol']['orbit_pos'] = -1
        with open("game_data/Data/sol_system.json", "w") as file:
            json.dump(self.sol_data, file, indent=4)

    def close_up(self):
        """
        Close the Map.
        """
        self.save_map_pos()
        self.game_view.setup()
        self.window.show_view(self.game_view)

    def rewards(self, company_name):
        """
        Calculate the rewards the player should be getting.

        :param company_name: The company that is dealing the rewards.
        """
        company = self.companies[company_name]
        if self.company_rep[company_name] % 2:
            self.active_upgrade = ui.ActiveUpgrade(self.companies[company_name], self)
            self.do_active = True
            self.active_upgrade.slide = 1
        else:
            self.reward_handler.reward(company)

    def on_mouse_motion(self, x: float, y: float, dx: float, dy: float):
        # Save the mouse pos.
        self.game_view.cursor_screen_pos = [x, y]


class RewardHandler:
    """
    The reward handler provides all of the reward calculations for the player. It only handles the passive bonuses.
    """

    def __init__(self, map_menu, game_window, player):
        self.map = map_menu
        self.game = game_window
        self.player = player

        # The current company and it's reward level.
        self.current_company = None
        self.rep_level = 0

        # All of the reward functions.
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
        """
        Run through each company and reward the player accordingly.
        """

        # Reset all of the variables.
        self.map.upgrade_generator.num_upgrades = 3

        self.map.mission_generator.num_missions = 3

        self.map.upgrade_generator.bane_modifier = 1
        self.map.upgrade_generator.all_modifier = 1
        self.map.upgrade_generator.cost_modifier = 1

        self.map.upgrade_tab.sell_bonus = 0.85

        self.game.mission.reputation_mod = 1

        self.game.player_max_speed = 95309
        self.game.player_gravity_dampening = 1

        # Do the reward for each company.
        for company in self.map.companies.values():
            self.reward(company)

    def reward(self, company):
        # Find the current company.
        self.current_company = company

        # Find the companies reputation level.
        rep = math.floor(company['reputation'] / 50)
        if company['reputation'] == 250:
            rep = 4

        if rep > 3:
            self.rep_level = 0
        elif rep > 1:
            self.rep_level = 1

        # If the company has a reputation level do the rewards.
        if rep:
            self.calc_reward()
            self.apply_reward()

        # Reset variables.
        self.current_company = None
        self.rep_level = 0

    def calc_reward(self):
        # Find the current rewards.
        self.current_reward = self.rewards[self.current_company['bonus']]

    def apply_reward(self):
        # Run the current award.
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
    """
    The upgrade generator creates all of the upgrades for the player. these are then stored in the Map.
    """

    def __init__(self, game_view):
        # Save all of the upgrades the player currently has.
        with open("game_data/Data/upgrade_data.json") as upgrade_file:
            upgrade_json = json.load(upgrade_file)
            self.static_abilities = upgrade_json['static_abilities']
            self.base_static_upgrade = upgrade_json['base_static']

        # These ranges are for the possible ranges of bonuses for MK I, II, and III upgrades.
        self.bonus_range = (
            (0.1, 0.15), (0.16, 0.21), (0.22, 0.27)
        )
        self.bane_range = (
            (0.03, 0.08), (0.09, 0.14), (0.15, 0.2)
        )
        self.cost_range = (
            (45, 65), (70, 90), (95, 115)
        )

        # The upgrade lists.
        self.upgrades = []
        self.shown_upgrades = []
        self.saved_upgrade = {}

        self.game_view = game_view

        # The number of upgrades and modifiers.
        self.num_upgrades = 3
        self.bane_modifier = 1
        self.cost_modifier = 1
        self.all_modifier = 1

        # Upgrade types with bonueses.
        self.bonus_upgrades = {}

    def setup_upgrades(self):
        # Create all the bonuses to different upgrades.
        self.bonus_upgrades = {}
        for companies in self.game_view.map.companies.values():
            self.bonus_upgrades[companies['upgrade']] = companies

        # Create all of the upgrades and save a select few.
        self.upgrades = []
        self.shown_upgrades = ()
        upgrade_variables = list(self.game_view.player.upgrade_mod)
        # First create a new upgrade for each passive upgrade the player already has.
        for upgrade in self.game_view.player.passive_upgrades:
            # If the passive upgrade is not the maximum level.
            if upgrade['level'] < 3:
                # Create a copy of the old upgrade but increase it's level by one and save the previous upgrade.
                new_upgrade = dict(upgrade)
                new_upgrade['level'] += 1
                new_upgrade['prev_upgrade'] = upgrade

                # Find a random value between 0 and 1
                random_points = random.random()

                # Find the right ranges for the current upgrade level
                bonus_points = self.bonus_range[upgrade['level']]
                bane_points = self.bane_range[upgrade['level']]
                cost_points = self.cost_range[upgrade['level']]

                # Calculate the bonus and bane and cost from the value and the ranges.
                bonus = (bonus_points[0] + (bonus_points[1] - bonus_points[0]) * random_points)
                bane = bane_points[0] + (bane_points[1] - bane_points[0]) * random_points
                new_upgrade['bonus'] = round(bonus * self.all_modifier, 2)
                new_upgrade['bane'] = round(bane * self.all_modifier * self.bane_modifier, 2)

                # Find the cost bonus if the bonus should be cheapened due to companies.
                if new_upgrade['bonus_name'] in self.bonus_upgrades:
                    bonus = 1 - (self.bonus_upgrades[new_upgrade['bonus_name']]['reputation'] / 250) * 0.25
                else:
                    bonus = 1

                cost = (cost_points[0] + (cost_points[1] - cost_points[0]) * random_points) * bonus
                new_upgrade['cost'] = round(cost * self.cost_modifier)

                # Find the new name by taking the old name and removing the MK ... from the end.
                broken = new_upgrade['name'].split(" ")
                first_half = broken[0]
                second_half = broken[1]
                # Create the new name from the first and second words.
                if new_upgrade['level'] == 2:
                    new_upgrade['name'] = first_half + " " + second_half + " MK_II"
                else:
                    new_upgrade['name'] = first_half + " " + second_half + " MK_III"

                # Remove the positive from the list of possible upgrade.
                upgrade_variables.remove(new_upgrade['bonus_name'])
                self.upgrades.append(new_upgrade)

        # Then for every positive upgrade left create an upgrade.
        # The method is the same as with the improved upgrades.
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

        # Randomly select a number of the upgrades equal to num_upgrades.
        self.shown_upgrades = tuple(random.sample(self.upgrades, self.num_upgrades))
        return self.shown_upgrades


class MissionEndCard(arcade.View):
    """
    The mission end card shows all of the variables from the mission to the player before they go back to the Map.
    """

    def __init__(self, game_view):
        super().__init__()
        self.mission_stats = None

        # The strings for all the text to be created.
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

        # The stars in the background.
        self.star_field = None
        self.false_screen_velocity = [0.0, 0.0]
        self.false_screen_acceleration = [0.0, 0.0]
        self.direction = 0

        self.game_view = game_view

    def setup(self, mission_stats):
        """
        Sets up all of the text to be shown on screen.

        :param mission_stats: The data from the mission
        """
        self.mission_stats = mission_stats
        self.text_strings = []

        # The position of all the text.
        s_x = SCREEN_WIDTH / 2 - 250
        s_y = SCREEN_HEIGHT / 2 + 140

        # Create all of the text.
        self.mission_strings = dict(self.base_strings)
        for string in self.mission_strings:
            string = self.mission_strings[string] + str(self.mission_stats[string])
            text = string.lower()
            self.text_strings.append(font.LetterList(text, s_x, s_y))
            s_y -= 18

    def on_show(self):
        """
        When the end card is shown, reset the left and bottom view of the game view and create the star field
        and a fake velocity.
        """

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
        # Update the velocity of the stars and update the stars.
        if self.false_screen_velocity[0] == 0 or self.false_screen_velocity[1] == 0:
            self.false_screen_velocity[0] = 0.5
            self.false_screen_velocity[0] = 0.5
        if math.sqrt(self.false_screen_velocity[0] ** 2 + self.false_screen_velocity[1] ** 2) <= 35:
            self.false_screen_velocity[0] += self.false_screen_acceleration[0] * delta_time
            self.false_screen_velocity[1] += self.false_screen_acceleration[1] * delta_time
        self.star_field.on_update(self.false_screen_velocity)

    def on_draw(self):
        # draw the stars, dim the background, and draw all of the text.
        arcade.start_render()
        self.star_field.draw()
        arcade.draw_rectangle_filled(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2,
                                     SCREEN_WIDTH + 150, SCREEN_HEIGHT + 150,
                                     (90, 90, 90, 90))
        for text in self.text_strings:
            text.draw()

    def on_key_press(self, symbol: int, modifiers: int):
        # On any key press open the map.
        self.game_view.open_upgrade_map()

    def on_mouse_press(self, x: float, y: float, button: int, modifiers: int):
        # On any mouse press open the map.
        self.game_view.open_upgrade_map()
