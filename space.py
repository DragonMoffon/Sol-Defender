import math
import random

import arcade

import vector

GRAVITY_CONSTANT = 6.67408 * 10 ** (-12)


class GravityHandler:

    def __init__(self):
        self.gravity_influences = arcade.SpriteList()
        self.gravity_objects = arcade.SpriteList()

    def set_gravity_object_influence(self, gravity_object):
        gravity_object.gravity_handler = self
        self.gravity_influences.append(gravity_object)

    def set_gravity_object(self, gravity_object):
        gravity_object.gravity_handler = self
        self.gravity_objects.append(gravity_object)

    def calculate_each_gravity(self):
        for gravity_object in self.gravity_objects:
            gravity_object.gravity_acceleration = [0.0, 0.0]
            gravity_object.gravity_influences = []
            for influences in self.gravity_influences:
                gravity_pos = (gravity_object.center_x, gravity_object.center_y)
                inf_pos = influences.center_x, influences.center_y
                base_distance = vector.find_distance(gravity_pos, inf_pos)
                distance = base_distance - (
                        influences.width / 2) + influences.planetary_radius
                direction = math.radians(vector.find_angle(inf_pos, gravity_pos))
                force = (GRAVITY_CONSTANT * gravity_object.weight * influences.weight) / (distance ** 2)
                acceleration = force / gravity_object.weight
                if base_distance <= influences.width / 2:
                    acceleration = force * 25 / gravity_object.weight
                    direction += math.pi
                    if gravity_object.health > 0:
                        gravity_object.health -= 1
                a_x = math.cos(direction) * acceleration
                a_y = math.sin(direction) * acceleration
                acceleration_vector = (a_x, a_y)
                #  print("distance:", distance, "SPEED!:", gravity_object.velocity)
                gravity_object.gravity_influences.append(acceleration_vector)
                gravity_object.gravity_acceleration[0] += a_x
                gravity_object.gravity_acceleration[1] += a_y

    def reset(self):
        self.gravity_influences = arcade.SpriteList()
        self.gravity_objects = arcade.SpriteList()


class Planet(arcade.Sprite):

    def __init__(self, game_window, planet_data: dict = None):
        super().__init__()

        self.game_window = game_window
        self.gravity_handler = None
        self.satellites = None
        self.game_window.gravity_handler.set_gravity_object_influence(self)

        if planet_data is not None:
            self.name = planet_data['name']
            self.type = planet_data['type']
            self.subset = planet_data['subset']
            self.weight = planet_data['weight']
            self.center_x = planet_data['x_pos']
            self.center_y = planet_data['y_pos']
            self.planetary_radius = planet_data['radius']
            self.satellites_data = planet_data['satellites']
            if self.subset == "gas":
                self.scale = 2.5
                self.width = 8000
                self.height = 8000
            else:
                self.scale = 1.5
                self.width = 1920
                self.height = 1920
            self.texture = self.game_window.planet_sprites[self.subset][self.type][planet_data['tex']]

            self.satellites = arcade.SpriteList()
            for satellites in self.satellites_data:
                satellite = Satellite(self, satellites)
                if satellites['gravity']:
                    self.game_window.gravity_handler.set_gravity_object_influence(satellite)
                self.satellites.append(satellite)

    def draw(self):
        if self.satellites is not None:
            self.satellites.draw()
        super().draw()

    def on_update(self, delta_time: float = 1/60):
        self.satellites.on_update(delta_time)

    def kill(self):
        for satellite in self.satellites:
            satellite.kill()
        self.remove_from_sprite_lists()
        del self


class Satellite(arcade.Sprite):

    def __init__(self, parent, satellite_data: dict = None):
        super().__init__()
        self.starting_angle = random.randrange(0, 360)
        self.current_angle = self.starting_angle

        self.parent = parent
        self.gravity_handler = None

        self.data = satellite_data

        self.orbit = 0
        self.gravity = False
        self.planetary_radius = 0
        self.weight = 0
        self.type = None
        self.subset = None
        self.speed = 0
        self.file_name = ''

        if satellite_data is not None:
            self.gravity = satellite_data['gravity']
            self.planetary_radius = satellite_data['radius']
            self.weight = satellite_data['weight']
            self.type = satellite_data['type']
            self.subset = satellite_data['subset']
            self.speed = satellite_data['speed']
            self.file_name = satellite_data['texture']
            self.texture = arcade.load_texture(self.file_name)
            self.orbit = parent.width + self.width + satellite_data['orbit']
            if self.type == "moon":
                self.scale = 1.5
                self.health = 1
            else:
                self.scale = 0.5
                self.health = 550

            rad_angle = math.radians(self.current_angle)
            self.center_x = self.parent.center_x + math.cos(rad_angle) * self.orbit
            self.center_y = self.parent.center_y + math.sin(rad_angle) * self.orbit

    def setup(self, gravity_handler=None):
        if self.gravity and gravity_handler is None:
            raise ValueError("Gravity Handler Expected For Satellite")
        elif self.gravity:
            self.gravity_handler = gravity_handler
            self.gravity_handler.set_gravity_object_influence(self)

    def on_update(self, delta_time: float = 1 / 60):
        self.current_angle += self.speed * delta_time
        rad_angle = math.radians(self.current_angle)
        self.center_x = self.parent.center_x + math.cos(rad_angle) * self.orbit
        self.center_y = self.parent.center_y + math.sin(rad_angle) * self.orbit

    def kill(self):
        self.remove_from_sprite_lists()
        del self


class SolarSystem(arcade.SpriteList):

    def __init__(self, setup: bool = False):
        super().__init__()
        if setup:
            self.generate_solar_system()

    def generate_solar_system(self):
        pass

    def get_planet(self, planet_data):
        pass
