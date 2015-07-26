"""Python module for reading TDMS files produced by LabView"""

# This file will create proxy classes based on whether cnptdms 
# works and can be imported.
# For now, the CFFI module is disabled by default.

from nptdms import cnptdms
try:
    from nptdms import cnptdms
    fast_implementation = True
except:
    fast_implementation = False
    pass

try:
    import pytz
except ImportError:
    pytz = None

if pytz:
    # Use UTC time zone if pytz is installed
    timezone = pytz.utc
else:
    timezone = None

# Disable fast_implementation by default for now
fast_implementation = False

if not fast_implementation:
    from nptdms import pynptdms

implementations = ["CFFI", "Python"]

class TdmsFile(object):
    def __init__(self, filename, memmap_dir=None, implementation = False):
        """Initialise a new TDMS file object, reading all data.

        :param file: Either the path to the tdms file to read or an already
            opened file.
        :param memmap_dir: The directory to store memmapped data files in,
            or None to read data into memory. The data files are created
            as temporary files and are deleted when the channel data is no
            longer used. tempfile.gettempdir() can be used to get the default
            temporary file directory.
        :param implementation: The implementation to use. Can be one
            of "CFFI" and "Python", or False for the default (currently "Python").
            The C++ implementation using CFFI is new, please test and report bugs.
        """
        if((implementation == False and fast_implementation) 
                or implementation == "CFFI"):
            self.__implementation = cnptdms.TdmsFile(filename)
            self.__implementation_name = "CFFI C++ implementation"
        elif((implementation == False and not fast_implementation) 
                or implementation == "Python"):
            self.__implementation = pynptdms.TdmsFile(filename)
            self.__implementation_name = "Pure Python implementation"
    def __getattr__(self, name):
        return getattr(self.__implementation, name)

    def implementation(self):
        return self.__implementation_name

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

