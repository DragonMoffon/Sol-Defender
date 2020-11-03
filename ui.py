import math
import time
import json
import copy as c
import random

from dataclasses import dataclass
from array import array
import arcade.gl as gl

import arcade

import vector
import font

COMPANY_TAB = arcade.load_texture("Sprites/Ui/Company Slide.png")
COMPANY_DIM = arcade.load_texture("Sprites/UI/Company Slide Dim.png")

UPGRADE_TAB = arcade.load_texture("Sprites/Ui/Upgrade Tab.png")
UPGRADE_TAB_2 = arcade.load_texture("Sprites/Ui/Upgrade Tab 2.png")
UPGRADE_TAB_3 = arcade.load_texture("Sprites/Ui/Upgrade Tab 3.png")
UPGRADE_SLIDE = arcade.load_texture("Sprites/Ui/Upgrade Slide.png")

ACTIVE_UPGRADE = arcade.load_texture("Sprites/Ui/Active Upgrade Tab.png")
ACTIVE_UPGRADE_TAB = arcade.load_texture("Sprites/Ui/active upgrade.png")

SHIP_TAB = arcade.load_texture("Sprites/Ui/ship_tab.png")
SHIP_DIM = arcade.load_texture("Sprites/Ui/ship_tab_dim.png")

SCREEN_WIDTH, SCREEN_HEIGHT = arcade.get_display_size()
GUN_METAL = 50, 59, 63
THRUSTER_BLUE = 0, 195, 255

REP_BAR_TEXTURES = []
for b_y in range(10):
    for b_x in range(25):
        b_texture = arcade.load_texture("Sprites/Ui/reputation_bar.png", 840 - (b_x * 35), 2250 - (b_y * 250), 35, 250)
        REP_BAR_TEXTURES.append(b_texture)
REP_BAR_TEXTURES.append(arcade.load_texture("Sprites/Ui/reputation_full.png"))


#   -- In Game UI --
#
# Pointer - Is used to point the player towards enemies and the wormhole.
#
# PlayerUI - All the ui elements around the corners of the screen.
#
# BossUI - The Bosses health bar.
#
# MiniMap - The mini map.

