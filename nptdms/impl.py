# File with common methods and stuff for cnptdms and pynptdms

import numpy as np
import itertools

try:
    long
    zip_longest = itertools.izip_longest
except NameError:
    # Python 3
    long = int
    zip_longest = itertools.zip_longest

from collections import namedtuple

# Class for describing data types, with data type name,
# identifier used by struct module, the size in bytes to read and the
# numpy data type where applicable/implemented
DataType = namedtuple("DataType",
        ('name', 'struct', 'length', 'nptype'))

tdsDataTypes = dict(enumerate((
    DataType('tdsTypeVoid', None, 0, None),
    DataType('tdsTypeI8', 'b', 1, np.int8),
    DataType('tdsTypeI16', 'h', 2, np.int16),
    DataType('tdsTypeI32', 'l', 4, np.int32),
    DataType('tdsTypeI64', 'q', 8, np.int64),
    DataType('tdsTypeU8', 'B', 1, np.uint8),
    DataType('tdsTypeU16', 'H', 2, np.uint16),
    DataType('tdsTypeU32', 'L', 4, np.uint32),
    DataType('tdsTypeU64', 'Q', 8, np.uint64),
    DataType('tdsTypeSingleFloat', 'f', 4, np.single),
    DataType('tdsTypeDoubleFloat', 'd', 8, np.double),
    DataType('tdsTypeExtendedFloat', None, None, None),
    DataType('tdsTypeDoubleFloatWithUnit', None, 8, None),
    DataType('tdsTypeExtendedFloatWithUnit', None, None, None)
)))

tdsDataTypes.update({
    0x19: DataType('tdsTypeSingleFloatWithUnit', None, 4, None),
    0x20: DataType('tdsTypeString', None, None, None),
    0x21: DataType('tdsTypeBoolean', 'b', 1, np.bool8),
    0x44: DataType('tdsTypeTimeStamp', 'Qq', 16, None),
    0xFFFFFFFF: DataType('tdsTypeDAQmxRawData', None, None, None)
})

class TdmsFile(object):
    def _path_components(self, path):
        """Convert a path into group and channel name components"""

        def yield_components(path):
            # Iterate over each character and the next character
            chars = zip_longest(path, path[1:])
            try:
                # Iterate over components
                while True:
                    c, n = next(chars)
                    if c != '/':
                        raise ValueError("Invalid path, expected \"/\"")
                    elif (n != None and n != "'"):
                        raise ValueError("Invalid path, expected \"'\"")
                    else:
                        # Consume "'" or raise StopIteration if at the end
                        next(chars)
                    component = []
                    # Iterate over characters in component name
                    while True:
                        c, n = next(chars)
                        if c == "'" and n == "'":
                            component += "'"
                            # Consume second "'"
                            next(chars)
                        elif c == "'":
                            yield "".join(component)
                            break
                        else:
                            component += c
            except StopIteration:
                return

        return list(yield_components(path))

class TdmsObject(object):
    def property(self, property_name):
        """Returns the value of a TDMS property

        :param property_name: The name of the property to get.
        :returns: The value of the requested property.
        :raises: KeyError if the property isn't found.

        """

        try:
            return self.properties[property_name]
        except KeyError:
            raise KeyError(
                "Object does not have property '%s'" % property_name)

    def time_track(self, absoluteTime=False, accuracy='ns'):
        """Return an array of time for this channel

        This depends on the object having the wf_increment
        and wf_start_offset properties defined.

        For larger timespans, the accuracy setting should be set lower.
        The default setting is 'ns', which has a timespan of [1678 AD, 2262 AD],
        for the exact ranges, refer to 
            http://docs.scipy.org/doc/numpy/reference/arrays.datetime.html
        section "Datetime Units".

        :param absoluteTime: Whether the returned numpy.array is a datetime64 array
        :param accuracy: The accuracy of the returned datetime64 array.
        :rtype: NumPy array.
        :raises: KeyError if required properties aren't found

        """

        try:
            increment = self.property('wf_increment')
            offset = self.property('wf_start_offset')
        except KeyError:
            raise KeyError("Object does not have time properties available.")

        periods = len(self.data)

        relativeTime = np.linspace(
                offset,
                offset + (periods - 1) * increment,
                periods)

        if not absoluteTime:
            return relativeTime

        try:
            starttime = self.property('wf_start_time')
        except KeyError:
            raise KeyError("Object does not have start time property available.")

        def unit_correction(u):
            if u is 's':
                return 1e0
            elif u is 'ms':
                return 1e3
            elif u is 'us':
                return 1e6
            elif u is 'ns':
                return 1e9

        # Because numpy only knows ints as its date datatype, 
        # convert to accuracy.
        return (np.datetime64(starttime) 
                + (relativeTime*unit_correction(accuracy)).astype(
                    "timedelta64["+accuracy+"]"
                    )
                )

    def as_dataframe(self, absoluteTime=False):
        """
        Converts the TDMS object to a DataFrame
        :return: The TDMS object data.
        :rtype: Pandas DataFrame
        """

        import pandas as pd

        # When absoluteTime is True, use the wf_start_time as offset for the time_track()
        time = self.time_track(absoluteTime)

        return pd.DataFrame(self.data,
                index=time,
                columns=[self.path])
