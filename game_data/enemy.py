import math
import random
import time
import PIL

import arcade

import game_data.bullet as bullet
import game_data.ui as ui
import game_data.vector as vector

# The screen width for spawning calculations and other algorithms.
SCREEN_WIDTH, SCREEN_HEIGHT = arcade.get_display_size()


class Cluster:
    """
    A Cluster is an object spawned by the enemy handler and acts as a way to separate the total number of enemies in
    a wave into smaller manageable segments. These clusters slowly travel towards the mission target.
    """

    def __init__(self, handler, target):
        # The number of enemies the cluster will spawn, and once they have spawned it also track the number still alive.
        self.num_enemies = 0

        # The speed it moves towards the target.
        self.speed = random.randint(80, 100)

        self.center_x = 0
        self.center_y = 0

        # The enemy handler and the target.
        self.handler = handler
        if target != self.handler.planet_data:
            self.target = target
        else:
            self.target = None

        # The bool which tells the handler and other objects that the cluster has spawned its enemies.
        self.spawned = False

        # A pointer just like those used by the enemies.
        self.point = ui.Pointer()
        self.point.holder = self.handler.player
        self.point.target = self
        self.handler.player.enemy_pointers.append(self.point)

        # The distance to the target and to the player.
        self.distance = 0
        self.p_distance = 0

    def spawn_enemies(self, delta_time):
        # This method calls every update and checks to see if the Cluster needs to spawn its enemies.

        # These are vector values for the player and the clusters position.
        p_d = self.handler.player.center_x, self.handler.player.center_y
        s_d = self.center_x, self.center_y

        # If the target is not None it find the distance to the target rather than the player.
        if self.target is not None:
            t_d = self.target.center_x, self.target.center_y
            angle = math.radians(vector.find_angle(t_d, s_d))
            self.distance = vector.find_distance(t_d, s_d)
            d_x = math.cos(angle) * self.speed * delta_time
            d_y = math.sin(angle) * self.speed * delta_time
            self.center_x += d_x
            self.center_y += d_y
        else:
            self.distance = vector.find_distance(p_d, s_d)

        # Find the player distance
        self.p_distance = vector.find_distance(p_d, s_d)

        self.spawn()

    def spawn(self):
        # This method runs the loop to spawn the enemies.

        # The same vectors.
        p_d = self.handler.player.center_x, self.handler.player.center_y
        s_d = self.center_x, self.center_y

        # If the cluster is within a screen of the player or of the target it shall spawn the enemies.
        if self.distance < SCREEN_WIDTH or self.p_distance < SCREEN_WIDTH:

            # Variables for the spaning method.
            planet_pos = (self.handler.planet_data.center_x, self.handler.planet_data.center_y)
            half_planet = self.handler.planet_data.width / 2
            r_angle_to_cluster = math.radians(vector.find_angle((self.center_x, self.center_y), planet_pos))

            # The distance to planet is the distance from the edge of the sprite. rather than the center.
            distance_to_planet = (vector.find_distance((self.center_x, self.center_y), planet_pos)
                                  - half_planet)

            # For every enemy in self.num_enemies, spawn an enemy away from the planet around the cluster.
            for i in range(self.num_enemies):
                # From the loaded data choose the enemy, and find it's bullet type/
                enemy_type = random.randrange(0, len(self.handler.basic_types))
                bullet_type = self.handler.bullet_types[self.handler.basic_types[enemy_type]["shoot_type"]]

                # Create the enemy and decide its initial target (The player, or the mission target).
                enemy = Enemy(self.handler.basic_types[enemy_type], bullet_type)
                target = self.target
                if vector.find_distance(s_d, p_d) < vector.find_distance(s_d, (target.center_x, target.center_y)):
                    target = self.handler.player
                enemy.setup(self.handler, target, s_d, self)

                # Place the enemy at the position of the planet to shorten the next lines.
                enemy.center_x = self.handler.planet_data.center_x
                enemy.center_y = self.handler.planet_data.center_y

                # choose a random angle between -5 and 5 degrees. In radians.
                random_angle = random.uniform(-0.0872665, 0.0872665)

                # Calculate the position of the enemy. It is spawned away from the planet rather than the cluster
                # this is so the enemy will never spawn inside the planet, making them pointless.
                enemy.center_x += math.cos(r_angle_to_cluster + random_angle) * (half_planet + distance_to_planet
                                                                                 + random.randint(-100, 100))
                enemy.center_y += math.sin(r_angle_to_cluster + random_angle) * (half_planet + distance_to_planet
                                                                                 + random.randint(-100, 100))
                self.handler.enemy_sprites.append(enemy)

            # We then remove the clusters point from the pointers list, and set the cluster to be spawned.
            self.point.remove_from_sprite_lists()
            self.spawned = True

    def slaughter(self):
        # Kill the cluster.
        self.spawned = True
        self.point.kill()
        self.num_enemies = 0


