import os
from os import path
from cairosvg import svg2png

def main():
    # source = '/home/pi/nhl_scoreboard/Assets/Images/Team Logos/SVG/'
    # destination = '/home/pi/nhl_scoreboard/Assets/Images/Team Logos/PNG/'

    source = '/Users/stephen/Development/nhl_scoreboard/Assets/Images/Team Logos/SVG/'
    destination = '/Users/stephen/Development/nhl_scoreboard/Assets/Images/Team Logos/PNG/'

    for filename in os.listdir(source):
        print(filename)
        if filename.endswith('.svg'):
            svg2png(url=source+filename, write_to=destination+filename[0:3]+".png")

if __name__ == '__main__':
    main()