import random

import arcade

SCREEN_WIDTH, SCREEN_HEIGHT = arcade.get_display_size()


class StarField:

    def __init__(self, game_view, true_move: bool = True):
        self.game_view = game_view

        self.LINE_X = [game_view.left_view - 80, game_view.left_view + SCREEN_WIDTH + 80]
        self.LINE_Y = [game_view.bottom_view - 80, game_view.bottom_view + SCREEN_HEIGHT + 80]
        self.LINES = (self.LINE_X, self.LINE_Y)
        self.kill_x = 0
        self.kill_y = 0
        self.spawn_x = 0
        self.spawn_y = 0

        self.close_list = StarList(0.85, self, game_view)
        self.med_list = StarList(0.9, self, game_view)
        self.far_list = StarList(0.95, self, game_view)

        self.true_move = true_move

    def draw(self):
        self.close_list.draw()
        self.med_list.draw()
        self.far_list.draw()

    def on_update(self, d_camera):
        self.LINE_X = [self.game_view.left_view - 80, self.game_view.left_view + SCREEN_WIDTH + 80]
        self.LINE_Y = [self.game_view.bottom_view - 80, self.game_view.bottom_view + SCREEN_HEIGHT + 80]
        self.LINES = (self.LINE_X, self.LINE_Y)

        if d_camera[0] > 0:
            self.kill_x = self.LINE_X[0]
            self.spawn_x = self.LINE_X[1]
        elif d_camera[0] < 0:
            self.kill_x = self.LINE_X[1]
            self.spawn_x = self.LINE_X[0]
        else:
            self.kill_x = 0
            self.spawn_x = 0

        if d_camera[1] > 0:
            self.kill_y = self.LINE_Y[0]
            self.spawn_y = self.LINE_Y[1]
        elif d_camera[1] < 0:
            self.kill_y = self.LINE_Y[1]
            self.spawn_y = self.LINE_Y[0]
        else:
            self.kill_y = 0
            self.spawn_y = 0

        d_x = d_camera[0]
        d_y = d_camera[1]
        if not self.true_move:
            d_x *= -1
            d_y *= -1
        self.close_list.move(d_x, d_y)
        self.med_list.move(d_x, d_y)
        self.far_list.move(d_x, d_y)

        self.close_list.update()
        self.med_list.update()
        self.far_list.update()


class StarList(arcade.SpriteList):

    def __init__(self, modifier, star_field: StarField = None, game_view: arcade.View = None):
        super().__init__()
        self.modifier = modifier
        self.star_field = star_field
        self.game_view = game_view

        self.max_stars = 120

        self.change_x = 0
        self.change_y = 0

        self.setup()

    def setup(self):
        while len(self) != self.max_stars:
            x = random.randint(self.star_field.LINE_X[0], self.star_field.LINE_X[1])
            y = random.randint(self.star_field.LINE_Y[0], self.star_field.LINE_Y[1])
            star = Star(x, y)
            self.append(star)

    def move(self, change_x: float, change_y: float):
        change_x *= self.modifier
        change_y *= self.modifier
        super().move(change_x, change_y)

    def update(self):
        safe_copy = self
        for stars in safe_copy:
            kill = False
            if self.star_field.kill_x == self.star_field.LINE_X[0]:
                if stars.center_x <= self.star_field.kill_x:
                    kill = True

            elif self.star_field.kill_x == self.star_field.LINE_X[1]:
                if stars.center_x >= self.star_field.kill_x:
                    kill = True

            if self.star_field.kill_y == self.star_field.LINE_Y[0]:
                if stars.center_y <= self.star_field.kill_y:
                    kill = True

            elif self.star_field.kill_y == self.star_field.LINE_Y[1]:
                if stars.center_y >= self.star_field.kill_y:
                    kill = True

            if kill:
                stars.remove_from_sprite_lists()
                del stars

        total = 0
        while len(self) < self.max_stars:
            total += 1
            pick = random.randint(0, 1)
            chosen_line = self.star_field.LINES[pick]
            if chosen_line == self.star_field.LINE_Y and self.star_field.spawn_x != 0:
                x = self.star_field.spawn_x
                y = random.uniform(chosen_line[0], chosen_line[1])
                star = Star(x, y)
                self.append(star)
            elif chosen_line == self.star_field.LINE_X and self.star_field.spawn_y != 0:
                x = random.uniform(chosen_line[0], chosen_line[1])
                y = self.star_field.spawn_y
                star = Star(x, y)
                self.append(star)
            elif chosen_line == self.star_field.LINE_Y and self.star_field.spawn_y == 0:
                chosen_line = self.star_field.LINE_X
                x = random.uniform(chosen_line[0], chosen_line[1])
                y = self.star_field.spawn_y
                star = Star(x, y)
                self.append(star)
            elif chosen_line == self.star_field.LINE_X and self.star_field.spawn_x == 0:
                chosen_line = self.star_field.LINE_Y
                x = self.star_field.spawn_x
                y = random.uniform(chosen_line[0], chosen_line[1])
                star = Star(x, y)
                self.append(star)
            if total > 9:
                break


class Star(arcade.Sprite):

    def __init__(self, x, y):
        super().__init__()
        self.texture = arcade.load_texture("Sprites/circles/circle_white.png")
        self.scale = random.uniform(0.002, 0.02)
        self.center_x = x
        self.center_y = y
