# PhidgetS - A Phidget HASS MQTT External Add-on
Provides an HASS MQTT interface to manage Phidget devices, Raspberry Pi gpios and USB relays.

## Standalone Server Installation
### Prepare Libraries
1. Download the files to `/home/pi/phidgets/` 
    1. Create log folder: `mkdir /home/pi/phidgets/log`
2. pip install -r requirements.txt
3. Install Phidget22 library for Python:
    https://www.phidgets.com/docs/OS_-_Linux

### Create Service
```
sudo ln -s /home/pi/phidgets/phidgets.service /etc/systemd/system/phidgets.service
sudo systemctl enable phidgets.service
```
The service will automatically start at system boot.
* To manually start:
`sudo service phidgets start`
* To manually stop:
`sudo service phidgets stop`

logs: ``` journalctl -u phidgets -f ```

### Sainsmart USB Relays
#### USB permission
```
sudo bash -c "printf 'SUBSYSTEM==\"usb\", ATTR{idVendor}==\"1a86\", ATTR{idProduct}==\"7523\", GROUP=\"pi\" MODE=\"0666\"' > /etc/udev/rules.d/51-usb-perms.rules"
sudo udevadm control --reload ; sudo udevadm trigger
```

### GPIO
```
sudo nano /etc/systemd/system/pigpiod.service
[Unit]
Description=Pigpio daemon

[Service]
ExecStart=/usr/local/bin/pigpiod
ExecStop=/bin/systemctl kill pigpiod

[Install]
WantedBy=multi-user.target

sudo systemctl enable pigpiod
sudo systemctl start pigpiod
```

## Docker Installation
### Build
docker build -t hass-phidgets .
docker save -o hass-phidgets.tar hass-phidgets:latest
gzip -c hass-phidgets.tar > hass-phidgets.tar.gz

### Install
Install the HASS SSH & Web Terminal Add-on
gunzip -c hass-phidgets.tar.gz | docker load
verify: docker images

### Run
docker run --name phidgets --restart always --privileged --device=/dev/bus/usb:/dev/usb --network=host -e MQTT_BROKER=localhost -e MQTT_PORT=1883 -e MQTT_USER=YOUR_MQTT_USERNAME -e MQTT_PASSWORD=YOUR_MQTT_PASSWORD -d hass-phidgets

### Logs
docker logs -f phidgets

## License
Licensed under the AGPL-3.0 License - see [LICENSE](LICENSE) for details

# Acknowledgments
* Many thanks to [@Patrick](https://www.phidgets.com/phorum/memberlist.php?mode=viewprofile&u=558) at [Phidgets](https://www.phidgets.com)
