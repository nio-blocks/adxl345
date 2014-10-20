from nio.modules.threading import sleep
from nio.util.support.block_test_case import NIOBlockTestCase
from nio.modules.scheduler import SchedulerModule

from ..accelerometer_chip_block.py import AccelerometerChip, ChipTypes, SampleTypes

def make_signals(num=1):
    return [Signal({"value": "test"}) for _ in range(num)]

class TestAccelerometer(NIOBlockTestCase):
    def signals_notified(self, signals):
        self._signals = signals

    def test_accelerometer(self):
        '''Doesn't do a true test. Just tries out the possibilities and prints the results'''
        print("Testing Accelerometer")

        accel = AccelerometerChip()
        self.configure_block(accel,
                {"name": value,
                 "address": 0x53,
                 "chip": ChipTypes.ADXL345,
                 "interval": {"microseconds": 50000},
                 "sample": SampleTypes.Last
                })

        accel.start()
        notified = 0

        accel.process_signals(make_signals())
        notified += 1
        self.assert_num_signals_notified(notified, accel)
        print("Accel Signals:", tuple(n.to_dict() for n in self._signals))

