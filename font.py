import arcade

LETTER_SIZE = 14

letter_set = []
for y in range(6):
    for x in range(7):
        letter = arcade.load_texture("Sprites/Font Plate Blue.png",
                                     x * LETTER_SIZE, (y * LETTER_SIZE),
                                     LETTER_SIZE, LETTER_SIZE)
        letter_set.append(letter)
LETTERS = tuple(letter_set)

LETTER_CODE = {
    "a": 0,
    "b": 1,
    "c": 2,
    "d": 3,
    "e": 4,
    "f": 5,
    "g": 6,
    "h": 7,
    "i": 8,
    "j": 9,
    "k": 10,
    "l": 11,
    "m": 12,
    "n": 13,
    "o": 14,
    "p": 15,
    "q": 16,
    "r": 17,
    "s": 18,
    "t": 19,
    "u": 20,
    "v": 21,
    "w": 22,
    "x": 23,
    "y": 24,
    "z": 25,
    "0": 26,
    "1": 27,
    "2": 28,
    "3": 29,
    "4": 30,
    "5": 31,
    "6": 32,
    "7": 33,
    "8": 34,
    "9": 35,
    ":": 36,
    "+": 37,
    "-": 38,
    "\"": 39,
    ".": 40,
    "%": 41
}

class LetterList(arcade.SpriteList):

    def __init__(self, string: str = None,
                 s_x: float = 0, s_y: float = 0,
                 scale: float = 1, gap: int = 2, mid_x=False):
        super().__init__()
        self.__x = 0
        self.__y = 0

        self.x = s_x
        self.y = s_y

        self.gen_letter_list(string, s_x, s_y, scale, gap, mid_x)

    def gen_letter_list(self, string: str = None,
                        s_x: float = 0, s_y: float = 0,
                        scale: float = 0.2, gap: int = 2, mid_x=False):
        """
        :param string: The actual string that is being converted
        :param s_x: The center x position of the first letter
        :param s_y: The center y position of the first letter
        :param scale: The scale of the sprite going from 0.1 to 1
        :param gap: The gap between the letters that is affected by scale
        :param mid_x: Changes the s_x to mean the middle x rather than the start.
        :return: It returns a SpriteList with all of the letter as Sprites
        """

        string = string.lower()
        if mid_x:
            total = (len(string) * LETTER_SIZE) + ((len(string) - 1) * gap)
            s_x = s_x - (total/2)
        for index, char in enumerate(string):
            if char != " " and char != "_":
                texture = LETTERS[LETTER_CODE[char]]
                cur_letter = arcade.Sprite(scale=scale,
                                           center_x=s_x + (((gap + LETTER_SIZE) * scale) * index),
                                           center_y=s_y)
                cur_letter.texture = texture
                self.append(cur_letter)

    @property
    def x(self):
        return self.__x

    @x.setter
    def x(self, value):
        diff_x = value - self.__x
        self.move(diff_x, 0)
        self.__x = value

    @property
    def y(self):
        return self.__y

    @y.setter
    def y(self, value):
        diff_y = value - self.__y
        self.move(0, diff_y)
        self.__y = value


DONKEY = """
    ██                                  ██
  ██▓▓██                              ██▓▓▓▓
  ██▓▓██                              ██▓▓▓▓
██▓▓▓▓██                              ██▓▓▓▓██
██▓▓▒▒▓▓██                          ██▓▓▒▒▓▓██
██▓▓▒▒▒▒▓▓▓▓                      ▓▓▓▓▒▒▒▒▓▓██
██▓▓▒▒▒▒▓▓██                      ██▒▒▒▒▒▒▓▓██
██▒▒▒▒▒▒▒▒██                      ██▒▒▓▓▒▒▓▓██
██▒▒▓▓▓▓▒▒██                      ██▓▓▓▓▒▒▓▓██
░░██▓▓▓▓▓▓▓▓▓▓                  ▓▓▓▓▓▓▓▓▓▓▓▓░░
  ██▒▒▓▓▓▓██▒▒██              ██▒▒██▓▓▓▓▒▒▓▓
  ██▒▒▓▓▓▓██████    ░░▒▒░░    ██████▓▓▓▓▒▒▓▓
  ░░██▓▓████████▓▓▒▒▒▒▓▓▒▒▒▒▓▓████████▓▓██
     ██▒▒████▓▓██▓▓██▓▓██▓▓██▓▓████▒▒██
       ██▓▓████▓▓▓▓▓▓▓▓▓▓▓▓▓▓████▓▓██
         ████▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓████
         ████▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓████
         ██▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓██
         ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓
         ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓██
       ██▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓
       ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓
     ██▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓██
     ██░░░░██▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓██░░░░██
       ▓▓░░░░▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░░░▓▓
       ██▓▓░░▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░▒▒██
       ▒▒██░░▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓██░░██▒▒
       ██░░▓▓██▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓██░░▓▓
       ██▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓██▓▓▓▓▓▓
       ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓
       ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓
       ██▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓██
         ██▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓██
         ██▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓██
         ██▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓██
         ██▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓██
           ▓▓▓▓▓▓▓▓▒▒░░▒▒▓▓▓▓▓▓██
           ▓▓▓▓██          ▓▓▓▓██
           ▓▓▓▓██        ░░▓▓▓▓██
           ▓▓██            ░░▓▓██
           ▓▓██            ░░▓▓██
           ░░░░              ░░░░
           ░░▒▒▒▒    ░░  ░░▒▒▒▒▒▒
           ▒▒██▒▒░░░░░░░░▒▒▓▓██▒▒
           ▒▒████▒▒▒▒▒▒▒▒▓▓████▒▒
           ▒▒▓▓██▓▓▓▓▓▓▓▓▓▓██▒▒▒▒
             ▒▒▒▒▓▓▓▓▓▓▓▓▓▓▓▓▒▒
               ▒▒▓▓▓▓▓▓▓▓▒▒▒▒
                ░░▒▒▒▒▒▒▒▒▒▒
                 ░░░░░░░░░░
"""