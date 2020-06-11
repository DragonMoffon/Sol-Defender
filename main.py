import time
import arcade

import enemy_handler
import player

SCREEN_WIDTH, SCREEN_HEIGHT = arcade.window_commands.get_display_size()
TITLE = "MVP Sol Defender"


class GameWindow(arcade.Window):

    def __init__(self, screen_width=1000, screen_height=750, title="Title"):

        super().__init__(screen_width, screen_height, title)
        arcade.set_background_color(arcade.color.BLACK)

        # check if on_update should run.
        self.process = True
        self.changed = False

        # x and y Coordinates for Reset Position
        self.center_x = SCREEN_WIDTH // 2
        self.center_y = SCREEN_HEIGHT // 2

        # The Player Sprite and Setup
        self.player = None

        # Asteroid Sprite and Setup
        self.asteroid = Asteroid()
        self.asteroid.center_x = self.center_x
        self.asteroid.center_y = self.center_y

        # Viewport Variables
        self.bottom_view = 0
        self.left_view = 0

        # Enemy Handler Variables
        self.enemy_handler = enemy_handler.EnemyHandler()

        # Text Sprite
        self.text_sprite = arcade.Sprite()
        self.show_text = False
        self.spawn_time = 0
        self.life_time = 0.6
        self.text_sprite.center_x, self.text_sprite.center_y = SCREEN_WIDTH // 2, SCREEN_WIDTH // 2

        # setup
        self.center_window()

    def on_update(self, delta_time: float = 1 / 60):

        """
        This method calls 60 times per second roughly and is what is used to update things such as positions, view ports,
        and scores
        """
        # FPS for debugging
        # print("FPS:",1/delta_time)
        if self.process:
            # Players Update
            self.player.on_update(delta_time)

            # Move Viewport
            self.view_port(delta_time)

            # Check The Asteroids Position
            self.asteroid.check_wall(self.left_view, self.bottom_view)

            # Enemy update
            if self.changed:
                self.enemy_handler.on_update(delta_time)

            if self.player.dead:
                self.text_sprite.center_x, self.text_sprite.center_y = self.left_view + SCREEN_WIDTH // 2, self.bottom_view + SCREEN_WIDTH // 2
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

    def on_draw(self):
        """
        Runs all of the draw functions for all Sprites and SpriteLists
        """
        arcade.start_render()
        text = "Player Health: " + str(self.player.health)
        arcade.draw_text(text, self.left_view + SCREEN_WIDTH // 2, self.bottom_view + SCREEN_HEIGHT - 50,
                         arcade.color.WHITE, font_size=15, anchor_x="center")
        self.asteroid.draw()
        self.player.draw()
        self.enemy_handler.draw()
        if self.show_text:
            self.text_sprite.draw()

    def reset(self):
        """
        Resets the game world.
        Needs to be neatened with setups.
        """
        self.process = True
        self.changed = False

        # view
        self.left_view = 0
        self.bottom_view = 0
        arcade.set_viewport(self.left_view,
                            SCREEN_WIDTH + self.left_view,
                            self.bottom_view,
                            SCREEN_HEIGHT + self.bottom_view)

        # player
        self.player = player.Player()
        self.player.center_x = self.center_x
        self.player.center_y = self.center_y

        # asteroid
        self.asteroid.center_x = self.center_x
        self.asteroid.center_y = self.center_y

        # enemies
        self.enemy_handler = enemy_handler.EnemyHandler()
        self.enemy_handler.player = self.player
        self.enemy_handler.setup()

        # player pointer
        self.player.enemy_handler = self.enemy_handler

    def on_key_press(self, key, modifiers):
        """
        Method runs each time the user presses a key.
        Each object that requires a key press has its own key down method for neatness
        """
        if self.process:
            self.player.key_down(key)

        if key == arcade.key.R:
            self.reset()

        if key == arcade.key.ESCAPE:
            self.close()

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


class Asteroid(arcade.Sprite):
    """
    A simple sprite class that shows how the player is moving
    """

    def __init__(self):
        super().__init__()
        self.texture = arcade.load_texture("Sprites/circle_white.png")
        self.scale = 0.15
        self.radius = 24

    def check_wall(self, left, bottom):
        """
        since there is only one asteroid this method moves the asteroid to the opposite side of the screen if it goes past
         the edge of the screen ensuring the player can always see it.
        """
        # left and right
        if left - self.radius > self.center_x:
            self.center_x = left + SCREEN_WIDTH + self.radius
        elif self.center_x > left + SCREEN_WIDTH + self.radius:
            self.center_x = left - self.radius

        # top and bottom
        if bottom - self.radius > self.center_y:
            self.center_y = bottom + SCREEN_HEIGHT + self.radius
        elif self.center_y > bottom + SCREEN_HEIGHT + self.radius:
            self.center_y = bottom - self.radius


def main():
    game = GameWindow(SCREEN_WIDTH, SCREEN_HEIGHT, TITLE)
    game.reset()
    arcade.run()


if __name__ == "__main__":
    main()
