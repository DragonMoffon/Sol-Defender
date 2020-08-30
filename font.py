import arcade


letter_set = []
for y in range(6):
    for x in range(7):
        letter = arcade.load_texture("Sprites/Font Plate Blue.png", x * 70, (y * 70), 70, 70)
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
    " ": 41
}
LETTER_SIZE = 70


def gen_letter_list(string: str = None, s_x: float = 0, s_y: float = 0, scale: float = 0.2, gap: int = 10):
    """
    :param string: The actual string that is being converted
    :param s_x: The center x position of the first letter
    :param s_y: The center y position of the first letter
    :param scale: The scale of the sprite going from 0.1 to 1
    :param gap: The gap between the letters that is affected by scale
    :return: It returns a SpriteList with all of the letter as Sprites
    """
    letter_list = arcade.SpriteList()
    string.lower()
    for index, char in enumerate(string):
        if char != " ":
            texture = LETTERS[LETTER_CODE[char]]
            cur_letter = arcade.Sprite(scale=scale, center_x=s_x + (((gap + LETTER_SIZE) * scale) * index), center_y=s_y)
            cur_letter.texture = texture
            letter_list.append(cur_letter)
    return letter_list
