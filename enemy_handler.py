import math
import random
import time

import arcade

import bullet
import pointer
import vector


class EnemyHandler:
    """
    The EnemyHandler class holds all of the data values necessary for the enemies to act. it is also responsible for
    creating waves and updating enemies
    """

    def __init__(self):
        # The player object. This allows the enemies to get its position.
        self.player = None

        # The sprite list that holds all of the enemy sprites
        self.enemy_sprites = None

        # the current wave, plus which stage of difficulty
        self.wave = 0
        self.stage = 0

        # The number of enemies and the starting number.
        self.starting_num_enemies = 2
        self.num_enemies = 0

        # the difficulty and whether the difficulty changes
        self.difficulty = 0
        self.stay_same = False

        # the wave times for difficulties
        self.wave_times = []
        self.average_time = 0
        self.current_wave_time = 0

        # player health for enemy waves
        self.last_player_health = 0

        # clustering variables
        self.count_in_clusters = 6
        self.cluster_count = 1

    def assign_player_health(self):
        """
        This method is Just to ensure no bugs arise.
        """
        if self.player is not None:
            self.last_player_health = self.player.health

    def calc_wave(self):

        """
        using variables calculated based on the how the player is doing
         the number of enemies is based of a difficult equation.
        """
        loss = self.last_player_health - self.player.health
        self.assign_player_health()
        if loss > 0:
            loss_factor = 1/loss
        else:
            loss_factor = 0

        if len(self.wave_times) > 0:
            time_factor = self.average_time / self.wave_times[-1]
        #    print(f"Average Time = {self.average_time}. Last Time = {self.wave_times[-1]}")
        else:
            time_factor = 0

        base = 1.05
        last_difficulty = self.difficulty
        if last_difficulty > 0:
            modifier = (loss_factor + time_factor + (last_difficulty-base))*(self.stage/20)
        #    print(
        #        f"difficulty = base[{base}] + (loss factor[{loss_factor}] + time factor[{time_factor}]"
        #        f" + last difficulty[{last_difficulty - base}])*(stage[{self.stage / 20}]). ")
        else:
            modifier = 0
        self.difficulty = round(base + modifier, 2)
        prev_num_enemies = self.num_enemies
        self.num_enemies = round(self.starting_num_enemies * (self.difficulty ** self.wave))

        if self.num_enemies < self.starting_num_enemies:
            self.num_enemies = self.starting_num_enemies

        if self.num_enemies < prev_num_enemies:
            self.num_enemies = prev_num_enemies

        print("difficulty =", self.difficulty, "- Number of enemies =", self.num_enemies)

    def do_wave_time(self):
        """
        All steps based on record keeping the time A player takes to complete a mission
        """
        if self.current_wave_time > 0:
            self.wave_times.append(time.time() - self.current_wave_time)
            total = 0
            for times in self.wave_times:
                total += times
            self.average_time = total/len(self.wave_times)
        self.current_wave_time = time.time()

    def setup_wave(self):
        """
        The method called to set up the next wave.
        """
        self.wave += 1
        if self.wave % 5 == 1:
            self.stage += 1
        print("Stage:", self.stage, "Wave:", self.wave)
        self.do_wave_time()
        self.calc_wave()

        self.enemy_sprites = arcade.SpriteList()
        for i in range(self.num_enemies):
            enemy = Enemy()
            enemy.setup(self)
            self.enemy_sprites.append(enemy)

    def draw(self):
        """
        draws all of the enemy sprites
        """
        for enemy in self.enemy_sprites:
            enemy.draw()
        if self.wave % 6 == 0:
            arcade.draw_text(str(self.stage), self.player.center_x, self.player.center_y - 30, arcade.color.WHITE)

    def on_update(self, delta_time: float = 1 / 60):
        """
        updates all of the enemies
        """
        self.enemy_sprites.on_update(delta_time)
        if len(self.enemy_sprites) == 0:
            self.setup_wave()


