from PIL import ImageFont


class Scene():
    def __init__(self):
        """ Defines font and colour details that are used by all scenes.
        This class is extended by those of specific scene types. An object of this class type is never created directly.
        """

        # Fonts.
        self.FONTS = {
            'sm':       ImageFont.load('assets/fonts/Tamzen5x9r.pil'),
            'sm_bold':  ImageFont.load('assets/fonts/Tamzen5x9b.pil'),
            'med':      ImageFont.load('assets/fonts/Tamzen6x12r.pil'),
            'med_bold': ImageFont.load('assets/fonts/Tamzen6x12b.pil'),
            'lrg':      ImageFont.load('assets/fonts/Tamzen8x15r.pil'),
            'lrg_bold': ImageFont.load('assets/fonts/Tamzen8x15b.pil'),
        }

        # Colours.
        self.COLOURS = {
            'white':    (255, 255, 255),
            'black':    (0, 0, 0),
            'red':      (255, 50, 50),
            'yellow':   (255, 209, 0)
        }