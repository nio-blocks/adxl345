import sys
import threading
from unittest.mock import patch, MagicMock

from nio.testing.block_test_case import NIOBlockTestCase
from nio.signal.base import Signal
from nio.block.terminals import DEFAULT_TERMINAL


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

    def setUp(self):
        super().setUp()
        sys.modules['smbus'] = MagicMock()
        from ..accelerometer_chip_block import \
            AccelerometerChip, ChipTypes, SampleTypes, Ranges
        global AccelerometerChip, ChipTypes, SampleTypes, Ranges

    def test_accelerometer(self):
        config = {
            "name": "value",
            "address": 0x53,
            "chip": ChipTypes.ADXL345,
            "interval": {"microseconds": 50000},
            "sample": SampleTypes.Last,
            "range": Ranges._2G
        }
        accel = AccelerometerChip()
        with patch(AccelerometerChip.__module__ + '.adxl345') as mock_adxl345:
            self.configure_block(accel, config)
            mock_adxl345.ADXL345.read.return_value = [2, 3]
        accel.start()
        accel.process_signals([Signal({"value": "test"})])
        self.assert_num_signals_notified(1, accel)
        self.assertDictEqual(
            self.last_notified[DEFAULT_TERMINAL][0].to_dict(),
            {
                'value': {
                    'last': [2, 3],
                    'last_magnitude': 3.605551275463989
                }
            })
        accel.stop()
