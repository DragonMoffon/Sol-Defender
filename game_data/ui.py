import math
import time
import json
import copy as c
import random

from dataclasses import dataclass
from array import array
import arcade.gl as gl

import arcade

import game_data.vector as vector
import game_data.font as font

# Pre loading textures to decrease the amount of accessing memory due to the large amount that happens with the json
# files.
COMPANY_TAB = arcade.load_texture("game_data/Sprites/Ui/Company Slide.png")
COMPANY_DIM = arcade.load_texture("game_data/Sprites/Ui/Company Slide Dim.png")

UPGRADE_TAB = arcade.load_texture("game_data/Sprites/Ui/Upgrade Tab.png")
UPGRADE_TAB_2 = arcade.load_texture("game_data/Sprites/Ui/Upgrade Tab 2.png")
UPGRADE_TAB_3 = arcade.load_texture("game_data/Sprites/Ui/Upgrade Tab 3.png")
UPGRADE_SLIDE = arcade.load_texture("game_data/Sprites/Ui/Upgrade Slide.png")

ACTIVE_UPGRADE = arcade.load_texture("game_data/Sprites/Ui/Active Upgrade Tab.png")
ACTIVE_UPGRADE_TAB = arcade.load_texture("game_data/Sprites/Ui/active upgrade.png")

SHIP_TAB = arcade.load_texture("game_data/Sprites/Ui/ship_tab.png")
SHIP_DIM = arcade.load_texture("game_data/Sprites/Ui/ship_tab_dim.png")

REP_BAR_TEXTURES = []
for b_y in range(10):
    for b_x in range(25):
        b_texture = arcade.load_texture("game_data/Sprites/Ui/reputation_bar.png",
                                        840 - (b_x * 35), 2250 - (b_y * 250), 35, 250)
        REP_BAR_TEXTURES.append(b_texture)
REP_BAR_TEXTURES.append(arcade.load_texture("game_data/Sprites/Ui/reputation_full.png"))

# The Screen Size for positioning.
SCREEN_WIDTH, SCREEN_HEIGHT = arcade.get_display_size()

#   -- In Game UI --
#
# Pointer - Is used to point the player towards enemies and the wormhole.
#
# PlayerUI - All the ui elements around the corners of the screen. Plus more
#
# MiniMap - The mini map.
#
# ThrusterExhaust - Player's thruster exhaust.


class Pointer(arcade.Sprite):

    def __init__(self, holder=None, target=None):

        super().__init__()

        self.holder = holder  # The arcade.Sprite that is where the pointer points from
        self.target = target  # The arcade.Sprite that the pointer points to
        self.push_out = 45  # The minimum distance the pointer can be from the holder
        self.texture = arcade.load_texture("game_data/Sprites/Player/Ui/Enemy Direction.png")  # The pointer's texture
        self.scale = 0.15  # The pointer's scale

    def kill(self):
        self.remove_from_sprite_lists()
        del self

    def on_update(self, delta_time: float = 1 / 60):
        """
        update the pointer.
        1st. find the angle to the target.
        2nd. calculate the distance from the target for the pointers distance from the holder
        3rd. set the pointers position
        4th. cap the pointers position at a quarter the screen height and width
        """

        holder_pos = self.holder.center_x, self.holder.center_y
        target_pos = self.target.center_x, self.target.center_y
        self.angle = vector.find_angle(target_pos, holder_pos)
        distance = vector.find_distance(holder_pos, target_pos)
        push_out = 45 + distance / 50
        rad_angle = math.radians(self.angle)
        self.center_x = holder_pos[0] + (math.cos(rad_angle) * push_out)
        self.center_y = holder_pos[1] + (math.sin(rad_angle) * push_out)

        if self.center_x > holder_pos[0] + SCREEN_WIDTH // 4:
            self.center_x = holder_pos[0] + SCREEN_WIDTH // 4
        elif self.center_x < holder_pos[0] - SCREEN_WIDTH // 4:
            self.center_x = holder_pos[0] - SCREEN_WIDTH // 4

        if self.center_y > holder_pos[1] + SCREEN_HEIGHT // 4:
            self.center_y = holder_pos[1] + SCREEN_HEIGHT // 4
        elif self.center_y < holder_pos[1] - SCREEN_HEIGHT // 4:
            self.center_y = holder_pos[1] - SCREEN_HEIGHT // 4


