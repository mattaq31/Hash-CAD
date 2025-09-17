from setuptools import setup, Extension, find_packages
from setuptools.command.build_ext import build_ext as _build_ext
import sys, platform, os, subprocess
import numpy as np
from pathlib import Path

# -----------------------------------------------------------------------------
# Custom build_ext with RPATH sanitization (macOS only)
# -----------------------------------------------------------------------------
class build_ext(_build_ext):
    def run(self):
        """Build and then sanitize rpaths in compiled extensions."""
        super().run()

        # Sanitize rpaths on the actually produced .so for each extension
        for ext in self.extensions:
            try:
                # 1) Exact built path (works for both in-place and normal builds)
                so_path = Path(self.get_ext_fullpath(ext.name))
                if so_path.exists():
                    self._sanitize_rpaths(so_path)

                # 2) Additionally, search common locations to be safe
                stem = ext.name.split(".")[-1]  # e.g., "eqcorr2d_engine"
                candidates = set()
                # build_lib (normal builds)
                if getattr(self, "build_lib", None):
                    candidates.add(Path(self.build_lib))
                # project root (editable/in-place)
                candidates.add(Path.cwd())
                for base in candidates:
                    if base.exists():
                        for cand in base.rglob(stem + "*.so"):
                            try:
                                self._sanitize_rpaths(cand)
                            except Exception:
                                pass
            except Exception:
                # Best-effort rpath cleanup; don’t fail the build on sanitizer issues
                pass


        # build_lib = Path(self.build_lib)
        # for ext in self.extensions:
        #     for so in build_lib.rglob(ext.name.split(".")[-1] + "*.so"):
        #         self._sanitize_rpaths(so)

    def _list_rpaths(self, so_path: Path):
        """Return a list of rpaths in a Mach-O binary using otool."""
        out = subprocess.check_output(["otool", "-l", str(so_path)], text=True)
        rpaths = []
        seen_cmd = False
        for line in out.splitlines():
            s = line.strip()
            if s == "cmd LC_RPATH":
                seen_cmd = True
            elif s.startswith("cmd ") and s != "cmd LC_RPATH":
                seen_cmd = False
            elif seen_cmd and s.startswith("path "):
                rpaths.append(s.split(" ", 1)[1].split(" (", 1)[0].strip())
        return rpaths

    def _delete_rpath_all(self, so_path: Path, target: str):
        """Delete *all* occurrences of a specific rpath from a binary."""
        while True:
            rpaths = self._list_rpaths(so_path)
            if target not in rpaths:
                break
            subprocess.check_call(
                ["install_name_tool", "-delete_rpath", target, str(so_path)]
            )

    def _sanitize_rpaths(self, so_path: Path):
        """Sanitize rpaths in a Mach-O .so on macOS. No-op elsewhere."""
        if sys.platform != "darwin":
            return  # skip non-macOS
        try:
            rpaths = self._list_rpaths(so_path)
        except subprocess.CalledProcessError:
            return  # binary not inspectable

        # 1) Remove all absolute rpaths (anything not starting with "@")
        for rp in sorted(set(r for r in rpaths if not r.startswith("@"))):
            self._delete_rpath_all(so_path, rp)

        # 2) Ensure exactly one @loader_path
        rpaths = self._list_rpaths(so_path)
        loader_count = sum(1 for r in rpaths if r == "@loader_path")

        if loader_count == 0:
            try:
                subprocess.check_call(
                    ["install_name_tool", "-add_rpath", "@loader_path", str(so_path)]
                )
            except subprocess.CalledProcessError:
                pass
        elif loader_count > 1:
            # Remove extras, then re-add one cleanly
            for _ in range(loader_count - 1):
                subprocess.check_call(
                    ["install_name_tool", "-delete_rpath", "@loader_path", str(so_path)]
                )
            subprocess.check_call(
                ["install_name_tool", "-add_rpath", "@loader_path", str(so_path)]
            )

# -----------------------------------------------------------------------------
# Compiler / linker flags
# -----------------------------------------------------------------------------
extra_compile_args = []
extra_link_args = []

# macOS arm64 (Apple Silicon)
if sys.platform == "darwin" and platform.machine() == "arm64":
    extra_compile_args = ["-O3", "-arch", "arm64", "-march=native", "-funroll-loops", "-ffast-math"]
    extra_link_args = ["-arch", "arm64", "-Wl,-rpath,@loader_path"]
# Windows (MSVC)
elif platform.system() == "Windows" and ("msvc" in (os.environ.get("CC", "") + os.environ.get("CXX", "")).lower() or "MSC" in sys.version):
    extra_compile_args = ["/O2", "/GL", "/fp:fast", "/arch:AVX2"]
else:
    # Assume Linux-like
    extra_compile_args = ["-O3", "-march=native", "-funroll-loops", "-ffast-math"]
    extra_link_args = []


# -----------------------------------------------------------------------------
# Extension module definition
# -----------------------------------------------------------------------------
mymodule = Extension(
    "eqcorr2d.eqcorr2d_engine",
    sources=["eqcorr2d/eqcorr2d_engine.c"],
    include_dirs=[np.get_include()],
    define_macros=[("NPY_NO_DEPRECATED_API", "NPY_1_7_API_VERSION")],
    extra_compile_args=extra_compile_args,
    extra_link_args=extra_link_args,
    language="c",
)

# -----------------------------------------------------------------------------
# Setup
# -----------------------------------------------------------------------------
setup(
    ext_modules=[mymodule],
    cmdclass={"build_ext": build_ext},
)