class Pointer(arcade.Sprite):

    def __init__(self, holder=None, target=None):

        super().__init__()

        self.holder = holder  # The arcade.Sprite that is where the pointer points from
        self.target = target  # The arcade.Sprite that the pointer points to
        self.push_out = 45  # The minimum distance the pointer can be from the holder
        self.texture = arcade.load_texture("Sprites/Player/Ui/Enemy Direction.png")  # The pointer's texture
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

    def __init__(self, player, game_screen):
        self.player = player
        self.game_screen = game_screen

        self.thrusters = ThrusterExhaust(game_screen.window, player, player.thruster_array)

        self.influence_warnings = None

        self.ui_list = arcade.SpriteList()

        self.top_left_sprite = arcade.Sprite("Sprites/Player/Ui/ui_top_left.png")
        self.ui_list.append(self.top_left_sprite)
        self.top_right_sprite = arcade.Sprite("Sprites/Player/Ui/ui_top_right.png")
        self.ui_list.append(self.top_right_sprite)
        self.bottom_left_sprite = arcade.Sprite("Sprites/Player/Ui/ui_bottom_left.png")
        self.bottom_right_sprite = None

        self.health_frame = arcade.Sprite("Sprites/Player/Ui/health arc frame.png")
        self.health_segments = (arcade.Sprite("Sprites/Player/Ui/health arc 1.png"),
                                arcade.Sprite("Sprites/Player/Ui/health arc 2.png"),
                                arcade.Sprite("Sprites/Player/Ui/health arc 3.png"),
                                arcade.Sprite("Sprites/Player/Ui/health arc 4.png"),
                                arcade.Sprite("Sprites/Player/Ui/health arc 5.png"))

        self.ui_list.append(self.health_frame)
        self.ui_list.extend(self.health_segments)

        self.heat_arc_frame = arcade.Sprite("Sprites/Player/Ui/heat arc frame.png")
        self.heat_arc_orange = arcade.Sprite("Sprites/Player/Ui/heat arc orange.png")
        self.heat_arc_red = arcade.Sprite("Sprites/Player/Ui/heat arc red.png")

        self.ui_list.append(self.heat_arc_orange)
        self.ui_list.append(self.heat_arc_red)

        self.ui_list.append(self.heat_arc_frame)

        self.transparency = 255

        self.mini_map = None

        self.overheating_sound = arcade.Sound("Music/A legit warning sound.wav", True)
        self.overheat_volume = 0
        self.overheating_sound.play(self.overheat_volume)

        self.station = game_screen.mission.target_object
        self.station_health = arcade.Sprite()
        self.station_health_segments = arcade.SpriteList()

    def draw(self):
        if self.mini_map is None:
            self.mini_map = MiniMap(self.player, self.game_screen)
        if self.overheating_sound.get_stream_position() == 0 and self.player.heat_level > 0.5:
            self.overheat_volume = self.player.heat_level
            self.overheating_sound.play(self.overheat_volume)
        elif self.overheating_sound.get_stream_position() != 0 and self.player.heat_level > 0.5:
            self.overheat_volume = self.player.heat_level
            self.overheating_sound.set_volume(self.overheat_volume)
        elif self.overheating_sound.get_stream_position() != 0:
            self.overheat_volume = self.player.heat_level * 0.5
            self.overheating_sound.set_volume(self.overheat_volume)

        # Player Gun Overheating Bar
        if self.player.alt:
            self.heat_arc_frame.center_x = self.game_screen.cursor.center_x
            self.heat_arc_frame.center_y = self.game_screen.cursor.center_y + 25
        else:
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

        # Player Health Arc
        segment_num = self.player.current_segment - 1
        segment_percent = (self.player.health % self.player.health_segment) / self.player.health_segment
        self.health_segments[segment_num].alpha = segment_percent * 255
        if self.player.health >= self.player.current_segment * self.player.health_segment:
            self.health_segments[segment_num].alpha = 255

        if self.player.alt:
            self.health_frame.center_x = self.game_screen.cursor.center_x
            self.health_frame.center_y = self.game_screen.cursor.center_y - 25
        else:
            self.health_frame.center_x = self.player.center_x
            self.health_frame.center_y = self.player.center_y - 25

        for segment in self.health_segments:
            segment.center_x = self.health_frame.center_x
            segment.center_y = self.health_frame.center_y
            if self.health_segments.index(segment) > segment_num:
                segment.alpha = 0

        top_right_corner = (SCREEN_WIDTH - 105, SCREEN_HEIGHT - 105)
        self.top_right_sprite.center_x = self.game_screen.left_view + top_right_corner[0]
        self.top_right_sprite.center_y = self.game_screen.bottom_view + top_right_corner[1]

        velocity_circle = self.game_screen.left_view + SCREEN_WIDTH - 35, \
                          self.game_screen.bottom_view + SCREEN_HEIGHT - 35

        top_left_corner = (101, SCREEN_HEIGHT - 64)
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

        if len(self.player.gravity_influences):
            bottom_left_corner = (self.game_screen.left_view + 86, self.game_screen.bottom_view + 86)
            circle_center = (self.game_screen.left_view + 58, self.game_screen.bottom_view + 58)

            self.bottom_left_sprite.center_x, self.bottom_left_sprite.center_y = bottom_left_corner
            self.bottom_left_sprite.draw()

            for _ in self.player.gravity_influences:
                maximum = 54
                force = [_[0] * maximum * 1.4, _[1] * maximum * 1.4]
                magnitude = math.sqrt(force[0] ** 2 + force[1] ** 2)
                if magnitude > maximum:
                    force[0] = (force[0] / magnitude) * maximum
                    force[1] = (force[1] / magnitude) * maximum

                arcade.draw_line(circle_center[0], circle_center[1],
                                 circle_center[0] + force[0], circle_center[1] + force[1], arcade.color.RADICAL_RED)

            arcade.draw_point(circle_center[0], circle_center[1], arcade.color.RADICAL_RED, 4)

        self.ui_list.draw()

        if self.player.velocity[0] or self.player.velocity[1]:
            velocity_pointer = arcade.Sprite("Sprites/Player/Ui/velocity_direction.png",
                                             center_x=velocity_circle[0], center_y=velocity_circle[1])
            velocity_pointer.angle = vector.find_angle(self.player.velocity, (0, 0))
            velocity_pointer.draw()

        if self.player.acceleration[0] or self.player.acceleration[0]:
            acceleration_pointer = arcade.Sprite("Sprites/Player/Ui/acceleration_direction.png",
                                                 center_x=velocity_circle[0], center_y=velocity_circle[1])
            acceleration_pointer.angle = vector.find_angle(self.player.acceleration, (0, 0))
            acceleration_pointer.draw()

        credit_text.draw()
        scrap_text.draw()

        self.mini_map.draw()

        self.influence_warnings = arcade.SpriteList()
        for influences in self.player.gravity_handler.gravity_influences:
            inf_x = influences.center_x
            inf_y = influences.center_y

            distance = vector.find_distance((self.player.center_x, self.player.center_y), (inf_x, inf_y))
            if distance <= (influences.width / 2) + SCREEN_WIDTH + 500:

                if inf_x < self.game_screen.left_view + 48:
                    inf_x = self.game_screen.left_view + 48
                elif self.game_screen.left_view + SCREEN_WIDTH - 48 < inf_x:
                    inf_x = self.game_screen.left_view + SCREEN_WIDTH - 48

                if inf_y < self.game_screen.bottom_view + 48:
                    inf_y = self.game_screen.bottom_view + 48
                elif self.game_screen.bottom_view + SCREEN_HEIGHT - 48 < inf_y:
                    inf_y = self.game_screen.bottom_view + SCREEN_HEIGHT - 48

                danger = arcade.Sprite("Sprites/Player/Ui/Gravity Influence Warning.png",
                                       center_x=inf_x, center_y=inf_y, scale=0.2)
                self.influence_warnings.append(danger)

        if len(self.influence_warnings) > 0:
            self.influence_warnings.draw()

    def under_draw(self):
        self.thrusters.on_draw()


MIN_FADE_TIME = 0.25
MAX_FADE_TIME = 0.75


@dataclass
class Burst:
    buffer: gl.Buffer
    vao: gl.Geometry
    start_time: float


