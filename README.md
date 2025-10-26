# Raspberry Pi LED Matrix NHL Scoreboard

Display live NHL game scores, start times, etc. on a LED matrix driven by a Raspberry Pi. Makes use of the __new__, still unofficial, [NHL API](https://gitlab.com/dword4/nhlapi/-/blob/master/new-api.md) for all game information.

Check out the accompanying [blog post](https://gidge.dev/nhl%20scoreboard/nhl-scoreboard/) from the initial release of this project for some background info and more examples.

Hardware requirements and installation instructions are below.

![Example](https://github.com/gidger/rpi-led-nhl-scoreboard/blob/54f7db74ade8e95ad5cc285441914ebde0c113b4/examples/demo.gif)

## In Development / Todo
1. ~~Migrate to Docker.~~ DONE-ish! Implemented, updated instructions incoming. Existing instructions will still work.
1. Allow user to specify alternative team logos.
1. Allow user to specify favorite team(s) and display a "next game" screen should they not be playing today.
1. Better document different user options and provide examples.
1. Generalize as much as possible to make easily extendable  for other sports.
1. ~~Implement additional transitions.~~ DONE!
1. ~~Revise brightness logic to allow for more user control.~~ DONE!

## Hardware Required
1. A Raspberry Pi Zero 2W and all Pi 3 or 4 models should work. The Pi 5 is currently unsupported.
1. An [Adafruit RGB Matrix Bonnet](https://www.adafruit.com/product/3211) (reccomended) or [RGB Matrix HAT + RTC](https://www.adafruit.com/product/2345).
1. HUB75 type 32x64 RGB LED matrix. These can be found at electronics hobby shops (or shipped from China for a lot cheaper). I reccomend heading to a shop to purchase if you're unsure of exactly what you need.
1. An appropriate power suppy. A 5V 4A power supply should suffice, but I offer the same advice as the LED matrix. I'm currently using a 5V 8A power supply as that's what I had lying around.
1. **OPTIONAL**: A soldering iron, solder, and a short wire.

## Installation Instructions
These instructitons assume some basic knowledge of electronics, Unix, and command line navigation. For additional details on driving the RGB matrix, check out my fork of [hzeller's rpi-rgb-led-matrix repo](https://github.com/gidger/rpi-rgb-led-matrix-python3.12-fix) (it's the submodule used in this project).

0. **OPTIONAL**, but reccomended: Solder a jumper wire between GPIO4 and GPIO18 on the Bonnet or Hat board. This will allow you to get the best image quality later in the setup.

1. On your personal computer, use the [Raspberry Pi Imager](https://www.raspberrypi.com/software/) to flash an SD card with Rasberry Pi OS Lite (64 bit). During this process, be sure to...
    - Set a password (keep username as "pi").
    - Set your time zone.
    - Specify WiFi credentials.
    - Enable SSH via password autentication.
    - See full Raspberry Pi Imager getting started guide [here](https://www.raspberrypi.com/documentation/computers/getting-started.html#raspberry-pi-imager).

1. Remove the SD card from your personal computer and insert it into your Raspberry Pi. 

1. Assemble all hardware per [these instructions](https://learn.adafruit.com/adafruit-rgb-matrix-bonnet-for-raspberry-pi/driving-matrices) (steps 1 - 5).

1. Plug in your Raspberry Pi. From your personal computer, SSH into it and enter the password you set earlier when prompted. Assuming a username of "pi" and a device name of raspberrypi, the command would look like this:
    ```bash
    ssh pi@raspberrypi.local
    ```

1. Once you've SSH'd into your Raspberry Pi... If you completed step 0, disable on-board sound to take advantage of the increased image quality. If you didn't complete step 0, skip this step.
    ```bash
    sudo nano /etc/modprobe.d/alsa-blacklist.conf
    ```
    Add the following:
    ```
    blacklist snd_bcm2835
    ```
    Save and exit. Then enter the following:
    ```bash
    sudo nano /boot/firmware/config.txt
    ```
    Edit the "dtparam=audio" line to match the following:
    ```
    dtparam=audio=off
    ```
    Save and exit.


1. Reboot your RPi.
    ```bash
    sudo reboot
    ```
    Wait a few minutes, then SSH into your RPi once  again.
    ```bash
    ssh pi@raspberrypi.local
    ```

1.  Update built-in software.
    ```bash
    sudo apt-get update -y
    sudo apt-get upgrade -y
    ```

1. Install additional required software.
    ```bash
    sudo apt-get install git python3-dev cython3 -y
    ```

1. Clone this repository, including all submodules.
    ```bash
    git clone --recursive https://github.com/gidger/rpi-led-nhl-scoreboard.git
    ```

1. Make a Python virtual environment and activate. First enter the directory we just cloned.
    ```bash
    cd rpi-led-nhl-scoreboard/
    ```
    Then, create and activate a virtual environment with the name "venv".
    ```bash
    python -m venv venv
    source venv/bin/activate
    ```

1. Install required Python packages.
    ```bash
    pip install -r requirements.txt
    ```
    
1. Install the LED matrix Python package. First, navagate to the LED matrix library directory.
    ```bash
    cd submodules/rpi-rgb-led-matrix
    ```
    Then, make and install:
    ```bash
    make build-python PYTHON=$(which python)
    sudo make install-python PYTHON=$(which python)
    ```

1. Return to the root of your clone of this repository.
    ```bash
    cd /home/pi/rpi-led-nhl-scoreboard/ 
    ```

1. If you're using a Raspberry Pi Zero 2W, 3B, or older, you'll need to update [gpio_slowdown in config.yaml](https://github.com/gidger/rpi-led-nhl-scoreboard/blob/c5b3245fc0115a5dd3719e4db59fd35350ff7c8d/config.yaml#L23)  to prevent flickering. Reduce value by 1 each test. You can experiment and see what looks best for your hardware.

1. If you did NOT completed step 0, you'll need to update [hardware_mapping in config.yaml](https://github.com/gidger/rpi-led-nhl-scoreboard/blob/c5b3245fc0115a5dd3719e4db59fd35350ff7c8d/config.yaml#L24)  to match the following:
    ```
    hardware_mapping: 'adafruit-hat'
    ```

1. Make the scoreboard script run at startup.
    ```bash
    nano ~/start-scoreboard.sh
    ```
    Paste the following:
    ```
    #!/bin/bash
    cd /home/pi/rpi-led-nhl-scoreboard
    source venv/bin/activate

    n=0
    until [ $n -ge 10 ]
    do
       sudo /home/pi/rpi-led-nhl-scoreboard/venv/bin/python rpi_led_nhl_scoreboard.py  && break
       n=$[$n+1]
       sleep 10
    done
    ```
    Save and exit.

    **OPTIONAL**: You can make this repository automatically stay up to date by using this edited version of the above start-scoreboard.sh. This will check for updates on reboot before running the Python script. Generally, I would not advise doing this, but it may be useful when making this project as a gift for a non tech savvy person. It's allowed me to issue hotfixes after API changes with no action on the owner's part.
    ```
    #!/bin/bash
    cd /home/pi/rpi-led-nhl-scoreboard
    source venv/bin/activate
    
    while ! ping -c 1 -W 1 github.com; do
        echo "Waiting for GitHub..."
        sleep 1
    done

    git pull origin main
    pip install -r requirements.txt

    n=0
    until [ $n -ge 10 ]
    do
        sudo /home/pi/rpi-led-nhl-scoreboard/venv/bin/python rpi_led_nhl_scoreboard.py  && break
        n=$[$n+1]
        sleep 10
    done
    ```

1. Now, let's make that script executable:
    ```
    chmod +x ~/start-scoreboard.sh
    ```

1. And make it run at boot:
    ```
    sudo crontab -e
    ```
    Copy the following to the bottom:

    ```
    @reboot /home/pi/start-scoreboard.sh > /home/pi/cron.log 2>&1
    ```
    Save and exit.

1. Finally, test your change by rebooting your Raspbery Pi. If everything was done correctly, the scoreboard should start automatically running shortly after boot.

    ```
    sudo reboot
    ```

1. Grab a drink and stare at your new scoreboard for way too long.
