import arcade
from dataclasses import dataclass
from array import array
import arcade.gl as gl
import random
import time
import math

import vector

SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768
TITlE = "Particle Test"

PARTICLE_COUNT = 15

MIN_FADE_TIME = 0.25
MAX_FADE_TIME = 1.5


@dataclass
class Burst:
    buffer: gl.Buffer
    vao: gl.Geometry
    start_time: float


class ParticleWindow(arcade.Window):

    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, TITlE)
        self.burst_list = []
        self.down = False
        self.mouse_pos = [0, 0]
        self.angle = 0
        self.num_particles = 1

        self.duration = 2500
        self.time = 0
        self.start = 0

        self.program = self.ctx.load_program(
            vertex_shader="vertex_shader.glsl",
            fragment_shader="fragment_shader.glsl"
        )

        self.ctx.enable_only(self.ctx.BLEND)

    def on_draw(self):
        """ Draw everything """
        self.clear()

        self.ctx.point_size = 5 * self.get_pixel_ratio()

        for burst in self.burst_list:
            self.program['time'] = time.time() - burst.start_time

            burst.vao.render(self.program, mode=self.ctx.POINTS)

    def on_update(self, dt):
        """ Update everything """
        temp_list = self.burst_list.copy()
        for burst in temp_list:
            if time.time() - burst.start_time > MAX_FADE_TIME:
                self.burst_list.remove(burst)

        if self.down:

            if (time.time() * 1000) - self.start:
                self.time = ((time.time() * 1000) - self.start) / self.duration
            else:
                self.time = 0

            if self.time >= 1:
                self.num_particles = PARTICLE_COUNT
            else:
                count = 1

                adj_t = self.time/1
                count = adj_t**3

                self.num_particles = round(count * PARTICLE_COUNT)
                if self.num_particles < 1:
                    self.num_particles = 1

            def _gen_initial_data(initial_x, initial_y):
                for i in range(self.num_particles):
                    angle = self.angle + math.radians(random.uniform(-5, 5))
                    speed = 0.3 + random.uniform(-0.15, 0.15)
                    dx = math.cos(angle) * speed
                    dy = math.sin(angle) * speed
                    fade_rate = random.uniform(1 / MIN_FADE_TIME, 1 / MAX_FADE_TIME)
                    yield initial_x
                    yield initial_y
                    yield dx
                    yield dy
                    yield fade_rate

            x2 = self.mouse_pos[0] / self.width * 2. - 1.
            y2 = self.mouse_pos[1] / self.height * 2. - 1.

            initial_data = _gen_initial_data(x2, y2)

            buffer = self.ctx.buffer(data=array('f', initial_data))

            buffer_description = gl.BufferDescription(buffer, '2f 2f f', ['in_pos', 'in_vel', 'in_fade'])

            vao = self.ctx.geometry([buffer_description])

            burst = Burst(buffer=buffer, vao=vao, start_time=time.time())
            self.burst_list.append(burst)

    def on_mouse_press(self, x: float, y: float, button: int, modifiers: int):
        """ User clicks mouse """
        self.down = True
        self.start = time.time() * 1000

    def on_mouse_release(self, x: float, y: float, button: int,
                         modifiers: int):
        """ User stops clicking mouse"""
        self.down = False

    def on_mouse_motion(self, x: float, y: float, dx: float, dy: float):
        self.angle = math.radians(vector.find_angle((0, 0), (dx, dy)))
        self.mouse_pos = (x, y)


if __name__ == '__main__':
    """window = ParticleWindow()
    window.center_window()
    arcade.run()"""

    print(vector.find_angle((-26, -33), (0, 0)))
