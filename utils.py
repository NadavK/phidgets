import uuid


def get_sn():
    # Alternatively, retrieve the MAC: www.raspberrypi-spy.co.uk/2012/06/finding-the-mac-address-of-a-raspberry-pi/
    cpuserial = "0000000000000000"
    try:
        f = open('/proc/cpuinfo', 'r')
        for line in f:
            if line[0:6] == 'Serial':
                cpuserial = line[10:26]
        f.close()
    except:
        cpuserial = "ERROR000000000"

    return cpuserial

def get_device_id():
    return get_sn().lstrip("0")

def generate_request_id():
    return uuid.uuid4().hex
