import time

import arcade

import enemy_handler
import player
import stars
import space

SCREEN_WIDTH, SCREEN_HEIGHT = arcade.window_commands.get_display_size()
TITLE = "Sol Defender - Sprint 3"


class GameWindow(arcade.Window):

    def __init__(self, screen_width=1000, screen_height=750, title="Title"):

        super().__init__(screen_width, screen_height, title, fullscreen=False)
        arcade.set_background_color(arcade.color.BLACK)
        # audio
        # file_name = "Music/Planetary.wav"
        # self.playback_audio = arcade.Sound(file_name, streaming=True)
        # self.playback_audio.play(volume=0.1)

        # Temporary Planet and Moon
        self.planet = None
        self.moon = None

        # gravity handler
        self.gravity_handler = None

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

        # setup
        self.center_window()

        # stars
        self.star_field = stars.StarField()
        self.star_field.holder = self

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

            # Move Planet and Moon
            if self.moon is not None:
                self.moon.on_update(delta_time)

            # Gravity Update
            self.gravity_handler.calculate_each_gravity()

            # Players Update
            self.player.on_update(delta_time)

            # Move Viewport
            self.view_port(delta_time)

            # Enemy update
            if self.changed:
                if self.player.start == 1:
                    self.enemy_handler.setup_wave()
                    self.player.start = 2

                if self.enemy_handler.enemy_sprites is not None:
                    self.enemy_handler.on_update(delta_time)

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

        if self.planet is not None:
            self.planet.draw()
            self.moon.draw()

        if self.enemy_handler.enemy_sprites is not None:
            self.enemy_handler.draw()

        self.player.draw()

        if self.show_text:
            self.text_sprite.draw()

    def reset(self, enemies=True, star_field=3):
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

        # enemies
        self.enemy_handler = enemy_handler.EnemyHandler(self)
        if enemies:
            self.enemy_handler.player = self.player
            self.enemy_handler.assign_player_health()
            self.player.start = 1

            # player pointer
            self.player.enemy_handler = self.enemy_handler
        else:
            pass

        self.planet = space.Planet(self)
        self.moon = space.Satellite(self.planet)
        self.moon.setup(self.gravity_handler)

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

        elif key == arcade.key.LSHIFT and self.process:
            self.process = False
            self.pause_delay = time.time()
        elif key == arcade.key.LSHIFT and not self.process and self.player.start:
            self.process = True
            self.pause_delay = time.time() - self.pause_delay
            for shots in self.player.bullets:
                shots.pause_delay += self.pause_delay
            self.enemy_handler.pause_delay(self.pause_delay)
            self.pause_delay = 0

        elif key == arcade.key.ESCAPE:
            self.close()

        elif key == arcade.key.P:
            self.reset(enemies=False, star_field=1)
        elif key == arcade.key.O:
            self.reset(star_field=0)
        elif key == arcade.key.I:
            self.reset(False, 3)
        elif key == arcade.key.L:
            self.reset(star_field=1)

    def on_key_release(self, key, modifier):
        """
        Similar to on_key_press this method calls when a user releases a key.
        All objects that need a key release have their own method for neatness
        """
        if self.process:
            self.player.key_up(key)

    def on_mouse_press(self, x: float, y: float, button: int, modifiers: int):
        """
        To find the distance between the players center and a point (mainly for turning thruster distances.)

        if button == arcade.MOUSE_BUTTON_LEFT:
            dx = self.player.center_x-x
            dy = self.player.center_y-y
            print(dx,dy)
            print(math.sqrt(dx**2 + dy**2))
        """


def main():
    game = GameWindow(SCREEN_WIDTH, SCREEN_HEIGHT, TITLE)
    game.reset()
    arcade.run()


if __name__ == "__main__":
    main()
