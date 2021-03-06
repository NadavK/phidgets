# PhidgetS - A Phidget Service
Provides an http interface to control and receive events from Phidget Devices.

## Installation
### Project
1. Download the files to `/home/pi/phidgets/` 
    1. Create log folder: `mkdir /home/pi/phidgets/log`
1. pip install -r requirements.txt
1. Install Phidget22 library for Python:

    ```
    sudo apt-get install libusb-1.0-0-dev -y
    https://www.phidgets.com/docs/OS_-_Linux#Programming
        sudo wget -qO- http://www.phidgets.com/gpgkey/pubring.gpg | sudo apt-key add -
        echo 'deb http://www.phidgets.com/debian stretch main' | sudo tee /etc/apt/sources.list.d/phidgets.list
        sudo apt-get update
        sudo apt-get install libphidget22 -y
    https://www.phidgets.com/docs/Language_-_Python_Linux_Terminal
        download latest: https://www.phidgets.com/downloads/phidget22/libraries/any/Phidget22Python/
        in the Phidget22Python directory: python setup.py install
    ```

### Service
```
sudo ln -s /home/pi/phidgets/phidgets.service /etc/systemd/system/phidgets.service
sudo systemctl enable phidgets.service
```
The service will automatically start at system boot.
* To manually start:
`sudo service phidgets start`
* To manually stop:
`sudo service phidgets stop`

logs:
    ```
    journalctl -u phidgets -f
    ```

### Sainsmart USB Relays
#### USB permission
```
sudo bash -c "printf 'SUBSYSTEM==\"usb\", ATTR{idVendor}==\"1a86\", ATTR{idProduct}==\"7523\", GROUP=\"pi\" MODE=\"0666\"' > /etc/udev/rules.d/51-usb-perms.rules"
sudo udevadm control --reload ; sudo udevadm trigger
```
## License
Licensed under the AGPL-3.0 License - see [LICENSE](LICENSE) for details

# Acknowledgments
* Many thanks to [@Patrick](https://www.phidgets.com/phorum/memberlist.php?mode=viewprofile&u=558) at [Phidgets](https://www.phidgets.com)