class PlayerUi:
    """
    Does all of the graphics for the player while in game.

    It handles:
        The large Ui pieces.
        The Health and Heat bar.
        The Thrusters.
        The Influence warnings.
    """

    def __init__(self, player, game_screen):
        self.player = player
        self.game_screen = game_screen

        # Thrusters for the player.
        self.thrusters = ThrusterExhaust(game_screen.window, player, player.thruster_array)

        self.influence_warnings = None

        # The large ui pieces.
        self.ui_list = arcade.SpriteList()

        self.top_left_sprite = arcade.Sprite("game_data/Sprites/Player/Ui/ui_top_left.png")
        self.ui_list.append(self.top_left_sprite)
        self.top_right_sprite = arcade.Sprite("game_data/Sprites/Player/Ui/ui_top_right.png")
        self.ui_list.append(self.top_right_sprite)
        self.bottom_left_sprite = arcade.Sprite("game_data/Sprites/Player/Ui/ui_bottom_left.png")
        self.bottom_right_sprite = None

        # The health frame and health segments.
        self.health_frame = arcade.Sprite("game_data/Sprites/Player/Ui/health arc frame.png")
        self.health_segments = (arcade.Sprite("game_data/Sprites/Player/Ui/health arc 1.png"),
                                arcade.Sprite("game_data/Sprites/Player/Ui/health arc 2.png"),
                                arcade.Sprite("game_data/Sprites/Player/Ui/health arc 3.png"),
                                arcade.Sprite("game_data/Sprites/Player/Ui/health arc 4.png"),
                                arcade.Sprite("game_data/Sprites/Player/Ui/health arc 5.png"))

        self.ui_list.append(self.health_frame)
        self.ui_list.extend(self.health_segments)

        # The heat frame and orange and red sprites.
        self.heat_arc_frame = arcade.Sprite("game_data/Sprites/Player/Ui/heat arc frame.png")
        self.heat_arc_orange = arcade.Sprite("game_data/Sprites/Player/Ui/heat arc orange.png")
        self.heat_arc_red = arcade.Sprite("game_data/Sprites/Player/Ui/heat arc red.png")

        self.ui_list.append(self.heat_arc_orange)
        self.ui_list.append(self.heat_arc_red)

        self.ui_list.append(self.heat_arc_frame)

        # The minimap.
        self.mini_map = None

        # overheating sound.
        self.overheating_sound = arcade.Sound("game_data/Music/overheat warning.wav", True)
        self.overheat_volume = 0
        self.overheating_sound.play(self.overheat_volume)

        # The target stations, and it's health.
        self.station = game_screen.mission.target_object
        self.station_health_segments = arcade.SpriteList()

        # load all of the health segments.
        for health in range(1, 6):
            segment = arcade.Sprite(f"game_data/Sprites/Player/Ui/station{health}.png")
            self.station_health_segments.append(segment)
            self.ui_list.append(segment)

    def draw(self):
        # If there is no minimap create one.
        if self.mini_map is None:
            self.mini_map = MiniMap(self.player, self.game_screen)

        # Calculate and play the overheating sound.
        if self.overheating_sound.get_stream_position() == 0 and self.player.heat_level > 0.5:
            # If the player is over 0.5 heat than play the audio.
            self.overheat_volume = self.player.heat_level
            self.overheating_sound.play(self.overheat_volume)
        elif self.overheating_sound.get_stream_position() != 0 and self.player.heat_level > 0.5:
            # If the player is over 0.5 heat than play the audio.
            self.overheat_volume = self.player.heat_level
            self.overheating_sound.set_volume(self.overheat_volume)
        elif self.overheating_sound.get_stream_position() != 0:
            # If the player is not over 0.5 heat and the audio is playing, lower it's volume twice as fast.
            self.overheat_volume = self.player.heat_level * 0.5
            self.overheating_sound.set_volume(self.overheat_volume)

        # Player Gun Overheating arc position and calculated alpha.
        self.heat_arc_frame.center_x = self.player.center_x
        self.heat_arc_frame.center_y = self.player.center_y + 25

        self.heat_arc_orange.center_x = self.heat_arc_frame.center_x
        self.heat_arc_red.center_x = self.heat_arc_frame.center_x

        self.heat_arc_orange.center_y = self.heat_arc_frame.center_y
        self.heat_arc_red.center_y = self.heat_arc_frame.center_y

        orange_alpha = self.player.heat_level * 2
        red_alpha = (self.player.heat_level - 0.5) * 2

        if 0 < orange_alpha < 1:
            self.heat_arc_orange.alpha = orange_alpha * 255
        elif orange_alpha > 1:
            self.heat_arc_orange.alpha = 255
        else:
            self.heat_arc_orange.alpha = 0

        if 0 < red_alpha < 1:
            self.heat_arc_red.alpha = red_alpha * 255
        elif orange_alpha > 1:
            self.heat_arc_red.alpha = 255
        else:
            self.heat_arc_red.alpha = 0

        # Player Health Arc. calculate position and alpha of each segement.
        segment_num = self.player.current_segment - 1
        segment_percent = (self.player.health % self.player.health_segment) / self.player.health_segment
        self.health_segments[segment_num].alpha = segment_percent * 255
        if self.player.health >= self.player.current_segment * self.player.health_segment:
            self.health_segments[segment_num].alpha = 255

        self.health_frame.center_x = self.player.center_x
        self.health_frame.center_y = self.player.center_y - 25

        for segment in self.health_segments:
            segment.center_x = self.health_frame.center_x
            segment.center_y = self.health_frame.center_y
            if self.health_segments.index(segment) > segment_num:
                segment.alpha = 0

        # The Ui block in the top right corner. This is the station health and the velocity and acceleration arrows.
        top_right_corner = (SCREEN_WIDTH - 67, SCREEN_HEIGHT - 66)
        self.top_right_sprite.center_x = self.game_screen.left_view + top_right_corner[0]
        self.top_right_sprite.center_y = self.game_screen.bottom_view + top_right_corner[1]
        if self.station is None:
            self.station = self.game_screen.mission.target_object

        # Calculate the position and alpha of each segement.
        for index, segment in enumerate(self.station_health_segments):
            segment.center_x = self.game_screen.left_view + top_right_corner[0]
            segment.center_y = self.game_screen.bottom_view + top_right_corner[1]

            if self.station is not None:
                current_segment = math.floor(self.station.health / 110)
                if current_segment < index:
                    segment.alpha = 0
                elif current_segment == index:
                    portion = (self.station.health / 110) - current_segment
                    segment.alpha = portion * 255
                else:
                    segment.alpha = 255
        # The center of the circle for the velocity and acceleration arrows.
        velocity_circle = self.game_screen.left_view + SCREEN_WIDTH - 35, \
                          self.game_screen.bottom_view + SCREEN_HEIGHT - 35

        # The top left corner ui block. This is the credit, scrap, and unimplemented active ability symbols.
        top_left_corner = (101, SCREEN_HEIGHT - 64)

        # calculate the credit and scrap text position and string.
        credit_text = (self.game_screen.left_view + 43, self.game_screen.bottom_view + SCREEN_HEIGHT - 21)
        scrap_text = (self.game_screen.left_view + 125, self.game_screen.bottom_view + SCREEN_HEIGHT - 21)
        credit = str(self.game_screen.player_credit)
        scrap = str(self.game_screen.player_scrap)
        if len(credit) > 4:
            credit = "9999"
        else:
            for z in range(4 - len(credit)):
                credit = "0" + credit

        if len(scrap) > 3:
            scrap = "999"
        else:
            for z in range(3 - len(scrap)):
                scrap = "0" + scrap

        credit_text = font.LetterList(credit, credit_text[0], credit_text[1])
        scrap_text = font.LetterList(scrap, scrap_text[0], scrap_text[1])

        self.top_left_sprite.center_x = self.game_screen.left_view + top_left_corner[0]
        self.top_left_sprite.center_y = self.game_screen.bottom_view + top_left_corner[1]

        # Calculate all of the gravity influences and draw them in the bottom left corner ui block,
        if len(self.player.gravity_influences):
            bottom_left_corner = (self.game_screen.left_view + 86, self.game_screen.bottom_view + 86)
            circle_center = (self.game_screen.left_view + 58, self.game_screen.bottom_view + 58)

            self.bottom_left_sprite.center_x, self.bottom_left_sprite.center_y = bottom_left_corner
            self.bottom_left_sprite.draw()

            # Draw a line for each influence on the Player.
            for inf in self.player.gravity_influences:
                maximum = 54
                force = [inf[0] * maximum * 1.4, inf[1] * maximum * 1.4]
                magnitude = math.sqrt(force[0] ** 2 + force[1] ** 2)
                if magnitude > maximum:
                    force[0] = (force[0] / magnitude) * maximum
                    force[1] = (force[1] / magnitude) * maximum

                arcade.draw_line(circle_center[0], circle_center[1],
                                 circle_center[0] + force[0], circle_center[1] + force[1], arcade.color.RADICAL_RED)

            arcade.draw_point(circle_center[0], circle_center[1], arcade.color.RADICAL_RED, 4)

        # Draw the Ui list.
        self.ui_list.draw()

        # Draw the velocity and acceleration pointers.
        if self.player.velocity[0] or self.player.velocity[1]:
            velocity_pointer = arcade.Sprite("game_data/Sprites/Player/Ui/velocity_direction.png",
                                             center_x=velocity_circle[0], center_y=velocity_circle[1])
            velocity_pointer.angle = vector.find_angle(self.player.velocity, (0, 0))
            velocity_pointer.draw()

        if self.player.acceleration[0] or self.player.acceleration[0]:
            acceleration_pointer = arcade.Sprite("game_data/Sprites/Player/Ui/acceleration_direction.png",
                                                 center_x=velocity_circle[0], center_y=velocity_circle[1])
            acceleration_pointer.angle = vector.find_angle(self.player.acceleration, (0, 0))
            acceleration_pointer.draw()

        # Draw the text.
        credit_text.draw()
        scrap_text.draw()

        # If the player has pressed tab show the minimap.
        if self.player.show_hit_box:
            self.mini_map.draw()

        # Find all near gravity influences and create a warning for them
        self.influence_warnings = arcade.SpriteList()
        for influences in self.player.gravity_handler.gravity_influences:
            inf_x = influences.center_x
            inf_y = influences.center_y

            distance = vector.find_distance((self.player.center_x, self.player.center_y), (inf_x, inf_y))
            if distance <= (influences.width / 2) + SCREEN_WIDTH * 3:

                if inf_x < self.game_screen.left_view + 48:
                    inf_x = self.game_screen.left_view + 48
                elif self.game_screen.left_view + SCREEN_WIDTH - 48 < inf_x:
                    inf_x = self.game_screen.left_view + SCREEN_WIDTH - 48

                if inf_y < self.game_screen.bottom_view + 48:
                    inf_y = self.game_screen.bottom_view + 48
                elif self.game_screen.bottom_view + SCREEN_HEIGHT - 48 < inf_y:
                    inf_y = self.game_screen.bottom_view + SCREEN_HEIGHT - 48

                danger = arcade.Sprite("game_data/Sprites/Player/Ui/Gravity Influence Warning.png",
                                       center_x=inf_x, center_y=inf_y, scale=0.2)
                self.influence_warnings.append(danger)

        # If there are any warnings draw them.
        if len(self.influence_warnings) > 0:
            self.influence_warnings.draw()

    def under_draw(self):
        """
        The under draw runs first before any other drawings.

        It draws the player thrusters.
        """
        self.thrusters.on_draw()


class MiniMap:
    """
    The minimap handles the minimap during play. It finds the relative position of everything.
    """

    def __init__(self, player, game_screen):
        self.player = player

        # Taking the different objects that's position is needed.
        self.enemy_handler = game_screen.mission.enemy_handler
        self.gravity_handler = game_screen.gravity_handler
        self.mission = game_screen.mission
        self.planet = game_screen.mission.curr_planet

        # The target satellite.
        self.target = self.mission.target_object

        # All of the objects that stay the same each update.
        self.rigid_list = arcade.SpriteList()

        self.game_view = game_screen

        # The scaling of different sprites. both for the position and sprite scaling.
        self.screen_scale = 0.5

        if self.planet is not None:
            self.planet_scale = 0.6  # (self.planet.width / (250 / self.screen_scale)) / 64
            self.divisor = (self.screen_scale * self.planet.width) / (self.planet_scale * 64)
        else:
            self.planet_scale = 1

        # The planet sprite.
        self.planet_sprite = arcade.Sprite("game_data/Sprites/Minimap/space/planet.png", scale=self.planet_scale)
        self.rigid_list.append(self.planet_sprite)

        # The target sprite.
        self.target_sprite = arcade.Sprite("game_data/Sprites/Minimap/space/current_satellite.png",
                                           scale=self.screen_scale)
        self.rigid_list.append(self.target_sprite)

        # The player sprite.
        self.player_textures = (arcade.load_texture("game_data/Sprites/Minimap/player/location.png"),
                                arcade.load_texture("game_data/Sprites/Minimap/player/off_map.png"))
        self.player_sprite = arcade.Sprite("game_data/Sprites/Minimap/player/location.png", scale=self.planet_scale)
        self.rigid_list.append(self.player_sprite)

        # All other sprites.
        self.other_sprites = None

        self.target_vec = (0, 0)

    def draw(self):
        # First it finds the position of the target sprite.
        self.target_sprite.center_x = self.game_view.left_view + SCREEN_WIDTH/2
        self.target_sprite.center_y = self.game_view.bottom_view + SCREEN_HEIGHT/2
        self.target_vec = (self.target.center_x, self.target.center_y)

        # It then defines the planet and player's sprites.
        self.planet_sprite.center_x, self.planet_sprite.center_y = self.define_pos(self.planet)

        self.player_sprite.center_x, self.player_sprite.center_y = self.define_pos(self.player)

        # It then finds the enemy and satellite sprites.
        self.other_sprites = arcade.SpriteList()
        self.enemy_draw()
        self.satellite_draw()

        # Finally everything is drawn.
        self.other_sprites.draw()
        self.rigid_list.draw()

    def enemy_draw(self):
        # For every cluster that has not yet spawned enemies, create a cluster sprite.
        for cluster in self.enemy_handler.clusters:
            if not cluster.spawned:
                pos = self.define_pos(cluster)
                sprite = arcade.Sprite("game_data/Sprites/Minimap/enemy/cluster.png", scale=self.planet_scale + 0.05,
                                       center_x=pos[0], center_y=pos[1])
                self.other_sprites.append(sprite)

        # For every enemy make a enemy sprite.
        if self.enemy_handler.enemy_sprites is not None:
            for enemy in self.enemy_handler.enemy_sprites:
                pos = self.define_pos(enemy)
                sprite = arcade.Sprite("game_data/Sprites/Minimap/enemy/position.png", scale=self.planet_scale,
                                           center_x=pos[0], center_y=pos[1])
                self.other_sprites.append(sprite)

    def satellite_draw(self):
        # For every satellite create a satellite sprite, either a moon symbol or a station symbol.
        for satellite in self.planet.satellites:
            pos = self.define_pos(satellite)
            sprite = None
            if satellite.subset == "moon":
                sprite = arcade.Sprite("game_data/Sprites/Minimap/space/moon.png", scale=self.planet_scale,
                                       center_x=pos[0], center_y=pos[1])
            else:
                if self.mission.target_object != satellite:
                    sprite = arcade.Sprite("game_data/Sprites/Minimap/space/satellite.png", scale=self.planet_scale,
                                           center_x=pos[0], center_y=pos[1])
            if sprite is not None:
                self.other_sprites.append(sprite)

    def define_pos(self, target):
        # Find the relative position scaled and return the vector pos.
        x_diff = (target.center_x - self.target.center_x) / (self.divisor / self.screen_scale)
        y_diff = (target.center_y - self.target.center_y) / (self.divisor / self.screen_scale)
        x_pos = self.target_sprite.center_x + x_diff
        y_pos = self.target_sprite.center_y + y_diff

        return [x_pos, y_pos]