class ThrusterExhaust:

    def __init__(self, window, craft, thruster_array):
        self.forward_thrusters = []
        self.forward_bursts = []
        self.forward_start = 0
        self.burn = True

        self.turning_thrusters = []
        self.turning_bursts = []
        self.turning_start = 0
        self.turning = 0

        self.max_particles = 25
        self.num_particles = 25

        self.craft = craft
        self.window = window

        self.thruster_array = thruster_array
        for thruster in thruster_array:
            if 'c' in thruster['alignment']:
                self.forward_bursts.append([])
                self.forward_thrusters.append(thruster)
            else:
                self.turning_bursts.append([])
                self.turning_thrusters.append(thruster)

        self.duration = 1250
        self.time = 0

        self.program = self.window.ctx.load_program(
            vertex_shader="glsl/vertex_shader.glsl",
            fragment_shader="glsl/fragment_shader.glsl"
        )

    def on_draw(self):
        if self.craft.thrusters_output['lc'] and self.craft.thrusters_output['rc'] and not self.burn:
            self.forward_start = time.time() * 1000
            self.burn = True
        elif not self.craft.thrusters_output['lc'] and not self.craft.thrusters_output['rc'] and self.burn:
            self.forward_start = 0
            self.burn = False

        if self.craft.thrusters_output['l'] != 0 and not self.craft.thrusters_output['r']:
            self.turning_start = time.time() * 1000
            self.turning = self.craft.thrusters_output['l']
        if self.craft.thrusters_output['r'] != 0 and not self.craft.thrusters_output['l']:
            self.turning_start = time.time() * 1000
            self.turning = self.craft.thrusters_output['r']

        if not self.craft.thrusters_output['l'] and not self.craft.thrusters_output['r']:
            self.turning_start = 0
            self.turning = 0

        temp_list = self.forward_bursts.copy()
        for index, burst_list in enumerate(temp_list):
            temp_burst = burst_list.copy()
            for burst in temp_burst:
                if time.time() - burst.start_time > MAX_FADE_TIME:
                    burst_list.remove(burst)
                else:
                    self.window.ctx.point_size = (self.forward_thrusters[index]['output'] * 2)\
                                                 * self.window.get_pixel_ratio()

                    self.program['time'] = time.time() - burst.start_time
                    """self.program['mod_pos'] = ((burst.s_x - self.craft.center_x)/SCREEN_WIDTH * 0.5,
                                               (burst.s_y - self.craft.center_y)/SCREEN_HEIGHT * 0.5)"""

                    burst.vao.render(self.program, mode=self.window.ctx.POINTS)

        temp_list = self.turning_bursts.copy()
        for index, burst_list in enumerate(temp_list):
            temp_burst = burst_list.copy()
            for burst in temp_burst:
                if time.time() - burst.start_time > MAX_FADE_TIME:
                    burst_list.remove(burst)
                else:
                    self.window.ctx.point_size = (self.turning_thrusters[index]['output'] * 2)\
                                                 * self.window.get_pixel_ratio()

                    self.program['time'] = time.time() - burst.start_time
                    """self.program['mod_pos'] = ((burst.s_x - self.craft.center_x) / SCREEN_WIDTH * 0.5,
                                               (burst.s_y - self.craft.center_y) / SCREEN_HEIGHT * 0.5)"""

                    burst.vao.render(self.program, mode=self.window.ctx.POINTS)

        def _gen_initial_data(initial_x, initial_y, force_v):
            r_a = math.radians(self.craft.angle)
            for i in range(self.num_particles):
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
            r_a = math.radians(self.craft.angle)
            for i in range(self.num_particles):
                v_x = -(force_v[0] * math.cos(r_a) - force_v[1] * math.sin(r_a))
                v_y = -(force_v[0] * math.sin(r_a) + force_v[1] * math.cos(r_a))
                speed = 100 + random.uniform(-50, 50)
                dx = (v_x * speed) / SCREEN_WIDTH
                dy = (v_y * speed) / SCREEN_HEIGHT
                fade_rate = random.uniform(1 / MIN_FADE_TIME, 1 / MAX_FADE_TIME)

                yield initial_x
                yield initial_y
                yield dx
                yield dy
                yield fade_rate

        def _find_count(start):
            if (time.time() * 1000) - start:
                self.time = ((time.time() * 1000) - start) / self.duration
            else:
                self.time = 0

            if self.time >= 1:
                self.num_particles = self.max_particles
            else:
                count = 1

                adj_t = self.time / 1
                count = adj_t ** 3

                self.num_particles = round(count * self.max_particles)
                if self.num_particles < 1:
                    self.num_particles = 1

        if self.burn:
            _find_count(self.forward_start)

            for index, thruster in enumerate(self.forward_thrusters):

                rad_angle = math.radians(self.craft.angle)

                start_x = thruster['position'][0] * math.cos(rad_angle) \
                          - thruster['position'][1] * math.sin(rad_angle)

                start_y = thruster['position'][0] * math.sin(rad_angle) \
                          + thruster['position'][1] * math.cos(rad_angle)

                s_x = self.craft.center_x + start_x
                s_y = self.craft.center_y + thruster['position'][1]

                x2 = start_x / (SCREEN_WIDTH * 0.5)
                y2 = start_y / (SCREEN_HEIGHT * 0.5)

                initial_data = _gen_initial_data(x2, y2, thruster['direction_v'])

                buffer = self.window.ctx.buffer(data=array('f', initial_data))

                buffer_description = gl.BufferDescription(buffer,
                                                          '2f 2f f',
                                                          ['in_pos', 'in_vel', 'in_fade'])

                vao = self.window.ctx.geometry([buffer_description])

                burst = Burst(buffer=buffer, vao=vao, start_time=time.time())
                self.forward_bursts[index].append(burst)

        if self.turning != 0:
            _find_count(self.turning_start)

            for index, thruster in enumerate(self.turning_thrusters):
                self.num_particles = math.ceil(self.num_particles * self.craft.thrusters_output[thruster['alignment']])
                if not self.num_particles:
                    self.num_particles = 1

                rad_angle = math.radians(self.craft.angle)

                start_x = thruster['position'][0] * math.cos(rad_angle)\
                          - thruster['position'][1] * math.sin(rad_angle)

                start_y = thruster['position'][0] * math.sin(rad_angle)\
                          + thruster['position'][1] * math.cos(rad_angle)

                s_x = self.craft.center_x + start_x
                s_y = self.craft.center_y + start_y

                x2 = start_x / (SCREEN_WIDTH * 0.5)
                y2 = start_y / (SCREEN_HEIGHT * 0.5)

                initial_data = _gen_initial_data(x2, y2, thruster['direction_v'])

                buffer = self.window.ctx.buffer(data=array('f', initial_data))

                buffer_description = gl.BufferDescription(buffer,
                                                          '2f 2f f',
                                                          ['in_pos', 'in_vel', 'in_fade'])

                vao = self.window.ctx.geometry([buffer_description])

                burst = Burst(buffer=buffer, vao=vao, start_time=time.time())
                if self.craft.thrusters_output[thruster['alignment']] > 0:
                    self.turning_bursts[index].append(burst)


