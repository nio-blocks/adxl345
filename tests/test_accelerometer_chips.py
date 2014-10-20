import time
import threading

from nio.modules.threading import sleep
from nio.util.support.block_test_case import NIOBlockTestCase
from nio.modules.scheduler import SchedulerModule
from nio.common.signal.base import Signal

from ..accelerometer_chip_block import AccelerometerChip, ChipTypes, SampleTypes, Ranges

def make_signals(num=1):
    return [Signal({"value": "test"}) for _ in range(num)]

class keep_calling(object):
    def __init__(self, function, *args, **kwargs):
        self.function = function
        self.args = args
        self.kwargs = kwargs
        self._kill = False
        self._thread = threading.Thread(target=self)
        self._thread.start()
        input("Press Enter to stop...")
        self._kill = True

    def __call__(self):
        while not self._kill:
            self.function(*self.args, **self.kwargs)

class TestAccelerometer(NIOBlockTestCase):
    def signals_notified(self, signals):
        self._signals = signals

    def test_accelerometer(self):
        '''Doesn't do a true test. Just tries out the possibilities and prints the results'''
        print("Testing Accelerometer")

        config = {"name": "value",
                 "address": 0x53,
                 "chip": ChipTypes.ADXL345,
                 "interval": {"microseconds": 50000},
                 "sample": SampleTypes.Last,
                 "range": Ranges._2G
        }
        accel = AccelerometerChip()
        self.configure_block(accel, config)

        notified = 0

        accel.process_signals(make_signals())
        notified += 1
        self.assert_num_signals_notified(notified, accel)

        def sample(accel):
            accel.process_signals(make_signals())
            print("Accel Signals:", tuple(n.to_dict() for n in self._signals))
            time.sleep(1)

        print("Sampling only once / second")
        keep_calling(sample, accel)
        accel.stop()
        del accel

        accel = AccelerometerChip()
        config["sample"] = SampleTypes.Stats
        self.configure_block(accel, config)
        accel.start()
        print("Sampling Statistics")
        keep_calling(sample, accel)