# Variables for thruster effects.
MIN_FADE_TIME = 0.25
MAX_FADE_TIME = 0.75


# A dataclass that holds the data for a single burst.
@dataclass
class Burst:
    buffer: gl.Buffer
    vao: gl.Geometry
    start_time: float
    thruster: float


class ThrusterExhaust:
    """
    The ThrusterExhaust class manages and creates all of the thruster visuals for the player. They use a vertex buffer
    rather than sprites to create the effects.

    It takes in a thruster array to create the different thruster visuals.
    """

    def __init__(self, window, craft, thruster_array):

        # The forward variables.
        self.bursts = []
        self.times = []

        for times in thruster_array:
            self.times.append(0)

        # The maximum and number of particles.
        self.max_particles = 25
        self.num_particles = 25

        # The player craft and the window.
        self.craft = craft
        self.window = window

        self.thruster_array = thruster_array

        # The number of milliseconds till the thrusters are at full burn.
        self.duration = 1250
        self.time = 0

        # The vertex program.
        self.program = self.window.ctx.load_program(
            vertex_shader="game_data/glsl/vertex_shader.glsl",
            fragment_shader="game_data/glsl/fragment_shader.glsl"
        )

    def on_draw(self):
        def _gen_initial_data(initial_x, initial_y, force_v):
            """
            This generates the burst data needed for the particles. It uses yield to create a long list of
            particle data which is then separated in the buffer description.

            This method is for the central thrusters that have a slightly lower output (visually but not literally.)

            :param initial_x: The initial x position of the burst.
            :param initial_y: The initial y position of the burst.
            :param force_v: The thruster force vector for directions.
            """
            for i in range(self.num_particles):
                r_a = math.radians(self.craft.angle) + random.uniform(-0.0872665, 0.0872665)
                v_x = -(force_v[0] * math.cos(r_a) - force_v[1] * math.sin(r_a)) + random.uniform(-0.2, 0.2)
                v_y = -(force_v[0] * math.sin(r_a) + force_v[1] * math.cos(r_a)) + random.uniform(-0.2, 0.2)
                speed = 60 + random.uniform(-30, 30)
                dx = (v_x * speed) / SCREEN_WIDTH
                dy = (v_y * speed) / SCREEN_HEIGHT
                fade_rate = random.uniform(1 / MIN_FADE_TIME, 1 / MAX_FADE_TIME)

                yield initial_x
                yield initial_y
                yield dx
                yield dy
                yield fade_rate

        def _gen_initial_data_turn(initial_x, initial_y, force_v):
            """
            This generates the burst data needed for the particles. It uses yield to create a long list of
            particle data which is then separated in the buffer description.

            This method is for the turning thusters that look visually more powerful.

            :param initial_x: The initial x position of the burst.
            :param initial_y: The initial y position of the burst.
            :param force_v: The thruster force vector for directions.
            """
            for i in range(self.num_particles):
                r_a = math.radians(self.craft.angle) + random.uniform(-0.0523599, 0.0523599)
                v_x = -(force_v[0] * math.cos(r_a) - force_v[1] * math.sin(r_a))
                v_y = -(force_v[0] * math.sin(r_a) + force_v[1] * math.cos(r_a))
                speed = 80 + random.uniform(-40, 40)
                dx = (v_x * speed) / SCREEN_WIDTH
                dy = (v_y * speed) / SCREEN_HEIGHT
                fade_rate = random.uniform(1 / MIN_FADE_TIME, 1 / MAX_FADE_TIME)

                yield initial_x
                yield initial_y
                yield dx
                yield dy
                yield fade_rate

        def _find_count(start):
            """
            This method uses the start time to find the total number of particles.

            This is to give the thrusters a "burn up" visual.

            :param start: The starting time of the calculation.
            :return: The number of particles.
            """
            particles = 0
            if (time.time() * 1000) - start:
                self.time = ((time.time() * 1000) - start) / self.duration
            else:
                self.time = 0

            if self.time >= 1:
                particles = self.max_particles
                return particles
            else:
                count = 1

                adj_t = self.time
                count = adj_t ** 3

                particles = round(count * self.max_particles)
                if particles < 1:
                    particles = 1

                return particles

        # First it loops through all of the bursts and delete all that are too old, it then draws the rest.
        temp_list = self.bursts.copy()
        for burst in temp_list:
            if time.time() - burst.start_time > MAX_FADE_TIME:
                self.bursts.remove(burst)
            else:
                # This sets the size of the particles.
                self.window.ctx.point_size = (self.thruster_array[burst.thruster]['output'])\
                                             * self.window.get_pixel_ratio()

                # For some unknown reason this must be here for the particles to have the correct size.
                self.window.ctx.point_size = 1

                # This is used to find the amount of fade each particle should have.
                self.program['time'] = time.time() - burst.start_time

                # This draws the particles in this burst.
                burst.vao.render(self.program, mode=self.window.ctx.POINTS)

        # This takes every thruster in the array and checks if it is creating thrust
        # If it is it creates a burst every draw until it is no longer thrusting.
        for index, thruster in enumerate(self.thruster_array):
            if self.craft.thrusters_output[thruster['alignment']] != 0:
                if not self.times[index]:
                    # If the thruster has not been burning set the start time for the particle calculations.
                    self.times[index] = time.time() * 1000

                # calculate the num particles.
                self.num_particles = math.ceil(_find_count(self.times[index]) * thruster['output'])

                # use the angle and a rotation matrix on the x and y vector to find the starting x and y.
                rad_angle = math.radians(self.craft.angle)

                start_x = thruster['position'][0] * math.cos(rad_angle) \
                          - thruster['position'][1] * math.sin(rad_angle)

                start_y = thruster['position'][0] * math.sin(rad_angle) \
                          + thruster['position'][1] * math.cos(rad_angle)

                # Converts start x and y to the -1 to 1 scale of the vertex buffer. (0, 0) is the center of the screen.
                x = start_x / (SCREEN_WIDTH * 0.5)
                y = start_y / (SCREEN_HEIGHT * 0.5)

                # creates burst data with different values depending on if the thruster is a central or not.
                if 'c' in thruster['alignment']:
                    initial_data = _gen_initial_data(x, y, thruster['direction_v'])
                else:
                    initial_data = _gen_initial_data_turn(x, y, thruster['direction_v'])

                # Create the buffer, buffer description and vertex array object (vao).
                buffer = self.window.ctx.buffer(data=array('f', initial_data))

                buffer_description = gl.BufferDescription(buffer,
                                                          '2f 2f f',
                                                          ['in_pos', 'in_vel', 'in_fade'])

                vao = self.window.ctx.geometry([buffer_description])

                # Create and append the burst.
                burst = Burst(buffer=buffer, vao=vao, start_time=time.time(), thruster=index)
                self.bursts.append(burst)
            else:
                # If the thruster is not creating force, reset the time.
                self.times[index] = 0

#   -- Map Ui --
#
#   Company Tab - Used for each company
#
#   Upgrade Tab - Used for buying upgrades
#       Upgrade Slide - One for each upgrade
#
#   Active Upgrade - Used for active upgrades
#       Active Upgrade Tab - Used for hit boxes and storage of the text for each active upgrade
#       Active Select - holds which key 1, 2, or 3 the active upgrade will go into.
#