class EnemyExhaust:

    def __init__(self, window, craft):

        self.rule_bursts = []

        self.window = window.window
        self.game_window = window
        self.craft = craft
        self.craft_effects = craft.rule_effects
        for output in craft.rule_effects:
            self.rule_bursts.append([])

        self.particle_count = 25
        self.base_count = 25
        self.peak = 4.5

        self.program = self.window.ctx.load_program(
            vertex_shader="glsl/vertex_shader_enemy.glsl",
            fragment_shader="glsl/fragment_shader.glsl"
        )

    def on_draw(self):

        for burst_list in self.rule_bursts:
            temp_list = burst_list.copy()
            for burst in temp_list:
                if time.time() - burst.start_time > MAX_FADE_TIME:
                    burst_list.remove(burst)
                else:
                    self.window.ctx.point_size = 3 * self.window.get_pixel_ratio()

                    self.program['time'] = time.time() - burst.start_time
                    pos_x = (self.craft.center_x - self.game_window.left_view) / SCREEN_WIDTH * 2 - 1
                    pos_y = (self.craft.center_y - self.game_window.bottom_view) / SCREEN_HEIGHT * 2 - 1

                    self.program['pos'] = (pos_x, pos_y)

                    burst.vao.render(self.program, mode=self.window.ctx.POINTS)

        def _gen_initial_data(initial_x, initial_y, velocity):
            self.particle_count = math.ceil(self.base_count * (vector.find_distance(velocity, (0, 0)) / self.peak))
            for i in range(self.particle_count):
                angle = math.radians(vector.find_angle(velocity, (0, 0)) + random.uniform(-10, 10))
                speed = 200 + random.uniform(-50, 50)
                dx = (math.cos(angle) * speed) / SCREEN_WIDTH
                dy = (math.sin(angle) * speed) / SCREEN_HEIGHT
                fade_rate = random.uniform(1 / MIN_FADE_TIME, 1 / MAX_FADE_TIME)

                yield initial_x
                yield initial_y
                yield dx
                yield dy
                yield fade_rate

        for index, effect in enumerate(self.rule_bursts):
            if self.craft.rule_effects[index][0] > 0 or self.craft.rule_effects[index][1] > 0:
                x2 = (self.craft.center_x - self.game_window.left_view) / SCREEN_WIDTH * 2 - 1
                y2 = (self.craft.center_y - self.game_window.bottom_view) / SCREEN_HEIGHT * 2 - 1

                initial_data = _gen_initial_data(x2, y2, self.craft.rule_effects[index])

                buffer = self.window.ctx.buffer(data=array('f', initial_data))

                buffer_description = gl.BufferDescription(buffer,
                                                          '2f 2f f',
                                                          ['in_pos', 'in_vel', 'in_fade'])

                vao = self.window.ctx.geometry([buffer_description])

                burst = Burst(buffer=buffer, vao=vao, start_time=time.time())
                effect.append(burst)


class BossUi:

    def __init__(self, game_screen):
        self.bosses = None
        self.game_screen = game_screen

    def setup(self, bosses):
        self.bosses = arcade.SpriteList()
        for boss in bosses:
            self.bosses.append(boss)

    def clear(self):
        self.bosses = None

    def draw(self):
        if self.bosses is not None:
            start_x = self.game_screen.left_view + (SCREEN_WIDTH / 2)
            start_y = self.game_screen.bottom_view + 15
            for boss in self.bosses:
                arcade.draw_rectangle_filled(start_x, start_y, boss.health, 15, arcade.color.RADICAL_RED)
                start_y += 20


