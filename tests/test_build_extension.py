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
