AccelerometerChip
=================
Read data from an accelerometer chip that is interfaced through I2C and SPI.

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
- **default**: 

Outputs
-------
- **default**: Signal with the reading from the accelerometer instrument.

Commands
--------
None