class MiniMap(arcade.SpriteList):

    def __init__(self, player, game_screen):
        super().__init__()
        self.player = player
        self.enemy_handler = game_screen.mission.enemy_handler
        self.gravity_handler = game_screen.gravity_handler
        self.mission = game_screen.mission
        self.planet = game_screen.mission.curr_planet

        self.target = self.mission.target_object

        self.game_view = game_screen
        self.screen_scale = 0.75

        if self.planet is not None:
            self.planet_scale = 0.5  # (self.planet.width / (250 / self.screen_scale)) / 64
            self.divisor = (self.screen_scale * self.planet.width) / (self.planet_scale * 64)
        else:
            self.planet_scale = 1

        self.screen = arcade.Sprite("Sprites/Minimap/map/minimap_screen.png", scale=self.screen_scale)
        self.append(self.screen)

        self.planet_sprite = arcade.Sprite("Sprites/Minimap/space/planet.png", scale=self.planet_scale)
        self.append(self.planet_sprite)

        self.target_sprite = arcade.Sprite("Sprites/Minimap/space/current_satellite.png", scale=self.screen_scale)
        self.append(self.target_sprite)

        self.player_textures = (arcade.load_texture("Sprites/Minimap/player/location.png"),
                                arcade.load_texture("Sprites/Minimap/player/off_map.png"))
        self.player_sprite = arcade.Sprite("Sprites/Minimap/player/location.png", scale=self.planet_scale)
        self.append(self.player_sprite)

        self.enemy_sprites = None
        self.satellite_sprites = None

        self.screen_frame = arcade.Sprite("Sprites/Minimap/map/minimap_frame.png",
                                          center_x=SCREEN_WIDTH / 2, center_y=SCREEN_HEIGHT / 2,
                                          scale=self.screen_scale)
        self.screen_frame_x = SCREEN_WIDTH - (self.screen_frame.width / 2)
        self.screen_frame_y = self.screen_frame.height / 2
        self.append(self.screen_frame)

    def draw(self):
        self.screen_frame.center_x = self.game_view.left_view + self.screen_frame_x
        self.screen_frame.center_y = self.game_view.bottom_view + self.screen_frame_y
        self.screen.center_x = self.game_view.left_view + self.screen_frame_x
        self.screen.center_y = self.game_view.bottom_view + self.screen_frame_y

        self.target_sprite.center_x = self.screen_frame.center_x + (5 * self.screen_scale)
        self.target_sprite.center_y = self.screen_frame.center_y - (5 * self.screen_scale)

        self.planet_sprite.center_x, self.planet_sprite.center_y = self.define_pos(self.planet)

        player_pos = self.define_pos(self.player)
        changed = False
        if player_pos[0] > self.screen.center_x + (self.screen.width / 2):
            player_pos[0] = self.screen.center_x + (self.screen.width / 2)
            changed = True
        elif player_pos[0] < self.screen.center_x - (self.screen.width / 2):
            player_pos[0] = self.screen.center_x - (self.screen.width / 2)
            changed = True
            self.player_sprite.angle = 180

        if player_pos[1] > self.screen.center_y + (self.screen.height / 2):
            player_pos[1] = self.screen.center_y + (self.screen.height / 2)
            changed = True
            self.player_sprite.angle = 270
        elif player_pos[1] < self.screen.center_y - (self.screen.height / 2):
            player_pos[1] = self.screen.center_y - (self.screen.height / 2)
            changed = True
            self.player_sprite.angle = 180

        if changed:
            self.player_sprite.texture = self.player_textures[1]
        else:
            self.player_sprite.texture = self.player_textures[0]
            self.player_sprite.angle = 0
        self.player_sprite.center_x = player_pos[0]
        self.player_sprite.center_y = player_pos[1]

        self.enemy_draw()
        self.satellite_draw()

        super().draw()

    def enemy_draw(self):
        self.enemy_sprites = arcade.SpriteList()
        for cluster in self.enemy_handler.clusters:
            if not cluster.spawned:
                pos = self.define_pos(cluster)
                sprite = arcade.Sprite("Sprites/Minimap/enemy/cluster.png", scale=self.planet_scale + 0.05,
                                       center_x=pos[0], center_y=pos[1])
                self.enemy_sprites.append(sprite)
        if self.enemy_handler.enemy_sprites is not None:
            for enemy in self.enemy_handler.enemy_sprites:
                pos = self.define_pos(enemy)
                if self.target_sprite.center_x - (self.screen.width / 2) < \
                        pos[0] < self.target_sprite.center_x + (self.screen.width / 2):
                    sprite = arcade.Sprite("Sprites/Minimap/enemy/position.png", scale=self.planet_scale,
                                           center_x=pos[0], center_y=pos[1])
                    self.enemy_sprites.append(sprite)

        self.enemy_sprites.draw()

    def satellite_draw(self):
        self.satellite_sprites = arcade.SpriteList()
        for satellite in self.planet.satellites:
            pos = self.define_pos(satellite)
            sprite = None
            if satellite.subset == "moon":
                sprite = arcade.Sprite("Sprites/Minimap/space/moon.png", scale=self.planet_scale,
                                       center_x=pos[0], center_y=pos[1])
            else:
                if self.mission.target_object != satellite:
                    sprite = arcade.Sprite("Sprites/Minimap/space/satellite.png", scale=self.planet_scale,
                                           center_x=pos[0], center_y=pos[1])
            if sprite is not None:
                self.satellite_sprites.append(sprite)

        self.satellite_sprites.draw()

    def define_pos(self, target):
        x_diff = (target.center_x - self.target.center_x) / (self.divisor / self.screen_scale)
        y_diff = (target.center_y - self.target.center_y) / (self.divisor / self.screen_scale)
        x_pos = self.target_sprite.center_x + x_diff
        y_pos = self.target_sprite.center_y + y_diff

        return [x_pos, y_pos]


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

    def __init__(self, x, y, data, m_data, map_menu):
        super().__init__()

        # parent class variables
        self.texture = COMPANY_DIM
        self.scale = 0.5
        self.center_x = x + 145
        self.center_y = y

        self.map = map_menu

        # relative position from the center of the screen.
        self.rel_x = self.center_x - (self.map.game_view.left_view + SCREEN_WIDTH / 2)
        self.rel_y = self.center_y - (self.map.game_view.bottom_view + SCREEN_HEIGHT / 2)

        # Company Data
        self.company_data = data
        self.mission_data = m_data
        self.state = 0
        if m_data[1] is not None:
            self.states = True
        else:
            self.states = False

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
            {'rel_x': -145, 'rel_y': 120, 'tex': arcade.load_texture(f"Sprites/Ui/Company Symbols/{data['type']}.png"),
             "scale": 0.4, "type": 'all'},
            {'rel_x': -110, 'rel_y': -35, 'tex': REP_BAR_TEXTURES[data['reputation']],
             "scale": 1, "type": 'slide'},
            {'rel_x': -110, 'rel_y': -35, 'tex': arcade.load_texture("Sprites/Ui/reputation_frame.png"),
             "scale": 1, "type": 'all'},
        ]
        if m_data[0] is None:
            self.items.append({'rel_x': -65, 'rel_y': 15,
                               'tex': arcade.load_texture(f"Sprites/Planets/symbol/none.png"),
                               "scale": 0.3, "type": 'content'})
            self.text.append({'rel_x': -32, 'rel_y': 32, 'text': f"No Mission", 'scale': 0.75})
            self.text.append({'rel_x': -82, 'rel_y': -18, 'text': f"Missions:", 'scale': 0.75})
            for missions in self.company_data['missions']:
                self.text.append({'rel_x': -68, 'rel_y': self.text[-1]['rel_y'] - 14,
                                  'text': f"{missions}", 'scale': 0.75})

        for index, mission in enumerate(m_data):
            if mission is not None:
                self.contents_lists.append(arcade.SpriteList())
                self.items.append({'rel_x': -65, 'rel_y': 15,
                                   'tex': arcade.load_texture(f"Sprites/Planets/symbol/{self.planet_data[index]['subset']}/"
                                                              f"{self.planet_data[index]['type']}.png"),
                                   "scale": 0.3, "type": 'content', 'state': index})
                self.text.append({'rel_x': -32, 'rel_y': 32, 'text': f"{self.planet_data[index]['name']}", 'scale': 0.75, 'state': index})
                self.text.append({'rel_x': -32, 'rel_y': 18, 'text': f"{self.planet_data[index]['subset']}", 'scale': 0.75, 'state': index})
                self.text.append({'rel_x': -32, 'rel_y': 4, 'text': f"{self.planet_data[index]['type']}", 'scale': 0.75, 'state': index})
                self.text.append({'rel_x': -82, 'rel_y': -18, 'text': f"Mission:", 'scale': 0.75, 'state': index})
                self.text.append({'rel_x': -82, 'rel_y': -32, 'text': f"{mission['name']}", 'scale': 0.75, 'state': index})

        for text in self.text:
            text_list = font.LetterList(text['text'], self.center_x + text['rel_x'], self.center_y + text['rel_y'],
                                        scale=text['scale'])
            try:
                self.contents_lists[text['state']].extend(text_list)
            except KeyError:
                self.contents_list.extend(text_list)

            self.all_text.append(text_list)

        for items in self.items:
            sprite = arcade.Sprite(scale=items['scale'],
                                   center_x=self.center_x + items['rel_x'], center_y=self.center_y + items['rel_y'])
            sprite.texture = items['tex']
            if items['type'] == 'all':
                self.grey_list.append(sprite)
                self.contents_list.append(sprite)
            elif items['type'] == 'grey':
                self.grey_list.append(sprite)
            else:
                try:
                    self.contents_lists[items['state']].append(sprite)
                except KeyError:
                    self.contents_list.append(sprite)

            self.all_list.append(sprite)

    def update_animation(self, delta_time: float = 1 / 60):
        if self.start_t:
            if (time.time() * 1000) - self.start_t:
                if self.slide == 1:
                    self.t = ((time.time() * 1000) - self.start_t) / self.d
                else:
                    self.t = ((time.time() * 1000) - self.start_t) / self.cd
            else:
                self.t = 0

            if self.t + self.b >= 1:
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

            adj_t = self.t / 0.5
            if adj_t < 1:
                move = 1 / 2 * adj_t * adj_t * adj_t + self.b
            else:
                adj_t -= 2
                move = 1 / 2 * (adj_t * adj_t * adj_t + 2) + self.b

            if self.slide == 1:
                self.center_x = self.start - (self.c * move)
            elif self.slide == -1:
                self.center_x = self.stop + (self.c * move)

            for index, item in enumerate(self.all_list):
                item.center_x = self.center_x + self.items[index]['rel_x']

            for index, item in enumerate(self.all_text):
                item.x = self.center_x + self.text[index]['rel_x']

    def mouse_over(self, check):
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
        self.center_x = self.map.game_view.left_view + SCREEN_WIDTH / 2 + self.rel_x
        self.center_y = self.map.game_view.bottom_view + SCREEN_HEIGHT / 2 + self.rel_y
        self.start = self.center_x
        self.stop = self.center_x - 290
        for index, item in enumerate(self.all_list):
            item.center_x = self.center_x + self.items[index]['rel_x']
            item.center_y = self.center_y + self.items[index]['rel_y']

        for index, item in enumerate(self.all_text):
            item.x = self.center_x + self.text[index]['rel_x']
            item.y = self.center_y + self.text[index]['rel_y']

    def draw(self):
        super().draw()
        if self.slide != 0:
            if self.texture != COMPANY_TAB:
                self.texture = COMPANY_TAB
            self.contents_list.draw()
            if len(self.contents_lists):
                self.contents_lists[self.state].draw()
        else:
            if self.texture != COMPANY_DIM:
                self.texture = COMPANY_DIM
            self.grey_list.draw()


