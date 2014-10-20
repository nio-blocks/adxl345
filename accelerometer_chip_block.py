from enum import Enum
import itertools
import math

from nio.common.block.base import Block
from nio.common.signal.base import Signal
from nio.metadata.properties.select import SelectProperty
from nio.metadata.properties.list import ListProperty
from nio.metadata.properties.string import StringProperty
from nio.metadata.properties.int import IntProperty
from nio.metadata.properties.string import StringProperty
from nio.metadata.properties.bool import BoolProperty
from nio.metadata.properties.timedelta import TimeDeltaProperty
from nio.metadata.properties.holder import PropertyHolder
from nio.common.discovery import Discoverable, DiscoverableType
from nio.modules.scheduler import Job
from nio.modules.threading import spawn


def get_adxl345():
    from adxl345.adxl345 import ADXL345
    class adxl345(ADXL345):
        def read(self):
            out = self.getAxes()
            return out['x'], out['y'], out['z']
    return adxl345

def avg(array):
    return sum(array) / len(array)

class ChipTypes(Enum):
    ADXL345 = "ADXL345"

class SampleTypes(Enum):
    Stats = "stats"
    Last = "last"

@Discoverable(DiscoverableType.block)
class AccelerometerChip(Block):

    """ A block enriches incoming signals with the current values of a
    set of input pins.

    """
    name = StringProperty(title="Name", default="pin{}_value")
    address = IntProperty(default=0x53, title="Address")
    chip = SelectProperty(ChipTypes, title="Chip", default=ChipTypes.ADXL345)
    interval = TimeDeltaProperty(title="Sampling Period", default={"microseconds": 50000})
    sample = SelectProperty(SampleTypes, title="Sample Type", default=SampleTypes.Stats)

    def configure(self, context):
        super().configure(context)
        if self.chip == ChipTypes.ADXL345:
            obj = get_adxl345()
            self._accel = obj(self.address)

        self._job = None
        if self.sample != SampleTypes.Last:
            self._samples = []
            self._job = Job(self._sample, self.interval, True)

    def _sample(self):
        self._samples.append(self._accel.read())

    def process_signals(self, signals):
        if self.sample == SampleTypes.Last:
            value = self._accel.read()
        else:
            samples = []
            pop = self._samples.pop
            # get data in threadsafe way
            while self._samples:
                samples.append(pop(0))

            if not samples:
                self._logger.error("Accelerometer has no samples!")
                return

            x, y, z = zip(*samples)
            # get gs squared
            x_gs = map(math.pow, x, itertools.repeat(2))
            y_gs = map(math.pow, y, itertools.repeat(2))
            z_gs = map(math.pow, z, itertools.repeat(2))

            # add them together x^2 + y^2 + z^2
            sample_gs = map(sum, zip(x_gs, y_gs, z_gs))

            # take their sqare root to get the vector value
            sample_gs = tuple(map(math.sqrt, sample_gs))

            max_i = sample_gs.index(max(sample_gs))
            min_i = sample_gs.index(min(sample_gs))
            avg_gs = sum(sample_gs) / len(sample_gs)

            value = {"max": samples[max_i],
                     "min": samples[min_i],
                     "avg": avg_gs,
                     "last": samples[-1]
                    }

        name = self.name
        for s in signals:
            setattr(s, name, value)

        self.notify_signals(signals)

