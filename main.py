from scenes.game_scenes.games_scene_nhl import NHLGamesScene
from scenes.fav_team_next_game_scenes.fav_team_next_game_scene_nhl import NHLFavTeamNextGameScene
from scenes.standings_scenes.standings_scene_nhl import NHLStandingsScene

from setup.matrix_setup import matrix_options, determine_matrix_brightness
from utils import data_utils


def run_scoreboard():
    # Instantiate objects for each of the "scenes" (i.e., visual ideas) supported.
    scene_mapping = {
        'nhl_games': NHLGamesScene(),
        'nhl_fav_team_next_game': NHLFavTeamNextGameScene(),
        'nhl_standings': NHLStandingsScene()
    }

    # Infinite loop.
    while True:
        # Determine the order scenes should be displayed per config.yaml.
        scene_order = data_utils.read_yaml('config.yaml')['scene_order']

        # Set matrix brightness.
        matrix_options.brightness = determine_matrix_brightness()

        # Display each scene in the order specified above.
        for scene in scene_order:
            scene_mapping[scene].display_scene()

# Entrypoint.
if __name__ == '__main__':
    run_scoreboard()