class Enemy(arcade.Sprite):
    """
    The Enemy class is used by the enemy handler in each wave. their movement works just like the
    players, however they have decision trees on whether to turn left or right or when to move forward.
    """

    def __init__(self):
        super().__init__()

        # checks if the enemy is in range of player
        self.handler = None

        # debug guff
        self.rule_1_effect = [0.0, 0.0]
        self.rule_2_effect = [0.0, 0.0]
        self.rule_3_effect = [0.0, 0.0]
        self.rule_4_effect = [0.0, 0.0]
        self.do_rule = 0

        # angle info
        self.target_angle = 0
        self.direction = 0
        self.difference = [0.0, 0.0]

        # distance info
        self.target_distance = 0

        # movement
        self.turning_speed = 100
        self.velocity = [0.0, 0.0]

        # shooting variables
        self.shooting = False
        self.bullets = arcade.SpriteList()
        self.last_shot = 0
        self.shoot_delay = 1
        self.next_shot = 0

        # sprites
        self.textures = []
        self.scale = 0.15
        self.get_sprites()
        self.health = 12
        self.full_health = 12
        self.health_segment = 4
        self.frame = 1

        # hit box
        self.point_list = [
                           (165.0, -15.0), (165.0, -115.0), (155.0, -115.0), (155.0, -125.0), (145.0, -125.0),
                           (145.0, -135.0), (125.0, -135.0), (125.0, -145.0), (115.0, -145.0), (115.0, -155.0),
                           (85.0, -155.0), (85.0, -165.0), (35.0, -165.0), (35.0, -155.0), (-5.0, -155.0),
                           (-5.0, -145.0), (-85.0, -145.0), (-85.0, -135.0), (-115.0, -135.0), (-115.0, -125.0),
                           (-145.0, -125.0), (-145.0, -115.0), (-105.0, -115.0), (-105.0, -105.0), (-155.0, -105.0),
                           (-155.0, -95.0), (-135.0, -95.0), (-135.0, -85.0), (-125.0, -85.0), (-125.0, -75.0),
                           (-165.0, -75.0), (-165.0, -65.0), (-145.0, -65.0), (-145.0, -55.0), (-125.0, -55.0),
                           (-125.0, -45.0), (-105.0, -45.0), (-105.0, -35.0), (-25.0, -35.0), (-25.0, -25.0),
                           (-45.0, -25.0), (-45.0, -15.0), (-75.0, -15.0), (-75.0, -5.0), (-125.0, -5.0), (-125.0, 5.0),
                           (-75.0, 5.0), (-75.0, 15.0), (-45.0, 15.0), (-45.0, 25.0), (-25.0, 25.0), (-25.0, 35.0),
                           (-105.0, 35.0), (-105.0, 45.0), (-125.0, 45.0), (-125.0, 55.0), (-145.0, 55.0),
                           (-145.0, 65.0), (-165.0, 65.0), (-165.0, 75.0), (-125.0, 75.0), (-125.0, 85.0),
                           (-135.0, 85.0), (-135.0, 95.0), (-155.0, 95.0), (-155.0, 105.0), (-105.0, 105.0),
                           (-105.0, 115.0), (-145.0, 115.0), (-145.0, 125.0), (-115.0, 125.0), (-115.0, 135.0),
                           (-85.0, 135.0), (-85.0, 145.0), (-5.0, 145.0), (-5.0, 155.0), (35.0, 155.0), (35.0, 165.0),
                           (85.0, 165.0), (85.0, 155.0), (115.0, 155.0), (115.0, 145.0), (125.0, 145.0), (125.0, 135.0),
                           (145.0, 135.0), (145.0, 125.0), (155.0, 125.0), (155.0, 105.0), (165.0, 105.0), (165.0, 15.0)
                            ]
        self.set_hit_box(self.point_list)

        # algorithm variables
        self.target = [0.0, 0.0]
        self.target_speed = 0

        # Rules
        self.rule_1_priority = 1
        self.rule_2_priority = 1
        self.rule_3_priority = 1
        self.rule_4_priority = 1

    def setup(self, handler):
        """
        sets up the enemy in relation to the player. it also gives the enemy the handler for easier access to variables
        """
        self.handler = handler
        self.angle = random.randint(0, 360)
        screen = arcade.get_display_size()
        close = True
        while close:
            self.center_x = handler.player.center_x + random.randint(-(screen[0] // 2) + 30, (screen[0] // 2) - 29)
            self.center_y = handler.player.center_y + random.randint(-(screen[1] // 2) + 30, (screen[1] // 2) - 29)
            self.target_distance = vector.find_distance((self.center_x, self.center_y),
                                                        (self.handler.player.center_x, self.handler.player.center_y))
            if self.target_distance > 300:
                close = False

        point = pointer.Pointer()
        point.holder = self.handler.player
        point.target = self
        self.handler.player.enemy_pointers.append(point)

    def get_sprites(self):
        """
        Gets all of the hurt sprites for the enemy
        """
        for i in range(4):
            texture = arcade.load_texture("Sprites/Enemy Hunter + Damage Frames.png", 0, 330*i, 330, 330)
            self.textures.append(texture)
        self.texture = self.textures[0]

    def shoot(self):
        """
        shoots a bullets.
        """
        shot = bullet.Bullet([self.center_x, self.center_y], self.angle, self.velocity)
        shot.texture = arcade.load_texture("Sprites/Enemy Bullet.png")
        shot.scale = 0.05
        point_list = ((-220.0, 10.0), (-110.0, 60.0), (150.0, 60.0), (200.0, 40.0), (220.0, 20.0), (220.0, -20.0),
                      (200.0, -40.0), (150.0, -60.0), (-110.0, -60.0), (-220.0, -10.0))
        shot.set_hit_box(point_list)
        self.bullets.append(shot)

    def draw(self):
        """
        Draws the enemy sprite and bullets, as well as debug information
        """
        if self.handler.player.show_hit_box:
            """
            arcade.draw_line(self.center_x,self.center_y, self.handler.player.center_x, self.handler.player.center_y, 
                             arcade.color.LIME_GREEN, 1)
            self.draw_hit_box(color=arcade.color.LIME_GREEN)
            """
            for shot in self.bullets:
                arcade.draw_line(shot.center_x, shot.center_y,
                                 shot.velocity[0] + shot.center_x, shot.velocity[1] + shot.center_y,
                                 arcade.color.CYBER_YELLOW)

            arcade.draw_line(self.center_x + self.rule_1_effect[0]*20, self.center_y + self.rule_1_effect[1]*20,
                             self.center_x, self.center_y,
                             arcade.color.RADICAL_RED)
            arcade.draw_line(self.center_x + self.rule_2_effect[0]*20, self.center_y + self.rule_2_effect[1]*20,
                             self.center_x, self.center_y,
                             arcade.color.LIME_GREEN)
            arcade.draw_line(self.center_x + self.rule_3_effect[0]*20, self.center_y + self.rule_3_effect[1]*20,
                             self.center_x, self.center_y,
                             arcade.color.OCEAN_BOAT_BLUE)
            arcade.draw_line(self.center_x, self.center_y,
                             self.center_x+self.rule_4_effect[0] * 20, self.center_y+self.rule_4_effect[1] * 20,
                             arcade.color.WHITE_SMOKE)
            arcade.draw_line(self.center_x + self.velocity[0], self.center_y + self.velocity[1],
                             self.center_x, self.center_y,
                             arcade.color.CYBER_YELLOW)
        self.bullets.draw()
        super().draw()

    def on_update(self, delta_time: float = 1/60):

        """
        Every update run different method for the enemy and its algorithms.
        """

        # check contact
        self.check_contact()
        self.if_hit_player()

        self.fix_angle()
        self.calculate_movement()

        self.turn(delta_time)

        self.do_rule += 1*delta_time
        self.rules()

        self.center_x += self.velocity[0] * delta_time
        self.center_y += self.velocity[1] * delta_time

        if self.last_shot + self.shoot_delay < time.time():
            if self.shooting:
                self.shoot()
            self.last_shot = time.time()
            self.shoot_delay = random.randrange(3, 7)
        self.bullets.on_update()

    def calculate_movement(self):
        """
        calculates the variables needed for the algorithms.
        """

        # get the angle towards the player
        target = self.handler.player
        self_pos = (self.center_x, self.center_y)
        target_pos = (target.center_x, target.center_y)
        self.target_angle = vector.find_angle(target_pos, self_pos)

        # find the difference and the direction
        self.difference = vector.calc_difference(self.target_angle, self.angle)
        self.direction = vector.calc_direction(self.target_angle, self.angle)

        # distance to player
        dx = self_pos[0] - target_pos[0]
        dy = self_pos[1] - target_pos[1]
        self.target_distance = math.sqrt(dx**2 + dy**2)
        self.target_speed = math.sqrt(target.acceleration[0]**2 + target.acceleration[1]**2)

    def turn(self, delta_time):
        """
        turn the enemy to face the player.
        """
        if self.direction == -1:
            small_difference = self.difference[1]
        else:
            small_difference = self.difference[0]

        if self.turning_speed * delta_time < small_difference:
            self.angle += self.turning_speed * delta_time * self.direction
        else:
            self.angle += small_difference * self.direction

    def fix_angle(self):
        """
        for ease of calculating difference, fix the angle of the enemy sprite.
        """
        if self.angle > 360:
            self.angle -= 360
        elif self.angle < 0:
            self.angle += 360

        self.radians = math.radians(self.angle)

    def check_contact(self):
        """
        Check to see if the player or an ally hits the enemy.
        """
        hits = arcade.check_for_collision_with_list(self, self.handler.player.bullets)
        for enemy in self.handler.enemy_sprites:
            if enemy != self:
                e_hits = arcade.check_for_collision_with_list(self, enemy.bullets)
                if len(e_hits) > 0:
                    for hit in e_hits:
                        hits.append(hit)
        if len(hits) > 0:
            hits[0].remove_from_sprite_lists()
            del hits[0]
            self.health -= self.handler.player.damage
            if self.health <= self.full_health - (self.frame * self.health_segment) and not self.health < 0:
                self.texture = self.textures[self.frame]
                self.frame += 1
            if self.health < 0:
                for point in self.handler.player.enemy_pointers:
                    if point.target == self:
                        point.remove_from_sprite_lists()
                        del point
                self.remove_from_sprite_lists()
                del self

    def if_hit_player(self):
        """
        check if the enemy hits the player
        """
        hits = arcade.check_for_collision_with_list(self.handler.player, self.bullets)
        if len(hits) > 0:
            self.handler.player.health -= 4
            if self.handler.player.health <= 0:
                self.handler.player.dead = True
            self.handler.player.hit = True
            for hit in hits:
                hit.remove_from_sprite_lists()
                del hit

    def rules(self):
        """
        all of the enemy rules for movement.
        """
        self.rule_1_effect = self.rule1()
        if self.do_rule > 0.1:
            self.do_rule = 0
            # self.rule_2_effect = self.rule2() - This rule makes the basic AI too smart. It wont be used on most AI
            self.rule_3_effect = self.rule3()
            self.rule_4_effect = self.rule4()
        final = [0.0, 0.0]
        final[0] = self.rule_1_effect[0] + self.rule_2_effect[0] + self.rule_3_effect[0] + self.rule_4_effect[0]
        final[1] = self.rule_1_effect[1] + self.rule_2_effect[1] + self.rule_3_effect[1] + self.rule_4_effect[1]

        self.velocity[0] += final[0]
        self.velocity[1] += final[1]

        speed_limit = 700
        speed = math.sqrt(self.velocity[0] ** 2 + self.velocity[1]**2)
        if speed > speed_limit:
            self.velocity[0] = (self.velocity[0] / speed) * speed_limit
            self.velocity[1] = (self.velocity[1] / speed) * speed_limit

        self.shooting = self.shoot_rule()

    def shoot_rule(self):
        """
        Calculates if the enemy should shoot.
        """
        player = self.handler.player
        angle_to_target = vector.find_angle((player.center_x, player.center_y),
                                            (self.center_x, self.center_y))
        difference = vector.calc_difference(angle_to_target, self.angle)
        distance_to_target = vector.find_distance((self.center_x, self.center_y), (player.center_x, player.center_y))
        result = False
        if difference[0] < 30 or difference[1] < 30:
            result = True
            for neighbor in self.handler.enemy_sprites:
                distance_to_neighbor = vector.find_distance((self.center_x, self.center_y),
                                                            (neighbor.center_x, neighbor.center_y))
                if neighbor != self:
                    if distance_to_neighbor < distance_to_target:
                        angle_to_neighbor = vector.find_angle((neighbor.center_x, neighbor.center_y),
                                                              (self.center_x, self.center_y))
                        difference = vector.calc_difference(angle_to_neighbor, self.angle)
                        if difference[0] < 20 or difference[1] < 20:
                            result = False

                    if result is False:
                        break
        return result

    def rule1(self):
        """
        Rule One: Move Towards the player but stay 300 pixels away.
        """
        target = self.handler.player
        distance = vector.find_distance((self.center_x, self.center_y),
                                        (target.center_x, target.center_y))
        rad_angle = math.radians(self.target_angle)
        if distance > 480:
            x = math.cos(rad_angle) * 2.8
            y = math.sin(rad_angle) * 2.8
        elif distance > 330:
            x = math.cos(rad_angle) * 2.5
            y = math.sin(rad_angle) * 2.5
        elif distance < 285:
            x = math.cos(rad_angle) * -2.5
            y = math.sin(rad_angle) * -2.5
        elif not self.target_speed:
            x = 0
            y = 0
        else:
            x = math.cos(rad_angle) * self.target_speed
            y = math.sin(rad_angle) * self.target_speed
        result = [x * self.rule_1_priority, y * self.rule_1_priority]
        return result

    def rule2(self):
        """
        Rule Two: Avoid being in front of the player.
        """
        player = self.handler.player
        angle_to_self = vector.find_angle((self.center_x, self.center_y),
                                          (player.center_x, player.center_y))
        difference = vector.calc_difference(player.angle, angle_to_self)
        direction = 0
        move = 0
        if difference[0] < 45 and difference[0] < difference[1]:
            direction = player.angle - 90
            move = (45 - difference[0])
        if difference[1] < 45 and difference[1] < difference[0]:
            direction = player.angle + 90
            move = (45 - difference[1])
        x, y = 0, 0
        if direction:
            rad_difference = math.radians(direction)
            x = math.cos(rad_difference) * move
            y = math.sin(rad_difference) * move
        result = [x * self.rule_2_priority * 0.05, y * self.rule_2_priority * 0.05]
        return result

    def rule3(self):
        """
        Avoid being in front of allies, and do not crash into each other.
        """
        x = 0
        y = 0
        total = 0
        for neighbor in self.handler.enemy_sprites:
            if neighbor != self:
                distance = vector.find_distance((self.center_x, self.center_y), (neighbor.center_x, neighbor.center_y))
                if distance < 100:
                    angle_to_self = vector.find_angle((self.center_x, self.center_y),
                                                      (neighbor.center_x, neighbor.center_y))
                    difference = vector.calc_difference(neighbor.angle, angle_to_self)
                    direction = vector.calc_direction(neighbor.angle, angle_to_self)
                    if difference[0] < 45 and difference[0] < difference[1]:
                        perpendicular_rad_angle = math.radians(neighbor.angle + 90 * -direction)
                        x += math.cos(perpendicular_rad_angle) * ((90 - difference[0])/45)
                        y += math.sin(perpendicular_rad_angle) * ((90 - difference[0])/45)
                    elif difference[1] < 45 and difference[1] < difference[0]:
                        perpendicular_rad_angle = math.radians(neighbor.angle + 90 * -direction)
                        x += math.cos(perpendicular_rad_angle) * ((90 - difference[1])/45)
                        y += math.sin(perpendicular_rad_angle) * ((90 - difference[1])/45)
                    else:
                        x += (self.center_x - neighbor.center_x)
                        y += (self.center_y - neighbor.center_y)
                        total += 1
        if total:
            x /= total
            y /= total
        result = [x * self.rule_3_priority * 0.05, y * self.rule_3_priority * 0.05]
        return result

    def rule4(self):
        """
        Attempt to slow down or speed up to match the players velocity
        """
        target = self.handler.player
        target_velocity = (target.velocity[0], target.velocity[1])
        distance = vector.find_distance((self.center_x, self.center_y), (target.center_x, target.center_y))
        result = [0.0, 0.0]
        if distance < 700:
            result[0] = (target_velocity[0] - self.velocity[0])/8
            result[1] = (target_velocity[1] - self.velocity[1])/8

        return [result[0] * 0.05 * self.rule_4_priority, result[1] * 0.05 * self.rule_4_priority]
