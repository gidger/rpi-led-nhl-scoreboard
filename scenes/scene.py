from PIL import Image, ImageDraw, ImageFont


class Scene():
    """ A scene can be thought of as a visual idea displayed on the matrix. These can be today's games, standings, etc.
    This class is extended by those of specific scene types. An object of this class type is never created directly.
    """
    
    def __init__(self):
        """ Defines font and colour details that are used by all scenes.
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
            'white':        (255, 255, 255),
            'black':        (0, 0, 0),
            'grey_dark':    (70, 70, 70),
            'grey_light':   (180, 180, 180),
            'red':          (255, 50, 50),
            'yellow':       (255, 209, 0),
            'green':        (28, 122, 0)
        }

    def create_faded_image(self, image, overlay_opacity):
        """ Takes the provided image and overlay_opacity and returns the same image with a black overlay with overlay_opacity applied.
        We can't use real opacity due to RGBMatrix only being able to display images of type RGB on a matrix.
        As such, we need to apply a black overlay with varying opacities to simulate a fade.

        Args:
            image (Image): Image to apply black overlay to.
            overlay_opacity (int): Opacity of black overlay to apply.

        Returns:
            Image: Provided image with a black overlay applied with opacity of overlay_opacity.
        """

        # Convert input image to RGBA. Needed in order to apply fade overlay.
        image = image.convert('RGBA')

        # Create a new image of the same size with a black rectangle with opacity of the input overlay_opacity.
        fade_overlay_image = Image.new('RGBA', image.size)
        fade_overlay_draw = ImageDraw.Draw(fade_overlay_image)
        fade_overlay_draw.rectangle([(0,0), fade_overlay_image.size], fill=self.COLOURS['black']+(overlay_opacity,))
        
        # Apply the overlay to the provided image and convert to RGB.
        faded_image = Image.alpha_composite(image, fade_overlay_image)
        faded_image = faded_image.convert('RGB')

        return faded_image