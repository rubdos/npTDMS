// Exception handling
const char* last_error();

// Stuff for reading files and objects
typedef struct _TDMS_file TDMS_file;
typedef struct _TDMS_object TDMS_object;

TDMS_file* tdms_read(const char* filepath);
const TDMS_object* tdms_object_by_path(TDMS_file*, const char* path);
const char* tdms_path_by_object(TDMS_object*);
void tdms_file_dispose(TDMS_file*);

// Stuff for iterating over properties
typedef struct _TDMS_object_properties_iterator TDMS_object_properties_iterator;

TDMS_object_properties_iterator* tdms_object_properties_iterator(TDMS_object*);
void tdms_object_properties_iterator_dispose(TDMS_object_properties_iterator*);
int tdms_property_iterator_next(TDMS_object_properties_iterator*); // Returns 0 when at ::end()
int tdms_property_iterator_ok(TDMS_object_properties_iterator*); // Returns 0 when at ::end()
const char* tdms_property_iterator_name(TDMS_object_properties_iterator*);
const char* tdms_property_iterator_type(TDMS_object_properties_iterator*);
void* tdms_property_iterator_value(TDMS_object_properties_iterator*);

// Value reading functions
const char* tdms_read_string(void*);
float tdms_read_float(void*);
double tdms_read_double(void*);
uint64_t tdms_read_uint64(void*);
uint32_t tdms_read_uint32(void*);
uint16_t tdms_read_uint16(void*);
uint8_t  tdms_read_uint8(void*);

int64_t tdms_read_int64(void*);
int32_t tdms_read_int32(void*);
int16_t tdms_read_int16(void*);
int8_t  tdms_read_int8(void*);


// Data reading out of object
size_t tdms_object_number_values(TDMS_object*);
const char* tdms_object_data_type(TDMS_object*);
void tdms_object_copy_data(TDMS_object*, void* dest);
const void* tdms_object_raw_data(TDMS_object*);

// Iterting over objects
typedef struct _TDMS_objects_iterator TDMS_objects_iterator;

TDMS_objects_iterator* tdms_objects_iterator(TDMS_file*);
const char* tdms_objects_iterator_next(TDMS_objects_iterator*);
void tdms_objects_iterator_dispose(TDMS_objects_iterator*);
