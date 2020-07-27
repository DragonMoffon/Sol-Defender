import math

import arcade

import vector

SCREEN_WIDTH, SCREEN_HEIGHT = arcade.get_display_size()
GUN_METAL = 50, 59, 63
THRUSTER_BLUE = 0, 195, 255


class Pointer(arcade.Sprite):

    def __init__(self, holder=None, target=None):

        super().__init__()

        self.holder = holder  # The arcade.Sprite that is where the pointer points from
        self.target = target  # The arcade.Sprite that the pointer points to
        self.push_out = 45  # The minimum distance the pointer can be from the holder
        self.texture = arcade.load_texture("Sprites/Enemy Direction.png")  # The pointer's texture
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

    def draw(self):

        # Players Direction and Thruster Direction Physical background
        direction_center_x = self.game_screen.left_view + SCREEN_WIDTH - 45
        direction_center_y = self.game_screen.bottom_view + SCREEN_HEIGHT - 45
        arcade.draw_circle_filled(direction_center_x, direction_center_y,
                                  35, GUN_METAL)
        arcade.draw_point(direction_center_x, direction_center_y, arcade.color.BLACK, 5)

        speed_x = direction_center_x - 69.5
        speed_y = direction_center_y + 19
        arcade.draw_rectangle_filled(speed_x, speed_y, 155, 31, GUN_METAL)

        health_box_x = direction_center_x + 12
        health_box_y = direction_center_y - self.player.max_health/2 - 20
        arcade.draw_rectangle_filled(health_box_x, health_box_y,
                                     45, self.player.max_health + 15 + 35,
                                     GUN_METAL)
        arcade.draw_point(health_box_x, health_box_y, arcade.color.BLACK, 1)

        arcade.draw_circle_outline(direction_center_x, direction_center_y,
                                   35, arcade.color.BLACK)

        # Player Gun Overheating Bar
        heat_width = 15
        heat_height = self.player.heat_level * 100
        heat_x = health_box_x + 10
        heat_y = direction_center_y - 40 - (50 - (((1 - self.player.heat_level) * 100)/2))
        arcade.draw_rectangle_filled(heat_x, heat_y, heat_width, heat_height, arcade.color.ORANGE)

        # Player Health Bar
        health_height = self.player.health
        health_width = 15
        health_x = health_box_x - 10
        health_y = direction_center_y - 40 - (50 - ((self.player.max_health - self.player.health)/2))
        arcade.draw_rectangle_filled(health_x, health_y, health_width, health_height,
                                     arcade.color.RED_DEVIL)

        for y in range(self.player.max_health//10):
            if (y * 10) > self.player.health or not y:
                continue
            line_y = direction_center_y - 40 - (y * 10)
            line_x_1 = health_box_x - 10 + 15/2
            line_x_2 = health_box_x - 10 - 15/2
            arcade.draw_line(line_x_1, line_y, line_x_2, line_y, arcade.color.BLACK, 1)

        # Player Velocity direction and Thrust Direction
        player_pos = self.player.velocity[0], self.player.velocity[1]
        if player_pos[0] or player_pos[1]:
            player_velocity_angle = vector.find_angle(player_pos, (0.0, 0.0))
            angle_rad = math.radians(player_velocity_angle)
            direction_end_x = direction_center_x + (math.cos(angle_rad) * 25)
            direction_end_y = direction_center_y + (math.sin(angle_rad) * 25)
            arcade.draw_line(direction_center_x, direction_center_y,
                             direction_end_x, direction_end_y, arcade.color.WHITE, 5)

        player_pos = self.player.acceleration[0], self.player.acceleration[1]
        if player_pos[0] or player_pos[1]:
            player_velocity_angle = vector.find_angle(player_pos, (0.0, 0.0))
            angle_rad = math.radians(player_velocity_angle)
            direction_end_x = direction_center_x + (math.cos(angle_rad) * 15)
            direction_end_y = direction_center_y + (math.sin(angle_rad) * 15)
            arcade.draw_line(direction_center_x, direction_center_y,
                             direction_end_x, direction_end_y, THRUSTER_BLUE, 3)

        # Player Speed Bar
        speed = math.sqrt(self.player.velocity[0]**2 + self.player.velocity[1]**2) / 25
        if speed < 100:
            speed_x = direction_center_x - 69.5 - 70 + speed/2
            arcade.draw_rectangle_filled(speed_x, speed_y, speed, 15, THRUSTER_BLUE)
        else:
            speed_x = direction_center_x - 69.5 - 70 + 50
            arcade.draw_rectangle_filled(speed_x, speed_y, 100, 15,
                                         (0 + round(speed), 195 + round(speed), 255 + round(speed)))

        speed_x_max = direction_center_x - 69.5 - 70 + 100
        speed_x_min = direction_center_x - 69.5 - 70

        speed_y_1 = speed_y - 15/2
        speed_y_2 = speed_y + 15/2
        arcade.draw_line(speed_x_max, speed_y_1, speed_x_max, speed_y_2, arcade.color.WHITE, 2)
        arcade.draw_line(speed_x_min, speed_y_1, speed_x_min, speed_y_2, arcade.color.WHITE, 2)

        # Player Gun Overheating Bar and Health Outline
        heat_1x = health_box_x + 10 + 15 / 2
        heat_2x = health_box_x + 10 - 15 / 2

        heat_1y = direction_center_y - 40 - 100
        heat_2y = direction_center_y - 40
        arcade.draw_line(heat_1x, heat_1y, heat_2x, heat_1y, arcade.color.WHITE, 2)
        arcade.draw_line(heat_1x, heat_2y, heat_2x, heat_2y, arcade.color.WHITE, 2)

        heat_1x = health_box_x - 10 + 15 / 2
        heat_2x = health_box_x - 10 - 15 / 2

        arcade.draw_line(heat_1x, heat_1y, heat_2x, heat_1y, arcade.color.WHITE, 2)
        arcade.draw_line(heat_1x, heat_2y, heat_2x, heat_2y, arcade.color.WHITE, 2)

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
