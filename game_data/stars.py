import random

import arcade

SCREEN_WIDTH, SCREEN_HEIGHT = arcade.get_display_size()

#
# The classes and functions needed to create a multi-layered parallax set of stars
#
# StarField - Creates each layer of the stars and interacts with the rest of the game.
#
# StarList - Is an individual layer of stars. It handles spawning it's own stars and moving them at a specific speed.
#
# Star - an individual star that holds all necessary data.
#


class StarField:

    def __init__(self, game_view, true_move: bool = True):
        """
        A three layered set of stars that creates an endless scrolling parallax background.

        :param game_view: The Game View that runs the main game. It also holds the position of the screen.
        :param true_move: Whether or not the game actually is moving or whether the movement data is created.
        """
        self.game_view = game_view

        # The line coordinates for spawning stars, and killing stars.
        self.LINE_X = [game_view.left_view - 80, game_view.left_view + SCREEN_WIDTH + 80]
        self.LINE_Y = [game_view.bottom_view - 80, game_view.bottom_view + SCREEN_HEIGHT + 80]
        self.LINES = (self.LINE_X, self.LINE_Y)

        # Variables derived from the LINE X and Y for spawning and killing stars.
        self.kill_x = 0
        self.kill_y = 0
        self.spawn_x = 0
        self.spawn_y = 0

        # The three layers of the parallax stars.
        self.close_list = StarList(0.85, self, game_view)
        self.med_list = StarList(0.9, self, game_view)
        self.far_list = StarList(0.95, self, game_view)

        # Whether true move is on.
        self.true_move = true_move

    def draw(self):
        # draws all of the layers
        self.close_list.draw()
        self.med_list.draw()
        self.far_list.draw()

    def on_update(self, d_camera):
        """
        The Update Function.
        Recalculates the Line X and Y, then updates the StarLists.

        :param d_camera: The movement of the view each update. is an (x, y) tuple
        """

        # Recalculates the LINE X and Y
        self.LINE_X = [self.game_view.left_view - 80, self.game_view.left_view + SCREEN_WIDTH + 80]
        self.LINE_Y = [self.game_view.bottom_view - 80, self.game_view.bottom_view + SCREEN_HEIGHT + 80]
        self.LINES = (self.LINE_X, self.LINE_Y)

        # Calculates the killing coordinates and the spawning coordinates
        if d_camera[0] > 0:
            # If moving forwards.
            self.kill_x = self.LINE_X[0]
            self.spawn_x = self.LINE_X[1]
        elif d_camera[0] < 0:
            # If moving backwards.
            self.kill_x = self.LINE_X[1]
            self.spawn_x = self.LINE_X[0]
        else:
            # If not moving horizontally.
            self.kill_x = 0
            self.spawn_x = 0

        if d_camera[1] > 0:
            # If moving upwards.
            self.kill_y = self.LINE_Y[0]
            self.spawn_y = self.LINE_Y[1]
        elif d_camera[1] < 0:
            # If moving downwards.
            self.kill_y = self.LINE_Y[1]
            self.spawn_y = self.LINE_Y[0]
        else:
            # If not moving vertically
            self.kill_y = 0
            self.spawn_y = 0

        # Splitting the d_camera into two variables
        d_x = d_camera[0]
        d_y = d_camera[1]
        if not self.true_move:
            # If true_move is false, flip the input.
            d_x *= -1
            d_y *= -1

        # Move the Layers.
        self.close_list.move(d_x, d_y)
        self.med_list.move(d_x, d_y)
        self.far_list.move(d_x, d_y)

        # Update the Layers.
        self.close_list.update()
        self.med_list.update()
        self.far_list.update()


