"""Build the SPy-generated native extension as part of a platform wheel."""

from __future__ import annotations

import os
import importlib.util
import shutil
from pathlib import Path

from setuptools import Distribution, setup
from setuptools.command.build_py import build_py as _build_py


_build_script = Path(__file__).parent / "tools" / "build_native.py"
_spec = importlib.util.spec_from_file_location("spy_ssz_build_native", _build_script)
if _spec is None or _spec.loader is None:
    raise RuntimeError(f"cannot load native build helper: {_build_script}")
_build_native = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_build_native)


class BinaryDistribution(Distribution):
    def has_ext_modules(self) -> bool:
        return True


class BuildPy(_build_py):
    def run(self) -> None:
        artifact = _build_native.build(
            _build_native.resolve_spy_root(os.environ.get("SPY_ROOT"))
        )
        super().run()
        target = Path(self.build_lib) / "spy_ssz" / artifact.name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(artifact, target)


setup(cmdclass={"build_py": BuildPy}, distclass=BinaryDistribution)
