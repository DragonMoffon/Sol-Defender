import time
import json
import math
import random

import arcade

import player
import stars
import space
import mission

SCREEN_WIDTH, SCREEN_HEIGHT = arcade.window_commands.get_display_size()
TITLE = "Sol Defender - Sprint 4"


class MapSymbol(arcade.Sprite):
    def __init__(self, x, y, base_distance, data):
        super().__init__(f"Sprites/Planets/Planet Symbols/{data['type']}.png", 0.15)
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

    def draw(self):
        super().draw()

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
        self.planet_symbols = arcade.SpriteList()
        self.sun = arcade.Sprite("Sprites/Planets/Planet Symbols/sun.png",
                                 center_x=self.game_view.left_view+SCREEN_WIDTH/2,
                                 center_y=self.game_view.bottom_view+SCREEN_HEIGHT/2,
                                 scale=0.15)
        with open("Data/sol_system.json") as sol_data:
            sol_json = json.load(sol_data)
            self.planet_data = sol_json
            base_orbit = self.max_orbit / len(sol_json['planets'])
            for planet in sol_json['planets']:
                x = self.sun.center_x
                y = self.sun.center_y
                planet = MapSymbol(x, y, base_orbit, planet['map_symbol'])
                with open("Data/mission_data.json") as mission_data:
                    mission_json = json.load(mission_data)
                    for missions in mission_json['start_missions']:
                        if planet.name == missions['planet']:
                            planet.current_mission = missions
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

    def on_draw(self):
        arcade.start_render()
        for planets in self.planet_symbols:
            planets.draw()
        self.sun.draw()
        if self.game_view.current_mission >= 0:
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
            self.selected_planet.draw_mission()
            launch = arcade.Sprite("Sprites/Player/Ui/launch.png", 0.2)
            launch.center_x = self.game_view.left_view + (SCREEN_WIDTH/2)
            launch.center_y = self.game_view.bottom_view + 60
            launch.draw()

        self.game_view.cursor.draw()

    def on_key_press(self, key: int, modifiers: int):
        if key == arcade.key.ENTER and self.selected_planet is not None and self.selected_planet != self.current_planet:
            self.current_mission = self.selected_planet.current_mission
            self.current_planet = self.selected_planet
            self.game_view.current_mission = self.current_mission['key']
            self.close_up()
        elif key == arcade.key.ESCAPE:
            self.reset_map_pos()
            self.window.close()
        elif key == arcade.key.KEY_1:
            self.selected_planet = self.planet_symbols[0]
        elif key == arcade.key.KEY_2:
            self.selected_planet = self.planet_symbols[0]
        elif key == arcade.key.KEY_3:
            self.selected_planet = self.planet_symbols[0]
        elif self.game_view.current_mission >= 0:
            self.save_map_pos()
            self.window.show_view(self.game_view)

    def on_mouse_press(self, x: float, y: float, button: int, modifiers: int):
        if button == arcade.MOUSE_BUTTON_LEFT:
            cxy = (self.game_view.left_view + self.game_view.cursor_screen_pos[0],
                   self.game_view.bottom_view + self.game_view.cursor_screen_pos[1])
            cursor_over = arcade.get_sprites_at_point(cxy, self.planet_symbols)
            if len(cursor_over) > 0:
                if self.selected_planet == cursor_over[0]:
                    self.game_view.current_mission = cursor_over[0].current_mission['key']
                    self.current_mission = cursor_over[0].current_mission
                    self.close_up()
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
        self.game_view.reset()
        self.window.show_view(self.game_view)

    def launch(self):
        pass

    def on_mouse_motion(self, x: float, y: float, dx: float, dy: float):
        self.game_view.cursor_screen_pos = [x, y]


