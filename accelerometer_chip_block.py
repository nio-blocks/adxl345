from enum import Enum
import itertools
import math
import statistics
import threading
import time
from nio.block.base import Block
from nio.properties.select import SelectProperty
from nio.properties.int import IntProperty
from nio.properties.string import StringProperty
from nio.properties.timedelta import TimeDeltaProperty
from nio.util.discovery import discoverable
from . import adxl345


def get_adxl345():
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
    _2G = 2
    _4G = 4
    _8G = 8
    _16G = 16


@discoverable
class AccelerometerChip(Block):

    """ A block enriches incoming signals with the current values of a
    set of input pins.

    """
    signal_name = StringProperty(title="Name", default="value")
    address = IntProperty(default=0x53, title="Address")
    chip = SelectProperty(ChipTypes, title="Chip", default=ChipTypes.ADXL345)
    interval = TimeDeltaProperty(
        title="Sampling Period",
        default={
            "microseconds": 50000})
    sample = SelectProperty(
        SampleTypes,
        title="Sample Type",
        default=SampleTypes.Stats)
    range = SelectProperty(Ranges, title="G Range", default=Ranges._2G)

    def configure(self, context):
        super().configure(context)
        if self.chip() == ChipTypes.ADXL345:
            obj = get_adxl345()

        self._accel = obj(self.address())
        self._accel.set_range(self.range().value)

        self._job = None
        if self.sample() != SampleTypes.Last:
            self._samples = []
            self._thread = threading.Thread(target=self._sample_threaded)
            self._kill = False
            self._thread.start()

    def stop(self):
        super().stop()
        self._kill = True

    def _sample_threaded(self):
        sleeptime = self.interval().seconds + self.interval().microseconds * 1e-6
        while not self._kill:
            self._sample()
            time.sleep(sleeptime)

    def _sample(self):
        self._samples.append(self._accel.read())

    def process_signals(self, signals):
        if self.sample() == SampleTypes.Last:
            value = self._accel.read()
            gval = sum(n ** 2 for n in value)
            gval = math.sqrt(gval)
            value = {"last": value,
                     "last_magnitude": gval,
                     }
        else:
            samples = []
            pop = self._samples.pop
            # get data in threadsafe way
            while self._samples:
                samples.append(pop(0))

            if not samples:
                self.logger.error("Accelerometer has no samples!")
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

            max_g = max(sample_gs)
            min_g = min(sample_gs)
            max_i = sample_gs.index(max_g)
            min_i = sample_gs.index(min_g)
            mean_gs = statistics.mean(sample_gs)
            if len(sample_gs) >= 2:
                stdev_gs = statistics.stdev(sample_gs, mean_gs)
            else:
                stdev_gs = None

            value = {"max": samples[max_i],
                     "min": samples[min_i],
                     "mean": mean_gs,
                     "stdev": stdev_gs,
                     "last": samples[-1],
                     "max_magnitude": max_g,
                     "min_magnitude": min_g,
                     "last_magnitude": sample_gs[-1]
                     }

        name = self.signal_name()
        for s in signals:
            setattr(s, name, value)

        self.notify_signals(signals)