class Enemy(arcade.Sprite):
    """
    The Enemy class is used by the enemy handler in each wave. their movement works on a set of rules that
    calculate how they should move every update.
    """

    def __init__(self, type_data: dict, bullet_type: dict):
        super().__init__()

        # type
        self.type_data = type_data
        self.type = type_data['type']
        self.super_type = type_data['super_type']

        # checks if the enemy is in range of player
        self.handler = None
        self.target = None
        self.cluster = None

        # gravity variables
        self.gravity_handler = None
        self.gravity_acceleration = [0.0, 0.0]
        self.weight = 549054

        # movement
        self.turning_speed = 100
        self.velocity = [0.0, 0.0]

        # shooting variables
        self.firing = False
        self.bullet_type = bullet_type
        self.bullets = arcade.SpriteList()
        self.last_shot = 0
        self.shoot_delay = 0.1
        self.shoot_delay_range = type_data['shoot_delay']
        self.next_shot = 0
        self.num_shots = type_data['num_shots']
        self.start_angle = type_data['start_angle']
        self.angle_mod = type_data['angle_mod']

        # shooting audio
        self.shot_sound = arcade.Sound("game_data/Music/Enemy Shot.wav")
        self.shot_panning = -1
        self.shot_volume = 0

        # rapid shooting variables
        self.shots_this_firing = 0
        self.next_shot_rapid = 0
        self.shot_gap = 0.15

        # shooting variable to fix bug
        self.first_shot = False

        # sprites
        self.textures = []
        self.scale = 0.15
        self.get_sprites(type_data['image_file'])
        self.health = type_data['health']
        self.full_health = self.health
        if len(self.textures) - 1:
            self.health_segment = self.health / (len(self.textures) - 1)
        else:
            self.health_segment = 1
        self.frame = 1

        # gravity variables
        self.gravity_handler = None
        self.gravity_acceleration = [0.0, 0.0]

        # algorithm variables
        self.target = [0.0, 0.0]
        self.target_speed = 0
        self.target_acceleration = 0
        self.target_velocity = [0.0, 0.0]

        self.target_angle = 0
        self.angle_to_target = 0
        self.direction = 0
        self.difference = [0.0, 0.0]

        self.speed = 0

        self.target_distance = 0

        self.correct = False

        # Movement Rules
        self.rule_1_effect = [0.0, 0.0]
        self.rule_2_effect = [0.0, 0.0]
        self.rule_3_effect = [0.0, 0.0]
        self.rule_4_effect = [0.0, 0.0]
        self.rule_5_effect = [0.0, 0.0]
        self.rule_effects = [self.rule_1_effect, self.rule_2_effect, self.rule_4_effect,
                             self.rule_5_effect]

        self.do_rule = 0

        self.rule_1_priority = type_data['rules'][0]
        self.rule_2_priority = type_data['rules'][1]
        self.rule_3_priority = type_data['rules'][2]
        self.rule_4_priority = type_data['rules'][3]
        self.rule_5_priority = type_data['rules'][4]

        # Ability Variables
        try:
            self.abilities = type_data['abilities']
            self.active_ability = None
            self.active_frames = []
            self.ability_frames = []
            for frames in type_data['ability_frames']:
                frame_list = []
                self.get_sprites(frames, frame_list)
                self.ability_frames.append(frame_list)

            self.cool_down = 0
            self.cool_down_delay = 4
            self.start_time = 0
            self.duration = 0

        except KeyError:
            self.abilities = None
            self.active_ability = None
            self.active_frames = None
            self.ability_frames = None
            self.start_time = 0
            self.duration = 0

    def setup(self, handler, target, x_y_pos: tuple = None, cluster: Cluster = None, ):
        """
        sets up the enemy in relation to the player. it also gives the enemy the handler for easier access to variables
        """
        self.cluster = cluster

        # If not pos was given set the pos to the players position.
        if x_y_pos is None:
            x_y_pos = handler.player.center_x, handler.player.center_y

        self.handler = handler

        self.angle = random.randint(0, 360)

        # Set_hit_box does not like lists of points even though that is what it requires. This is a bug with formating
        # rather than an issue in the code.
        self.set_hit_box(points=self.type_data['point_list'])

        # Adds the enemy as a gravity object
        handler.game_window.gravity_handler.set_gravity_object(self)

        # If there is no cluster spawn the enemies around the player.
        if self.cluster is not None:
            pass
        else:
            rad_angle = round(random.uniform(0.0, 2 * math.pi), 2)
            self.center_x = x_y_pos[0] + math.cos(rad_angle) + random.randint(320, 600)
            self.center_y = x_y_pos[1] + math.sin(rad_angle) + random.randint(320, 600)

        # The pointer for the enemy.
        point = ui.Pointer()
        point.holder = self.handler.player
        point.target = self
        self.handler.player.enemy_pointers.append(point)

        # Set the target to the given target, and set the enemies velocity to half the target's velocity.
        self.target = target
        self.velocity[0] = self.target.velocity[0] / 2
        self.velocity[1] = self.target.velocity[1] / 2

    def get_sprites(self, image_file, list_to_append: list = None):
        """
        Gets all of the damage sprites for the enemy.

        To make it easier to calculate, the sprite sheet is always one column. The width is then used to find the number
        of frames.
        """
        image = PIL.Image.open(image_file)
        num_frames = image.size[1] // image.size[0]
        x = image.size[0]
        y = image.size[1] / num_frames
        for i in range(num_frames):
            texture = arcade.load_texture(image_file, 0, y * i, x, y)
            if list_to_append is None:
                self.textures.append(texture)
            else:
                list_to_append.append(texture)
        if list_to_append is None:
            self.texture = self.textures[0]

    def draw(self):
        """
        Draws the enemy sprite and bullets.
        """
        self.bullets.draw()
        super().draw()

    def on_update(self, delta_time: float = 1 / 60):
        """
        Every update run different methods for the enemy and its algorithms.
        """

        # A check to ensure the enemy dies.
        if self.health <= 0:
            self.kill()

        # check contact
        self.check_contact()
        self.if_hit_player()

        # fix the enemies angle to be in the range 0 - 360
        self.fix_angle()

        # calculate different variables needed for the rules
        self.calculate_movement()

        # turn towards the player
        self.turn(delta_time)

        # gravity
        self.velocity[0] += self.gravity_acceleration[0]
        self.velocity[1] += self.gravity_acceleration[1]

        # run a counter to check when to do some of the rules, then calculate the rules and the resultant velocity
        self.do_rule += 1 * delta_time
        self.rules()

        # apply velocity
        self.center_x += self.velocity[0] * delta_time
        self.center_y += self.velocity[1] * delta_time

        # abilities
        if self.abilities is not None:
            self.ability_rules()

        # shooting
        if self.active_ability is None:
            self.shoot_rule()
            if self.firing:
                self.shoot()
        self.bullets.on_update(delta_time)

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

    def drop_scrap(self):
        """
        Called when the enemy dies, it drops a random amount scrap.
        """
        if self.super_type != "boss":
            # If the enemy is not a boss then spawn the scrap.
            num = random.randrange(0, 4)
            for scrap in range(num):
                x_y = (self.center_x + random.randrange(-15, 16), self.center_y + random.randrange(-15, 16))
                drop = vector.Scrap(self.handler.player, self.handler, x_y)
                self.handler.scrap_list.append(drop)
            self.handler.count_dropped_scrap(num)

    def kill(self):
        # Kills the enemies, spawns scrap, and counts the killed enemy.
        self.handler.count_enemy_death()
        self.drop_scrap()

        for point in self.handler.player.enemy_pointers:
            if point.target == self:
                point.kill()

        if self.cluster is not None:
            self.cluster.num_enemies -= 1

        self.remove_from_sprite_lists()
        del self

    """
    Methods for different contact. Either being hit or hitting the player.
    """

    def check_contact(self):
        """
        Check to see if the player or an ally hits the enemy.
        """
        # First it checks if the player's bullets are hitting the enemy.
        hits = arcade.check_for_collision_with_list(self, self.handler.player.bullets)

        # It then adds any other bullets from it's allies to the list
        for enemy in self.handler.enemy_sprites:
            if enemy != self and type(enemy) != vector.AnimatedTempSprite:
                e_hits = arcade.check_for_collision_with_list(self, enemy.bullets)
                if len(e_hits) > 0:
                    for hit in e_hits:
                        hits.append(hit)

        # Finally if any bullets hit the enemy, deal damage for each bullet and kill the bullet.
        if len(hits) > 0:
            hit_copy = hits
            for index, hit in enumerate(hit_copy):
                self.health -= hit.damage
                if self.health <= 0:
                    # If the enemy has no health, then spawn a death animation, and kill the enemy.
                    death = vector.AnimatedTempSprite("game_data/Sprites/Enemies/enemy explosions.png",
                                                      (self.center_x, self.center_y))
                    self.handler.enemy_sprites.append(death)
                    self.kill()
                elif self.health <= self.full_health - (self.frame * self.health_segment):
                    # If the enemy has taken enough damage to switch damage frame, change the enemy's texture.
                    self.texture = self.textures[self.frame]
                    self.frame += 1
                hit.kill()

    def if_hit_player(self):
        """
        check if the enemy hits the player
        """
        # Find every bullet that is hitting the target and damage the target and play the player hit sound.
        hits = arcade.check_for_collision_with_list(self.target, self.bullets)
        if len(hits) > 0:
            for hit in hits:
                self.target.health -= self.bullet_type['damage']
                self.target.last_damage = time.time()
                file = "game_data/Music/player_damage.wav"
                sound = arcade.Sound(file)
                sound.play(volume=self.shot_volume, pan=self.shot_panning)

                if self.target.health <= 0:
                    self.target.health = 0
                    self.target.dead = True

                self.target.hit = True
                hit.kill()

    """
    Methods for calculating the different rules.
    """

    def calculate_movement(self):
        """
        calculates the variables needed for the algorithms.
        """

        # Shortening variables.
        player = self.handler.player
        target = self.target
        self_pos = (self.center_x, self.center_y)
        target_pos = (target.center_x, target.center_y)

        # get the angle towards the player
        self.target_angle = vector.find_angle(target_pos, self_pos)

        # find the difference and the direction
        self.difference = vector.calc_difference(self.target_angle, self.angle)
        self.direction = vector.calc_direction(self.target_angle, self.angle)

        # Find the targets speed
        self.target_velocity = target.velocity
        self.target_speed = math.sqrt(target.velocity[0] ** 2 + target.velocity[1] ** 2)

        # Find the players acceleration, if it is greater than the acceleration found than set the enemies acceleration
        # to the new acceleration.
        forward_acceleration = math.sqrt(player.acceleration[0]**2 + player.acceleration[1]**2)
        if forward_acceleration > self.target_acceleration:
            self.target_acceleration = forward_acceleration

        # distance to target
        self.target_distance = vector.find_distance(self_pos, target_pos)

        # self speed
        self.speed = vector.find_distance((0.0, 0.0), self.velocity)

        # Find the audio volume to the left or right depending on the enemies position.
        diff_panning = self_pos[0] - target_pos[0]
        if abs(diff_panning) < SCREEN_WIDTH:
            self.shot_panning = diff_panning / (SCREEN_WIDTH * 2)
        else:
            self.shot_panning = 0

        # Find the total audio volume of shots depending on the distance.
        player_distance = vector.find_distance(self_pos, (player.center_x, player.center_y))
        if player_distance < SCREEN_WIDTH:
            self.shot_volume = 0.12 - self.target_distance / (SCREEN_WIDTH * 12)
        else:
            self.shot_volume = 0

    def rules(self):
        """
        all of the enemy rules for movement.
        """

        # The enemy always calculates rule one, however it only finds new effects for each rule every tenth of a second.
        self.rule_1_effect = self.rule1()
        if self.do_rule > 0.1:
            self.do_rule = 0
            if self.rule_2_priority:
                self.rule_2_effect = self.rule2()
            if self.rule_3_priority:
                self.rule_3_effect = self.rule3()
            if self.rule_4_priority:
                self.rule_4_effect = self.rule4()
            if self.rule_5_priority:
                self.rule_5_effect = self.rule5()

        self.rule_effects = [self.rule_1_effect, self.rule_2_effect, self.rule_3_effect,
                             self.rule_4_effect, self.rule_5_effect]

        # Add all of the rule affects together to create a final acceleration.
        final = [0.0, 0.0]
        final[0] = self.rule_1_effect[0] \
                   + self.rule_2_effect[0] \
                   + self.rule_3_effect[0] \
                   + self.rule_4_effect[0] \
                   + self.rule_5_effect[0]
        final[1] = self.rule_1_effect[1] \
                   + self.rule_2_effect[1] \
                   + self.rule_3_effect[1] \
                   + self.rule_4_effect[1] \
                   + self.rule_5_effect[1]

        self.velocity[0] += final[0]
        self.velocity[1] += final[1]

    def ability_rules(self):
        """
        This method was to find activate the abilities of different enemies, however is was never completed.
        """

        # If the enemy had an active ability, run through them until one of their active abilities triggers.
        if self.active_ability is None:
            for frames, ability in enumerate(self.abilities):
                if ability == 'invisibility':
                    self.invisibility_rule(frames)

                if self.active_ability is not None:
                    break

        # If the active rule is not None do the specified rule.
        if self.active_ability == 'invisibility':
            self.invisibility_rule()

    """
    The Shooting Methods
    """

    def shoot_rule(self):
        """
        The shoot rule method decides when the enemy can shoot. It is the same no matter how the enemies actual shooting
        differs.
        """

        # First it ensures that enough time has passed since the last shot.
        if not self.firing and self.last_shot + self.shoot_delay < time.time():

            # Then it checks to see if the enemy is aiming at its target.
            if self.difference[0] < 20 or self.difference[1] < 20 and self.target_distance < 750:
                self.firing = True

                # It then checks to see if it is aiming at any of its neighbors.
                for neighbor in self.handler.enemy_sprites:
                    distance_to_neighbor = vector.find_distance((self.center_x, self.center_y),
                                                                (neighbor.center_x, neighbor.center_y))
                    if neighbor != self:
                        # If they are in between the enemy and the player than do not shoot.
                        if distance_to_neighbor < self.target_distance + 200:
                            angle_to_neighbor = vector.find_angle((neighbor.center_x, neighbor.center_y),
                                                                  (self.center_x, self.center_y))
                            difference = vector.calc_difference(angle_to_neighbor, self.angle)
                            # Than if the
                            if difference[0] < 45 or difference[1] < 45:
                                self.firing = False

                        # If they did not shoot reset the timer and break from the loop.
                        if self.firing is False:
                            self.last_shot = time.time()
                            self.shoot_delay = random.randrange(self.shoot_delay_range[0], self.shoot_delay_range[1])
                            break

    def shoot(self):
        """
        This method creates an adaptable shooting system that allows for different varibles to change the shooting.
        """

        # If the enemy should shoot and the time till next shot is less than the current time.
        if self.firing and time.time() > self.next_shot:
            # Set the angle. This angle is based of the enemies current angle, the start angle
            # and the angle modifier. This system allows for enemies to shoot in circles or "shotgun" spreads.
            angle = self.angle + self.start_angle + (self.angle_mod * self.shots_this_firing)

            # It then creates a shot and appends it.
            shot = bullet.Bullet([self.center_x, self.center_y], angle, self.velocity, self.bullet_type)
            self.bullets.append(shot)

            # It then increases the shots this firing, finds the time until the next shot, and plays some audio.
            self.shots_this_firing += 1
            self.shot_sound.play(self.shot_volume, self.shot_panning)
            self.next_shot = time.time() + self.shot_gap

            # If the number of shots fired is equal to the total num of shots each firing than reset the variables.
            if self.shots_this_firing >= self.num_shots:
                self.firing = False
                self.shots_this_firing = 0
                self.next_shot = 0
                self.last_shot = time.time()
                self.shoot_delay = random.randrange(self.shoot_delay_range[0], self.shoot_delay_range[1])

    """
    The Movement Rules:
    Rule One: Move Towards the player but stay 300 pixels away.
    Rule Two: Avoid being in front of allies, and do not crash into each other.
    Rule Three: Attempt to slow down or speed up to match the players velocity.
    Rule Four: Avoid being in front of the player.
    Rule Five: Move Away from Gravity
    """

    def rule1(self):
        """
        Rule One: Move Towards the player but stay 300 pixels away.
        """

        # Find the distance and the angle in radians.
        distance = self.target_distance
        rad_angle = math.radians(self.target_angle)

        if distance > SCREEN_WIDTH * 10:
            # If the enemy is very far from the target accelerate in that direction aggressively.
            x = math.cos(rad_angle) * self.target_acceleration * 4
            y = math.sin(rad_angle) * self.target_acceleration * 4
        if distance > SCREEN_HEIGHT/2 + 50:
            # If the distance is large but not huge, than accelerate towards the target, faster than the target.
            x = math.cos(rad_angle) * (self.target_acceleration + 1.4)
            y = math.sin(rad_angle) * (self.target_acceleration + 1.4)
        elif distance > SCREEN_HEIGHT/2 - 25:
            # If the enemies is just on screen accelerate with the target.
            x = math.cos(rad_angle) * self.target_acceleration
            y = math.sin(rad_angle) * self.target_acceleration
        elif distance < SCREEN_HEIGHT/2 - 130:
            # If they are close to the target move away
            x = math.cos(rad_angle) * -2.5
            y = math.sin(rad_angle) * -2.5
        elif distance < 75:
            # If they are too close quickly move away
            x = math.cos(rad_angle) * -4
            y = math.sin(rad_angle) * -4
        else:
            # If in the sweet spot stay as they are.
            x = 0
            y = 0

        # Find the result and increase it by 1.5 times to ensure they do not run away.
        result = [x * self.rule_1_priority * 1.5, y * self.rule_1_priority * 1.5]
        return result

    def rule2(self):
        """
        Rule Two: Avoid being in front of allies, and do not crash into each other.
        """
        x = 0
        y = 0
        total = 0

        # Find the average of all their motions and move in that average direction.
        for neighbor in self.handler.enemy_sprites:
            if neighbor != self:
                distance = vector.find_distance((self.center_x, self.center_y), (neighbor.center_x, neighbor.center_y))
                # If the distance is too close than dodge.
                if distance < 250:
                    total += 1

                    angle_neighbor = vector.find_angle((self.center_x, self.center_y),
                                                       (neighbor.center_x, neighbor.center_y))
                    difference_neighbor = vector.calc_difference(neighbor.angle, angle_neighbor)
                    direction = 0
                    move = 0
                    if difference_neighbor[0] < 45 and difference_neighbor[0] < difference_neighbor[1]:
                        # If the neighbor is looking at the enemy and the left side is closer, dodge left.
                        direction = neighbor.angle - 90
                        move = (45 - difference_neighbor[0])
                    if difference_neighbor[1] < 45 and difference_neighbor[1] < difference_neighbor[0]:
                        # If the neighbor is looking at the enemy and the right side is closer, dodge right.
                        direction = neighbor.angle + 90
                        move = (45 - difference_neighbor[1])
                    if direction:
                        # If they should dodge, than find the dodge velocity.
                        rad_difference = math.radians(direction)
                        x += math.cos(rad_difference) * move
                        y += math.sin(rad_difference) * move
                    else:
                        # Else move away from the neighbor from distance rather than view.
                        x += (self.center_x - neighbor.center_x)
                        y += (self.center_y - neighbor.center_y)

        # Find the average and apply it.
        if total:
            x /= total
            y /= total
        result = [x * self.rule_2_priority * 0.05, y * self.rule_2_priority * 0.05]
        return result

    def rule3(self):
        """
        Rule Three: Attempt to slow down or speed up to match the players velocity
        """
        result = [0.0, 0.0]
        if self.target_distance < SCREEN_WIDTH * 1.5 and abs(self.speed - self.target_speed) > 250:
            # If the target's speed is very different from the enemy and they are close enough, slow down.
            result[0] = (self.target_velocity[0] - self.velocity[0]) / 8
            result[1] = (self.target_velocity[1] - self.velocity[1]) / 8
        elif self.target_distance < SCREEN_WIDTH:
            # If the enemy is close to the target slow down to match their speed.
            result[0] = (self.target_velocity[0] - self.velocity[0]) / 4
            result[1] = (self.target_velocity[1] - self.velocity[1]) / 4

        return [result[0] * 0.05 * self.rule_3_priority, result[1] * 0.05 * self.rule_3_priority]

    def rule4(self):
        """
        Rule Four: Avoid being in front of the player.
        """
        player = self.handler.player
        angle_to_self = vector.find_angle((self.center_x, self.center_y),
                                          (player.center_x, player.center_y))
        difference = vector.calc_difference(player.angle, angle_to_self)
        direction = 0
        move = 0

        # Same as with Rule 2. If the Left is better dodge left, elif the right is better dodge right.
        if difference[0] < 45 and difference[0] < difference[1]:
            direction = player.angle - 90
            move = (45 - difference[0])
        if difference[1] < 45 and difference[1] < difference[0]:
            direction = player.angle + 90
            move = (45 - difference[1])
        x, y = 0, 0
        # As before if they need to dodge find the dodge acceleration.
        if direction:
            rad_difference = math.radians(direction)
            x = math.cos(rad_difference) * move
            y = math.sin(rad_difference) * move
        result = [x * self.rule_4_priority * 0.05, y * self.rule_4_priority * 0.05]
        return result

    def rule5(self):
        """
        Rule Five: avoid planets
        """
        x = 0
        y = 0
        total = 0
        for influence in self.gravity_handler.gravity_influences:
            # For each gravity influence find the distance from the edge of the sprite.
            distance = vector.find_distance((self.center_x, self.center_y),
                                            (influence.center_x, influence.center_y)) - (influence.width / 2)

            # if the enemy is within 2500 pixels dodge the planet.
            if 0 < distance < 2500:

                total += 1

                # Find the opposite direction, and use that as the acceleration
                neg_direction = math.radians(vector.find_angle((self.center_x, self.center_y),
                                                               (influence.center_x, influence.center_y)))

                neg_x = math.cos(neg_direction) * distance
                neg_y = math.sin(neg_direction) * distance

                x += neg_x / 2500
                y += neg_y / 2500

                # Inverse the acceleration so the closer they are the stronger the push.
                if x < 0:
                    x = -1 - x
                else:
                    x = 1 - x

                if y < 0:
                    y = -1 - y
                else:
                    y = 1 - y

                # Increase the acceleration by 3
                x *= 3
                y *= 3

        # Find the average.
        if total:
            x /= total
            y /= total

        result = [x * self.rule_5_priority, y * self.rule_5_priority]
        return result

    """
    Ability Rules:
        Note:
            A Spacecraft can have multiple abilities but only on will be active at a time
            When doing abilities the order in which they are sorted in the json file changes there priority
            if the ability takes any frames of animation they go in a second list in the same order
    Invisibility: for a set amount of time based on the difficulty of the enemy,
                  change the frame to a perfect black frame. Also change their rules to strongly dodge attacks
                  and try move away from the player

    """

    def invisibility_rule(self, frames=None):
        """
        The invisibility ability sets their texture to a pitch black silhouette. This means they hide stars but are still
        hard to see.
        """

        if self.active_ability is None:
            # If the no ability is currently active.
            do_rule = False
            if time.time() > self.cool_down and self.target_distance > 330:
                # If they are far enough from the player and the cool down is over than do the ability.
                do_rule = True
            if do_rule:
                # Set the ability to 'invisibility', set the texture and set the duration.
                self.active_ability = 'invisibility'
                self.active_frames = self.ability_frames[frames]
                self.start_time = time.time()
                self.duration = 3 * self.handler.difficulty
                self.texture = self.active_frames[0]

                # Change the priority of rule 4 so they dodge more.
                self.rule_4_priority = 2.0

                # Remove the point which aims at the enemy.
                for point in self.handler.player.enemy_pointers:
                    if point.target == self:
                        point.remove_from_sprite_lists()
                        del point

        elif time.time() > self.start_time + self.duration:
            # If the ability is over reset all of the variables.

            # Turn of the active ability and frames.
            self.active_ability = None
            self.active_frames = []

            # Reset the texture and the rules affected.
            self.texture = self.textures[self.frame]
            self.rule_4_priority = self.type_data['rules'][3]

            # Reset the time variables.
            self.start_time = 0
            self.duration = 0

            # Find the cool down.
            self.cool_down = time.time() + self.cool_down_delay

            # Create a new pointer for the enemy.
            point = ui.Pointer()
            point.holder = self.handler.player
            point.target = self
            self.handler.player.enemy_pointers.append(point)