class StarList(arcade.SpriteList):

    def __init__(self, modifier, star_field: StarField = None, game_view=None):
        """
        A Single Layer of the StarField. Manages the spawning and killing of it's own stars.

        :param modifier: A modifier that slows the stars down.
        :param star_field: The creator of the StarList
        :param game_view: The Game View,
        """
        super().__init__()
        self.modifier = modifier
        self.star_field = star_field
        self.game_view = game_view

        # The maximum number of stars it will be in the Layer.
        self.max_stars = 120

        # The change in x and y if the stars on the Layer.
        self.change_x = 0
        self.change_y = 0

        # Setup Layer.
        self.setup()

    def setup(self):
        """
        Spawns a star until the layer holds the maximum number of stars.
        """

        while len(self) != self.max_stars:
            # Choose random x and y position
            x = random.uniform(self.game_view.left_view - 80,
                               self.game_view.left_view + SCREEN_WIDTH + 80)
            y = random.uniform(self.game_view.bottom_view - 80,
                               self.game_view.bottom_view + SCREEN_WIDTH + 80)

            # create and append star.
            star = Star(x, y)
            self.append(star)

    def move(self, change_x: float, change_y: float):
        # modify the change_x and change_y using the predefined modifier before moving all of the stars.
        change_x *= self.modifier
        change_y *= self.modifier
        super().move(change_x, change_y)

    def update(self):
        """
        The Update Function.
        Kills all of the stars that are past the kill lines. Then spawns new stars on the spawn lines.

        """

        # Kills the stars.
        safe_copy = self
        for stars in safe_copy:
            kill = False
            # kills the stars on the X axis
            if self.star_field.kill_x == self.star_field.LINE_X[0]:
                if stars.center_x <= self.star_field.kill_x:
                    kill = True

            elif self.star_field.kill_x == self.star_field.LINE_X[1]:
                if stars.center_x >= self.star_field.kill_x:
                    kill = True

            # kills stars on the Y axis
            if self.star_field.kill_y == self.star_field.LINE_Y[0]:
                if stars.center_y <= self.star_field.kill_y:
                    kill = True

            elif self.star_field.kill_y == self.star_field.LINE_Y[1]:
                if stars.center_y >= self.star_field.kill_y:
                    kill = True

            if kill:
                stars.remove_from_sprite_lists()
                del stars

        # Spawns stars.
        total = 0
        while len(self) < self.max_stars:
            total += 1
            # picks either line_x or line_y.
            pick = random.randint(0, 1)
            chosen_line = self.star_field.LINES[pick]

            if chosen_line == self.star_field.LINE_Y and self.star_field.spawn_x != 0:
                # If the pick is the Y line, randomly choose the stars Y position and then set its x to spawn_x.
                x = self.star_field.spawn_x
                y = random.uniform(chosen_line[0], chosen_line[1])
                star = Star(x, y)
                self.append(star)
            elif chosen_line == self.star_field.LINE_X and self.star_field.spawn_y != 0:
                # If the pick is the X line, randomly choose the stars X position and then set its y to spawn_y
                x = random.uniform(chosen_line[0], chosen_line[1])
                y = self.star_field.spawn_y
                star = Star(x, y)
                self.append(star)
            elif chosen_line == self.star_field.LINE_Y and self.star_field.spawn_x == 0:
                # If the chosen line is LINE_Y but there is not spawn_x flip the spawning.
                chosen_line = self.star_field.LINE_X
                x = random.uniform(chosen_line[0], chosen_line[1])
                y = self.star_field.spawn_y
                star = Star(x, y)
                self.append(star)
            elif chosen_line == self.star_field.LINE_X and self.star_field.spawn_y == 0:
                # If the chosen line is LINE_X but there is no spawn_y flip the spawning.
                chosen_line = self.star_field.LINE_Y
                x = self.star_field.spawn_x
                y = random.uniform(chosen_line[0], chosen_line[1])
                star = Star(x, y)
                self.append(star)
            if total > 2:
                # if more than two stars have spawned stop.
                break


class Star(arcade.Sprite):

    def __init__(self, x, y):
        """
        A star with a random scale. Is found only within each layer of the StarField.
        :param x: The X position of the star at spawn.
        :param y: The Y position of the star at spawn.
        """
        super().__init__()
        self.texture = arcade.load_texture("game_data/Sprites/circles/circle_white.png")
        self.scale = random.uniform(0.002, 0.02)
        self.center_x = x
        self.center_y = y
