#include <tdms.hpp>
#include <stdint.h>

typedef TDMS::file TDMS_file;
typedef TDMS::object TDMS_object;

struct TDMS_object_properties_iterator
{
    std::map<std::string, std::shared_ptr<TDMS::object::property>>::const_iterator it;
    std::map<std::string, std::shared_ptr<TDMS::object::property>> _map;
};

std::string _last_error;

void handle_exception(std::exception& e)
{
    _last_error = std::string(e.what());
}

extern "C" 
{
    const char* last_error()
    {
        return _last_error.c_str();
    }
    TDMS_file* tdms_read(const char* path)
    {
        try
        {
            return new TDMS_file(std::string(path));
        }
        catch(std::exception& e)
        {
            handle_exception(e);
            return NULL;
        }
    }
    void tdms_file_dispose(TDMS_file* f)
    {
        delete f;
    }

    const TDMS_object* tdms_object_by_path(TDMS_file* t, const char* path)
    {
        try
        {
            return (*t)[std::string(path)];
        }
        catch(std::out_of_range& e)
        {
            _last_error = (std::string(path) + " is not an object").c_str();
            return NULL;
        }
    }
    const char* tdms_path_by_object(TDMS_object* o)
    {
        return o->get_path().c_str();
    }

    // Object properties stuff
    TDMS_object_properties_iterator* tdms_object_properties_iterator(TDMS_object* o)
    {
        TDMS_object_properties_iterator* a = new TDMS_object_properties_iterator;
        a->_map = o->get_properties();
        a->it = a->_map.begin();
        return a;
    }
    void tdms_object_properties_iterator_dispose(TDMS_object_properties_iterator* o)
    {
        delete o;
    }
    int tdms_property_iterator_ok(TDMS_object_properties_iterator* a)
    {
        return (a->it == a->_map.end()) ? 0 : 1;
    }
    int tdms_property_iterator_next(TDMS_object_properties_iterator* a)
    {
        ++(a->it);
        return (a->it == a->_map.end()) ? 0 : 1;
    }
    const char* tdms_property_iterator_name(TDMS_object_properties_iterator* a)
    {
        return a->it->first.c_str();
    }
    const char* tdms_property_iterator_type(TDMS_object_properties_iterator* a)
    {
        return a->it->second->data_type.name.c_str();
    }
    void* tdms_property_iterator_value(TDMS_object_properties_iterator* a)
    {
        return a->it->second->value;
    }


    // Type readers
    const char* tdms_read_string(void* v)
    {
        // Special case, convert to std::string and get the c_str
        return ((std::string*) v)->c_str();
    }

    float tdms_read_float(void* v)
    {
        return *((float*)v);
    }
    double tdms_read_double(void* v)
    {
        return *((double*)v);
    }

    int64_t tdms_read_int64(void* v)
    {
        return *((int64_t*)v);
    }
    int32_t tdms_read_int32(void* v)
    {
        return *((int32_t*)v);
    }
    int16_t tdms_read_int16(void* v)
    {
        return *((int16_t*)v);
    }
    int8_t tdms_read_int8(void* v)
    {
        return *((int8_t*)v);
    }

    uint64_t tdms_read_uint64(void* v)
    {
        return *((int64_t*)v);
    }
    uint32_t tdms_read_uint32(void* v)
    {
        return *((int32_t*)v);
    }
    uint16_t tdms_read_uint16(void* v)
    {
        return *((int16_t*)v);
    }
    uint8_t tdms_read_uint8(void* v)
    {
        return *((int8_t*)v);
    }


    size_t tdms_object_number_values(TDMS_object* o)
    {
        return o->number_values();
    }
    const char* tdms_object_data_type(TDMS_object* o)
    {
        return o->data_type().c_str();
    }
    void tdms_object_copy_data(TDMS_object* o, void* dest)
    {
        memcpy((void*)dest, o->data(), o->bytes());
    }
    const void* tdms_object_raw_data(TDMS_object* o)
    {
        return o->data();
    }

    // Iterating over objects

    struct TDMS_objects_iterator
    {
        TDMS_objects_iterator(TDMS_file* f)
            : f(f), it(f->begin())
        {
        }
        TDMS_file* f;
        TDMS_file::iterator it;
    };

    TDMS_objects_iterator* tdms_objects_iterator(TDMS_file* f)
    {
        TDMS_objects_iterator* it = new TDMS_objects_iterator(f);
        return it;
    }
    const char* tdms_objects_iterator_next(TDMS_objects_iterator* it)
    {
        if(it->it != it->f->end())
        {
            TDMS_object* a = *(it->it);
            ++(it->it);
            return a->get_path().c_str();
        }
        else
        {
            return NULL;
        }
    }
    void tdms_objects_iterator_dispose(TDMS_objects_iterator* it)
    {
        delete it;
    }
}
