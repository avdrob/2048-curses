import enum


# TODO: Use game mode
class Mode(enum.Enum):
    Small = 1
    Large = 2


# Probability to get 4 (instead of 2), in percentages
four_probability = 10

numbers_large = {
    2: [
        '####',
        '   #',
        '####',
        '#   ',
        '####'
    ],
    4: [
        '#  #',
        '#  #',
        '####',
        '   #',
        '   #'
    ],
    8: [
        '####',
        '#  #',
        '####',
        '#  #',
        '####'
    ],
    16: [
        '  # ####',
        ' ## #  ',
        '# # ####',
        '  # #  #',
        '  # ####',
    ],
    32: [
        '#### ####',
        '   #    #',
        '#### ####',
        '   # #   ',
        '#### ####'
    ],
    64: [
        '#### #  #',
        '#    #  #',
        '#### ####',
        '#  #    #',
        '####    #'
    ],
    128: [
        '  # #### ####',
        ' ##    # #  #',
        '# # #### ####',
        '  # #    #  #',
        '  # #### ####'
    ],
    256: [
        '#### #### ####',
        '   # #    #   ',
        '#### #### ####',
        '#       # #  #',
        '#### #### ####'
    ],
    512: [
        '####   # ####',
        '#     ##    #',
        '#### # # ####',
        '   #   # #   ',
        '####   # ####'
    ],
    1024: [
        '  # #### #### #  #',
        ' ## #  #    # #  #',
        '# # #  # #### ####',
        '  # #  # #       #',
        '  # #### ####    #'
    ],
    2048: [
        '#### #### #  # ####',
        '   # #  # #  # #  #',
        '#### #  # #### ####',
        '#    #  #    # #  #',
        '#### ####    # ####'
    ],
    4096: [
        '#  # #### #### ####',
        '#  # #  # #  # #   ',
        '#### #  # #### ####',
        '   # #  #    # #  #',
        '   # #### #### ####'
    ],
    8192: [
        '####   # #### ####',
        '#  #  ## #  #    #',
        '#### # # #### ####',
        '#  #   #    # #   ',
        '####   # #### ####'
    ]
}

numbers_small = {k: [str(k)] for k in numbers_large}

game_modes = {
    Mode.Small: {
        'size': 4,
        'cell_nlines': 3,
        'cell_ncols': 7,
        'numbers': numbers_small,
    },
    Mode.Large: {
        'size': 4,
        'cell_nlines': 9,
        'cell_ncols': 21,
        'numbers': numbers_large
    }
}

colors = {
    None: (0, 188),   # Grey
    2: (0, 230),      # Black on Cornsilk
    4: (0, 224),      # Black on MistyRose
    8: (15, 216),     # White on LightSalmon
    16: (15, 214),    # White on Orange1
    32: (15, 208),    # White on DarkOrange
    64: (15, 202),    # White on OrangeRed
    128: (0, 222),    # Black on LightGoldenrod
    256: (15, 220),   # White on Gold1
    512: (15, 178),   # White on Gold3
    1024: (15, 136),  # White on DarkGoldenrod
    2048: (15, 172),  # White on Orange3
    4096: (0, 170),   # Black on Orchid
    8192: (15, 162)   # White on DeepPink
}

# color_pairs[None] = 1, color_pairs[2] = 2, etc.
color_pairs = {v: k for k, v in enumerate(colors, 1)}
