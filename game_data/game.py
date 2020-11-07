import time
import random
import math
import os
from PIL import Image
import json

import arcade

import game_data.player as player
import game_data.stars as stars
import game_data.space as space
import game_data.mission as mission
import game_data.menu as menu
import game_data.sol_system_generator as sol_system_generator
import game_data.ui as ui
import game_data.vector as vector

SCREEN_WIDTH, SCREEN_HEIGHT = arcade.window_commands.get_display_size()
TITLE = "Sol Defender"


class GameWindow(arcade.View):
    """
    The Game Window Class.
    This class is the game,
    it has the main game loop,
    and is where the player will spend most of their time.
    """

    def __init__(self):
        super().__init__()
        arcade.set_background_color(arcade.color.BLACK)

        # audio
        file_name = "game_data/Music/Mars.wav"
        self.music = arcade.Sound(file_name, streaming=True)
        self.music.play(volume=0)
        self.music.stop()

        # The Cursor.
        self.cursor = arcade.Sprite("game_data/Sprites/Player/Ui/cross_hair_light.png", 0.1, center_x=0, center_y=0)
        self.cursor_screen_pos = [0.0, 0.0]

        # The Gravity Handler
        self.gravity_handler = None

        # The Missions
        self.mission = mission.Mission(self)
        self.prev_difficulty = 1.05
        self.current_mission = None
        self.solar_system = None

        # check if on_update should run.
        self.process = True
        self.changed = False
        self.pause_delay = 0

        # x and y Coordinates for Reset Position
        self.center_x = SCREEN_WIDTH // 2
        self.center_y = SCREEN_HEIGHT // 2

        # The Player Sprite
        self.player = None
        self.player_ship = "Saber"
        self.player_max_speed = 95309
        self.player_gravity_dampening = 1

        # Player Ship Types
        with open("game_data/Data/player.json") as player_file:
            self.player_ships = json.load(player_file)

        # Viewport Variables
        self.bottom_view = 0
        self.left_view = 0

        # Menu Screens
        self.map = None
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
        self.screen_glow = arcade.load_texture("game_data/Sprites/Player/Screen Glow.png")
        self.max_frames = 36
        self.player_dead = False
        for y in range(6):
            for x in range(6):
                frame = arcade.load_texture("game_data/Sprites/Player/Player Death.png", x * 300, 300 * y,
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
                frame = arcade.load_texture("game_data/Sprites/Player/Wormhole Full.png", x * 320, y * 320, 320, 320)
                self.wormhole_animation.append(frame)
        self.worm_sprite.texture = self.wormhole_animation[0]

        # SCRAP AND CREDITS
        self.player_scrap = 0
        self.player_credit = 0

        # Planet Sprites for protecting memory.
        self.planet_sprites = {}

    def on_show(self):
        if self.pause_delay != 0:
            self.pause_delay = time.time() - self.pause_delay
            for shots in self.player.bullets:
                shots.pause_delay += self.pause_delay
            self.mission.enemy_handler.pause_delay(self.pause_delay)
            self.pause_delay = 0

        if self.music.get_stream_position() == 0:
            self.music.play(vector.VOLUME * 0.25)

    def open_map(self):
        """
        Opens the map to show the planets
        """
        self.window.show_view(self.map)

    def open_end_card(self, mission_stats):
        """
        Opens the mission end card, this shows the stats for the mission
        :param mission_stats: The stats of the mission.
        """
        self.end_card.setup(mission_stats)
        self.window.show_view(self.end_card)

    def open_clean_map(self):
        """
        Creates a new map object and opens it.
        """
        self.current_mission = None
        self.map = menu.Map(self)
        self.open_map()

    def open_upgrade_map(self):
        """
        Sets up the map with upgrades then opens it.
        """
        self.current_mission = None
        self.map.setup(True)
        self.open_map()

    def open_dead_map(self):
        """
        Regenerates the Solar System and opens a new Map.
        """
        generator = sol_system_generator.Generator(self)
        self.open_clean_map()

    def wormhole_update(self, delta_time):
        """
        Sets up and animates the end of mission wormhole.
        :param delta_time: The frame time.
        """
        # If a wormhole has not been created
        if not self.wormhole:
            self.wormhole = True

            self.music.stop()
            win_sound = arcade.Sound("game_data/Music/Win Jingle.wav")
            win_sound.play(vector.VOLUME)

            # create a pointer that shows the player to the wormhole.
            point = ui.Pointer()
            point.texture = arcade.load_texture("game_data/Sprites/Player/Ui/wormhole direction.png")
            point.holder = self.player
            point.target = self.worm_sprite
            self.player.enemy_pointers.append(point)

            # calculate the position and place the wormhole.
            p_v_angle = vector.find_angle(self.player.velocity, (0, 0))
            self.worm_sprite.angle = p_v_angle + 180
            self.worm_sprite.center_x = self.player.center_x + math.cos(math.radians(p_v_angle)) * SCREEN_WIDTH
            self.worm_sprite.center_y = self.player.center_y + math.sin(math.radians(p_v_angle)) * SCREEN_WIDTH

        else:
            # Shortening variables.
            worm_pos = self.worm_sprite.center_x, self.worm_sprite.center_y
            player_pos = self.player.center_x, self.player.center_y
            distance = vector.find_distance(worm_pos, player_pos)

            # If the player is in the wormhole end mission.
            if distance <= 80:
                self.open_end_card(self.mission.current_mission_data)

            # angle the wormhole towards the player
            self.worm_sprite.angle = vector.find_angle(worm_pos, player_pos)

            # animate the wormhole.
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
        view ports, and scores. It also updates all features of the game, such as enemy calculations and player actions
        """
        # FPS for debugging
        # print("FPS:", 1/delta_time, "\n")

        # If the main game should be processing, run the main game.
        if self.process and not self.player_dead:

            # print("position:", self.playback_audio.get_stream_position(), "Length:", self.playback_audio.get_length())

            if self.music.get_stream_position() == 0 and not self.wormhole:
                self.music.play(vector.VOLUME * 0.25)

            # Gravity Update
            self.gravity_handler.calculate_each_gravity()

            # Players Update
            self.player.on_update(delta_time)

            # Move Viewport
            self.view_port(delta_time)

            # if there should be/is a wormhole, update it.
            if self.wormhole:
                self.wormhole_update(delta_time)

            self.cursor.center_x = self.left_view + self.cursor_screen_pos[0]
            self.cursor.center_y = self.bottom_view + self.cursor_screen_pos[1]
            self.player.after_update()

            self.mission.on_update(delta_time)

            # Enemy update
            if self.changed:
                self.mission.check_setup()

        # If player dead, do dead animation.
        if self.player.dead:
            self.dead_text(delta_time)

    def view_port(self, delta_time):
        """
        Function for cleaning up on_update.
        Moves the Viewport to keep the player in the center of the screen, and animates the star background.
        """

        # If the viewport has changed, and the previous screen pos.
        self.changed = False
        prev_value = [self.left_view, self.bottom_view]

        # Move the screen pos so the player is in the center.
        left_view = self.player.center_x - SCREEN_WIDTH/2
        bottom_view = self.player.center_y - SCREEN_HEIGHT/2
        self.left_view = left_view
        self.bottom_view = bottom_view

        # If the screen moved change the viewport.
        if prev_value[0] != self.left_view or prev_value[1] != self.bottom_view:
            self.changed = True
            rand_angle = random.uniform(0, 2 * math.pi)
            mod_left = self.left_view + (math.cos(rand_angle) * (self.player.speed / self.player.max_speed))
            mod_bottom = self.bottom_view + (math.sin(rand_angle) * (self.player.speed / self.player.max_speed))

            arcade.set_viewport(mod_left,
                                SCREEN_WIDTH + mod_left,
                                mod_bottom,
                                SCREEN_HEIGHT + mod_bottom)

            # If there are stars move them by the difference.
            if self.star_field.game_view is not None:
                change = (self.left_view - prev_value[0], self.bottom_view - prev_value[1])
                self.star_field.on_update(change)

    def on_draw(self):
        """
        Runs all of the draw functions for all Sprites and SpriteLists
        """
        self.window.ctx.enable_only(self.window.ctx.BLEND)
        arcade.start_render()

        # If there are stars draw them.
        if self.star_field.game_view is not None:
            self.star_field.draw()

        # If there is a Mission (which there always should be) run its draw method.
        if self.mission is not None:
            self.mission.draw()

        # If the player is dead and the pause before the death animation has happened, play the death animation
        if self.player.dead and self.player_dead:
            arcade.draw_lrwh_rectangle_textured(self.left_view, self.bottom_view,
                                                SCREEN_WIDTH, SCREEN_HEIGHT,
                                                self.screen_glow, alpha=255 * self.screen_shake)
            self.player_death.draw()

        # If there is a wormhole draw it.
        if self.wormhole:
            self.worm_sprite.draw()

        # Draw the player.
        self.player.draw()

        # Draw the cursor.
        if self.player.alt or self.window.current_view != self:
            self.cursor.draw()

        # If the player is dead but their death animation has not started.
        if self.player.dead:
            arcade.draw_rectangle_filled(self.left_view + SCREEN_WIDTH/2, self.bottom_view + SCREEN_HEIGHT/2,
                                         SCREEN_WIDTH, SCREEN_HEIGHT,
                                         (0, 0, 0, 255*self.blackout))

    def dead_text(self, delta_time):
        """
        update the death animation, first the blackout then the temporal collapse.
        Name Should Be Changed.
        :param delta_time: The frame time
        """

        # If the player has not yet started dying set the time of their death.
        if self.death_wait == 0:
            self.death_wait = time.time()
        # once they have been blacking out do the temporal collapse.
        elif time.time() > self.death_wait + 3:
            # slowly remove the blackout effect.
            if self.blackout > 0:
                self.blackout -= 0.05
            else:
                self.blackout = 0
            # Set death wait to -3 as it is no longer needed.
            self.death_wait = -3

            # No longer let the main game run, and show the player death animation.
            self.process = False
            self.player_dead = True
            self.player_death.center_x = self.player.center_x
            self.player_death.center_y = self.player.center_y

            # Screen Shake
            direction = random.uniform(0, 2 * 3.1415)
            left_mod = self.left_view + math.cos(direction) * (5 * self.screen_shake)
            bottom_mod = self.bottom_view + math.sin(direction) * (5 * self.screen_shake)
            arcade.set_viewport(left_mod, left_mod + SCREEN_WIDTH,
                                bottom_mod, bottom_mod + SCREEN_HEIGHT)

            # Update death animation.
            self.frame_time += delta_time
            if self.frame_time >= self.frame_step:
                self.frame_time -= delta_time
                if self.current_death_frame < 35:
                    self.current_death_frame += 1
                    self.player_death.texture = self.death_frames[self.current_death_frame]
                    self.screen_shake = (self.current_death_frame+1)/36
                else:
                    self.clean()
                    self.open_dead_map()
        # If the player is dead but is blacking out, keep blacking them out.
        elif self.death_wait > 0:
            self.blackout = (time.time() - self.death_wait) / 3

    def clean(self):
        """
        Purges all Data From The Game View for a clean reset
        """
        self.process = True
        self.changed = False

        # KILL EVERYTHING
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
        self.death_wait = 0
        self.blackout = 0
        self.player_death = arcade.Sprite()
        self.player_death.texture = self.death_frames[0]

        # wormhole
        self.wormhole = False
        self.worm_sprite = arcade.Sprite()
        self.current_worm_frame = 0
        self.worm_time = 0
        self.worm_sprite.texture = self.wormhole_animation[0]

        # SCRAP AND CREDITS
        self.player_scrap = 0
        self.player_credit = 0

    def setup(self):
        """
        Setups up the Game view and loads in the mission.
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

        # player
        self.player = player.Player(self.player_ships[self.player_ship], self,
                                    self.player_max_speed, self.player_gravity_dampening)
        self.player.read_upgrades()

        # mission
        self.mission.mission_setup(self.current_mission)
        point = ui.Pointer(self.player, self.mission.target_object)
        point.texture = arcade.load_texture("game_data/Sprites/Player/Ui/wormhole direction.png")
        self.player.enemy_pointers.append(point)
        self.player.start = 1

        self.player.center_x = self.mission.target_object.center_x + random.randint(-1250, 1250)
        self.player.center_y = self.mission.target_object.center_y + random.randint(-1250, 1250)

        # view
        self.left_view = self.player.center_x - SCREEN_WIDTH/2
        self.bottom_view = self.player.center_y - SCREEN_HEIGHT/2
        arcade.set_viewport(self.left_view,
                            SCREEN_WIDTH + self.left_view,
                            self.bottom_view,
                            SCREEN_HEIGHT + self.bottom_view)

        # stars
        self.star_field = stars.StarField(self)

        # wormhole
        self.wormhole = False
        self.worm_sprite = arcade.Sprite()
        self.current_worm_frame = 0
        self.worm_time = 0
        self.worm_sprite.texture = self.wormhole_animation[0]

        # dead
        self.current_death_frame = 0
        self.screen_shake = 0
        self.death_wait = 0
        self.blackout = 0
        self.player_dead = False

    def reset(self):
        """
        Resets variables but does not clean all data or destroy thing such as the player. used to restart a mission.
        """
        self.process = True
        self.changed = False

        self.player.reset()
        self.player.center_x = self.mission.target_object.center_x + random.randint(-1250, 1250)
        self.player.center_y = self.mission.target_object.center_y + random.randint(-1250, 1250)

        # view
        self.left_view = self.player.center_x - (SCREEN_WIDTH/2)
        self.bottom_view = self.player.center_y - (SCREEN_HEIGHT/2)
        arcade.set_viewport(self.left_view,
                            SCREEN_WIDTH + self.left_view,
                            self.bottom_view,
                            SCREEN_HEIGHT + self.bottom_view)

        self.mission.reload()
        point = ui.Pointer(self.player, self.mission.target_object)
        point.texture = arcade.load_texture("game_data/Sprites/Player/Ui/wormhole direction.png")
        self.player.enemy_pointers.append(point)

        print(self.left_view)
        self.star_field = stars.StarField(self)

        # dead
        self.current_death_frame = 0
        self.screen_shake = 0
        self.death_wait = 0
        self.blackout = 0
        self.player_dead = False

    def on_key_press(self, key, modifiers):
        """
        Method runs each time the user presses a key.
        Each object that requires a key press has its own key down method for neatness
        """

        # If the main game should be running
        if self.process:
            # Run the player class's key press method.
            self.player.key_down(key)

            if key == arcade.key.R:
                # Reset.
                self.reset()

            elif key == arcade.key.F and self.wormhole:
                # Finish Level
                self.open_end_card(self.mission.current_mission_data)

            elif key == arcade.key.ESCAPE:
                # Open the map
                self.pause_delay = time.time()
                self.open_map()

    def on_key_release(self, key, modifier):
        """
        Similar to on_key_press this method calls when a user releases a key.
        All objects that need a key release have their own method for neatness
        """
        if self.process:
            # Run the player class's key release method.
            self.player.key_up(key)

    def on_mouse_motion(self, x: float, y: float, dx: float, dy: float):
        # when the mouse moves move the cursor.
        self.cursor_screen_pos = [x, y]
        if self.process:
            self.player.on_mouse_movement(x, y)

    def on_mouse_press(self, x: float, y: float, button: int, modifiers: int):
        """
        :param x: The X position of the mouse relative to the bottom left corner of the screen
        :param y: The Y position of the mouse relative to the bottom left corner of the screen
        :param button: The button pressed
        :param modifiers: Don't know man
        """

        # If the main game loop is running run the player's on mouse press method.
        if self.process:
            self.player.on_mouse_press(button)

    def on_mouse_release(self, x: float, y: float, button: int,
                         modifiers: int):
        # If the main game loop is running run the player's on mouse release method.
        if self.process:
            self.player.on_mouse_release(button)

    def do_planet_sprites(self):
        """
        Create a dictionary of all the sprites for every type of planet
        so memory doesnt get clogged up loading them over and over
        """
        exo = {}
        gas = {}

        # walk through the exo planets.
        for root, dirs, exo_sprites in os.walk("game_data/Sprites/Planets/exo"):
            # for every sprite create the
            for names in exo_sprites:
                textures = []
                image = Image.open(os.path.join(root, names))
                image_width, image_height = image.width, image.height
                frames = image_height//image_width
                for y in range(frames):
                    texture = arcade.load_texture(os.path.join(root, names), 0, y * image_width,
                                                  image_width, image_width)
                    textures.append(texture)
                exo[names[:-4]] = textures
        for root, dirs, exo_sprites in os.walk("game_data/Sprites/Planets/gas"):
            for names in exo_sprites:
                textures = []
                image = Image.open(os.path.join(root, names))
                image_width, image_height = image.width, image.height
                frames = image_height//image_width
                for y in range(frames):
                    texture = arcade.load_texture(os.path.join(root, names), 0, y * image_width,
                                                  image_width, image_width)
                    textures.append(texture)
                gas[names[:-4]] = textures
        self.planet_sprites['exo'] = exo
        self.planet_sprites['gas'] = gas


def main():
    game_window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, TITLE, fullscreen=True)
    game_window.center_window()
    game_window.set_mouse_visible(False)
    game_window.ctx.enable_only(game_window.ctx.BLEND, game_window.ctx.NEAREST)
    title_screen = menu.TitleScreen(game_window)
    game_window.show_view(title_screen)
    arcade.run()


if __name__ == "__main__":
    main()