class CompanyTab(arcade.Sprite):
    """
    The CompanyTab class is an object which holds all of the information of a single company and all of the missions
    that company holds.

    As such there is one for every company.

    Like the Title the company tab uses states to show each mission possible.
    """

    def __init__(self, x, y, data, m_data, map_menu):
        super().__init__()

        # parent class variables
        self.texture = COMPANY_DIM
        self.scale = 0.5
        self.center_x = x + 145
        self.center_y = y

        # Map which shows the tab.
        self.map = map_menu

        # relative position from the center of the screen.
        self.rel_x = self.center_x - (self.map.game_view.left_view + SCREEN_WIDTH / 2)
        self.rel_y = self.center_y - (self.map.game_view.bottom_view + SCREEN_HEIGHT / 2)

        # Company Data
        self.company_data = data
        self.mission_data = m_data

        # Decides if there will be states or not.
        self.state = 0
        if m_data[1] is not None:
            self.states = True
        else:
            self.states = False

        # If there are states then set the planet data.
        if self.states:
            self.planet_data = (m_data[0]['planet_data'], m_data[1]['planet_data'])
        elif m_data[0] is not None:
            self.planet_data = (m_data[0]['planet_data'], None)
        else:
            self.planet_data = (None, None)

        # hit box calculator
        self.points = [(-421, 242), (-368, 344), (-161, 421), (419, 421),
                       (420, -419), (-163, -420), (-368, -340), (-368, 137)]

        # the slide position. -1 - Coming In, 0 - In, 1 - Coming Out, 2 - Out
        self.slide = 0
        self.selected = False

        # start - In position, stop - out position.
        self.start = x + 145
        self.stop = x - 145

        # the 4 variables for animating the slide
        self.t = 0
        self.b = 0
        self.c = 290
        self.d = 1500
        self.cd = 1250

        # the starting time of the animation.
        self.start_t = 0

        # The contents of the slide.
        self.contents_list = arcade.SpriteList()
        self.contents_lists = []

        # The contents greyed out
        self.grey_list = arcade.SpriteList()

        # all lists
        self.all_list = []
        self.all_text = []

        # text lists for slide states
        self.base_text = []
        self.texts = []

        # The text on the slide
        self.text = [
            {'rel_x': -100, 'rel_y': 134, 'text': f"{data['name']}", 'scale': 1},
            {'rel_x': -95, 'rel_y': 120, 'text': f"Home Planet: {data['home_planet']}", 'scale': 0.75},
            {'rel_x': -95, 'rel_y': 100, 'text': f"Planets:", 'scale': 0.75},
        ]
        for planets in data['planets']:
            p_dict = {'rel_x': self.text[2]['rel_x'] + 14, 'rel_y': self.text[-1]['rel_y'] - 14,
                      'text': f"{planets}", 'scale': 0.75}
            self.text.append(p_dict)

        # The items on the slide
        self.items = [
            {'rel_x': -145, 'rel_y': 120,
             'tex': arcade.load_texture(f"game_data/Sprites/Ui/Company Symbols/{data['type']}.png"),
             "scale": 0.4, "type": 'all'},
            {'rel_x': -110, 'rel_y': -35,
             'tex': REP_BAR_TEXTURES[data['reputation']],
             "scale": 1, "type": 'slide'},
            {'rel_x': -110, 'rel_y': -35,
             'tex': arcade.load_texture("game_data/Sprites/Ui/reputation_frame.png"),
             "scale": 1, "type": 'all'},
        ]
        # If there are no missions load the none texture.
        if m_data[0] is None:
            self.items.append({'rel_x': -65, 'rel_y': 15,
                               'tex': arcade.load_texture(f"game_data/Sprites/Planets/symbol/none.png"),
                               "scale": 0.3, "type": 'content'})
            self.text.append({'rel_x': -32, 'rel_y': 32, 'text': f"No Mission", 'scale': 0.75})
            self.text.append({'rel_x': -82, 'rel_y': -18, 'text': f"Missions:", 'scale': 0.75})
            for missions in self.company_data['missions']:
                self.text.append({'rel_x': -68, 'rel_y': self.text[-1]['rel_y'] - 14,
                                  'text': f"{missions}", 'scale': 0.75})

        # For every mission create the items and text, plus set the state.
        for index, mission in enumerate(m_data):
            if mission is not None:
                self.contents_lists.append(arcade.SpriteList())
                self.items.append({'rel_x': -65, 'rel_y': 15,
                                   'tex': arcade.load_texture(
                                       f"game_data/Sprites/Planets/symbol/{self.planet_data[index]['subset']}/"
                                       f"{self.planet_data[index]['type']}.png"),
                                   "scale": 0.3, "type": 'content', 'state': index})
                self.text.append({'rel_x': -32, 'rel_y': 32,
                                  'text': f"{self.planet_data[index]['name']}", 'scale': 0.75, 'state': index})
                self.text.append({'rel_x': -32, 'rel_y': 18,
                                  'text': f"{self.planet_data[index]['subset']}", 'scale': 0.75, 'state': index})
                self.text.append({'rel_x': -32, 'rel_y': 4,
                                  'text': f"{self.planet_data[index]['type']}", 'scale': 0.75, 'state': index})
                self.text.append({'rel_x': -82, 'rel_y': -18,
                                  'text': f"Mission:", 'scale': 0.75, 'state': index})
                self.text.append({'rel_x': -82, 'rel_y': -32,
                                  'text': f"{mission['name']}", 'scale': 0.75, 'state': index})

        # For all the text in self.text, create a text list.
        for text in self.text:
            text_list = font.LetterList(text['text'], self.center_x + text['rel_x'], self.center_y + text['rel_y'],
                                        scale=text['scale'])
            # If there is a state set in the data put it into one of the content lists, if there isn't then add it to
            # content list.
            try:
                self.contents_lists[text['state']].extend(text_list)
            except KeyError:
                self.contents_list.extend(text_list)

            # Add the text to the all text for positioning.
            self.all_text.append(text_list)

        # For all items in self.items, create a sprite.
        for items in self.items:
            sprite = arcade.Sprite(scale=items['scale'],
                                   center_x=self.center_x + items['rel_x'], center_y=self.center_y + items['rel_y'])
            sprite.texture = items['tex']
            # See what list to append the data too.
            if items['type'] == 'all':
                self.grey_list.append(sprite)
                self.contents_list.append(sprite)
            elif items['type'] == 'grey':
                self.grey_list.append(sprite)
            else:
                # If it should be stated added it to the state lists, otherwise leave it.
                try:
                    self.contents_lists[items['state']].append(sprite)
                except KeyError:
                    self.contents_list.append(sprite)

            # Add the sprite to the all list.
            self.all_list.append(sprite)

    def update_animation(self, delta_time: float = 1 / 60):
        """
        The update animation method is used to create the smooth sliding animation on the Company Tab.

        This method is very similar between all of the animated Ui elements.
        """

        if self.start_t:

            # Find the normalized time between 0 and 1.
            if (time.time() * 1000) - self.start_t:
                if self.slide == 1:
                    self.t = ((time.time() * 1000) - self.start_t) / self.d
                else:
                    self.t = ((time.time() * 1000) - self.start_t) / self.cd
            else:
                self.t = 0

            # If the time is greater than 1 the animation has finished.
            if self.t + self.b >= 1:
                # reset all the variables and place the tab in it's final location.
                self.start_t = 0
                self.t = 0
                self.b = 0
                if self.slide == -1:
                    self.center_x = self.start
                    self.slide = 0
                    if self.map.current_slide == self:
                        self.map.current_slide = None
                elif self.slide == 1:
                    self.center_x = self.stop
                    self.slide = 2

            # Do the calculations for a smooth cubic transition.
            adj_t = self.t / 0.5
            if adj_t < 1:
                move = 1 / 2 * adj_t * adj_t * adj_t + self.b
            else:
                adj_t -= 2
                move = 1 / 2 * (adj_t * adj_t * adj_t + 2) + self.b

            # Find the position using the calculated value.
            if self.slide == 1:
                self.center_x = self.start - (self.c * move)
            elif self.slide == -1:
                self.center_x = self.stop + (self.c * move)

            # Move all text, and all sprites.
            for index, item in enumerate(self.all_list):
                item.center_x = self.center_x + self.items[index]['rel_x']

            for index, item in enumerate(self.all_text):
                item.x = self.center_x + self.text[index]['rel_x']

    def mouse_over(self, check):
        """
        The method checks if the slide should start to animate and to see if it should show its data.

        :param check: A bool telling the slide if it is being hovered over.
        """
        if not check and not self.selected and self.slide == 2:
            self.slide = -1
            self.start_t = time.time() * 1000
            self.b = 0
        elif check or self.selected:
            if not self.slide:
                if self.mission_data is not None:
                    self.selected = True
                    self.map.current_slide = self
                    if self.states:
                        self.state = 1 - self.state
                self.slide = 1
                self.start_t = time.time() * 1000
                self.b = 0

    def update_position(self):
        """
        This Positions the entire slide realtive to the view port position. It uses the SCREEN_WIDTH and SCREEN_HEIGHT
        to always be exactly where it should be dynamic of the size of the users screen.
        """
        self.center_x = self.map.game_view.left_view + SCREEN_WIDTH / 2 + self.rel_x
        self.center_y = self.map.game_view.bottom_view + SCREEN_HEIGHT / 2 + self.rel_y
        self.start = self.center_x
        self.stop = self.center_x - 290

        # position all of the text and sprites.
        for index, item in enumerate(self.all_list):
            item.center_x = self.center_x + self.items[index]['rel_x']
            item.center_y = self.center_y + self.items[index]['rel_y']

        for index, item in enumerate(self.all_text):
            item.x = self.center_x + self.text[index]['rel_x']
            item.y = self.center_y + self.text[index]['rel_y']

    def draw(self):
        super().draw()
        # If the tab is not resting closed draw the content and the state.
        if self.slide != 0:
            if self.texture != COMPANY_TAB:
                self.texture = COMPANY_TAB
            self.contents_list.draw()
            if len(self.contents_lists):
                self.contents_lists[self.state].draw()
        else:
            # If the tab is closed only draw the grey list.
            if self.texture != COMPANY_DIM:
                self.texture = COMPANY_DIM
            self.grey_list.draw()


