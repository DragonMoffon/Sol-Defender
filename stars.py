import random

import arcade


class StarListsField:
    
    def __init__(self, holder, modifier):
        self.screen_size = arcade.get_display_size()

        self.star_lists = [StarList(self)]
        
        self.movement_x = 0
        self.movement_y = 0

        self.holder = holder

        self.modifier = modifier
        
    def on_update(self, camera_movement: tuple = (0.0, 0.0)):
        self.movement_x, self.movement_y = camera_movement[0] * self.modifier, camera_movement[1] * self.modifier

        close_copy = self.star_lists
        for index, lists in enumerate(close_copy):
            lists.calc_field_sides()

            if lists.center_on_screen:
                lists.all_false()
                for other_lists in self.star_lists:
                    if other_lists.center_x > lists.center_x and \
                            other_lists.center_y > lists.center_y:
                        lists.stars_tr = True

                    if other_lists.center_x < lists.center_x and \
                            other_lists.center_y > lists.center_y:
                        lists.stars_tl = True

                    if other_lists.center_x > lists.center_x and \
                            other_lists.center_y < lists.center_y:
                        lists.stars_br = True

                    if other_lists.center_x < lists.center_x and \
                            other_lists.center_y < lists.center_y:
                        lists.stars_bl = True

                    if other_lists.center_x > lists.center_x and \
                            other_lists.center_y == lists.center_y:
                        lists.stars_r = True

                    if other_lists.center_x < lists.center_x and \
                            other_lists.center_y == lists.center_y:
                        lists.stars_l = True

                    if other_lists.center_x == lists.center_x and \
                            other_lists.center_y > lists.center_y:
                        lists.stars_t = True

                    if other_lists.center_x == lists.center_x and \
                            other_lists.center_y < lists.center_y:
                        lists.stars_b = True

                # If there is no star to the top or right of center make a corner star to the top right
                if lists.stars_tr is False and camera_movement[0] >= 0 and camera_movement[1] >= 0:
                    star_list = StarList(self,
                                         lists.center_x + lists.base_field_size[0],
                                         lists.center_y + lists.base_field_size[1])
                    self.star_lists.append(star_list)
                    lists.stars_tr = True

                # If there is no star to the top or left of center make a corner star to the top left
                if lists.stars_tl is False and camera_movement[0] <= 0 and camera_movement[1] >= 0:
                    star_list = StarList(self,
                                         lists.center_x - lists.base_field_size[0],
                                         lists.center_y + lists.base_field_size[1])
                    self.star_lists.append(star_list)
                    self.star_lists[-1].creator = self.star_lists[index]
                    lists.stars_tl = True

                # If there is no star to the bottom or right of center make a corner star to the bottom right
                if lists.stars_br is False and camera_movement[0] >= 0 and camera_movement[1] <= 0:
                    star_list = StarList(self,
                                         lists.center_x + lists.base_field_size[0],
                                         lists.center_y - lists.base_field_size[1])
                    self.star_lists.append(star_list)
                    self.star_lists[-1].creator = self.star_lists[index]
                    lists.stars_br = True

                # If there is no star to the bottom or left of center make a corner star to the bottom left
                if lists.stars_bl is False and camera_movement[0] <= 0 and camera_movement[1] <= 0:
                    star_list = StarList(self,
                                         lists.center_x - lists.base_field_size[0],
                                         lists.center_y - lists.base_field_size[1])
                    self.star_lists.append(star_list)
                    self.star_lists[-1].creator = self.star_lists[index]
                    lists.stars_bl = True

                # If there is no list to the right make a new list to the right
                if lists.stars_r is False and camera_movement[0] > 0:
                    star_list = StarList(self,
                                         lists.center_x + lists.base_field_size[0],
                                         lists.center_y)
                    self.star_lists.append(star_list)
                    self.star_lists[-1].creator = self.star_lists[index]
                    lists.stars_r = True

                # If there is no list to the left make a new list to the left
                if lists.stars_l is False and camera_movement[0] < 0:
                    star_list = StarList(self,
                                         lists.center_x - lists.base_field_size[0],
                                         lists.center_y)
                    self.star_lists.append(star_list)
                    self.star_lists[-1].creator = self.star_lists[index]
                    lists.stars_l = True

                # If there is no list above make a new list above
                if lists.stars_t is False and camera_movement[1] > 0:
                    star_list = StarList(self,
                                         lists.center_x,
                                         lists.center_y + lists.base_field_size[1])
                    self.star_lists.append(star_list)
                    self.star_lists[-1].creator = self.star_lists[index]
                    lists.stars_t = True

                # If there is no list bellow make a new list bellow
                if lists.stars_b is False and camera_movement[1] < 0:
                    star_list = StarList(self,
                                         lists.center_x,
                                         lists.center_y - lists.base_field_size[1])
                    self.star_lists.append(star_list)
                    self.star_lists[-1].creator = self.star_lists[index]
                    lists.stars_b = True

            if lists.right_side < self.holder.left_view and camera_movement[0] > 0:
                self.star_lists.remove(lists)
            elif lists.left_side > self.holder.left_view + self.screen_size[0] and camera_movement[0] < 0:
                self.star_lists.remove(lists)

            elif lists.top_side < self.holder.bottom_view and camera_movement[1] > 0:
                self.star_lists.remove(lists)
            elif lists.bottom_side > self.holder.bottom_view + self.screen_size[1] and camera_movement[1] < 0:
                self.star_lists.remove(lists)

        for lists in self.star_lists:
            lists.change_x = self.movement_x
            lists.change_y = self.movement_y
            lists.update()

    def draw(self):
        for star_lists in self.star_lists:
            star_lists.draw()
        

