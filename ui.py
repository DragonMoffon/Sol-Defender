import math

import arcade

import vector
import font

SCREEN_WIDTH, SCREEN_HEIGHT = arcade.get_display_size()
GUN_METAL = 50, 59, 63
THRUSTER_BLUE = 0, 195, 255

HEALTH_BAR = "Sprites/Player/Ui/health_bar.png"
HEAT_BAR = "Sprites/Player/Ui/heat_bar.png"
BAR_FRAME = "Sprites/Player/Ui/bar_frame.png"


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

        self.influence_warnings = None

        self.ui_list = arcade.SpriteList()
        self.health_bar = arcade.Sprite(HEALTH_BAR)
        self.ui_list.append(self.health_bar)
        self.health_frame = arcade.Sprite(BAR_FRAME)
        self.ui_list.append(self.health_frame)

        self.heat_textures = []
        self.health_textures = []
        for y in range(10):
            for x in range(10):
                texture = arcade.load_texture(HEAT_BAR, x * 15, y * 100, 15, 100)
                self.heat_textures.append(texture)
                texture = arcade.load_texture(HEALTH_BAR, x * 15, y * 100, 15, 100)
                self.health_textures.append(texture)
        self.health_textures.append(arcade.load_texture('Sprites/Player/Ui/health_bar_full.png'))
        self.heat_textures.append(arcade.load_texture("Sprites/Player/Ui/heat_bar_full.png"))
        self.heat_bar = arcade.Sprite()
        self.heat_bar.angle = 90
        self.heat_frame = arcade.Sprite(BAR_FRAME)
        self.heat_frame.angle = 90
        self.ui_list.append(self.heat_bar)
        self.ui_list.append(self.heat_frame)

        self.transparency = 255

        self.mini_map = None

        self.overheating_sound = arcade.Sound("Music/A legit warning sound.wav", True)
        self.overheat_volume = 0
        self.overheating_sound.play(self.overheat_volume)

        self.top_left_sprite = arcade.Sprite("Sprites/Player/Ui/ui_top_left.png")
        self.top_right_sprite = arcade.Sprite("Sprites/Player/Ui/ui_top_right.png")

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
        heat_height = round(self.player.heat_level * 100)
        self.heat_bar.texture = self.heat_textures[heat_height]
        heat_pos = (self.game_screen.left_view + SCREEN_WIDTH - 140, self.game_screen.bottom_view + SCREEN_HEIGHT - 20)
        self.heat_bar.center_x, self.heat_bar.center_y = heat_pos
        self.heat_frame.center_x, self.heat_frame.center_y = heat_pos

        # Player Health Bar
        health_height = round((self.player.health / self.player.max_health) * 100)
        self.health_bar.texture = self.health_textures[health_height]
        health_pos = (self.game_screen.left_view + SCREEN_WIDTH - 20,
                      self.game_screen.bottom_view + SCREEN_HEIGHT - 140)
        self.health_bar.center_x, self.health_bar.center_y = health_pos
        self.health_frame.center_x, self.health_frame.center_y = health_pos

        # Gravity Lines
        if len(self.player.gravity_influences):
            point_list = (
                         (self.game_screen.left_view, self.game_screen.bottom_view),
                         (self.game_screen.left_view, self.game_screen.bottom_view + 125),
                         (self.game_screen.left_view + 50, self.game_screen.bottom_view + 125),
                         (self.game_screen.left_view + 125, self.game_screen.bottom_view + 50),
                         (self.game_screen.left_view + 125, self.game_screen.bottom_view)
                         )
            arcade.draw_polygon_filled(point_list, GUN_METAL)

            center_x = self.game_screen.left_view + 50
            center_y = self.game_screen.bottom_view + 50
            arcade.draw_circle_filled(center_x, center_y, 45, GUN_METAL)
            arcade.draw_circle_outline(center_x, center_y, 45, arcade.color.BLACK)
            for influences in self.player.gravity_influences:
                direction = math.radians(vector.find_angle(influences, (0.0, 0.0)))
                mag = math.sqrt(influences[0]**2 + influences[1]**2)
                if mag < 40 / 25:
                    e_x = center_x + (math.cos(direction) * mag * 25)
                    e_y = center_y + (math.sin(direction) * mag * 25)
                else:
                    e_x = center_x + (math.cos(direction) * 40)
                    e_y = center_y + (math.sin(direction) * 40)

                arcade.draw_line(center_x, center_y, e_x, e_y, THRUSTER_BLUE)

            direction = math.radians(vector.find_angle(self.player.gravity_acceleration, (0.0, 0.0)))
            mag = math.sqrt(self.player.gravity_acceleration[0] ** 2 + self.player.gravity_acceleration[1] ** 2)
            if mag < 40 / 25:
                e_x = center_x + (math.cos(direction) * mag * 25)
                e_y = center_y + (math.sin(direction) * mag * 25)
            else:
                e_x = center_x + (math.cos(direction) * 40)
                e_y = center_y + (math.sin(direction) * 40)
            arcade.draw_line(center_x, center_y, e_x, e_y, arcade.color.ORANGE)

        top_right_corner = (SCREEN_WIDTH - 105, SCREEN_HEIGHT - 105)
        self.top_right_sprite.center_x = self.game_screen.left_view + top_right_corner[0]
        self.top_right_sprite.center_y = self.game_screen.bottom_view + top_right_corner[1]

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

        credit_text = font.gen_letter_list(credit, credit_text[0], credit_text[1])
        scrap_text = font.gen_letter_list(scrap, scrap_text[0], scrap_text[1])

        self.top_left_sprite.center_x = self.game_screen.left_view + top_left_corner[0]
        self.top_left_sprite.center_y = self.game_screen.bottom_view + top_left_corner[1]

        self.top_left_sprite.draw()
        self.top_right_sprite.draw()
        credit_text.draw()
        scrap_text.draw()

        self.ui_list.draw()
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
        # Thruster Visuals
        back_angle = self.player.angle + 180
        rad_back = math.radians(back_angle)

        width_1 = self.player.thrusters_output[0] * 15
        height_1 = 3
        d_1 = 20.81

        if self.player.thrusters_output[0] > 0:
            a_1 = rad_back + math.radians(54.78)
            x_1 = self.player.center_x + math.cos(a_1) * d_1 + (math.cos(rad_back) * (width_1 / 2))
            y_1 = self.player.center_y + math.sin(a_1) * d_1 + (math.sin(rad_back) * (width_1 / 2))
            arcade.draw_rectangle_filled(x_1, y_1, width_1, height_1, arcade.color.ORANGE, 360 - back_angle)
        elif self.player.thrusters_output[0] < 0:
            a_1 = rad_back - math.radians(54.78)
            x_1 = self.player.center_x + math.cos(a_1) * d_1 - (math.cos(rad_back) * (width_1 / 2))
            y_1 = self.player.center_y + math.sin(a_1) * d_1 - (math.sin(rad_back) * (width_1 / 2))
            arcade.draw_rectangle_filled(x_1, y_1, width_1, height_1, arcade.color.ORANGE, 360 - back_angle)
        else:
            a_1 = rad_back + math.radians(54.78)
            x_1 = self.player.center_x + math.cos(a_1) * d_1
            y_1 = self.player.center_y + math.sin(a_1) * d_1
            arcade.draw_point(x_1, y_1, arcade.color.RADICAL_RED, 2)
            a_1 = rad_back - math.radians(54.78)
            x_1 = self.player.center_x + math.cos(a_1) * d_1
            y_1 = self.player.center_y + math.sin(a_1) * d_1
            arcade.draw_point(x_1, y_1, arcade.color.RADICAL_RED, 2)

        width_1 = self.player.thrusters_output[1] * 10

        if self.player.thrusters_output[1]:
            a_2 = rad_back + math.radians(49.76)
            d_2 = 17.03
            x_2 = self.player.center_x + math.cos(a_2) * d_2 + (math.cos(rad_back) * (width_1 / 2))
            y_2 = self.player.center_y + math.sin(a_2) * d_2 + (math.sin(rad_back) * (width_1 / 2))
            arcade.draw_rectangle_filled(x_2, y_2, width_1, height_1, THRUSTER_BLUE, 360 - back_angle)

            a_2 = rad_back - math.radians(49.76)
            d_2 = 17.03
            x_2 = self.player.center_x + math.cos(a_2) * d_2 + (math.cos(rad_back) * (width_1 / 2))
            y_2 = self.player.center_y + math.sin(a_2) * d_2 + (math.sin(rad_back) * (width_1 / 2))
            arcade.draw_rectangle_filled(x_2, y_2, width_1, height_1, THRUSTER_BLUE, 360 - back_angle)

            a_3 = rad_back + math.radians(30.96)
            d_3 = 11.66
            x_3 = self.player.center_x + math.cos(a_3) * d_3 + (math.cos(rad_back) * (width_1 / 2))
            y_3 = self.player.center_y + math.sin(a_3) * d_3 + (math.sin(rad_back) * (width_1 / 2))
            arcade.draw_rectangle_filled(x_3, y_3, width_1, height_1, THRUSTER_BLUE, 360 - back_angle)

            a_3 = rad_back - math.radians(30.96)
            d_3 = 11.66
            x_3 = self.player.center_x + math.cos(a_3) * d_3 + (math.cos(rad_back) * (width_1 / 2))
            y_3 = self.player.center_y + math.sin(a_3) * d_3 + (math.sin(rad_back) * (width_1 / 2))
            arcade.draw_rectangle_filled(x_3, y_3, width_1, height_1, THRUSTER_BLUE, 360 - back_angle)


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

        self.game_view = game_screen
        self.screen_scale = 1.5

        if self.planet is not None:
            self.planet_scale = 0.5  # (self.planet.width / (250 / self.screen_scale)) / 64
            self.divisor = (self.screen_scale * self.planet.width) / (self.planet_scale * 64)
        else:
            self.planet_scale = 1

        self.screen_frame_x = SCREEN_WIDTH - (self.screen_scale * 165 / 2)
        self.screen_frame_y = self.screen_scale * 135 / 2
        self.screen = arcade.Sprite("Sprites/Minimap/map/minimap_screen.png", scale=self.screen_scale)
        self.append(self.screen)

        self.planet_sprite = arcade.Sprite("Sprites/Minimap/space/planet.png", scale=self.planet_scale)
        self.append(self.planet_sprite)

        self.player_textures = (arcade.load_texture("Sprites/Minimap/player/location.png"),
                                arcade.load_texture("Sprites/Minimap/player/off_map.png"))
        self.player_sprite = arcade.Sprite("Sprites/Minimap/player/location.png", scale=self.planet_scale)
        self.append(self.player_sprite)

        self.enemy_sprites = None
        self.satellite_sprites = None

        self.screen_frame = arcade.Sprite("Sprites/Minimap/map/minimap.png",
                                          center_x=SCREEN_WIDTH / 2, center_y=SCREEN_HEIGHT / 2,
                                          scale=self.screen_scale)
        self.append(self.screen_frame)

    def draw(self):
        self.screen_frame.center_x = self.game_view.left_view + self.screen_frame_x
        self.screen_frame.center_y = self.game_view.bottom_view + self.screen_frame_y
        self.screen.center_x = self.game_view.left_view + self.screen_frame_x
        self.screen.center_y = self.game_view.bottom_view + self.screen_frame_y

        self.planet_sprite.center_x = self.screen_frame.center_x + (5 * self.screen_scale)
        self.planet_sprite.center_y = self.screen_frame.center_y - (5 * self.screen_scale)

        player_pos = self.define_pos(self.player)
        changed = False
        if player_pos[0] > self.planet_sprite.center_x + ((160 * self.screen_scale) / 2):
            player_pos[0] = self.planet_sprite.center_x + ((160 * self.screen_scale) / 2)
            changed = True
        elif player_pos[0] < self.planet_sprite.center_x - ((160 * self.screen_scale) / 2):
            player_pos[0] = self.planet_sprite.center_x - ((160 * self.screen_scale) / 2)
            changed = True
            self.player_sprite.angle = 180

        if player_pos[1] > self.planet_sprite.center_y + ((130 * self.screen_scale) / 2):
            player_pos[1] = self.planet_sprite.center_y + ((130 * self.screen_scale) / 2)
            changed = True
            self.player_sprite.angle = 270
        elif player_pos[1] < self.planet_sprite.center_y - ((130 * self.screen_scale) / 2):
            player_pos[1] = self.planet_sprite.center_y - ((130 * self.screen_scale) / 2)
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
                if self.planet_sprite.center_x - ((160 * self.screen_scale) / 2) <\
                            pos[0] < self.planet_sprite.center_x + ((160 * self.screen_scale) / 2):
                    sprite = arcade.Sprite("Sprites/Minimap/enemy/position.png", scale=self.planet_scale,
                                           center_x=pos[0], center_y=pos[1])
                    self.enemy_sprites.append(sprite)

        self.enemy_sprites.draw()

    def satellite_draw(self):
        self.satellite_sprites = arcade.SpriteList()
        for satellite in self.planet.satellites:
            pos = self.define_pos(satellite)
            if satellite.subset == "moon":
                sprite = arcade.Sprite("Sprites/Minimap/space/moon.png", scale=self.planet_scale,
                                       center_x=pos[0], center_y=pos[1])
            else:
                sprite = arcade.Sprite("Sprites/Minimap/space/satellite.png", scale=self.planet_scale,
                                       center_x=pos[0], center_y=pos[1])
            self.satellite_sprites.append(sprite)

        self.satellite_sprites.draw()

    def define_pos(self, target):
        x_diff = (target.center_x - self.mission.curr_planet.center_x) / (self.divisor / self.screen_scale)
        y_diff = (target.center_y - self.mission.curr_planet.center_y) / (self.divisor / self.screen_scale)
        x_pos = self.planet_sprite.center_x + x_diff
        y_pos = self.planet_sprite.center_y + y_diff

        return [x_pos, y_pos]
