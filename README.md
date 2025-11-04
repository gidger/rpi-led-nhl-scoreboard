# Raspberry Pi LED Matrix NHL Scoreboard

Display live NHL game scores, start times, etc. on an LED matrix driven by a Raspberry Pi. Makes use of the new, still unofficial, [NHL API](https://gitlab.com/dword4/nhlapi/-/blob/master/new-api.md) for all game information.

Check out the accompanying [blog post](https://gidge.dev/nhl%20scoreboard/nhl-scoreboard/) from the initial release of this project (≥3 years ago) for some background info and more examples.

Hardware requirements and installation instructions (with and without Docker) are below.

![Scoreboard Demo](https://github.com/gidger/rpi-led-nhl-scoreboard/blob/faff034cd4345b75cd255f0d0725470577fc673f/examples/modern-horizontal.gif)

## Contents
1. [In Development / Todo](#dev)
1. [Hardware Required](#hardware)
1. [Installation Instructions](#install)
1. [Configuration & Examples](#config)  

<a name="dev"/>

## In Development / Todo
1. Allow user to apply alternative team logos.
1. Allow user to specify favorite team(s) and display a "next game" screen should they not be playing today.
1. Standings functionality that displays team records and divisional standings.
1. Revise brightness logic to allow for more user control.
1. Add tracking & better logic for special events (e.g., World Cup of Hockey).
1. Generalize as much as possible to make easily extendable for other sports.
1. ~~Implement additional transitions.~~ Done!
1. ~~Migrate to Docker.~~ Done!
1. ~~Document different user options in config.yaml and provide examples.~~ Done!

<a name="hardware"/>

## Hardware Required
1. A Raspberry Pi Zero 2W and all Pi 3 or 4 models should work. The Pi 5 is currently unsupported due to a critical dependency being incompatible with that device.
1. An [Adafruit RGB Matrix Bonnet](https://www.adafruit.com/product/3211) (recommended) or [RGB Matrix HAT + RTC](https://www.adafruit.com/product/2345).
1. HUB75 type 32x64 RGB LED matrix. These can be found at electronics hobby shops (or shipped from China for a lot cheaper). I recommend heading to a shop to purchase if you're unsure of exactly what you need.
1. An appropriate power supply. A 5V 4A power supply should suffice, but I offer the same advice as the LED matrix. I'm currently using a 5V 8A power supply as that's what I had lying around.
1. **OPTIONAL**: A soldering iron, solder, and a short wire.

<a name="install"/>

## Installation Instructions
These instructions assume some very basic knowledge of electronics and Linux command line navigation. For additional details on driving an RGB matrix with a Raspberry Pi, check out my fork of [hzeller's rpi-rgb-led-matrix repo](https://github.com/gidger/rpi-rgb-led-matrix-python3.12-fix) (it's the submodule used in this project).

As of release V3.0.0, the recommended installation method for this project leverages Docker. Instructions are provided for installation with or without Docker.

### Initial Setup: All Options
Any installation will need to start with these steps:

0. **OPTIONAL**, but recommended: Solder a jumper wire between GPIO4 and GPIO18 on the Bonnet or HAT board. This will allow you to get the best image quality later in the setup.

1. On your personal computer, use the [Raspberry Pi Imager](https://www.raspberrypi.com/software/) to flash an SD card with Raspberry Pi OS Lite (64 bit). During this process, be sure to...
    - Set a password (keep username as "pi").
    - Set your time zone.
    - Specify WiFi credentials.
    - Enable SSH via password authentication.
    
    See full Raspberry Pi Imager getting started guide [here](https://www.raspberrypi.com/documentation/computers/getting-started.html#raspberry-pi-imager).

1. Remove the SD card from your computer and insert it into your Raspberry Pi. 

1. Assemble all hardware per [these instructions](https://learn.adafruit.com/adafruit-rgb-matrix-bonnet-for-raspberry-pi/matrix-setup) (steps 1 - 5).

1. Plug in your Raspberry Pi. From your personal computer, SSH into it and enter the password you set when prompted. These instructions will assume the default user of "pi" and device name of raspberrypi. The command would look like this:
    ```bash
    ssh pi@raspberrypi.local
    ```

1. If you completed step 0 disable on-board sound to take advantage of the increased image quality. If you didn't complete step 0, skip this step.
    ```bash
    echo "blacklist snd_bcm2835" | sudo tee -a /etc/modprobe.d/alsa-blacklist.conf
    ```

1.  Update built-in packages.
    ```bash
    sudo apt-get update && sudo apt-get upgrade -y
    ```

### Option 1: Docker (Recommended)

7. Install Docker via installation script.
    ```bash
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    ```

    Then add the current user to the "docker" group. This will enable us to run "docker" commands without sudo.
    ```bash
    sudo usermod -aG docker $USER
    ```

1. Reboot your Raspberry Pi.
    ```bash
    sudo reboot
    ```
    Wait a couple minutes, then SSH back into your Raspberry Pi.
    ```bash
    ssh pi@raspberrypi.local
    ```

1. Clone this repository, including submodules.
    ```bash
    git clone --recursive https://github.com/gidger/rpi-led-nhl-scoreboard.git
    ```

1. Navigate to the repository we just cloned.
    ```bash
    cd rpi-led-nhl-scoreboard
    ```

1. **If you're using a Raspberry Pi 4, skip this step.** If you're using a Raspberry Pi Zero 2W, 3B, or older, you'll need to update [gpio_slowdown in config.yaml](https://github.com/gidger/rpi-led-nhl-scoreboard/blob/c5b3245fc0115a5dd3719e4db59fd35350ff7c8d/config.yaml#L23) to prevent flickering. It's recommended that you reduce the value by 1 each test and try every option to see what looks best for your hardware.

1. **If you completed Step 0, skip this step.** If not, you'll need to update [hardware_mapping in config.yaml](https://github.com/gidger/rpi-led-nhl-scoreboard/blob/c5b3245fc0115a5dd3719e4db59fd35350ff7c8d/config.yaml#L24) to match the following:
    ```yaml
    hardware_mapping: 'adafruit-hat'
    ```

1. Start scoreboard. It will start running shortly after entering the below command. The scoreboard will also automatically run after a reboot.
    ```bash
    docker compose up -d
    ```

1. Done!

### Option 2: Manual Installation

7. Install required packages.
   ```bash
    sudo apt-get install -y git make build-essential python3 python3-dev python3-venv cython3
    ```

1. Clone this repository, including submodules.
    ```bash
    git clone --recursive https://github.com/gidger/rpi-led-nhl-scoreboard.git
    ```

1. Navigate to the repository we just cloned.
    ```bash
    cd rpi-led-nhl-scoreboard
    ```

1. Create a Python virtual environment with the name "venv". Then activate.
    ```bash
    python -m venv venv
    source venv/bin/activate
    ```

1. Install required Python packages.
    ```bash
    pip install -r requirements.txt
    ```
    
1. Install the LED matrix Python package. First, navigate to the LED matrix library directory.
    ```bash
    cd submodules/rpi-rgb-led-matrix
    ```
    Then, build and install:
    ```bash
    make build-python PYTHON=$(which python)
    sudo make install-python PYTHON=$(which python)
    ```

1. Return to the root of your clone of this repository.
    ```bash
    cd /home/pi/rpi-led-nhl-scoreboard/ 
    ```

1. **If you're using a Raspberry Pi 4, skip this step.** If you're using a Raspberry Pi Zero 2W, 3B, or older, you'll need to update [gpio_slowdown in config.yaml](https://github.com/gidger/rpi-led-nhl-scoreboard/blob/c5b3245fc0115a5dd3719e4db59fd35350ff7c8d/config.yaml#L23) to prevent flickering. It's recommended that you reduce the value by 1 each test and try every option to see what looks best for your hardware.

1. **If you completed Step 0, skip this step.** If not, you'll need to update [hardware_mapping in config.yaml](https://github.com/gidger/rpi-led-nhl-scoreboard/blob/c5b3245fc0115a5dd3719e4db59fd35350ff7c8d/config.yaml#L24) to match the following:
    ```yaml
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

1. Now, let's make that script executable:
    ```
    chmod +x ~/start-scoreboard.sh
    ```

1. And make it run at boot. First, enter:
    ```
    sudo crontab -e
    ```
    Then paste the following at the bottom:

    ```
    @reboot /home/pi/start-scoreboard.sh > /home/pi/cron.log 2>&1
    ```
    Save and exit.

1. Finally, test your change by rebooting your Raspberry Pi. If everything was done correctly, the scoreboard should start automatically running shortly after boot.

    ```
    sudo reboot
    ```

1. Done!

<a name="config"/>

## Configurations & Examples

The following settings in can be edited in [config.yaml](https://github.com/gidger/rpi-led-nhl-scoreboard/blob/c5b3245fc0115a5dd3719e4db59fd35350ff7c8d/config.yaml) to fine tune your scoreboard experience.

### Transitions
*Can be edited without restarting program or Docker container.*

#### ``scoreboard_behaviour.transition_type``
- **Definition**: Which transition to use between screens. Default modern-horizontal.
- **Options**:
    - **cut**: Simple jump cut between screens.
        
        ![Transition cut](https://github.com/gidger/rpi-led-nhl-scoreboard/blob/a3c45338a33f71f90637255030e2637f749f0f3a/examples/cut.gif)

    - **fade**: Fade between screens.
        
        ![Transition fade](https://github.com/gidger/rpi-led-nhl-scoreboard/blob/a3c45338a33f71f90637255030e2637f749f0f3a/examples/fade.gif)

    - **scroll-vertical**: Vertical scroll between screens.
        
        ![Transition scroll-vertical](https://github.com/gidger/rpi-led-nhl-scoreboard/blob/a3c45338a33f71f90637255030e2637f749f0f3a/examples/scroll-vertical.gif)

    - **scroll-horizontal**: Horizontal scroll between screens.
        
        ![Transition scroll-horizontal](https://github.com/gidger/rpi-led-nhl-scoreboard/blob/a3c45338a33f71f90637255030e2637f749f0f3a/examples/scroll-horizontal.gif)

    - **modern-vertical**: Vertical scroll between screens with fade in/out.
        
        ![Transition modern-vertical](https://github.com/gidger/rpi-led-nhl-scoreboard/blob/a3c45338a33f71f90637255030e2637f749f0f3a/examples/modern-vertical.gif)

    - **modern-horizontal**: Horizontal scroll between screens with fade in/out.
        
        ![Transition modern-horizontal](https://github.com/gidger/rpi-led-nhl-scoreboard/blob/faff034cd4345b75cd255f0d0725470577fc673f/examples/modern-horizontal.gif)

    - **random**: Random transition from the above list in and out of every screen.
          
        ![Transition random](https://github.com/gidger/rpi-led-nhl-scoreboard/blob/a3c45338a33f71f90637255030e2637f749f0f3a/examples/random.gif)

#### ``scoreboard_behaviour.goal_fade_animation``
- **Definition**: If score number should fade back to white after a goal is scored. If false will remain red. Default True.
- **Options**: True or False.
- This example is when the value is Ture. When false, the number will remain red until the next game is displayed.

    ![Goal Fade Animation](https://github.com/gidger/rpi-led-nhl-scoreboard/blob/a3c45338a33f71f90637255030e2637f749f0f3a/examples/goal-fade-aimation.gif)


### Display Durations
*Can be edited without restarting program or Docker container.*

#### ``scoreboard_behaviour.display_duration``
- **Definition**: How long to remain on a game in normal situations. Default 3.5 seconds.
- **Options**: Any number > 0.

#### ``scoreboard_behaviour.display_duration_single_game``
- **Definition**: How long to remain on a game in if there's only one game that day. Default 10 seconds.
- **Options**: Any number > 0.

#### ``scoreboard_behaviour.display_duration_no_games``
- **Definition**: How long to remain on the No Game screen. Default 600 seconds.
- **Options**: Any number > 0.


### Brightness
*Can be edited without restarting program or Docker container.*

#### ``scoreboard_behaviour.brightness_mode``
- **Definition**: How brightness will be determined. Default auto.
- **Options**:
    - **auto**: Automatically determines brightness based on time of day
    - **static**: Set static brightness.
    - **scaled**: automatically determine brightness, with a max of ``scoreboard_behaviour.max_brightness``.

#### ``scoreboard_behaviour.max_brightness``
- **Definition**: Max brightness to be used for static or scaled ``scoreboard_behaviour.brightness_mode``. 
- **Note**: This is commented out by default. Uncomment if setting ``scoreboard_behaviour.brightness_mode``. to static or scaled.
- **Options**: Any number between 15 and 100.


### Day Rollover Times
*Requires restarting the program or Docker container for changes to take effect.*

#### ``scoreboard_behaviour.display_current_day_start_time``
- **Definition**: Time of day to start reporting on that days games. Will report on yesterday and today until date_rollover_time. Default 09:00.
- **Options**: Any time in 'HH:MM' format.

#### ``scoreboard_behaviour.date_rollover_time``
- Definition: Time of day to stop reporting on the previous days games. Default 12:00.
- **Options**: Any time in 'HH:MM' format.
