import arcade
import math

import vector


class Pointer(arcade.Sprite):

    def __init__(self):

        super().__init__()

        self.holder = None
        self.target = None
        self.push_out = 45
        self.texture = arcade.load_texture("Enemy Direction.png")
        self.scale = 0.15

    def on_update(self, delta_time: float = 1/60):
        holder_pos = self.holder.center_x, self.holder.center_y
        target_pos = self.target.center_x, self.target.center_y
        self.angle = vector.find_angle(target_pos, holder_pos)
        rad_angle = math.radians(self.angle)
        self.center_x = holder_pos[0] + (math.cos(rad_angle)*self.push_out)
        self.center_y = holder_pos[1] + (math.sin(rad_angle)*self.push_out)

