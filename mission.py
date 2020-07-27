import time
import math
import json

import arcade

import vector
import player
import space
import ui
import enemy_handler


class Mission:

    def __init__(self, game_window, level_data: dict = None):
        self.game_window = game_window

        if level_data is not None:
            self.num_stages = level_data['stages']
            self.possible_enemies = level_data['possible_enemies']
            self.possible_bosses = level_data['possible_bosses']
            self.planets_data = level_data['planets']
            self.satellites_data = level_data['satellites']
            self.asteroids_data = level_data['asteroids']
        else:
            self.num_stages = 5
            self.possible_enemies = None
            self.possible_bosses = None
            self.planets_data = None
            self.satellites_data = None
            self.asteroids_data = None
        self.enemy_handler = None
        self.planets = None
        self.satellites = None
        self.asteroids = None

    def load_mission(self):
        self.enemy_handler = enemy_handler.EnemyHandler(self.possible_enemies, self.possible_bosses)
        """
        Asteroids not yet implemented.
        Satellites not yet implemented.
        
        if self.satellites_data is not None:
            self.satellites = arcade.SpriteList()
            for data in self.satellites_data:
                satellite = space.Satellite(data)
                self.satellites.append(asteroid)
           
        if self.asteroids_data is not None:
            self.asteroids = arcade.SpriteList()
            for data in self.asteroids_data:
                asteroid = space.Asteroid(data)
                self.asteroids.append(asteroid)
        """

        if self.planets_data is None:
            self.planets = arcade.SpriteList()
            self.planets.append(space.Planet())
        else:
            self.planets = arcade.SpriteList()
            for data in self.planets_data:
                planet = space.Planet(data)
                self.planets.append(planet)

    def draw(self):
        if self.enemy_handler is not None:
            self.enemy_handler.draw()

        if self.planets is not None:
            for planet in self.planets:
                planet.draw()

        if self.asteroids is not None:
            for asteroid in self.asteroids:
                asteroid.draw()

        if self.satellites is not None:
            for satellites in self.satellites:
                satellites.draw()

    def on_update(self, delta_time: float = 1/60):
        if self.enemy_handler is not None:
            self.enemy_handler.on_update(delta_time)

        if self.planets is not None:
            self.planets.on_update(delta_time)

        if self.asteroids is not None:
            for asteroid in self.asteroids:
                asteroid.on_update(delta_time)

        if self.satellites is not None:
            for satellites in self.satellites:
                satellites.on_update(delta_time)
