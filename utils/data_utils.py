import yaml


def read_yaml(file_path) -> dict:
    """ Safely reads a .YAML file and returns a dict.

    Args:
        file_path (str): Path of .YAML file.

    Returns:
        dict: Dict correspond to the values in the .YAML file.
    """
    
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)