class GameWindow(arcade.View):

    def __init__(self):

        super().__init__()
        arcade.set_background_color(arcade.color.BLACK)
        # audio
        # file_name = "Music/Planetary.wav"
        # self.playback_audio = arcade.Sound(file_name, streaming=True)
        # self.playback_audio.play(volume=0.1)

        self.cursor = arcade.Sprite("Sprites/Player/Ui/cross_hair_light.png", 0.1, center_x=0, center_y=0)
        self.cursor_screen_pos = [0.0, 0.0]

        # gravity handler
        self.gravity_handler = None

        # Menu Screens
        self.map = None

        # missions
        self.mission = mission.Mission(self)
        self.current_mission = -1

        # check if on_update should run.
        self.process = True
        self.changed = False
        self.pause_delay = 0

        self.menus = False
        self.menu = None

        # x and y Coordinates for Reset Position
        self.center_x = SCREEN_WIDTH // 2
        self.center_y = SCREEN_HEIGHT // 2

        # The Player Sprite and Setup
        self.player = None

        # Viewport Variables
        self.bottom_view = 0
        self.left_view = 0

        # Enemy Handler Variables
        self.enemy_handler = None

        # Text Sprite
        self.text_sprite = arcade.Sprite()
        self.show_text = False
        self.spawn_time = 0
        self.life_time = 0.6
        self.text_sprite.center_x, self.text_sprite.center_y = SCREEN_WIDTH // 2, SCREEN_WIDTH // 2

        # stars
        self.star_field = stars.StarField()
        self.star_field.holder = self

    def open_map(self):
        self.window.show_view(self.map)

    def open_clean_map(self):
        self.map = Map(self)
        self.open_map()

    def on_update(self, delta_time: float = 1 / 60):

        """
        This method calls 60 times per second roughly and is what is used to update things such as positions,
        view ports, and scores
        """
        # FPS for debugging
        # print("FPS:",1/delta_time)
        if self.menus:
            pass
        elif self.process:
            # print("position:", self.playback_audio.get_stream_position(), "Length:", self.playback_audio.get_length())

            # if self.playback_audio.get_stream_position() == 0:
            #     self.playback_audio.play(0.1)

            # Gravity Update
            self.gravity_handler.calculate_each_gravity()

            # Players Update
            self.player.on_update(delta_time)

            # Move Viewport
            self.view_port(delta_time)
            self.cursor.center_x = self.left_view + self.cursor_screen_pos[0]
            self.cursor.center_y = self.bottom_view + self.cursor_screen_pos[1]

            self.mission.on_update(delta_time)

            # Enemy update
            if self.changed:
                self.mission.check_setup()

            if self.player.dead:
                self.text_sprite.center_x, self.text_sprite.center_y = [self.left_view + SCREEN_WIDTH // 2,
                                                                        self.bottom_view + SCREEN_WIDTH // 2]
                self.text_sprite.texture = arcade.load_texture("Sprites/dead.png")
                self.show_text = True
                self.spawn_time = time.time()
                self.process = False

        if self.spawn_time + self.life_time < time.time() and self.show_text:
            self.show_text = False
            self.reset()

    def view_port(self, delta_time):
        """
        Function for cleaning up on_update.
        Moves the Viewport to keep the player in the center of the screen.
        """

        self.changed = False
        prev_value = [self.left_view, self.bottom_view]

        self.left_view += self.player.velocity[0] * delta_time
        self.bottom_view += self.player.velocity[1] * delta_time

        if prev_value[0] != self.left_view or prev_value[1] != self.bottom_view:
            self.changed = True

        if self.changed:
            arcade.set_viewport(self.left_view,
                                SCREEN_WIDTH + self.left_view,
                                self.bottom_view,
                                SCREEN_HEIGHT + self.bottom_view)

            if self.star_field.holder is not None:
                change = (self.left_view - prev_value[0], self.bottom_view - prev_value[1])
                self.star_field.on_update(change)

    def on_draw(self):
        """
        Runs all of the draw functions for all Sprites and SpriteLists
        """
        arcade.start_render()

        if self.star_field.holder is not None:
            self.star_field.draw()

        if self.mission is not None:
            self.mission.draw()

        self.player.draw()

        if self.show_text:
            self.text_sprite.draw()

        self.cursor.draw()

    def reset(self, missions=True, star_field=3):
        """
        Resets the game world.
        Needs to be neatened with setups.
        """
        self.process = True
        self.changed = False
        self.gravity_handler = space.GravityHandler()

        # view
        self.left_view = 0
        self.bottom_view = 0
        arcade.set_viewport(self.left_view,
                            SCREEN_WIDTH + self.left_view,
                            self.bottom_view,
                            SCREEN_HEIGHT + self.bottom_view)

        # player
        self.player = player.Player(self)
        self.player.center_x = self.center_x
        self.player.center_y = self.center_y

        # mission
        if missions:
            with open("Data/mission_data.json") as mission_data:
                curr_mission = json.load(mission_data)['start_missions'][self.current_mission]
                self.mission.mission_setup(curr_mission)
                self.player.start = 1
        else:
            self.mission.mission_setup()

        # stars
        self.star_field = stars.StarField(star_field)
        if star_field:
            self.star_field.setup(self)

    def on_key_press(self, key, modifiers):
        """
        Method runs each time the user presses a key.
        Each object that requires a key press has its own key down method for neatness
        """
        if self.process:
            self.player.key_down(key)

        if key == arcade.key.R:
            self.reset()
        elif key == arcade.key.P:
            self.reset(star_field=0)
        elif key == arcade.key.O:
            self.reset(missions=False, star_field=0)
        elif key == arcade.key.I:
            self.reset(missions=False, star_field=1)
        elif key == arcade.key.L:
            self.reset(star_field=1)

        elif key == arcade.key.LSHIFT and self.process:
            self.process = False
            self.pause_delay = time.time()
        elif key == arcade.key.LSHIFT and not self.process and self.player.start:
            self.process = True
            self.pause_delay = time.time() - self.pause_delay
            for shots in self.player.bullets:
                shots.pause_delay += self.pause_delay
            self.mission.enemy_handler.pause_delay(self.pause_delay)
            self.pause_delay = 0

        elif key == arcade.key.ESCAPE:
            self.open_map()

    def on_key_release(self, key, modifier):
        """
        Similar to on_key_press this method calls when a user releases a key.
        All objects that need a key release have their own method for neatness
        """
        if self.process:
            self.player.key_up(key)

    def on_mouse_motion(self, x: float, y: float, dx: float, dy: float):
        self.cursor_screen_pos = [x, y]
        if self.process:
            self.player.on_mouse_movement(x, y)

    def on_mouse_press(self, x: float, y: float, button: int, modifiers: int):
        if self.process:
            self.player.on_mouse_press(button)

    def on_mouse_release(self, x: float, y: float, button: int,
                         modifiers: int):
        if self.process:
            self.player.on_mouse_release(button)


def main():
    game_window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, TITLE)
    game_window.center_window()
    game_window.set_mouse_visible(False)
    game = GameWindow()
    mini_map = Map(game)
    game_window.show_view(mini_map)
    arcade.run()


if __name__ == "__main__":
    main()
