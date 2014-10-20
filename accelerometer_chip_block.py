from enum import Enum
import itertools
import math
import statistics
import threading
import time

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
    from .adxl345 import adxl345
    class obj(adxl345.ADXL345):
        def read(self):
            out = self.getAxes(True)
            return out['x'], out['y'], out['z']

        def set_range(self, grange):
            if grange == 2:
                val = adxl345.RANGE_2G
            elif grange == 4:
                val = adxl345.RANGE_4G
            elif grange == 8:
                val = adxl345.RANGE_8G
            elif grange == 16:
                val = adxl345.RANGE_16G
            else:
                raise ValueError(grange)
            return self.setRange(val)

    return obj

def avg(array):
    return sum(array) / len(array)

class ChipTypes(Enum):
    ADXL345 = "ADXL345"

class SampleTypes(Enum):
    Stats = "stats"
    Last = "last"

class Ranges(Enum):
    _2G =  2
    _4G =  4
    _8G =  8
    _16G = 16

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
    range = SelectProperty(Ranges, title="G Range", default=Ranges._2G)

    def configure(self, context):
        super().configure(context)
        if self.chip == ChipTypes.ADXL345:
            obj = get_adxl345()

        self._accel = obj(self.address)
        self._accel.set_range(self.range.value)

        self._job = None
        if self.sample != SampleTypes.Last:
            self._samples = []
            #self._job = Job(self._sample, self.interval, True)
            self._thread = threading.Thread(target=self._sample_threaded)
            sleeptime = self.interval.seconds + self.interval.microseconds * 1e-6
            self._kill = False
            self._thread.start()

    def stop(self):
        super().stop()
        self._kill = True

    def _sample_threaded(self):
        sleeptime = self.interval.seconds + self.interval.microseconds * 1e-6
        while not self._kill:
            print("Taking data", time.time())
            self._sample()
            time.sleep(sleeptime)

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
            mean_gs = statistics.mean(sample_gs)
            if len(sample_gs) >= 2:
                stdev_gs = statistics.stdev(sample_gs, mean_gs)
            else:
                stdev_gs = None

            value = {"max": samples[max_i],
                     "min": samples[min_i],
                     "mean": mean_gs,
                     "stdev": stdev_gs,
                     "last": samples[-1]
            }

        name = self.name
        for s in signals:
            setattr(s, name, value)

        self.notify_signals(signals)

