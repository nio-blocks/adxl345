AccelerometerChip
=================
Read data from an accelerometer chip that is interfaced through I2C and SPI. 

Follow the instructions [here](https://learn.adafruit.com/adafruits-raspberry-pi-lesson-4-gpio-setup/configuring-i2c) for getting smbus and I2C set up before installing this block. You also may need to install FFI support like so: `sudo apt-get install libffi-dev`

Properties
----------
- **address**: Device address to connect.
- **chip**: Type of accelerometer chip in use.
- **interval**: How often to read from the accelerometer.
- **range**: Set the measurement range for 10-bit readings.
- **sample**: Select to either read the accelerometer's stats or most recent (last) reading.
- **signal_name**: Label name to apply to the output signal.

Inputs
------
- **default**: Any list of signals.

Outputs
-------
- **default**: Signal with the reading from the accelerometer instrument.

Commands
--------
None

Dependencies
--------
smbus-cffi