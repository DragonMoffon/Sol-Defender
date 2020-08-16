import time
import json


import arcade

import player
import stars
import space
import mission
import menu
import sol_system_generator

SCREEN_WIDTH, SCREEN_HEIGHT = arcade.window_commands.get_display_size()
TITLE = "Sol Defender - Sprint 4"


class GameWindow(arcade.View):

    def __init__(self):

        super().__init__()
        print(SCREEN_WIDTH)
        arcade.set_background_color(arcade.color.BLACK)
        # audio
        # file_name = "Music/Planetary.wav"
        # self.playback_audio = arcade.Sound(file_name, streaming=True)
        # self.playback_audio.play(volume=0.1)1

        self.cursor = arcade.Sprite("Sprites/Player/Ui/cross_hair_light.png", 0.1, center_x=0, center_y=0)
        self.cursor_screen_pos = [0.0, 0.0]

        # gravity handler
        self.gravity_handler = None

        # missions
        self.mission = mission.Mission(self)
        self.current_mission = None

        # check if on_update should run.
        self.process = True
        self.changed = False
        self.pause_delay = 0

        # x and y Coordinates for Reset Position
        self.center_x = SCREEN_WIDTH // 2
        self.center_y = SCREEN_HEIGHT // 2

        # The Player Sprite and Setup
        self.player = None

        # Viewport Variables
        self.bottom_view = 0
        self.left_view = 0

        # Menu Screens
        self.map = None
        self.upgrades = menu.UpgradeMenu(self)

        # Enemy Handler Variables
        self.enemy_handler = None

        # Text Sprite
        self.text_sprite = arcade.Sprite()
        self.show_text = False
        self.text_sprite.texture = arcade.load_texture('Sprites/dead.png')
        self.spawn_time = 0
        self.life_time = 0.6
        self.text_sprite.center_x, self.text_sprite.center_y = SCREEN_WIDTH // 2, SCREEN_WIDTH // 2

        # stars
        self.star_field = stars.StarField(self)

    def open_map(self):
        self.window.show_view(self.map)

    def open_upgrade(self):
        self.window.show_view(self.upgrades)

    def open_clean_map(self):
        self.current_mission = None
        self.map = menu.Map(self)
        self.open_map()

    def on_update(self, delta_time: float = 1 / 60):

        """
        This method calls 60 times per second roughly and is what is used to update things such as positions,
        view ports, and scores
        """
        # FPS for debugging
        # print("FPS:",1/delta_time)
        if self.process:
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
            self.player.after_update()

            self.mission.on_update(delta_time)

            # Enemy update
            if self.changed:
                self.mission.check_setup()

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

            if self.star_field.game_view is not None:
                change = (self.left_view - prev_value[0], self.bottom_view - prev_value[1])
                self.star_field.on_update(change)

    def on_draw(self):
        """
        Runs all of the draw functions for all Sprites and SpriteLists
        """
        arcade.start_render()

        if self.star_field.game_view is not None:
            self.star_field.draw()

        if self.mission is not None:
            self.mission.draw()

        self.player.draw()

        self.dead_text()

        self.cursor.draw()

    def dead_text(self):
        if self.process:
            if self.player.dead:
                self.text_sprite.center_x, self.text_sprite.center_y = [self.left_view + SCREEN_WIDTH // 2,
                                                                        self.bottom_view + SCREEN_WIDTH // 2]
                self.show_text = True
                self.spawn_time = time.time()
                self.process = False

        if self.spawn_time + self.life_time < time.time() and self.show_text:
            self.show_text = False
            self.reset()
            self.open_clean_map()

        if self.show_text:
            self.text_sprite.draw()

    def reset(self, missions=True, star_field=3):
        """
        Resets the game world.
        Needs to be neatened with setups.
        """
        self.process = True
        self.changed = False
        if self.gravity_handler is not None:
            del self.gravity_handler

        if self.player is not None:
            self.player.kill()
        if self.enemy_handler is not None:
            self.enemy_handler.slaughter()
            del self.enemy_handler

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
        self.player.read_upgrades()
        self.player.center_x = self.center_x
        self.player.center_y = self.center_y

        # mission
        if missions:
            with open("Data/mission_data.json") as mission_data:
                self.mission.mission_setup(self.current_mission)
                self.player.start = 1
        else:
            self.mission.mission_setup()

        # stars
        self.star_field = stars.StarField(self)

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

        elif key == arcade.key.F:
            self.mission.enemy_handler.slaughter()

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
        elif key == arcade.key.Z:
            self.open_upgrade()

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

    def on_show(self):
        self.reset()


def main():
    sol_system_generator.Generator()
    game_window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, TITLE, fullscreen=False)
    game_window.center_window()
    game_window.set_mouse_visible(False)
    game = GameWindow()
    mini_map = menu.Map(game)
    game_window.show_view(mini_map)
    arcade.run()


if __name__ == "__main__":
    main()
