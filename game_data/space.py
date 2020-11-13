import math
import random

import arcade

import game_data.vector as vector

# the gravity constant for calculations.
GRAVITY_CONSTANT = 6.67408 * 10 ** (-12)


class GravityHandler:
    """
    Handles all of the gravity accelerations of each object in game.
    """

    def __init__(self):
        # The gravity influences, the objects that accelerate other object towards the.
        self.gravity_influences = arcade.SpriteList()

        # The gravity objects, the objects that get affected by gravity.
        self.gravity_objects = arcade.SpriteList()

    def set_gravity_object_influence(self, gravity_object):
        # adds a gravity influence.
        gravity_object.gravity_handler = self
        self.gravity_influences.append(gravity_object)

    def set_gravity_object(self, gravity_object):
        # adds a gravity object.
        gravity_object.gravity_handler = self
        self.gravity_objects.append(gravity_object)

    def calculate_each_gravity(self):

        # ### IT EXPECTS EACH OBJECT TO BE A SPRITE HOWEVER THAT IS NOT THE CASE SO IT COMPLAINS ###

        # for every gravity object calculate the gravity of evey influence and accelerate the object.
        for gravity_object in self.gravity_objects:
            gravity_object.gravity_acceleration = [0.0, 0.0]
            gravity_object.gravity_influences = []
            for influences in self.gravity_influences:

                # create vectors of the two objects positions. and find the distance from the objects.
                gravity_pos = (gravity_object.center_x, gravity_object.center_y)
                inf_pos = influences.center_x, influences.center_y
                base_distance = vector.find_distance(gravity_pos, inf_pos)

                # because the scale on screen is not the true scale an extra distance must be added to the sprite
                # without this the planet sprites would have to be 12 million pixels in size.
                # (to have a similar gravity to earth)
                distance = base_distance - (
                        influences.width / 2) + influences.planetary_radius

                # find the direction towards the influence.
                direction = math.radians(vector.find_angle(inf_pos, gravity_pos))

                # calculate the force the influence and the acceleration of the object.
                force = (GRAVITY_CONSTANT * gravity_object.weight * influences.weight) / (distance ** 2)
                acceleration = force / gravity_object.weight

                # if the object is within the radius of the influence push them out of the influence.
                if base_distance <= influences.width / 2:
                    acceleration = force * 25 / gravity_object.weight
                    direction += math.pi

                    # if the objects health is greater than Zero damage them.
                    if gravity_object.health > 0:
                        gravity_object.health -= 1

                # the acceleration as a vector.
                a_x = math.cos(direction) * acceleration
                a_y = math.sin(direction) * acceleration
                acceleration_vector = (a_x, a_y)

                # apply the acceleration.
                gravity_object.gravity_influences.append(acceleration_vector)
                gravity_object.gravity_acceleration[0] += a_x
                gravity_object.gravity_acceleration[1] += a_y

    def reset(self):
        # If the game resets, reset the gravity influences to ensure nothing carries over.

        self.gravity_influences = arcade.SpriteList()
        self.gravity_objects = arcade.SpriteList()


class Planet(arcade.Sprite):

    def __init__(self, game_window, planet_data: dict = None):
        super().__init__()

        self.game_window = game_window
        self.gravity_handler = None
        self.satellites = None
        self.game_window.gravity_handler.set_gravity_object_influence(self)

        # Set all of the data of this planet.
        if planet_data is not None:
            self.name = planet_data['name']
            self.type = planet_data['type']
            self.subset = planet_data['subset']
            self.weight = planet_data['weight']
            self.center_x = planet_data['x_pos']
            self.center_y = planet_data['y_pos']
            self.planetary_radius = planet_data['radius']
            self.satellites_data = planet_data['satellites']

            # due to the imperfect scaling of sprites for memory, gas giants are scaled to a larger size.
            if self.subset == "gas":
                self.scale = 2.5
                self.width = 8000
                self.height = 8000
            else:
                self.scale = 1.5
                self.width = 1920
                self.height = 1920

            self.texture = self.game_window.planet_sprites[self.subset][self.type][planet_data['tex']]

            # create the satllites.
            self.satellites = arcade.SpriteList()
            for satellites in self.satellites_data:
                satellite = Satellite(self, satellites)
                if satellites['gravity']:
                    self.game_window.gravity_handler.set_gravity_object_influence(satellite)
                self.satellites.append(satellite)

    def draw(self):
        # if the planet has satellites draw them.
        if self.satellites is not None:
            self.satellites.draw()
        super().draw()

    def on_update(self, delta_time: float = 1/60):
        # update all satellites.
        self.satellites.on_update(delta_time)

    def kill(self):
        # destroy all satellites.
        for satellite in self.satellites:
            satellite.kill()

        # kill self.
        self.remove_from_sprite_lists()
        del self


class Satellite(arcade.Sprite):

    def __init__(self, parent, satellite_data: dict = None):
        super().__init__()

        # choose the angle the satellite spawns at.
        self.starting_angle = random.randrange(0, 360)
        self.current_angle = self.starting_angle

        self.parent = parent
        self.gravity_handler = None

        self.data = satellite_data

        # variables initialised in case no data was supplied.
        self.orbit = 0
        self.gravity = False
        self.planetary_radius = 0
        self.weight = 0
        self.type = None
        self.subset = None
        self.speed = 0
        self.file_name = ''

        self.velocity = [0.0, 0.0]

        if satellite_data is not None:
            # if the object will affect gravity objects.
            self.gravity = satellite_data['gravity']

            # its planetary radius and weight for gravity calculations.
            self.planetary_radius = satellite_data['radius']
            self.weight = satellite_data['weight']

            self.type = satellite_data['type']
            self.subset = satellite_data['subset']
            self.speed = satellite_data['speed']
            self.file_name = satellite_data['texture']
            self.texture = arcade.load_texture(self.file_name)
            self.orbit = parent.width + self.width + satellite_data['orbit']

            # due to memory issues the different types of satellites have different gravity.
            if self.type == "moon":
                self.scale = 1.5
                self.health = 1
            else:
                self.scale = 0.5
                self.health = 550

            # position the satellite based on its orbit and angle.
            rad_angle = math.radians(self.current_angle)
            self.center_x = self.parent.center_x + math.cos(rad_angle) * self.orbit
            self.center_y = self.parent.center_y + math.sin(rad_angle) * self.orbit

    def setup(self, gravity_handler=None):

        # If it should have gravity adding it to the gravity object
        if self.gravity and gravity_handler is None:
            raise ValueError("Gravity Handler Expected For Satellite")
        elif self.gravity:
            self.gravity_handler = gravity_handler
            self.gravity_handler.set_gravity_object_influence(self)

    def on_update(self, delta_time: float = 1 / 60):
        # applying its calculated velocity.
        self.center_x += self.velocity[0] * delta_time
        self.center_y += self.velocity[1] * delta_time

        # finding its velocity
        angle = vector.find_angle((self.center_x, self.center_y), (self.parent.center_x, self.parent.center_y)) + 90
        rad_angle = math.radians(angle)
        self.velocity[0] = math.cos(rad_angle) * self.speed * 30
        self.velocity[1] = math.sin(rad_angle) * self.speed * 30

    def kill(self):
        # kill self
        self.remove_from_sprite_lists()
        del self
