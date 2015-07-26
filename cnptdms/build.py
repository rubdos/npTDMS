import os
from cffi import FFI

current_directory = os.path.dirname(os.path.realpath(__file__))

ffi = FFI()

sources = [
    "log.cpp", 
    "tdms_file.cpp", 
    "tdms_segment.cpp"]

sources = [os.path.join("TDMSpp", "src", source) for source in sources]
sources.append("cffi_tdms.c")
sources = [os.path.join(current_directory, source) for source in sources]

source = "".join([open(f).read() for f in sources])
header = open(os.path.join(current_directory, "cffi_tdms.h")).read()
include_paths = [
        os.path.join(current_directory, "TDMSpp", "src"),
        current_directory
        ]

ffi.set_source("cnpTDMS", 
        source,
        source_extension=".cpp",
        include_dirs=include_paths,
        extra_compile_args=["-std=c++11"])

ffi.cdef(header)

if __name__ == "__main__":
    ffi.compile()
