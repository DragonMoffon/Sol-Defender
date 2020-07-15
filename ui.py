import math

import arcade

import vector

SCREEN_WIDTH, SCREEN_HEIGHT = arcade.get_display_size()


class Pointer(arcade.Sprite):

    def __init__(self):

        super().__init__()

        self.holder = None  # The arcade.Sprite that is where the pointer points from
        self.target = None  # The arcade.Sprite that the pointer points to
        self.push_out = 45  # The minimum distance the pointer can be from the holder
        self.texture = arcade.load_texture("Sprites/Enemy Direction.png")  # The pointer's texture
        self.scale = 0.15  # The pointer's scale

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

        # Player Gun Overheating Bar Outline
        heat_1x = self.game_screen.left_view + 10
        heat_2x = self.game_screen.left_view + 110

        heat_1y = self.game_screen.bottom_view + 20 + 15/2
        hear_2y = self.game_screen.bottom_view + 20 - 15/2
        arcade.draw_line(heat_1x, heat_1y, heat_1x, hear_2y, arcade.color.WHITE, 2)
        arcade.draw_line(heat_2x, heat_1y, heat_2x, hear_2y, arcade.color.WHITE, 2)

        # Player Gun Overheating Bar
        heat_width = self.player.heat_level * 100
        heat_height = 15
        heat_x = self.game_screen.left_view + 10 + (50 - (((1 - self.player.heat_level) * 100)/2))
        heat_y = self.game_screen.bottom_view + 20
        arcade.draw_rectangle_filled(heat_x, heat_y, heat_width, heat_height, arcade.color.ORANGE)

        # Player Health Bar
        health_width = self.player.health
        health_height = 15
        health_x = self.game_screen.left_view + 10 + (50 - ((self.player.max_health - self.player.health)/2))
        health_y = self.game_screen.bottom_view + SCREEN_HEIGHT - 20
        arcade.draw_rectangle_filled(health_x, health_y, health_width, health_height,
                                     arcade.color.CG_RED)

        for x in range(self.player.max_health//10):
            if x * 10 > self.player.health:
                continue
            line_x = (x * 10) + self.game_screen.left_view + 10
            line_y_1 = self.game_screen.bottom_view + SCREEN_HEIGHT - 20 + 15/2
            line_y_2 = self.game_screen.bottom_view + SCREEN_HEIGHT - 20 - 15/2
            arcade.draw_line(line_x, line_y_1, line_x, line_y_2, arcade.color.BLACK, 1)

        # Players Direction and Thruster Direction
        direction_center_x = self.game_screen.left_view + SCREEN_WIDTH - 45
        direction_center_y = self.game_screen.bottom_view + 45
        arcade.draw_circle_filled(direction_center_x, direction_center_y,
                                  35, arcade.color.ROCKET_METALLIC)
        arcade.draw_point(direction_center_x, direction_center_y, arcade.color.BLACK, 5)

        speed_x = self.game_screen.left_view + SCREEN_WIDTH - 125
        speed_y = self.game_screen.bottom_view + 17
        arcade.draw_rectangle_filled(speed_x + 17, speed_y + 9, 120, 31, arcade.color.ROCKET_METALLIC)

        player_pos = self.player.velocity[0], self.player.velocity[1]
        if player_pos[0] != 0 and player_pos[1]:
            player_velocity_angle = vector.find_angle(player_pos, (0.0, 0.0))
            angle_rad = math.radians(player_velocity_angle)
            direction_end_x = direction_center_x + (math.cos(angle_rad) * 25)
            direction_end_y = direction_center_y + (math.sin(angle_rad) * 25)
            arcade.draw_line(direction_center_x, direction_center_y,
                             direction_end_x, direction_end_y, arcade.color.BLACK, 5)

        player_pos = self.player.acceleration[0], self.player.acceleration[1]
        if player_pos[0] != 0 and player_pos[1] != 0:
            player_velocity_angle = vector.find_angle(player_pos, (0.0, 0.0))
            angle_rad = math.radians(player_velocity_angle)
            direction_end_x = direction_center_x + (math.cos(angle_rad) * 15)
            direction_end_y = direction_center_y + (math.sin(angle_rad) * 15)
            arcade.draw_line(direction_center_x, direction_center_y,
                             direction_end_x, direction_end_y, arcade.color.BLIZZARD_BLUE, 3)

        speed_text = "Speed: " + str(round(math.sqrt(self.player.velocity[0]**2 + self.player.velocity[1]**2)))
        arcade.draw_text(speed_text, speed_x, speed_y, arcade.color.BLACK, anchor_x='center')
