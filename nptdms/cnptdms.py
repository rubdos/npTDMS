from cnpTDMS import ffi, lib
from datetime import datetime, timedelta
from collections import OrderedDict
import numpy as np
import sys

from . import impl

if sys.version < '3':
    def bin_to_str(x):
        return x
else:
    def bin_to_str(x):
        return x.decode('utf-8')

# Map of datatype. First value in tuple is reader for single value
# Second value in tuple is the numpy datatype
tdsDataTypes = {
    'tdsTypeVoid': (None, None),
    'tdsTypeI8': (lib.tdms_read_int8, np.int8),
    'tdsTypeI16': (lib.tdms_read_int16, np.int16),
    'tdsTypeI32': (lib.tdms_read_int32, np.int32),
    'tdsTypeI64': (lib.tdms_read_int64, np.int64),
    'tdsTypeU8': (lib.tdms_read_uint8, np.uint8),
    'tdsTypeU16': (lib.tdms_read_uint16, np.uint16),
    'tdsTypeU32': (lib.tdms_read_uint32, np.uint32),
    'tdsTypeU64': (lib.tdms_read_uint64, np.uint64),
    'tdsTypeSingleFloat': (lib.tdms_read_float, np.single),
    'tdsTypeDoubleFloat': (lib.tdms_read_double, np.double),
    'tdsTypeExtendedFloat': (None, None),
    'tdsTypeDoubleFloatWithUnit': (None, None),
    'tdsTypeExtendedFloatWithUnit': (None, None)
    }

def read_type(typ, val):
    if typ == 'tdsTypeString':
        return bin_to_str(ffi.string(lib.tdms_read_string(val)))
    if typ == 'tdsTypeTimeStamp':
        print("WARNING: TIMESTAMPS NOT SUPPORTED")
        return datetime.now()
    try:
        return tdsDataTypes[typ][0](val)
    except TypeError:
        raise TypeError("Datatype '" + typ + "' reading is not supported")

def handle_exception():
    what = lib.last_error()
    raise Exception(ffi.string(what).decode('utf-8'))

def handle_exception_if_null(obj):
    if obj == ffi.NULL:
        handle_exception()

def nptocharcode(npt):
    if npt == np.int32:
        return '<i4'
    if npt == np.uint32:
        return '<u4'
    if npt == np.float32:
        return '<f4'
    return None

class TdmsFile(impl.TdmsFile):
    def __init__(self, filename):
        if hasattr(filename, "read"):
            # It's a stream. Currently the C++ implementation doesn't
            # read these, so we write to a temporary file
            stream = filename
            import os, tempfile
            tmpdir = tempfile.mkdtemp()
            filename = os.path.join(tmpdir, 'temp.tdms')
            
            f = open(filename, 'wb+')
            f.write(stream.read())
            f.close()

            self._ctdmsfile = lib.tdms_read(filename.encode('utf-8'))

            os.remove(filename)
            os.rmdir(tmpdir)
        else:
            self._ctdmsfile = lib.tdms_read(filename.encode('utf-8'))

        handle_exception_if_null(self._ctdmsfile)
        self._objects = {}
        self._load_paths()

    def __del__(self):
        if(self._ctdmsfile != ffi.NULL):
            lib.tdms_file_dispose(self._ctdmsfile)

    def channel_data(self, *path):
        o = self.object(*path)
        return o.get_data()

    def _load_paths(self):
        self._paths = []
        it = lib.tdms_objects_iterator(self._ctdmsfile)
        path = lib.tdms_objects_iterator_next(it)
        while path != ffi.NULL:
            self._paths.append(ffi.string(path).decode('utf-8'))
            path = lib.tdms_objects_iterator_next(it)
        lib.tdms_objects_iterator_dispose(it)

    def groups(self):
        """Return the names of groups in the file

        Note that there is not necessarily a TDMS object associated with
        each group name.

        :rtype: List of strings.

        """

        # Split paths into components and take the first (group) component.
        object_paths = (self._path_components(path)
                for path in self._paths)
        group_names = (path[0] for path in object_paths if len(path) > 0)

        # Use an ordered dict as an ordered set to find unique
        # groups in order.
        groups_set = OrderedDict()
        for group in group_names:
            groups_set[group] = None
        return list(groups_set)

    def group_channels(self, group):
        """Returns a list of channel objects for the given group

        :param group: Name of the group to get channels for.
        :rtype: List of :class:`TdmsObject` objects.

        """

        path = self._path(group)
        print("Finding channels in path " + path)
        return [
            self._object(p)
            for p in self._paths
            if p.startswith(path + '/')]

    def object(self, *path):
        p = self._path(*path)
        return self._object(p)

    def _object(self, p):
        if not p in self._objects:
            self._objects[p] = TdmsObject(self._ctdmsfile, p)

        return self._objects[p]

    def _path(self, *args):
        """Convert group and channel to object path"""

        return ('/' + '/'.join(
                ["'" + arg.replace("'", "''") + "'" for arg in args]))

