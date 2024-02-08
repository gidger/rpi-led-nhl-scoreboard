from PIL import Image


def crop_image(image) -> Image:
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
    cropped_image = Image.new('RGB', image.size, (0, 0, 0, 255))
    cropped_image.paste(image)

    return cropped_image