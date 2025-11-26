import yaml


def read_yaml(file_path):
    """ Safely reads a .yaml file and returns a dict.

    Args:
        file_path (str): Path of .yaml file.

    Returns:
        dict: Dict correspond to the values in the .yaml file.
    """
    
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)