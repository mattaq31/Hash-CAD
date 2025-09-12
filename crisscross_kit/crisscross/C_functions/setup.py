from setuptools import setup, Extension
import sys, os, platform
import numpy as np

# setup is doing the C compilation. when pip installed. the functions are compiler flags for different operating systems.

def msvc_flags():
    flags = ["/O2", "/GL", "/fp:fast"]
    # Use AVX2 if available; drop to /arch:AVX if your CPU/toolchain needs it.
    flags += ["/arch:AVX2"]
    # OpenMP (won’t hurt even if we set threads=1)
    flags += ["/openmp"]
    return flags

def gcc_clang_flags():
    flags = ["-O3", "-march=native", "-funroll-loops", "-ffast-math"]
    # Link-time optimization
    flags += ["-flto"]
    # OpenMP (ok even if OMP_NUM_THREADS=1)
    flags += ["-fopenmp"]
    return flags

def gcc_clang_link_flags():
    # LTO + OpenMP need link flags too
    return ["-flto", "-fopenmp"]

is_msvc = platform.system() == "Windows" and ("msvc" in (os.environ.get("CC","") + os.environ.get("CXX","")).lower() or "MSC" in sys.version)

extra_compile_args = msvc_flags() if is_msvc else gcc_clang_flags()
extra_link_args    = [] if is_msvc else gcc_clang_link_flags()

ext = Extension(
    "eqcorr2d",
    sources=["eqcorr2d.c"],
    include_dirs=[np.get_include()],
    define_macros=[("NPY_NO_DEPRECATED_API", "NPY_1_7_API_VERSION")],
    extra_compile_args=extra_compile_args,
    extra_link_args=extra_link_args,
    language="c",
)

setup(
    name="eqcorr2d",
    version="0.1.0",
    description="2D equality-correlation (full) for uint8 arrays",
    ext_modules=[ext],
)
