from pathlib import Path

import pytest

from tools import build_extension


def test_explicit_invalid_spy_root_does_not_fall_back_or_clone(
    tmp_path, monkeypatch
) -> None:
    def fail(*args, **kwargs):
        raise AssertionError("an invalid explicit checkout must not trigger a clone")

    monkeypatch.setattr(build_extension.subprocess, "run", fail)
    with pytest.raises(ValueError, match="not a SPy source checkout"):
        build_extension.resolve_spy_root(tmp_path / "missing")


def test_explicit_spy_root_is_resolved(tmp_path) -> None:
    makefile = tmp_path / "spy" / "libspy" / "Makefile"
    makefile.parent.mkdir(parents=True)
    makefile.touch()
    assert build_extension.resolve_spy_root(tmp_path) == tmp_path.resolve()


def test_source_staging_rejects_ambiguous_module_names(tmp_path, monkeypatch) -> None:
    source = tmp_path / "src"
    for fork in ("electra", "gloas"):
        module = source / fork / "codec.spy"
        module.parent.mkdir(parents=True)
        module.write_text("# example\n")
    monkeypatch.setattr(build_extension, "SOURCE", source)
    monkeypatch.setattr(build_extension, "BUILD", source / "build")
    with pytest.raises(RuntimeError, match="module basename collision"):
        build_extension.stage_spy_sources()


def test_source_staging_excludes_previous_build_outputs(tmp_path, monkeypatch) -> None:
    source = tmp_path / "src"
    build = source / "build"
    build.mkdir(parents=True)
    (source / "codec.spy").write_text("# authoritative source\n")
    (build / "codec.spy").write_text("# stale generated source\n")
    monkeypatch.setattr(build_extension, "SOURCE", source)
    monkeypatch.setattr(build_extension, "BUILD", build)
    staged: Path = build_extension.stage_spy_sources()
    assert (staged / "codec.spy").read_text() == "# authoritative source\n"


@pytest.fixture
def extension_setup(monkeypatch):
    import runpy

    import setuptools

    options = {}
    monkeypatch.setattr(setuptools, "setup", lambda **kwargs: options.update(kwargs))
    namespace = runpy.run_path(str(Path(__file__).resolve().parents[1] / "setup.py"))
    return namespace, options


@pytest.mark.parametrize("inplace", [False, True])
def test_setuptools_build_ext_installs_native_artifact(
    tmp_path, monkeypatch, extension_setup, inplace
) -> None:
    from setuptools import Distribution

    namespace, options = extension_setup
    monkeypatch.chdir(tmp_path)
    (tmp_path / "spy_ssz").mkdir()
    artifact = tmp_path / "compiled" / "_spy.so"
    artifact.parent.mkdir()
    artifact.write_bytes(b"compiled extension")
    helper = namespace["_build_extension"]
    monkeypatch.setattr(helper, "resolve_spy_root", lambda value: tmp_path)
    monkeypatch.setattr(helper, "build", lambda root: artifact)

    distribution = Distribution({**options, "packages": ["spy_ssz"]})
    command = distribution.get_command_obj("build_ext")
    command.inplace = inplace
    command.ensure_finalized()
    command.run()

    assert Path(command.get_ext_fullpath("spy_ssz._spy")).read_bytes() == (
        b"compiled extension"
    )
    assert distribution.has_ext_modules()


def test_setuptools_build_ext_propagates_compiler_failure(
    tmp_path, monkeypatch, extension_setup
) -> None:
    from setuptools import Distribution

    namespace, options = extension_setup
    monkeypatch.chdir(tmp_path)
    helper = namespace["_build_extension"]
    monkeypatch.setattr(helper, "resolve_spy_root", lambda value: tmp_path)

    def fail(root):
        raise RuntimeError("native compilation failed")

    monkeypatch.setattr(helper, "build", fail)
    command = Distribution(options).get_command_obj("build_ext")
    command.ensure_finalized()
    with pytest.raises(RuntimeError, match="native compilation failed"):
        command.run()
