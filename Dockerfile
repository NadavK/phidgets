# Use a lightweight Python image
FROM python:3.11-slim

# Set a working directory inside the container
WORKDIR /app

# Install necessary system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libusb-1.0-0-dev \
    wget \
    tar \
    nano \
    git \
    python3-dev \
    udev \
    && apt-get clean

# Phidget22 library installation
RUN mkdir -p /tmp/phidgets_install \
    && cd /tmp/phidgets_install \
    && wget https://cdn.phidgets.com/downloads/phidget22/libraries/linux/libphidget22.tar.gz \
    && wget https://cdn.phidgets.com/downloads/phidget22/libraries/linux/libphidget22extra.tar.gz \
    && wget https://cdn.phidgets.com/downloads/phidget22/tools/linux/phidget22admin.tar.gz \
    && tar -xvzf libphidget22.tar.gz \
    && tar -xvzf libphidget22extra.tar.gz \
    && tar -xvzf phidget22admin.tar.gz \
    && cd libphidget22-* \
    && ./configure && make && make install \
    && cd ../libphidget22extra-* \
    && ./configure && make && make install \
    && cd ../phidget22admin-* \
    && ./configure && make && make install \
    && echo "/usr/local/lib" >> /etc/ld.so.conf.d/phidget22.conf && ldconfig \
    && cd / && rm -rf /tmp/phidgets_install

# Set up USB access rules for Phidget devices
RUN mkdir -p /etc/udev/rules.d && \
    echo 'SUBSYSTEMS=="usb", ACTION=="add", ATTRS{idVendor}=="06c2", ATTRS{idProduct}=="00[3-a][0-f]", MODE="666"' > /etc/udev/rules.d/99-libphidget22.rules

# Copy the project files into the container
COPY . .

# Install Python dependencies
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

# Set the entrypoint to run your Python main script
CMD ["python", "main.py"]