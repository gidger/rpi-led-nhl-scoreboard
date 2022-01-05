# Raspberry Pi LED Matrix NHL Scoreboard
Display live NHL game scores, start times, etc. on a LED matrix driven by a Raspberry Pi. Makes use of the unofficial [NHL API](https://gitlab.com/dword4/nhlapi/-/blob/master/stats-api.md) for all game information.

Check out the accompanying [blog post](https://gidge.dev/nhl%20scoreboard/nhl-scoreboard/) for more info and examples.

![Example](https://github.com/gidger/rpi-led-nhl-scoreboard/blob/8dcf3104e2d6d7a9a0412b74bff32985df2af1f0/examples/demo.gif)


## Installation Instructions
These instructitons assume some basic knowledge of Unix and how to edit files via the command line.
1. Flash an SD card with [Rasberry Pi OS Lite](https://www.raspberrypi.org/software/operating-systems/) on your personal computer.

2. Unplug and replug the SD card.

3. Add an empty file named "ssh" to the boot directory on the SD card. Navagate to the SD card and enter the following command.
    ```bash
    touch ssh
    ```

4. Add and configure wpa_supplicant.conf.

    ```
    touch wpa_supplicant.conf
    ```

    Add the following to wpa_supplicant.conf using your text editor of choice. Configure the network information and two didgit [country code](https://www.iban.com/country-codes) as per your needs.
    ```
    country=CA
    ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
    update_config=1

    network={
        ssid="NETWORK-NAME"
        psk="NETWORK-PASSWORD"
    }
    ```

5. Remove the SD card from your personal computer and insert it into your Raspberry Pi. Boot up and SSH into your RPi.

6. Set location/time zone and new password via [raspi-config](https://www.raspberrypi.org/documentation/configuration/raspi-config.md).
    ```bash
    sudo raspi-config
    ```

7. Get the latest updates.
    ```bash
    sudo apt-get update -y
    sudo apt-get upgrade -y
    ```

8. Disable on-board sound.
    ```
    sudo nano /boot/config.txt
    ```
    Edit the dtparam line to look like this:
    ```
    dtparam=audio=off
    ```

9. Disable sleep. 

    ```bash
    sudo nano /etc/rc.local
    ```

    Above the line that says "exit 0" insert the following command and save the file:
    ```
    /sbin/iw wlan0 set power_save off
    ```

10. Install pip3.
    ```bash
    sudo apt-get install python3-pip -y
    ```

11. Install git.
    ```bash
    sudo apt-get install git -y
    ```

12. Copy this repository.
    ```bash
    git clone --recursive https://github.com/gidger/rpi-led-nhl-scoreboard.git
    ```
    Note for RPi 4 or newer: you'll need to update [this line](https://github.com/gidger/rpi-led-nhl-scoreboard/blob/da3933aa03ef17313b8c3c4073e25ad1bc6e3f44/rpi-led-nhl-scoreboard.py#L616) in rpi-led-nhl-scoreboard.py to prevent flickering. Edit it to loo like this:
    ```bash
    options.gpio_slowdown = 4
    ```

13. Install the LED Matrix Python package. Navagate to the root directory of the matrix library (/submodules/rpi-rgb-led-matrix) and enter the following commands.
    ```bash
    sudo apt-get update && sudo apt-get install python3-dev python3-pillow -y

    make build-python PYTHON=$(which python3)

    sudo make install-python PYTHON=$(which python3)
    ```

14. Install any missing requirements. Return to the root of your clone of this repository and enter the following command.

    ```bash
    pip3 install -r requirements.txt
    ```

15. Make main code run at RPi startup.

    ```bash
    nano ~/start-scoreboard.sh
    ```
    Copy-paste the following:
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

    **OPTIONAL**: you can make this repository automatically stay up to date by using this edited version of the above start-scoreboard.sh. This will check for updates on reboot before starting the program. I generally would not advise doing this, but it may be useful when making as a gift for a non tech savvy person. Note that this will prevent anything from being displayed if there's no internet connection (not that anything of interest would be displayed without internet anyhow...).
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

    Save and exit. Now, let's make that script executable:

    ```
    chmod +x ~/start-scoreboard.sh
    ```

    Make the script run on boot:

    ```
    sudo crontab -e
    ```
    Add the following command to the bottom:

    ```
    @reboot /home/pi/start-scoreboard.sh > /home/pi/cron.log 2>&1
    ```

    Save and exit. Finally, test your change by rebooting your RPi.

    ```
    sudo reboot
    ```