class UpgradeTab(arcade.Sprite):

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

        self.map = map_menu
        self.upgrade_data = upgrade_data

        self.center_x = map_menu.game_view.left_view - 77
        self.center_y = map_menu.game_view.bottom_view + SCREEN_HEIGHT / 2

        self.rel_x = self.center_x - (self.map.game_view.left_view + SCREEN_WIDTH / 2)
        self.rel_y = self.center_y - (self.map.game_view.bottom_view + SCREEN_HEIGHT / 2)

        self.hit_box = ((-301, 348), (41, 348), (248, 272), (300, 166), (252, 70), (228, 61), (214, 25),
                        (218, -21), (231, -42), (246, -46), (246, -57), (224, -70), (214, -100), (218, -147),
                        (231, -168), (246, -172), (246, -184), (224, -197), (214, -227), (218, -274), (238, -300),
                        (145, -348), (-301, -348))

        self.selected_upgrade = None
        self.current_credits = self.map.game_view.player_credit
        self.current_scrap = self.map.game_view.player_scrap
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

        self.sell_s = arcade.Sprite("Sprites/Ui/Sell_ S.png",
                                    center_x=self.center_x-125, center_y=self.center_y+125,
                                    hit_box_algorithm="None")
        self.sell_s.change_x = -96
        self.sell_s.change_y = 78
        self.sell_bonus = 0.85

    def draw(self):
        for slides in self.slides:
            slides.draw()

        if len(self.upgrade_data) > 3:
            self.center_y -= 63

        super().draw()

        if len(self.upgrade_data) > 3:
            self.center_y += 63

        for text in self.text:
            text.draw()

        self.sell_s.center_x = self.center_x + self.sell_s.change_x
        self.sell_s.center_y = self.center_y + self.sell_s.change_y
        self.sell_s.draw()

    def update_animation(self, delta_time: float = 1 / 60):
        if self.current_credits > self.map.game_view.player_credit:
            self.current_credits -= 1
            self.update_text()
        elif self.current_credits < self.map.game_view.player_credit:
            self.current_credits += 1
            self.update_text()

        if self.current_scrap > self.map.game_view.player_scrap:
            self.current_scrap -= 1
            self.update_text()

        if self.slide_back >= len(self.slides):
            self.selected = False
        self.slides.update_animation(delta_time)
        if self.b:
            if (time.time() * 1000) - self.b:
                self.t = ((time.time() * 1000) - self.b) / self.d
            else:
                self.t = 0
            if self.t >= 1:
                self.t = 0
                self.b = 0
                if self.slide == -1:
                    self.center_x = self.start_x
                    self.slide = 0
                elif self.slide == 1:
                    self.center_x = self.end_x
                    self.slide = 2

            adj_t = self.t / 0.5
            if adj_t < 1:
                move = 1 / 2 * adj_t * adj_t * adj_t
            else:
                adj_t -= 2
                move = 1 / 2 * (adj_t * adj_t * adj_t + 2)

            if self.slide == 1:
                self.center_x = self.start_x + (move * self.c)
            elif self.slide == -1:
                self.center_x = self.end_x - (move * self.c)

            for slides in self.slides:
                slides.update_pos()

            for index, item in enumerate(self.text):
                item.x = self.center_x + self.text_data[index]['rel_x']

    def check(self, check):
        if self.selected:
            cxy = self.map.game_view.cursor.center_x, self.map.game_view.cursor.center_y
            for slides in self.slides:
                slides.check(slides.collides_with_point(cxy))
        if check or self.selected:
            if not self.slide:
                self.slide = 1
                self.b = time.time() * 1000
        elif not check and not self.selected and self.slide == 2:
            self.slide = -1
            self.b = time.time() * 1000

    def update_position(self):
        self.center_x = self.map.game_view.left_view + SCREEN_WIDTH / 2 + self.rel_x
        self.center_y = self.map.game_view.bottom_view + SCREEN_HEIGHT / 2 + self.rel_y
        self.start_x = self.center_x
        self.end_x = self.center_x + 227

        for index, item in enumerate(self.text):
            item.x = self.center_x + self.text_data[index]['rel_x']
            item.y = self.center_y + self.text_data[index]['rel_y']

    def update_text(self):
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
        if self.sell_s.collides_with_point((x, y)):
            self.map.game_view.player_credit += int(self.map.game_view.player_scrap * self.sell_bonus)
            self.map.game_view.player_scrap = 0

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
                if not slide.back:
                    slide.go_back()
                    self.slide_back = 0


