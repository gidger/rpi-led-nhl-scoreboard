# Raspberry Pi LED Matrix NHL Scoreboard

Display live NHL game scores, start times, etc. on a LED matrix driven by a Raspberry Pi. Makes use of the __new__, still unofficial, [NHL API](https://gitlab.com/dword4/nhlapi/-/blob/master/new-api.md) for all game information.

Check out the accompanying [blog post](https://gidge.dev/nhl%20scoreboard/nhl-scoreboard/) from the initial release of this project for some background info and more examples.

Hardware requirements and installation instructions are below.

![Example](https://github.com/gidger/rpi-led-nhl-scoreboard/blob/8dcf3104e2d6d7a9a0412b74bff32985df2af1f0/examples/demo.gif)

## In Development / Todo
1. Implement additional transitions.
2. Revise brightness logic to allow for more user control.
3. Allow user to specify alternative team logos.
4. Allow user to specify favorite team(s) and display a "next game" screen should they not be playing today.
5. Better document different user options and provide examples.
6. Generalize as much as possible to make easily extendable  for other sports.

## Hardware Required
1. A Raspberry Pi. Zero 2W and all Pi 3/4/5 models should work.
2. An [Adafruit RGB Matrix Bonnet](https://www.adafruit.com/product/3211) (reccomended) or [RGB Matrix HAT + RTC](https://www.adafruit.com/product/2345).
3. HUB75 type 32x64 RGB LED matrix. These can be found at electronic hobby shops (or shipped from China for a lot cheaper). I reccomend heading to a shop to purchase if you're unsure of exactly what you need.
4. A appropriate power suppy. A 5V 4A power supply should suffice, but I offer the same advice as the LED matrix. I'm currently using a 5V 8A power supply as that's what I had lying around.
5. **OPTIONAL**: A soldering iron, solder, and a short wire.

## Installation Instructions
These instructitons assume some basic knowledge of electronics, Unix, and command line navigation. For additional details on driving the RGB matrix, check out [hzeller's repo](https://github.com/hzeller/rpi-rgb-led-matrix) (it's the submodule used in this project).

0. **OPTIONAL**, but reccomended: Solder a jumper wire between GPIO4 and GPIO18 on the Bonnet or Hat board. This will allow you to get the best image quality later in the setup.

1. On your personal computer, use [Raspberry Pi Imager](https://www.raspberrypi.com/software/) to flash a SD card with Rasberry Pi OS Lite. During this process, be sure to...
    - Set a username and password (reccomend keeping username as "pi" but setting your own password).
    - Set your time zone.
    - Specify WiFi credentials.
    - Enable SSH via password autentication.
    - See full Raspberry Pi Imager getting started guide [here](https://www.raspberrypi.com/documentation/computers/getting-started.html#raspberry-pi-imager).

2. Remove the SD card from your personal computer and insert it into your Raspberry Pi. 

3. Assemble all hardware per [these instructions](https://learn.adafruit.com/adafruit-rgb-matrix-bonnet-for-raspberry-pi/driving-matrices) (steps 1 - 5).

4. Plug in your Raspberry Pi. From your personal computer, SSH into it and enter the password you set earlier when prompted. Assuming a username of "pi" and a device name of raspberrypi, the command would look like this.

    ```bash
    ssh pi@raspberrypi.local
    ```

5. Once you're connected to the Raspberry Pi, get the latest updates.
    ```bash
    sudo apt-get update -y
    sudo apt-get upgrade -y
    ```

6. If you completed step 0, to take advantage of the increase quality, disable on-board sound.
    ```
    sudo nano /boot/firmware/config.txt
    ```
    Edit the dtparam line match the following:
    ```
    dtparam=audio=off
    ```
    Save and exit.

7. Disable sleep. 

    ```bash
    sudo nano /etc/rc.local
    ```

    Above the line that says "exit 0" insert the following:
    ```
    /sbin/iw wlan0 set power_save off
    ```
    Save and exit.

8. Install pip3.
    ```bash
    sudo apt-get install python3-pip -y
    ```

9. Install git.
    ```bash
    sudo apt-get install git -y
    ```

10. Clone this repository, including all submodules.
    ```bash
    git clone --recursive https://github.com/gidger/rpi-led-nhl-scoreboard.git
    ```
    
11. Install the LED Matrix Python package. First, navagate to the root directory of the matrix library (rpi-led-nhl-scoreboard/submodules/rpi-rgb-led-matrix). Then enter the following commands.
    ```bash
    sudo apt-get update && sudo apt-get install python3-dev python3-pillow -y

    make build-python PYTHON=$(which python3)

    sudo make install-python PYTHON=$(which python3)
    ```

12. Return to the root of your clone of this repository and enter the following command to install any missing Python packages.
    ```bash
    pip3 install -r requirements.txt
    ```

13. Note for people using Raspberry Pi 4 or newer, you'll need to update [this line](https://github.com/gidger/rpi-led-nhl-scoreboard/blob/c5b3245fc0115a5dd3719e4db59fd35350ff7c8d/config.yaml#L23) in config.yaml to prevent flickering. Reccomend setting to 4, but you can experiment and see what works best in your situation.

14. If you did NOT completed step 0, you'll need to update [this line](https://github.com/gidger/rpi-led-nhl-scoreboard/blob/c5b3245fc0115a5dd3719e4db59fd35350ff7c8d/config.yaml#L24) in config.yaml to match the following:
    ```
    hardware_mapping: 'adafruit-hat'
    ```

15. Make this project run at startup.
    ```bash
    nano ~/start-scoreboard.sh
    ```
    Copy-paste the following into your newly created file.
    ```
    #!/bin/bash
    cd /home/pi/rpi-led-nhl-scoreboard
    n=0
    until [ $n -ge 10 ]
    do
       sudo python3 rpi-led-nhl-scoreboard.py  && break
       n=$[$n+1]
       sleep 10
    done
    ```
    Save and exit.

16. **OPTIONAL**: You can make this repository automatically stay up to date by using this edited version of the above start-scoreboard.sh. This will check for updates on reboot before running the Python script. Generally, I would not advise doing this, but it may be useful when making this project as a gift for a non tech savvy person. It's allowed me to issue hotfixes after API changes and have people's gifted version resume operation with no action on their part.
    ```
    #!/bin/bash
    cd /home/pi/rpi-led-nhl-scoreboard
    
    while ! ping -c 1 -W 1 github.com; do
        echo "Waiting for GitHub..."
        sleep 1
    done

    git pull origin main

    n=0
    until [ $n -ge 10 ]
    do
        sudo python3 rpi-led-nhl-scoreboard.py  && break
        n=$[$n+1]
        sleep 10
    done
    ```

17. Now, let's make that script executable:
    ```
    chmod +x ~/start-scoreboard.sh
    ```

18. And make the script run on boot:
    ```
    sudo crontab -e
    ```
    Add the following to the bottom:

    ```
    @reboot /home/pi/start-scoreboard.sh > /home/pi/cron.log 2>&1
    ```
    Save and exit.

19. Finally, test your change by rebooting your Raspbery Pi. If everything was done correctly, the scoreboard should start automatically running shortly after boot.

    ```
    sudo reboot
    ```

20. Grab a drink and stare at your new scoreboard for way too long.
