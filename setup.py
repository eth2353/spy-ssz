"""Build the SPy-generated extension as part of a platform wheel."""

from __future__ import annotations

import os
import importlib.util
import shutil
from pathlib import Path

from setuptools import Distribution, setup
from setuptools.command.build_py import build_py as _build_py


_build_script = Path(__file__).parent / "tools" / "build_extension.py"
_spec = importlib.util.spec_from_file_location("spy_ssz_build_extension", _build_script)
if _spec is None or _spec.loader is None:
    raise RuntimeError(f"cannot load SPy build helper: {_build_script}")
_build_extension = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_build_extension)


class BinaryDistribution(Distribution):
    def has_ext_modules(self) -> bool:
        return True


class BuildPy(_build_py):
    def run(self) -> None:
        artifact = _build_extension.build(
            _build_extension.resolve_spy_root(os.environ.get("SPY_ROOT"))
        )
        super().run()
        target = Path(self.build_lib) / "spy_ssz" / artifact.name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(artifact, target)


setup(cmdclass={"build_py": BuildPy}, distclass=BinaryDistribution)