class UpgradeTab(arcade.Sprite):
    """
    The UpgradeTab holds the upgrades generated by the Map object. It like the company tab is animated.

    It however also holds multiple upgrade slides which also animate.
    """

    def __init__(self, map_menu, upgrade_data):
        super().__init__()
        # parent variable
        self.scale = 0.5
        if len(upgrade_data) == 4:
            self.texture = UPGRADE_TAB_2
        elif len(upgrade_data) > 4:
            self.texture = UPGRADE_TAB_3
        else:
            self.texture = UPGRADE_TAB

        self.center_x = map_menu.game_view.left_view - 77
        self.center_y = map_menu.game_view.bottom_view + SCREEN_HEIGHT / 2

        self.rel_x = self.center_x - (map_menu.game_view.left_view + SCREEN_WIDTH / 2)
        self.rel_y = self.center_y - (map_menu.game_view.bottom_view + SCREEN_HEIGHT / 2)

        self.hit_box = ((-301, 348), (41, 348), (248, 272), (300, 166), (252, 70), (228, 61), (214, 25),
                        (218, -21), (231, -42), (246, -46), (246, -57), (224, -70), (214, -100), (218, -147),
                        (231, -168), (246, -172), (246, -184), (224, -197), (214, -227), (218, -274), (238, -300),
                        (145, -348), (-301, -348))

        self.map = map_menu
        self.upgrade_data = upgrade_data

        self.selected_upgrade = None
        self.current_credits = self.map.game_view.player_credit
        self.current_scrap = self.map.game_view.player_scrap

        # The animation variables.
        self.slide_back = 0

        self.start_x = map_menu.game_view.left_view - 77
        self.end_x = map_menu.game_view.left_view + 150

        self.t = 0
        self.b = 0
        self.c = 227
        self.d = 1500

        self.slide = 0
        self.selected = False

        self.current_slide = None

        # The data for what is shown on the tab.
        self.slides = arcade.SpriteList()
        self.text = []
        self.slide_data = []
        self.text_data = [
            {'rel_x': -135, 'rel_y': 125, 'text': f"Credits: +{self.current_credits}", 'scale': 1},
            {'rel_x': -135, 'rel_y': 105, 'text': f"Scrap: {self.current_scrap}\" ", 'scale': 1}
        ]

        # Create Upgrade Slides
        s_x = -43
        s_y = 6
        for data in self.upgrade_data:
            slide_dict = {'rel_x': s_x, 'rel_y': s_y, 'upgrade': data}
            s_y -= 63
            if data is None:
                slide_dict['back'] = True
                self.selected = False
            else:
                slide_dict['back'] = False
                self.selected = True

            self.slide_data.append(slide_dict)

        for slides in self.slide_data:
            slide = UpgradeSlide(self, slides)
            self.slides.append(slide)

        # Create Text
        s_y = 6
        s_x = -120
        for data in self.upgrade_data:
            if data is not None:
                t_s_y = s_y + 14
                text = data['name'].split(" ")
                for word in text:
                    text_dict = {'rel_x': s_x, 'rel_y': t_s_y, 'text': f"{word}", 'scale': 0.75}
                    t_s_y -= 14
                    self.text_data.append(text_dict)

            s_y -= 63

        for text in self.text_data:
            text_list = font.LetterList(text['text'], self.center_x + text['rel_x'], self.center_y + text['rel_y'],
                                        scale=text['scale'])
            self.text.append(text_list)

        # The sell scrap button, This button converts the players scrap to credits.
        self.sell_s = arcade.Sprite("game_data/Sprites/Ui/Sell_ S.png",
                                    center_x=self.center_x-125, center_y=self.center_y+125,
                                    hit_box_algorithm="None")
        self.sell_s.change_x = -96
        self.sell_s.change_y = 78
        self.sell_bonus = 0.85

    def draw(self):
        for slides in self.slides:
            slides.draw()

        # Because the number of upgrades changes the texture the slide must be moved before it is drawn
        if len(self.upgrade_data) > 4:
            self.center_y -= 63
        elif len(self.upgrade_data) > 3:
            self.center_y -= 31.5

        super().draw()

        # After is has been draw, the position is reset.
        if len(self.upgrade_data) > 4:
            self.center_y += 63
        elif len(self.upgrade_data) > 3:
            self.center_y += 31.5

        for text in self.text:
            text.draw()

        self.sell_s.center_x = self.center_x + self.sell_s.change_x
        self.sell_s.center_y = self.center_y + self.sell_s.change_y
        self.sell_s.draw()

    def update_animation(self, delta_time: float = 1 / 60):
        """
        Like the company tab the animation uses a cubic function to find its position relative to a start time.
        """

        # Change shown credits so that it matches the real amount in the game view.
        if self.current_credits > self.map.game_view.player_credit:
            self.current_credits -= 1
            self.update_text()
        elif self.current_credits < self.map.game_view.player_credit:
            self.current_credits += 1
            self.update_text()

        # Change the shown scrap to match the real amount in the game view
        if self.current_scrap > self.map.game_view.player_scrap:
            self.current_scrap -= 1
            self.update_text()

        # When all of the upgrade slides have slid back allow the tab to slide back.
        if self.slide_back >= len(self.slides):
            self.selected = False

        # Animate the slides.
        self.slides.update_animation(delta_time)

        # If the start time has been set.
        if self.b:
            # Find the normalized time between 0 and 1.
            if (time.time() * 1000) - self.b:
                self.t = ((time.time() * 1000) - self.b) / self.d
            else:
                self.t = 0

            # If the time is greater than 1 the animation has finished.
            if self.t >= 1:
                self.t = 0
                self.b = 0
                if self.slide == -1:
                    self.center_x = self.start_x
                    self.slide = 0
                elif self.slide == 1:
                    self.center_x = self.end_x
                    self.slide = 2

            # Do the calculations for a smooth cubic transition.
            adj_t = self.t / 0.5
            if adj_t < 1:
                move = 1 / 2 * adj_t * adj_t * adj_t
            else:
                adj_t -= 2
                move = 1 / 2 * (adj_t * adj_t * adj_t + 2)

            # Find the position using the calculated value.
            if self.slide == 1:
                self.center_x = self.start_x + (move * self.c)
            elif self.slide == -1:
                self.center_x = self.end_x - (move * self.c)

            # Move all text, and all sprites.
            for slides in self.slides:
                # IT EXPECTS THE SLIDES TO BE BASE SPRITES WHICH THEY ARE NOT, THIS ISN'T A REAL ERROR.
                slides.update_pos()

            for index, item in enumerate(self.text):
                item.x = self.center_x + self.text_data[index]['rel_x']

    def check(self, check):
        """
        This method checks to see if the tab is hovered over or the upgrade slides are bing hovered over
        and animates them accordingly.

        :param check: A bool telling the tab if it is being hovered over.
        """

        # If the tab is selected run the hover code for the slides.
        if self.selected:
            cxy = self.map.game_view.cursor.center_x, self.map.game_view.cursor.center_y
            for slides in self.slides:
                slides.check(slides.collides_with_point(cxy))

        # If the slide is being hovered over then animate it.
        if check or self.selected:
            if not self.slide:
                self.slide = 1
                self.b = time.time() * 1000
        elif not check and not self.selected and self.slide == 2:
            self.slide = -1
            self.b = time.time() * 1000

    def update_position(self):
        """
        Update the position of the tab and the slides to match the viewport.
        """
        self.center_x = self.map.game_view.left_view + SCREEN_WIDTH / 2 + self.rel_x
        self.center_y = self.map.game_view.bottom_view + SCREEN_HEIGHT / 2 + self.rel_y
        self.start_x = self.center_x
        self.end_x = self.center_x + 227

        for index, item in enumerate(self.text):
            item.x = self.center_x + self.text_data[index]['rel_x']
            item.y = self.center_y + self.text_data[index]['rel_y']

    def update_text(self):
        """
        Recreates all the text incase it ever changes.
        """
        self.text_data = [
            {'rel_x': -135, 'rel_y': 125, 'text': f"Credits: +{self.current_credits}", 'scale': 1},
            {'rel_x': -135, 'rel_y': 105, 'text': f"Scrap: {self.current_scrap}\"", 'scale': 1}
        ]
        self.text = []

        # Create Text
        s_y = 6
        s_x = -120
        for data in self.upgrade_data:
            if data is not None:
                t_s_y = s_y + 14
                text = data['name'].split(" ")
                for word in text:
                    text_dict = {'rel_x': s_x, 'rel_y': t_s_y, 'text': f"{word}", 'scale': 0.75}
                    t_s_y -= 14
                    self.text_data.append(text_dict)

            s_y -= 63

        for text in self.text_data:
            text_list = font.LetterList(text['text'], self.center_x + text['rel_x'], self.center_y + text['rel_y'],
                                        scale=text['scale'])
            self.text.append(text_list)

    def on_mouse_press(self, x, y):
        """
        When the player clicks it checks to see if any of the slides are selected. If they are it buys the upgrade
        if they can afford it.

        :param x: x pos of mouse.
        :param y: y pos of mouse.
        """

        # sells all scrap the player has.
        if self.sell_s.collides_with_point((x, y)):
            self.map.game_view.player_credit += int(self.map.game_view.player_scrap * self.sell_bonus)
            self.map.game_view.player_scrap = 0

        # If they click on a slide, and the slide is fully out, and they can afford it, buy an upgrade.
        if self.selected_upgrade is not None and self.current_slide.slide == 2 \
                and self.selected_upgrade['cost'] <= self.map.game_view.player_credit:

            self.map.game_view.player_credit -= self.selected_upgrade['cost']

            if self.selected_upgrade['prev_upgrade'] != {}:
                self.update_text()
                self.map.game_view.player.passive_upgrades.remove(self.selected_upgrade['prev_upgrade'])

            self.map.game_view.player.setup_upgrades(self.selected_upgrade)
            self.map.game_view.player.dump_upgrades()
            self.selected_upgrade = None

            if self.map.ship_tab is not None:
                self.map.ship_tab.reapply_text()

            for slide in self.slides:
                # IT ASSUMES THE SLIDES ARE STANDARD SPRITES SO THIS ERROR IS FALSE
                if not slide.back:
                    slide.go_back()
                    self.slide_back = 0