class StarList(arcade.SpriteList):

    def __init__(self, holder,
                 center_x=None, center_y=None,
                 size_x: float = arcade.get_display_size()[0], size_y: float = arcade.get_display_size()[1],
                 skip_side: tuple = (0, 0, 0, 0)):
        super().__init__()

        self.base_field_size = (round_to_80(size_x),
                                round_to_80(size_y))

        self.creator = None

        self.stars_t = False
        self.stars_b = False

        self.stars_l = False
        self.stars_r = False

        self.stars_tr = False
        self.stars_tl = False

        self.stars_br = False
        self.stars_bl = False

        self.center_on_screen = False

        self.skip_side = skip_side
        self.lost_side = [0, 0, 0, 0]

        if center_x is not None:
            self.center_x = center_x
        else:
            self.center_x = arcade.get_display_size()[0]/2

        if center_y is not None:
            self.center_y = center_y
        else:
            self.center_y = arcade.get_display_size()[1]/2

        self.top_side = self.center_y
        self.bottom_side = self.center_y
        self.left_side = self.center_x
        self.right_side = self.center_x

        self.holder = holder

        self.change_y = 0
        self.change_x = 0

        self.setup_stars()

    def all_false(self):
        self.stars_t = False
        self.stars_b = False

        self.stars_l = False
        self.stars_r = False

        self.stars_tr = False
        self.stars_tl = False

        self.stars_br = False
        self.stars_bl = False

    def update(self):
        self.center_x += self.change_x
        self.center_y += self.change_y
        for stars in self:
            stars.change_x = self.change_x
            stars.change_y = self.change_y
            stars.update()

    def draw(self):
        super().draw()

    def setup_stars(self):
        start_x = int(self.center_x - (self.base_field_size[0]//2))
        start_y = int(self.center_y - (self.base_field_size[1]//2))
        end_x = int(self.center_x + (self.base_field_size[0]//2))
        end_y = int(self.center_y + self.base_field_size[1]//2)

        if self.skip_side[0]:
            start_x += 80
            self.lost_side[0] = 1
        if self.skip_side[1]:
            start_y += 80
            self.lost_side[1] = 1
        if self.skip_side[2]:
            end_x -= 80
            self.lost_side[2] = 1
        if self.skip_side[3]:
            end_y -= 80
            self.lost_side[3] = 1

        for x in range(start_x, end_x + 1, 80):
            for y in range(start_y, end_y + 1, 80):
                self.make_gridded_star(x, y)

    def give_edge(self, direction):
        if direction == 1:
            for y in range(self.bottom_side, self.top_side + 1, 80):
                self.make_gridded_star(self.left_side - 80, y)
        elif direction == 2:
            for x in range(self.left_side, self.right_side + 1, 80):
                self.make_gridded_star(x, self.bottom_side - 80)
        elif direction == 3:
            for y in range(self.bottom_side, self.top_side + 1, 80):
                self.make_gridded_star(self.right_side + 80, y)
        elif direction == 4:
            for x in range(self.left_side, self.right_side + 1, 80):
                self.make_gridded_star(x, self.top_side + 80)

    def calc_field_sides(self):
        true_holder = self.holder.holder

        self.bottom_side = self.center_y
        self.top_side = self.center_y

        self.left_side = self.center_x
        self.left_side = self.center_x

        if true_holder.left_view < self.center_x < true_holder.left_view + self.holder.screen_size[0]\
                and true_holder.bottom_view < self.center_y < true_holder.bottom_view + self.holder.screen_size[1]:
            self.center_on_screen = True
        else:
            self.center_on_screen = False

        for stars in self:
            if stars.core_y < self.bottom_side:
                self.bottom_side = stars.core_y
            elif stars.core_y > self.top_side:
                self.top_side = stars.core_y

            if stars.core_x < self.left_side:
                self.left_side = stars.core_x
            elif stars.core_x > self.right_side:
                self.right_side = stars.core_x

    def make_gridded_star(self, x, y):
        s_x = x + random.randint(-40, 40)
        s_y = y + random.randint(-40, 40)
        star = self.make_star((s_x, s_y))
        star.core_x = x
        star.core_y = y

        self.append(star)

    def make_star(self, spawn_pos: tuple = (0.0, 0.0)):
        star = StarBody()
        star.center_x = spawn_pos[0]
        star.center_y = spawn_pos[1]
        star.change_y = 0
        star.change_x = 0
        star.core_x = spawn_pos[0]
        star.core_y = spawn_pos[1]
        star.holder = self.holder

        return star


class StarBody(arcade.Sprite):

    def __init__(self):
        super().__init__()
        self.texture = arcade.load_texture("Sprites/circle_white.png")
        self.scale = round(random.uniform(0.005, 0.02), 3)

        self.core_x = 0
        self.core_y = 0
        self.core_star = None

        self.spawned = False
        self.spawned_x = False
        self.spawned_y = False

    def update(self):
        self.core_x += self.change_x
        self.core_y += self.change_y

        super().update()


class StarField:

    def __init__(self):
        self.screen_size = arcade.get_display_size()

        self.close_lists = None
        self.med_lists = None
        self.far_lists = None

        self.holder = None

        self.camera_dx = 0
        self.camera_dy = 0

    def setup(self, holder):
        self.holder = holder
        self.close_lists = StarListsField(holder, 0.85)
        self.med_lists = StarListsField(holder, 0.9)
        self.far_lists = StarListsField(holder, 0.95)

    def on_update(self, camera_movement: tuple = (0.0, 0.0)):
        self.close_lists.on_update(camera_movement)
        self.med_lists.on_update(camera_movement)
        self.far_lists.on_update(camera_movement)

    def draw(self):
        self.close_lists.draw()
        self.med_lists.draw()
        self.far_lists.draw()
    

def round_to_n(num_round, n):
    n_gap = num_round % n
    if n_gap != 0:
        if n_gap > n / 2:
            result = num_round + (n - n_gap)
        else:
            result = num_round - n_gap
        return int(result)
    return int(num_round)


def round_to_80(num):
    eighty_gap = num % 80
    if eighty_gap != 0:
        if eighty_gap > 40:
            result = num + (80 - eighty_gap)
        else:
            result = num - eighty_gap
        return int(result)
    return int(num)