class UpgradeSlide(arcade.Sprite):

    def __init__(self, tab, data):
        super().__init__()
        self.texture = UPGRADE_SLIDE
        self.scale = 0.5

        self.tab = tab
        self.data = data
        self.upgrade = data['upgrade']

        self.center_x = tab.center_x + data['rel_x']
        self.center_y = tab.center_y + data['rel_y']

        self.back_x = tab.center_x + data['rel_x'] - 18
        self.start_x = tab.center_x + data['rel_x']
        self.end_x = tab.center_x + data['rel_x'] + 300

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

        point_list = [(-351, 59), (324, 60), (347, 33), (350, -14), (341, -45), (324, -59), (-350, -59)]
        self.set_hit_box(point_list)

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
        if not self.back:
            if check:
                if not self.slide and self.tab.selected_upgrade is None:
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
        self.center_x = self.tab.center_x + self.data['rel_x']
        self.start_x = self.center_x
        self.end_x = self.center_x + 300
        self.back_x = self.center_x - 18
        if self.back:
            self.center_x = self.back_x

    def update_animation(self, delta_time: float = 1 / 60):
        if self.b:
            if (time.time() * 1000) - self.b:
                self.t = ((time.time() * 1000) - self.b) / self.d
            else:
                self.t = 0
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

            adj_t = self.t / 0.5
            if adj_t < 1:
                move = 1 / 2 * adj_t * adj_t * adj_t
            else:
                adj_t -= 2
                move = 1 / 2 * (adj_t * adj_t * adj_t + 2)

            if self.slide == 1:
                self.center_x = self.start_x + (move * self.c)
            elif self.slide == -1:
                self.center_x = self.end_x - (move * self.c)

            for index, text in enumerate(self.text):
                text.x = self.center_x + self.text_data[index]['rel_x']

    def draw(self):
        super().draw()
        if not self.back and self.slide != 0:
            for text in self.text:
                text.draw()

    def go_back(self):
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

    def __init__(self, company, map_menu):
        super().__init__()
        self.texture = ACTIVE_UPGRADE
        self.scale = 0.5

        self.center_x = (SCREEN_WIDTH / 2)
        self.center_y = SCREEN_HEIGHT + 205

        self.rel_x = self.center_x - (map_menu.game_view.left_view + SCREEN_WIDTH / 2)
        self.rel_y = self.center_y - (map_menu.game_view.bottom_view + SCREEN_HEIGHT / 2)

        self.company = company
        self.map = map_menu
        self.upgrade_tab = None

        self.start_y = SCREEN_HEIGHT + 305
        self.end_y = self.start_y - 500

        self.slide = 0

        self.t = 0
        self.c = 500
        self.d = 3000

        self.start_t = 0

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
            {'tex': arcade.load_texture(f"Sprites/Ui/Company Symbols/{company['type']}.png"),
             'rel_x': -220, 'rel_y': -160, 'scale': 0.41}
        ]
        self.items = arcade.SpriteList()
        for items in self.item_data:
            item = arcade.Sprite(scale=items['scale'],
                                 center_x=self.center_x + items['rel_x'], center_y=self.center_y + items['rel_y'])
            item.texture = items['tex']
            self.items.append(item)

        self.icons = arcade.SpriteList()
        self.icon_data = [
            {'rel_x': 264.5, 'rel_y': 167.5},
            {'rel_x': 264.5, 'rel_y': 122.5},
            {'rel_x': 264.5, 'rel_y': 78.5}
        ]

        for icon in self.icon_data:
            sprite = arcade.Sprite("Sprites/Ui/ability  case.png", 0.5,
                                   center_x=self.center_x + icon['rel_x'],
                                   center_y=self.center_y + icon['rel_y'])
            self.icons.append(sprite)

        self.select = ActiveSelect(self)

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
        arcade.draw_point(self.center_x, self.center_y, arcade.color.RADICAL_RED, 5)

    def check(self, cxy):
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
        upgrades = []
        with open("Data/upgrade_data.json") as upgrade_file:
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
                print(upgrade['name'])

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
        if self.upgrade_tab is not None and self.slide == 2:
            wanted_pos = self.map.game_view.player.activated_upgrades[self.select.selected - 1]
            if wanted_pos is None:
                self.upgrade_tab.upgrade['activate_key'] = self.select.selected
                self.map.game_view.player.activated_upgrades[self.select.selected - 1] = self.upgrade_tab.upgrade
                self.map.game_view.player.dump_upgrades()
                self.start_t = time.time() * 1000
                self.t = 0
                self.slide = -1
            elif wanted_pos == self.upgrade_tab.upgrade['prev_upgrade']:
                self.map.game_view.player.activated_upgrades[self.select.selected - 1] = self.upgrade_tab.upgrade
                self.map.game_view.player.dump_upgrades()
                self.start_t = time.time() * 1000
                self.t = 0
                self.slide = -1
            elif wanted_pos is not None:
                self.upgrade_tab.upgrade['activate_key'] = self.select.selected
                self.map.game_view.player.activated_upgrades[self.select.selected - 1] = self.upgrade_tab.upgrade
                self.map.game_view.player.dump_upgrades()
                self.start_t = time.time() * 1000
                self.t = 0
                self.slide = -1