class UpgradeSlide(arcade.Sprite):
    """
    The UpgradeSlide is a part of the upgrade tab. It holds a single upgrade and is used to select a specific upgrade.
    """

    def __init__(self, tab, data):
        super().__init__()

        # parent variables.
        self.texture = UPGRADE_SLIDE
        self.scale = 0.5

        self.center_x = tab.center_x + data['rel_x']
        self.center_y = tab.center_y + data['rel_y']

        self.tab = tab
        self.data = data
        self.upgrade = data['upgrade']

        # Animation variables.
        self.back_x = tab.center_x + data['rel_x'] - 18
        self.start_x = tab.center_x + data['rel_x']
        self.end_x = tab.center_x + data['rel_x'] + 300

        # Back is a bool for after the purchase of an upgrade.
        if self.data['back']:
            self.center_x = self.back_x
            self.back = True
        else:
            self.back = False

        self.t = 0
        self.b = 0
        self.c = 300
        self.d = 1500

        self.selected = False
        self.slide = 0

        # Hit Box.
        self.points = [(-351, 59), (324, 60), (347, 33), (350, -14), (341, -45), (324, -59), (-350, -59)]

        # Text data and creation.
        self.text = []
        if self.upgrade is not None:
            self.text_data = [
                {'rel_x': -100, 'rel_y': 14, 'text': f"Cost: +{self.upgrade['cost']}"},
                {'rel_x': -100, 'rel_y': 0, 'text': f"Bonus: {self.upgrade['bonus_name']}"
                                                    f" {int(self.upgrade['bonus'] * 100)}%"},
                {'rel_x': -100, 'rel_y': -14, 'text': f"Bane: {self.upgrade['bane_name']}"
                                                      f" -{int(self.upgrade['bane'] * 100)}%"}
            ]
        else:
            self.text_data = []

        for text in self.text_data:
            text_list = font.LetterList(text['text'], self.center_x + text['rel_x'], self.center_y + text['rel_y'],
                                        scale=0.666)
            self.text.append(text_list)

    def check(self, check):
        """
        Checks and animates the slide if it is being hovered over.

        :param check: A Bool value saying that the slide is being hovered over.
        """
        if not self.back:
            # If it is being hovered over slide the slide out, else slide it back.
            if check and not self.slide and self.tab.selected_upgrade is None:
                self.slide = 1
                self.b = time.time() * 1000
                self.tab.selected_upgrade = self.upgrade
                self.tab.current_slide = self
            elif not check and not self.selected and self.slide == 2:
                self.slide = -1
                self.b = time.time() * 1000
                if self.tab.selected_upgrade == self.upgrade:
                    self.tab.selected_upgrade = None
                if self.tab.current_slide == self:
                    self.tab.current_slide = None

    def update_pos(self):
        """
        Update the position of the slide and the text it holds.
        """
        self.center_x = self.tab.center_x + self.data['rel_x']
        self.start_x = self.center_x
        self.end_x = self.center_x + 300
        self.back_x = self.center_x - 18
        if self.back:
            self.center_x = self.back_x

    def update_animation(self, delta_time: float = 1 / 60):
        """
        Animate the slide just like the upgrade tab and company tab.
        """

        # If the beginning time has been set
        if self.b:
            # Find the normalized time between 0 and 1.
            if (time.time() * 1000) - self.b:
                self.t = ((time.time() * 1000) - self.b) / self.d
            else:
                self.t = 0

            # If the time is greater than 1 the animation has finished.
            if self.t >= 1:
                self.t = 0
                self.b = 0
                if self.slide == -1:
                    self.center_x = self.start_x
                    self.slide = 0
                    if self.back:
                        self.tab.slide_back += 1
                elif self.slide == 1:
                    self.center_x = self.end_x
                    self.slide = 2
                    self.tab.selected_upgrade = self.upgrade

            # Do the calculations for a smooth cubic transition.
            adj_t = self.t / 0.5
            if adj_t < 1:
                move = 1 / 2 * adj_t * adj_t * adj_t
            else:
                adj_t -= 2
                move = 1 / 2 * (adj_t * adj_t * adj_t + 2)

            # Find the position using the calculated value.
            if self.slide == 1:
                self.center_x = self.start_x + (move * self.c)
            elif self.slide == -1:
                self.center_x = self.end_x - (move * self.c)

            # Move all text
            for index, text in enumerate(self.text):
                text.x = self.center_x + self.text_data[index]['rel_x']

    def draw(self):
        # draw the slide and the text.
        super().draw()
        if not self.back and self.slide != 0:
            for text in self.text:
                text.draw()

    def go_back(self):
        """
        Once an upgrade has been bought the slides all move further back into the upgrade tab than normal
        this is to show the player they cannot but any more upgrades.
        """

        self.back = True
        self.b = time.time() * 1000
        if self.slide > 0:
            self.start_x = self.back_x
        else:
            self.end_x = self.start_x
            self.start_x = self.back_x

        self.c = self.end_x - self.start_x

        self.slide = -1


