import time
import random
import math

import arcade

import player
import stars
import space
import mission
import menu
import sol_system_generator
import ui
import vector

SCREEN_WIDTH, SCREEN_HEIGHT = arcade.window_commands.get_display_size()
TITLE = "Sol Defender - Sprint 4"


class GameWindow(arcade.View):

    def __init__(self):

        super().__init__()
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
        self.solar_system = None

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
        self.end_card = menu.MissionEndCard(self)

        # Enemy Handler Variables
        self.enemy_handler = None

        # stars
        self.star_field = stars.StarField(self)

        # Player Death
        self.death_frames = []
        self.current_death_frame = 0
        self.screen_shake = 0
        self.death_wait = 0
        self.blackout = 0
        self.screen_glow = arcade.load_texture("Sprites/Player/Screen Glow.png")
        self.max_frames = 36
        self.player_dead = False
        for y in range(6):
            for x in range(6):
                frame = arcade.load_texture("Sprites/Player/Player Death.png", x*300, 300*y,
                                            300, 300)

                self.death_frames.append(frame)
        self.frame_step = 1/6
        self.frame_time = 0
        self.player_death = arcade.Sprite()
        self.player_death.texture = self.death_frames[0]

        # Wormhole
        self.wormhole = False
        self.worm_sprite = arcade.Sprite()
        self.wormhole_animation = []
        self.current_worm_frame = 0
        self.worm_step = 1/12
        self.worm_time = 0
        for y in range(3):
            for x in range(3):
                frame = arcade.load_texture("Sprites/Player/Wormhole Full.png", x * 240, y * 310, 240, 310)
                self.wormhole_animation.append(frame)
        self.worm_sprite.texture = self.wormhole_animation[0]

        # SCRAP AND CREDITS
        self.player_scrap = 0
        self.player_credit = 0

    def open_map(self):
        self.window.show_view(self.map)

    def open_upgrade(self):
        self.window.show_view(self.upgrades)

    def open_end_card(self, mission_stats):
        self.end_card.setup(mission_stats)
        self.window.show_view(self.end_card)

    def open_clean_map(self):
        self.current_mission = None
        self.map = menu.Map(self)
        self.open_map()

    def open_dead_map(self):
        self.current_mission = None
        generate = sol_system_generator.Generator()
        self.map = menu.Map(self)
        self.open_map()

    def wormhole_update(self, delta_time):
        if not self.wormhole:
            self.wormhole = True
            point = ui.Pointer()
            point.texture = arcade.load_texture("Sprites/Player/Ui/wormhole direction.png")
            point.holder = self.player
            point.target = self.worm_sprite
            self.player.enemy_pointers.append(point)
            p_v_angle = vector.find_angle(self.player.velocity, (0, 0))
            self.worm_sprite.angle = p_v_angle + 180
            self.worm_sprite.center_x = self.player.center_x + math.cos(math.radians(p_v_angle)) * SCREEN_WIDTH
            self.worm_sprite.center_y = self.player.center_y + math.sin(math.radians(p_v_angle)) * SCREEN_WIDTH

        else:
            worm_pos = self.worm_sprite.center_x, self.worm_sprite.center_y
            player_pos = self.player.center_x, self.player.center_y
            distance = vector.find_distance(worm_pos, player_pos)
            if distance <= 30:
                self.open_end_card(self.mission.current_mission_data)

            self.worm_sprite.angle = vector.find_angle(worm_pos, player_pos)
            self.worm_time += delta_time
            if self.worm_time >= self.worm_step:
                self.worm_time -= self.worm_step
                if self.current_worm_frame < 8:
                    self.current_worm_frame += 1
                else:
                    self.current_worm_frame = 0
                self.worm_sprite.texture = self.wormhole_animation[self.current_worm_frame]

    def on_update(self, delta_time: float = 1 / 60):

        """
        This method calls 60 times per second roughly and is what is used to update things such as positions,
        view ports, and scores
        """
        # FPS for debugging
        # print("FPS:",1/delta_time)
        if self.player.dead:
            self.dead_text(delta_time)
        if self.process and not self.player_dead:
            if self.wormhole:
                self.wormhole_update(delta_time)

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

        if self.player.dead and self.player_dead:
            arcade.draw_lrwh_rectangle_textured(self.left_view, self.bottom_view,
                                                SCREEN_WIDTH, SCREEN_HEIGHT,
                                                self.screen_glow, alpha=255 * self.screen_shake)
            self.player_death.draw()

        if self.wormhole:
            self.worm_sprite.draw()

        self.player.draw()

        self.cursor.draw()

        if self.player.dead:
            arcade.draw_rectangle_filled(self.left_view + SCREEN_WIDTH/2, self.bottom_view + SCREEN_HEIGHT/2,
                                         SCREEN_WIDTH, SCREEN_HEIGHT,
                                         (0, 0, 0, 255*self.blackout))

    def dead_text(self, delta_time):
        if self.death_wait == 0:
            self.death_wait = time.time()
        elif time.time() > self.death_wait + 3:
            if self.blackout > 0:
                self.blackout -= 0.05
            else:
                self.blackout = 0
            self.death_wait = -1
            self.process = False
            self.player_dead = True
            self.player_death.center_x = self.player.center_x
            self.player_death.center_y = self.player.center_y
            direction = random.uniform(0, 2 * 3.1415)
            left_mod = self.left_view + math.cos(direction) * (5 * self.screen_shake)
            bottom_mod = self.bottom_view + math.sin(direction) * (5 * self.screen_shake)
            arcade.set_viewport(left_mod, left_mod + SCREEN_WIDTH,
                                bottom_mod, bottom_mod + SCREEN_HEIGHT)
            self.frame_time += delta_time
            if self.frame_time >= self.frame_step:
                self.frame_time -= delta_time
                if self.current_death_frame < 35:
                    self.current_death_frame += 1
                    self.player_death.texture = self.death_frames[self.current_death_frame]
                    self.screen_shake = (self.current_death_frame+1)/36
                else:
                    self.clean()
                    self.open_clean_map()
        elif self.death_wait > 0:
            self.blackout = (time.time() - self.death_wait) / 3

    def clean(self):
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

        self.gravity_handler = None

        # view
        self.left_view = 0
        self.bottom_view = 0
        arcade.set_viewport(self.left_view,
                            SCREEN_WIDTH + self.left_view,
                            self.bottom_view,
                            SCREEN_HEIGHT + self.bottom_view)

        # player
        self.player = None

        # mission
        self.mission = mission.Mission(self)

        # stars
        self.star_field = None

        # Player Death
        self.frame_time = 0
        self.current_death_frame = 0
        self.screen_shake = 0
        self.player_death = arcade.Sprite()
        self.player_death.texture = self.death_frames[0]

        # wormhole
        self.wormhole = False
        self.worm_sprite = arcade.Sprite()
        self.current_worm_frame = 0
        self.worm_time = 0
        self.worm_sprite.texture = self.wormhole_animation[0]

    def setup(self, missions=True, star_field=3):
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

        # wormhole
        self.wormhole = False
        self.worm_sprite = arcade.Sprite()
        self.current_worm_frame = 0
        self.worm_time = 0
        self.worm_sprite.texture = self.wormhole_animation[0]

    def reset(self):
        self.process = True
        self.changed = False

        # view
        self.left_view = 0
        self.bottom_view = 0
        arcade.set_viewport(self.left_view,
                            SCREEN_WIDTH + self.left_view,
                            self.bottom_view,
                            SCREEN_HEIGHT + self.bottom_view)

        self.player.reset()
        self.player.center_x = SCREEN_WIDTH/2
        self.player.center_y = SCREEN_HEIGHT/2

        self.mission.reload()

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
                self.setup(star_field=0)
            elif key == arcade.key.O:
                self.setup(missions=False, star_field=0)
            elif key == arcade.key.I:
                self.setup(missions=False, star_field=1)
            elif key == arcade.key.L:
                self.setup(star_field=1)
            elif key == arcade.key.SPACE:
                self.player.dead = True

            elif key == arcade.key.F:
                self.mission.enemy_handler.slaughter()

            elif key == arcade.key.ESCAPE:
                self.open_map()
            elif key == arcade.key.Z:
                self.open_upgrade()

        if key == arcade.key.LSHIFT and self.process:
            self.process = False
            self.pause_delay = time.time()
        elif key == arcade.key.LSHIFT and not self.process and self.player.start:
            self.process = True
            self.pause_delay = time.time() - self.pause_delay
            for shots in self.player.bullets:
                shots.pause_delay += self.pause_delay
            self.mission.enemy_handler.pause_delay(self.pause_delay)
            self.pause_delay = 0

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
        """if button == arcade.MOUSE_BUTTON_RIGHT:
            if x < SCREEN_WIDTH/2:
                print(f"self.left_view + {x}")
            elif x > SCREEN_WIDTH/2:
                print(f"self.left_view + SCREEN_WIDTH - {SCREEN_WIDTH - x}")

            if y < SCREEN_HEIGHT/2:
                print(f"self.bottom_view + {y}")
            elif y > SCREEN_HEIGHT/2:
                print(f"self.bottom_view + SCREEN_HEIGHT - {SCREEN_HEIGHT - y}")"""

        if self.process:
            self.player.on_mouse_press(button)

    def on_mouse_release(self, x: float, y: float, button: int,
                         modifiers: int):
        if self.process:
            self.player.on_mouse_release(button)

    def on_show(self):
        self.setup(True)


def main():
    game_window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, TITLE, fullscreen=False)
    game_window.center_window()
    game_window.set_mouse_visible(False)
    generator = sol_system_generator.Generator
    game = GameWindow()
    mini_map = menu.Map(game)
    game_window.show_view(mini_map)
    arcade.run()


if __name__ == "__main__":
    main()