class TdmsObject(impl.TdmsObject):
    """Represents an object in a TDMS file.

    :ivar path: The TDMS object path.
    :ivar properties: Dictionary of TDMS properties defined for this object,
                      for example the start time and time increment for
                      waveforms.
    :ivar has_data: Boolean, true if there is data associated with the object.
    :ivar data: NumPy array containing data if there is data, otherwise None.

    """
    def __init__(self, tdms_file, path):
        self._ctdmsfile = tdms_file
        self._path = path
        self._properties = None
        self._data = None
        self._ctdmsobject = lib.tdms_object_by_path(tdms_file, path.encode('utf-8'))
        if(self._ctdmsobject == ffi.NULL):
            raise KeyError(path + " is not an object")

        self.number_values = lib.tdms_object_number_values(self._ctdmsobject)
        self._data_type = ffi.string(lib.tdms_object_data_type(self._ctdmsobject)).decode('utf-8')
        self.data_type = [impl.tdsDataTypes[dt] for dt in impl.tdsDataTypes if impl.tdsDataTypes[dt].name == self._data_type]
        if len(self.data_type) > 0:
            self.data_type = self.data_type[0]
        else:
            self.data_type = None
        
    def _load_properties(self):
        self._properties = OrderedDict()
        p_it = lib.tdms_object_properties_iterator(self._ctdmsobject);
        while lib.tdms_property_iterator_ok(p_it):
            key = bin_to_str(ffi.string(lib.tdms_property_iterator_name(p_it)))
            typ = bin_to_str(ffi.string(lib.tdms_property_iterator_type(p_it)))
            val = read_type(typ, lib.tdms_property_iterator_value(p_it))
            self._properties[key] = val
            lib.tdms_property_iterator_next(p_it)
            
        lib.tdms_object_properties_iterator_dispose(p_it)

    def get_properties(self):
        if self._properties is None:
            self._load_properties()
        return self._properties;

    def _load_data(self):
        dt=tdsDataTypes[self._data_type][1]
        ai = self._array_interface()
        if ai is None:
            self._data = np.zeros(
                    self.number_values, 
                    dtype=dt)
            lib.tdms_object_copy_data(self._ctdmsobject, 
                    ffi.cast("void *", self._data.ctypes.data))
            return
        print("Using array interface")
        self._data = np.asarray(self)

    def _array_interface(self):
        # TODO: what if the TdmsFile gets destroyed? MEMORYLEAK
        dt=tdsDataTypes[self._data_type][1]
        cc = nptocharcode(dt)
        if cc is None:
            return None
        return dict(
                shape=(self.number_values, 1),
                data=(int(ffi.cast("uintptr_t", lib.tdms_object_raw_data(self._ctdmsobject))), True),
                typestr=cc,
                version=3
                )

    def get_data(self):
        if self._data is None:
            self._load_data()
        return self._data

    def property(self, name):
        return self.properties[name]

    def __getattr__(self, name):
        if name == 'path':
            return bin_to_str(
                    ffi.string(
                        lib.tdms_path_by_object(self._ctdmsobject)
                        )
                    )
        if name == 'properties':
            return self.get_properties()
        if name == 'data':
            return self.get_data()
        if name == '__array_interface__':
            return self._array_interface()
        raise AttributeError("'TdmsObject' has no attribute '" + name + "'")