class ActiveUpgrade(arcade.Sprite):
    """
    The ActiveUpgrade class is a holder of active upgrades, which are a reward from companies.
    """

    def __init__(self, company, map_menu):
        super().__init__()

        # Parent Variables.
        self.texture = ACTIVE_UPGRADE
        self.scale = 0.5

        self.center_x = (SCREEN_WIDTH / 2)
        self.center_y = SCREEN_HEIGHT + 205

        self.rel_x = self.center_x - (map_menu.game_view.left_view + SCREEN_WIDTH / 2)
        self.rel_y = self.center_y - (map_menu.game_view.bottom_view + SCREEN_HEIGHT / 2)

        # Data.
        self.company = company
        self.map = map_menu
        self.upgrade_tab = None

        # Animation Variables.
        self.start_y = SCREEN_HEIGHT + 305
        self.end_y = self.start_y - 500

        self.slide = 0

        self.t = 0
        self.c = 500
        self.d = 3000

        self.start_t = 0

        # Text and item data and creation.
        self.text_data = [
            {'text': f"Active Upgrade Reward", 'rel_x': -280, 'rel_y': -25, 'scale': 0.7, 'mid': False},
            {'text': f"Reputation: {company['reputation']}", 'rel_x': -280, 'rel_y': -45, 'scale': 0.7, 'mid': False},
            {'text': f"{company['name']}", 'rel_x': 0, 'rel_y': -160, 'scale': 1, 'mid': True}
        ]
        self.text = []

        for text in self.text_data:
            text_list = font.LetterList(text['text'], self.center_x + text['rel_x'], self.center_y + text['rel_y'],
                                        scale=text['scale'], mid_x=text['mid'])
            self.text.append(text_list)

        self.item_data = [
            {'tex': arcade.load_texture(f"game_data/Sprites/Ui/Company Symbols/{company['type']}.png"),
             'rel_x': -220, 'rel_y': -160, 'scale': 0.41}
        ]
        self.items = arcade.SpriteList()
        for items in self.item_data:
            item = arcade.Sprite(scale=items['scale'],
                                 center_x=self.center_x + items['rel_x'], center_y=self.center_y + items['rel_y'])
            item.texture = items['tex']
            self.items.append(item)

        # Icons for selection.
        self.icons = arcade.SpriteList()
        self.icon_data = [
            {'rel_x': 264.5, 'rel_y': 167.5},
            {'rel_x': 264.5, 'rel_y': 122.5},
            {'rel_x': 264.5, 'rel_y': 78.5}
        ]

        for icon in self.icon_data:
            sprite = arcade.Sprite("game_data/Sprites/Ui/ability  case.png", 0.5,
                                   center_x=self.center_x + icon['rel_x'],
                                   center_y=self.center_y + icon['rel_y'])
            self.icons.append(sprite)

        # Select Sprite..
        self.select = ActiveSelect(self)

        # Active Upgrade Generation Data.
        self.upgrade_ranges = ((5.50, 7.00), (7.50, 9.50))
        self.upgrade_banes = ((0.55, 0.70), (0.75, 0.95))
        self.upgrade_durations = ((9, 4.5), (14, 9.5))

        self.upgrades = []
        self.upgrade_list = arcade.SpriteList()
        self.upgrade_data = []
        self.setup_upgrades()
        s_x = self.center_x - 156
        s_y = self.center_y + 160

        for upgrade in self.upgrades:
            self.upgrade_data.append({'rel_x': -155, 'rel_y': s_y - self.center_y, 'upgrade': upgrade})
            tab = ActiveUpgradeTab(upgrade, s_x, s_y, self)
            self.upgrade_list.append(tab)

            s_y -= 70

    def update_animation(self, delta_time: float = 1 / 60):
        """
        Exactly the same as the other animated pieces, however it changes the y rather than the x.
        """
        self.upgrade_list.update_animation()
        if self.start_t:
            if (time.time() * 1000) - self.start_t:
                self.t = ((time.time() * 1000) - self.start_t) / self.d
            else:
                self.t = 0

            if self.t >= 1:
                self.t = 0
                self.start_t = 0
                if self.slide == -1:
                    self.center_y = self.start_y
                    self.slide = 0
                    self.map.do_active = False
                elif self.slide == 1:
                    self.center_y = self.end_y
                    self.slide = 2

            adj_t = self.t / 0.5
            if adj_t < 1:
                move = 1 / 2 * adj_t * adj_t * adj_t
            else:
                adj_t -= 2
                move = 1 / 2 * (adj_t * adj_t * adj_t + 2)

            if self.slide == 1:
                self.center_y = self.start_y - (move * self.c)
            elif self.slide == -1:
                self.center_y = self.end_y + (move * self.c)

            for index, item in enumerate(self.text):
                item.y = self.center_y + self.text_data[index]['rel_y']

            for index, item in enumerate(self.items):
                item.center_y = self.center_y + self.item_data[index]['rel_y']

            for index, item in enumerate(self.icons):
                item.center_y = self.center_y + self.icon_data[index]['rel_y']
            self.select.update_pos()

            for index, item in enumerate(self.upgrade_list):
                item.center_y = self.center_y + self.upgrade_data[index]['rel_y']
                item.fix()

    def update_position(self):
        """
        Corrects the position of everything dependant of the View Port.
        """
        self.center_x = self.map.game_view.left_view + SCREEN_WIDTH / 2 + self.rel_x
        self.center_y = self.map.game_view.bottom_view + SCREEN_HEIGHT / 2 + self.rel_y
        self.start_y = self.center_y
        self.end_y = self.center_y - 400

        for index, item in enumerate(self.text):
            item.x = self.center_x + self.text_data[index]['rel_x']
            item.y = self.center_y + self.text_data[index]['rel_y']

        for index, item in enumerate(self.items):
            item.center_x = self.center_y + self.item_data[index]['rel_x']
            item.center_y = self.center_y + self.item_data[index]['rel_y']

        for index, item in enumerate(self.icons):
            item.center_x = self.center_y + self.icon_data[index]['rel_x']
            item.center_y = self.center_y + self.icon_data[index]['rel_y']
        self.select.update_pos()

        for index, item in enumerate(self.upgrade_list):
            item.center_x = self.center_x + self.upgrade_data[index]['rel_y']
            item.center_y = self.center_y + self.upgrade_data[index]['rel_y']
            item.fix()

    def draw(self):
        super().draw()
        self.items.draw()
        for text in self.text:
            text.draw()

        for upgrade in self.upgrade_list:
            upgrade.draw()

        self.select.draw()
        self.icons.draw()

        # to show the player what upgrades they have gotten, 2 small letters says what upgrade they have over each icon.
        for index, icon in enumerate(self.icons):
            if self.map.game_view.player.activated_upgrades[index] is not None:
                text = str(self.map.game_view.player.activated_upgrades[index]['bonus_name'])[:1]
                letter = font.LetterList(text, icon.center_x, icon.center_y, 0.5, mid_x=True)
                letter.draw()

    def check(self, cxy):
        """
        Finds what the mouse is hovering over.

        :param cxy: vector pos of mouse.
        """
        hover = arcade.get_sprites_at_point(cxy, self.upgrade_list)
        if len(hover):
            self.upgrade_tab = hover[-1]
        else:
            self.upgrade_tab = None

        hover = arcade.get_sprites_at_point(cxy, self.icons)
        if len(hover):
            self.select.selected = self.icons.index(hover[-1]) + 1
            self.select.update_pos()

    def setup_upgrades(self):
        """
        Like the upgrade generator in menu.py however it creates active upgrades rather than passive ones.
        """
        upgrades = []
        with open("game_data/Data/upgrade_data.json") as upgrade_file:
            upgrade_json = json.load(upgrade_file)
            abilities = upgrade_json['static_abilities']
            base_upgrade = upgrade_json['base_active']
            prefixes = upgrade_json['active_name_prefix']

        base_upgrade['company'] = self.company['name']

        for prev_upgrade in self.map.game_view.player.activated_upgrades:
            if prev_upgrade is not None and prev_upgrade['company'] == self.company['name']:
                upgrade = c.deepcopy(base_upgrade)
                upgrade['prev_upgrade'] = prev_upgrade
                upgrade['level'] = 2
                upgrade['bonus_name'] = prev_upgrade['bonus_name']
                upgrade['bane_name'] = prev_upgrade['bane_name']

                prev_modifier = ((prev_upgrade['bonus'] - self.upgrade_ranges[0][0]) /
                                 (self.upgrade_ranges[0][1] - self.upgrade_ranges[0][0]))

                bonus = self.upgrade_ranges[1]
                bane = self.upgrade_banes[1]
                duration = self.upgrade_durations[1]
                upgrade['bonus'] = round(bonus[0] + (bonus[1] - bonus[0]) * prev_modifier, 2)
                upgrade['bane'] = round(bane[0] + (bane[1] - bane[0]) * prev_modifier, 2)
                upgrade['duration'] = round(duration[0] + (duration[1] - duration[0]) * prev_modifier, 1)

                split = prev_upgrade['name'].split(" ")
                name_words = split[:-1]
                name_words.append("MK_II")
                upgrade['name'] = " ".join(map(str, name_words))

                upgrades.append(upgrade)
                break

        pick = None
        for picks in abilities:
            if picks['name'] == self.company['upgrade']:
                pick = picks
                break

        bane_list = c.copy(abilities)

        while len(upgrades) < 3:
            upgrade = c.deepcopy(base_upgrade)
            temp_bane = c.copy(bane_list)
            if pick is None:
                raise TypeError("\nWHY IS IT NONE \nWHAT HAVE YOU DONE!")
            temp_bane.remove(pick)

            bane_pick = random.choice(temp_bane)
            bane_list.remove(bane_pick)
            upgrade['bonus_name'] = pick['name']
            upgrade['bane_name'] = bane_pick['name']

            random_value = random.random()
            bonus = self.upgrade_ranges[0]
            bane = self.upgrade_banes[0]
            duration = self.upgrade_durations[0]
            upgrade['bonus'] = round(bonus[0] + (bonus[1] - bonus[0]) * random_value, 2)
            upgrade['bane'] = round(bane[0] + (bane[1] - bane[0]) * random_value, 2)
            upgrade['duration'] = round(duration[0] + (duration[1] - duration[0]) * random_value, 1)

            upgrade['name'] = f"{random.choice(prefixes)} {bane_pick['negative']} {pick['positive']} MK_I"

            upgrades.append(upgrade)

        self.upgrades = upgrades

    def trigger(self):
        """
        This method gives the player an upgrade when they click. It overrides the upgrade that is in the selected slot.
        """
        if self.upgrade_tab is not None and self.slide == 2:
            wanted_pos = self.map.game_view.player.activated_upgrades[self.select.selected - 1]
            if wanted_pos == self.upgrade_tab.upgrade['prev_upgrade']:
                self.map.game_view.player.activated_upgrades[self.select.selected - 1] = self.upgrade_tab.upgrade
                self.map.game_view.player.dump_upgrades()
                self.start_t = time.time() * 1000
                self.t = 0
                self.slide = -1
            else:
                self.upgrade_tab.upgrade['activate_key'] = self.select.selected
                self.map.game_view.player.activated_upgrades[self.select.selected - 1] = self.upgrade_tab.upgrade
                self.map.game_view.player.dump_upgrades()
                self.start_t = time.time() * 1000
                self.t = 0
                self.slide = -1


