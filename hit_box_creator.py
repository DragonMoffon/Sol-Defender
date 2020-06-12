import arcade

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
SCREEN_TITLE = "Hit Box Maker"


class HitBoxWindow(arcade.Window):
    """
    PLEASE READ ALL OF THIS COMMENT

    This Script is used to easily make a sprite's hit box.

    The Sprite should be scaled up by 10 to use this script properly.

    HOW TO USE:

        On line 52 put the name of your sprite into the brackets as a string. You can now run the script.

        The mouse cursor is a blue square that shows where a point of the hit box will appear.

        To add a point simply Left Click with the mouse, this will add a point to the pointlist.

        The first point is always Red, all other points are Lime Green

        If a point is in the wrong place simply press D to delete the last placed point.

        Once every outer vertex(corner) on the sprite has a point you can copy the tuple of points printed in the terminal. This is your final pointlist for you sprite's hit box

    WARNINGS:

        The mouse pointer is rounded to every 5 pixels this means it can suddenly jump messing up points so be careful.

        The screen size may be too small. If it is DO NOT scale the sprite simply change the size of the screen

        The Delete button (the D key) ONLY removes the LAST point added. If you make a mistake but continue you will have to delete all you work back to the messed up point.

        You may find that having a point on every outer vertex may cause the sprite to catch on objects.
        you can mitigate this by skipping points that travel in a diagonal mostly straight line, or skipping over large gaps in the sprite.

    """

    def __init__(self, width, height, title):
        super().__init__(width, height, title)

        arcade.set_background_color(arcade.color.WHITE)

        # This is the sprite you wish to edit..
        self.sprite = arcade.Sprite()
        self.sprite.texture = arcade.load_texture("Sprites/Enemy Bullet.png")  # Put the name of the texture in the "". Make sure the your texture's pixels are 10x.

        # This centers the sprite
        self.sprite.center_x = SCREEN_WIDTH//2
        self.sprite.center_y = SCREEN_HEIGHT//2

        # This is the mouses position relative to the center of the sprite.
        self.relative_mouse_x = 0
        self.relative_mouse_y = 0

        # This is the mouse position relative of the 0,0 coordinate point, however it will is rounded to the nearest 5 for ease of use.
        self.mouse_x = 0
        self.mouse_y = 0

        # The pointlist that becomes the sprite's hit box.
        self.point_list = []

        # This hides the mouse cursor so you can see the rounded mouse position for ease of use.
        self.set_mouse_visible(False)

        # These variables are to ensure that the point rounds to the corners of every pixel
        self.round_x = 0
        if self.sprite.width/10 % 2 != 0:
            self.round_x = 5

        self.round_y = 0
        if self.sprite.height/10 % 2 != 0:
            self.round_y = 5

    def on_draw(self):
        """
        This Draws the Hit Box of the sprite, as well as the points of the pointlist, the mouse pointer, and the text saying the relative mouse position.
        """
        arcade.start_render()

        # This text says the relative mouse position.
        text = "Relative X: " + str(self.relative_mouse_x) + " : " + "Relative Y: " + str(self.relative_mouse_y)
        arcade.draw_text(text, SCREEN_WIDTH // 2, SCREEN_HEIGHT - 50,
                         arcade.color.BLACK, font_size=15, anchor_x="center")

        # The sprite itself being drawn and the center point of the sprite
        self.sprite.draw()
        arcade.draw_point(self.sprite.center_x, self.sprite.center_y, arcade.color.RADICAL_RED, 10)

        # This only draws the points of the pointlist if there are any points to draw. This is to stop errors
        if len(self.point_list) != 0:

            # for every point in the pointlist draw a Lime Green Square
            for point in self.point_list:
                arcade.draw_point(self.sprite.center_x + point[0],
                                  self.sprite.center_y + point[1], arcade.color.LIME_GREEN, 5)
            # draw the actual hit box of the sprite
            self.sprite.draw_hit_box(color=arcade.color.LIME_GREEN)

            # draw a red square for the first point in the pointlist. Try making a circut of points around the outer edge of the sprite that starts and ends here.
            arcade.draw_point(self.sprite.center_x + self.point_list[0][0],
                              self.sprite.center_y + self.point_list[0][1], arcade.color.RADICAL_RED, 5)

        # this draws the mouse pointer.
        arcade.draw_point(self.mouse_x, self.mouse_y, arcade.color.OCEAN_BOAT_BLUE, 5)

    def on_mouse_motion(self, x: float, y: float, dx: float, dy: float):
        """
        When the mouse moves this sets the X and Y position of the mouse pointer rounded to the nearest 5 and sets the mouses relative position rounded to 5
        """

        # Sets the mouse pointer X and Y to the nearest 5
        self.mouse_x = round_to_num(x, self.round_x)
        self.mouse_y = round_to_num(y, self.round_y)

        # Sets the relative mouse pointer X and Y to the nearest %
        self.relative_mouse_x = self.mouse_x - self.sprite.center_x
        self.relative_mouse_y = self.mouse_y - self.sprite.center_y

    def on_mouse_press(self, x, y, button, key_modifiers):
        # This adds the relative position of the mouse to the pointlist
        self.point_list.append((self.relative_mouse_x, self.relative_mouse_y))

        # This sets the Sprites Hit Box to the pointlist only if there is 1 or more points in the list. To protect against errors
        if len(self.point_list) >= 1:
            self.sprite.set_hit_box(self.point_list)
            # Prints the pointlist for access once done.
            print(self.point_list)

    def on_key_press(self, key: int, modifiers: int):
        # If the D key is pressed remove the last point from the pointlist
        if key == arcade.key.D:
            self.point_list.pop(-1)
            # This sets the Sprites Hit Box to the pointlist only if there is 1 or more points in the list. To protect against errors
            if len(self.point_list) >= 1:
                self.sprite.set_hit_box(self.point_list)
                # Prints the pointlist for access once done.
                print(self.point_list)


def round_to_num(round_num, num_to_round):
    """
    This function rounds the last character (including a decimal place e.g. 123. turns into 1235) in any number to the inputted .
    e.g. 122 is rounded to 125, or 129.3421 is rounded to 129.3425
    """
    # Initialise the list that will hold each character of the number.
    str_list = []
    # Add each character to the str-list.
    [str_list.append(i) for i in str(round_num)]

    # If the last character is not 5, make it 5
    if str_list[-1] != str(num_to_round):
        str_list[-1] = str(num_to_round)

    # turn the list of characters into a single string
    string = ""
    for i in str_list:
        string += i

    # return the string as a new float.
    return float(string)


def main():
    """ Main method """
    game = HitBoxWindow(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
    arcade.run()


if __name__ == "__main__":
    main()