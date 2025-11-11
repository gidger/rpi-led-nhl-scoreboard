from PIL import Image


def crop_image(image):
    """ Crops all transparent space around an image.

    Args:
        image (image): Image to have transparent space cropped.

    Returns:
        image: Cropped image.
    """

    # Get the bounding box of the image. Aka, boundries of what's non-transparent. Crop the image to the contents of the bounding box.
    bbox = image.getbbox()
    image = image.crop(bbox)
    
    # Create a new image object for the output image. Paste the cropped image onto the new image.
    cropped_image = Image.new('RGBA', image.size)
    cropped_image.paste(image)

    return cropped_image

def clear_image(image, image_draw):
    """ Draws a black rectangle over a specific image. Effectively, "clearing" it to default state.

    Args:
        image (Image): PIL Image to clear.
        image_draw (ImageDraw): PIL ImageDraw object associated with the image.
    """
    image_draw.rectangle([(0,0), image.size], fill=(0,0,0,255))