class ActiveUpgradeTab(arcade.Sprite):
    """
    The Active Upgrade Tab is used to store an individual active upgrade as a hit box holder.
    """

    def __init__(self, upgrade, s_x, s_y, active_tab: ActiveUpgrade):
        super().__init__()
        # parent variables.
        self.scale = 0.5
        self.texture = ACTIVE_UPGRADE_TAB

        self.center_x = s_x
        self.center_y = s_y

        self.rel_x = self.center_x - active_tab.center_x
        self.rel_y = self.center_y - active_tab.center_y

        self.hit_box = ((-288, -59), (-288, 59), (288, 59), (288, -59))

        # Data and holder variables.
        self.upgrade = upgrade
        self.active_tab = active_tab
        self.hover = False

        # Text. In this case hover means whether the text is shown when the player hovers over the upgrade or not.
        name_split = upgrade['name'].split(" ")
        self.text = []
        self.hover_text = []
        self.all_text = []
        s_x = - self.rel_x
        s_y = - self.rel_y
        self.text_data = [
            {'rel_x': -115, 'rel_y': 8, 'text': f"{name_split[0]} {name_split[1]}",
             'scale': 0.65, "hover": False, 'mid': False},
            {'rel_x': -115, 'rel_y': -8, 'text': f"{name_split[2]} {name_split[3]}",
             'scale': 0.65, "hover": False, 'mid': False},
            {'rel_x': s_x + 25, 'rel_y': s_y + 150, 'text': f"Duration: {upgrade['duration']}s",
             'scale': 0.65, "hover": True, 'mid': False},
            {'rel_x': s_x + 25, 'rel_y': s_y + 125, 'text': f"Bonus: {upgrade['bonus_name']}",
             'scale': 0.65, "hover": True, 'mid': False},
            {'rel_x': s_x + 75, 'rel_y': s_y + 100, 'text': f"{round(upgrade['bonus'] * 100)}%",
             'scale': 1, "hover": True, 'mid': True},
            {'rel_x': s_x + 25, 'rel_y': s_y + 75, 'text': f"Bane: {upgrade['bane_name']}",
             'scale': 0.65, "hover": True, 'mid': False},
            {'rel_x': s_x + 75, 'rel_y': s_y + 50, 'text': f"{round(upgrade['bane'] * 100)}%",
             'scale': 1, "hover": True, 'mid': True},
            {'rel_x': s_x + 25, 'rel_y': s_y + 25, 'text': f"Symbol:",
             'scale': 0.65, "hover": True, 'mid': False},
        ]

        # Create the text.
        for text in self.text_data:
            text_list = font.LetterList(text['text'],
                                        self.center_x + text['rel_x'], self.center_y + text['rel_y'],
                                        text['scale'], mid_x=text['mid'])

            self.all_text.append(text_list)
            if text['hover']:
                self.hover_text.append(text_list)
            else:
                self.text.append(text_list)

    def update_animation(self, delta_time: float = 1 / 60):
        """
        Checks each update if it should be showing non hover text or hover text.
        """
        if self.active_tab.upgrade_tab == self:
            self.hover = True
        else:
            self.hover = False

    def fix(self):
        """
        Fix the position of the text and sprite..
        """
        for index, text in enumerate(self.all_text):
            text.x = self.center_x + self.text_data[index]['rel_x']
            text.y = self.center_y + self.text_data[index]['rel_y']

    def draw(self):
        # Draw the text in self.text and if hovering show the hover text.
        for text in self.text:
            text.draw()

        if self.hover:
            for text in self.hover_text:
                text.draw()


class ActiveSelect(arcade.Sprite):
    """
    The active select is used to hold which button the active upgrade will be stored in
    either 1, 2 or 3.
    """

    def __init__(self, map_menu):
        super().__init__()
        # Parent variables
        self.texture = arcade.load_texture("game_data/Sprites/Ui/Select.png")
        self.scale = 0.5

        self.center_x = map_menu.center_x + map_menu.icon_data[0]['rel_x']
        self.center_y = map_menu.center_y + map_menu.icon_data[0]['rel_y']

        self.map = map_menu
        self.selected = 1

    def update_pos(self):
        # Fix its relative position to the active upgrade tab.
        self.center_x = self.map.center_x + self.map.icon_data[self.selected - 1]['rel_x']
        self.center_y = self.map.center_y + self.map.icon_data[self.selected - 1]['rel_y']


class ShipTab(arcade.Sprite):

    def __init__(self, player_upgrades, game_view, map_menu):
        super().__init__()
        # Parent Variables
        self.scale = 0.5
        self.texture = SHIP_DIM
        self.center_x = game_view.left_view + SCREEN_WIDTH/2
        self.center_y = game_view.bottom_view - 175/2 + 25

        self.upgrades = player_upgrades

        # holders.
        self.game = game_view
        self.map = map_menu

        # Animation variables.
        self.start_y = self.center_y
        self.c = 150
        self.d = 1500
        self.t = 0
        self.s = 0

        self.selected = False
        self.slide = 0

        # Text data. 'num' is the number shown.
        self.text = {
            'max_health': {'rel_x': -55, 'rel_y': -26, 'num': 0},
            'time_heal': {'rel_x': -39, 'rel_y': 51, 'num': 0},
            'heal_rate': {'rel_x': -28, 'rel_y': -51, 'num': 0},
            'cool_speed': {'rel_x': 131, 'rel_y': -32, 'num': 0},
            'heat_speed': {'rel_x': 130, 'rel_y': -3, 'num': 0},
            'damage': {'rel_x': -53, 'rel_y': 17, 'num': 0},
            'thruster_force': {'rel_x': 106, 'rel_y': -62, 'num': 0},
            'shoot_delay': {'rel_x': 88, 'rel_y': 33, 'num': 0}
        }
        self.texts = []

        # Find the value for each upgrade.
        for upgrade in player_upgrades:
            if upgrade['bonus_name'] in self.text:
                edit = self.text[upgrade['bonus_name']]
                edit['num'] += int(upgrade['bonus'] * 100)
            if upgrade['bane_name'] in self.text:
                edit = self.text[upgrade['bane_name']]
                edit['num'] -= int(upgrade['bane'] * 100)

        # Create the text for each upgrade.
        for text in self.text.values():
            letters = str(int(text['num'])) + "%"
            if -10 < text['num'] < 10:
                letters = '0'+letters

            if text['num'] < 0:
                letters = '-' + letters

            text_list = font.LetterList(letters, self.center_x + text['rel_x'], self.center_y + text['rel_y'], 0.5)
            self.texts.append(text_list)

    def update_animation(self, delta_time: float = 1/60):
        """
        Animate the slide just like all of the other animated UI, however like the active upgrade tab it moves on the y.
        """
        if self.s:
            if (time.time() * 1000) - self.s:
                self.t = ((time.time() * 1000) - self.s) / self.d
            else:
                self.t = 0

            if self.t >= 1:
                self.t = 0
                self.s = 0
                if self.slide == -1:
                    self.slide = 0
                    self.center_y = self.start_y
                else:
                    self.slide = 2
                    self.center_y = self.start_y + self.c

            adj_t = self.t / 0.5
            if adj_t < 1:
                move = 1 / 2 * adj_t * adj_t * adj_t
            else:
                adj_t -= 2
                move = 1 / 2 * (adj_t * adj_t * adj_t + 2)

            if self.slide == 1:
                self.center_y = self.start_y + (move * self.c)
            elif self.slide == -1:
                self.center_y = self.start_y + ((1 - move) * self.c)

            for index, text in enumerate(list(self.text.values())):
                self.texts[index].y = self.center_y + text['rel_y']

    def draw(self):
        """
        If the player is not hovering over the tab make it dim, otherwise make it light and draw the text.
        """
        if self.slide != 0:
            self.texture = SHIP_TAB
        else:
            self.texture = SHIP_DIM

        super().draw()

        for text in self.texts:
            text.draw()

    def mouse_over(self, check):
        """
        :param check: A Bool that says whether the slide is being hovered over or not.
        """
        if check and not self.slide:
            self.slide = 1
            self.s = time.time() * 1000
        elif not check and self.slide == 2:
            self.slide = -1
            self.s = time.time() * 1000

    def reapply_text(self):
        """
        This recalculates and recreates all of the text.
        """
        self.texts = []

        for upgrade in self.upgrades:
            if upgrade['bonus_name'] in self.text:
                edit = self.text[upgrade['bonus_name']]
                edit['num'] += int(upgrade['bonus'] * 100)
            if upgrade['bane_name'] in self.text:
                edit = self.text[upgrade['bane_name']]
                edit['num'] -= int(upgrade['bane'] * 100)

        for text in self.text.values():
            letters = str(int(text['num'])) + "%"
            if 0 < text['num'] < 10:
                letters = '0' + letters

            text_list = font.LetterList(letters, self.center_x + text['rel_x'], self.center_y + text['rel_y'], 0.5)
            self.texts.append(text_list)