class ActiveUpgradeTab(arcade.Sprite):

    def __init__(self, upgrade, s_x, s_y, active_tab: ActiveUpgrade):
        super().__init__()
        self.scale = 0.5
        self.texture = ACTIVE_UPGRADE_TAB

        self.hit_box = ((-288, -59), (-288, 59), (288, 59), (288, -59))

        self.upgrade = upgrade
        self.active_tab = active_tab
        self.hover = False

        self.center_x = s_x
        self.center_y = s_y

        self.rel_x = self.center_x - active_tab.center_x
        self.rel_y = self.center_y - active_tab.center_y

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
        if self.active_tab.upgrade_tab == self:
            self.hover = True
        else:
            self.hover = False

    def fix(self):
        for index, text in enumerate(self.all_text):
            text.x = self.center_x + self.text_data[index]['rel_x']
            text.y = self.center_y + self.text_data[index]['rel_y']

    def draw(self):
        for text in self.text:
            text.draw()

        if self.hover:
            for text in self.hover_text:
                text.draw()


class ActiveSelect(arcade.Sprite):

    def __init__(self, map_menu):
        super().__init__()
        self.texture = arcade.load_texture("Sprites/Ui/Select.png")
        self.scale = 0.5

        self.map = map_menu
        self.selected = 1

        self.center_x = map_menu.center_x + map_menu.icon_data[self.selected - 1]['rel_x']
        self.center_y = map_menu.center_y + map_menu.icon_data[self.selected - 1]['rel_y']

    def update_pos(self):
        self.center_x = self.map.center_x + self.map.icon_data[self.selected - 1]['rel_x']
        self.center_y = self.map.center_y + self.map.icon_data[self.selected - 1]['rel_y']


class ShipTab(arcade.Sprite):

    def __init__(self, player_upgrades, game_view, map_menu):
        super().__init__()
        self.scale = 0.5
        self.texture = SHIP_DIM

        self.upgrades = player_upgrades

        self.game = game_view
        self.map = map_menu

        self.center_x = game_view.left_view + SCREEN_WIDTH/2
        self.center_y = game_view.bottom_view - 175/2 + 25

        self.start_y = self.center_y
        self.c = 150
        self.d = 1500
        self.t = 0
        self.s = 0

        self.selected = False
        self.slide = 0

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

        for upgrade in player_upgrades:
            if upgrade['bonus_name'] in self.text:
                edit = self.text[upgrade['bonus_name']]
                edit['num'] += int(upgrade['bonus'] * 100)
            if upgrade['bane_name'] in self.text:
                edit = self.text[upgrade['bane_name']]
                edit['num'] -= int(upgrade['bane'] * 100)

        for text in self.text.values():
            letters = str(int(text['num'])) + "%"
            if -10 < text['num'] < 10:
                letters = '0'+letters

            if text['num'] < 0:
                letters = '-' + letters

            text_list = font.LetterList(letters, self.center_x + text['rel_x'], self.center_y + text['rel_y'], 0.5)
            self.texts.append(text_list)

    def update_animation(self, delta_time: float = 1/60):

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
        if self.slide != 0:
            self.texture = SHIP_TAB
        else:
            self.texture = SHIP_DIM

        super().draw()

        for text in self.texts:
            text.draw()

    def mouse_over(self, check):
        if check and not self.slide:
            self.slide = 1
            self.s = time.time() * 1000
        elif not check and self.slide == 2:
            self.slide = -1
            self.s = time.time() * 1000

    def reapply_text(self):
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
