from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from cffi import FFI


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src"
BUILD = SOURCE / "build"
SPY_REVISION = "012ae501eb6a0adc3baff261c97ec9b56c80c2d1"
SPY_REPOSITORY = "https://github.com/spylang/spy.git"


def run(command: list[str], *, env: dict[str, str]) -> None:
    subprocess.run(command, cwd=ROOT, env=env, check=True)


def resolve_spy_root(value: str | Path | None = None) -> Path:
    candidates = [Path(value)] if value else []
    candidates.append(ROOT / ".deps" / "spy")
    for candidate in candidates:
        if (candidate / "spy" / "libspy" / "Makefile").is_file():
            return candidate.resolve()

    checkout = Path(tempfile.gettempdir()) / f"spy-ssz-{SPY_REVISION[:12]}"
    if not (checkout / "spy" / "libspy" / "Makefile").is_file():
        subprocess.run(
            ["git", "clone", "--filter=blob:none", SPY_REPOSITORY, str(checkout)],
            check=True,
        )
        subprocess.run(["git", "checkout", SPY_REVISION], cwd=checkout, check=True)
    return checkout.resolve()


def build(spy_root: Path) -> Path:
    spy_root = spy_root.resolve()
    if not (spy_root / "spy" / "libspy" / "Makefile").is_file():
        raise SystemExit(f"not a SPy source checkout: {spy_root}")

    env = os.environ.copy()
    env["PYTHONPATH"] = str(spy_root)
    env["PATH"] = f"{Path(sys.executable).parent}:{env.get('PATH', '')}"
    env.setdefault("ZIG_GLOBAL_CACHE_DIR", "/tmp/spy-zig-global-cache")
    env.setdefault("ZIG_LOCAL_CACHE_DIR", "/tmp/spy-zig-local-cache")

    run([sys.executable, str(ROOT / "tools" / "generate_spy_metadata.py")], env=env)

    libspy = spy_root / "spy" / "libspy"
    run(
        ["make", "-C", str(libspy), "TARGET=wasi", "BUILD_TYPE=debug"],
        env=env,
    )
    run(
        ["make", "-C", str(libspy), "TARGET=native", "BUILD_TYPE=release"],
        env=env,
    )
    # SPy does not remove generated units that disappeared from the import
    # graph.  A clean directory prevents stale schema/parser C files from
    # being compiled into the extension.
    shutil.rmtree(BUILD, ignore_errors=True)
    run(
        [
            str(Path(sys.executable).with_name("spy")),
            "build",
            "--output-kind",
            "py-cffi",
            "--no-compile",
            "--release",
            "--gc",
            "none",
            "-O",
            "3",
            str(SOURCE / "api.spy"),
        ],
        env=env,
    )

    sources = sorted((BUILD / "src").glob("*.c"))
    if not sources:
        raise SystemExit("SPy did not generate C sources")

    ffi = FFI()
    ffi.cdef(
        """
        typedef struct { uint8_t *p; } spy_gc_ptr_u8;
        typedef struct {
            size_t length;
            int32_t hash;
            spy_gc_ptr_u8 data;
        } spy_BytesObject;
        typedef struct { void *p; } spy_raw_ssz_ptr;

        spy_raw_ssz_ptr spy_schema_deneb_decode_owned(spy_BytesObject *source);
        spy_raw_ssz_ptr spy_schema_deneb_decode_ssz_owned(
            spy_BytesObject *source);
        spy_raw_ssz_ptr spy_schema_deneb_decode_attestation_ssz_owned(
            spy_BytesObject *source);
        spy_raw_ssz_ptr spy_schema_electra_decode_owned(spy_BytesObject *source);
        spy_raw_ssz_ptr spy_schema_electra_decode_preset_owned(
            spy_BytesObject *source, int32_t preset);
        spy_raw_ssz_ptr spy_schema_electra_decode_ssz_owned(spy_BytesObject *source);
        spy_raw_ssz_ptr spy_schema_electra_decode_ssz_preset_owned(
            spy_BytesObject *source, int32_t preset);
        spy_raw_ssz_ptr spy_schema_fulu_decode_owned(spy_BytesObject *source);
        spy_raw_ssz_ptr spy_schema_fulu_decode_preset_owned(
            spy_BytesObject *source, int32_t preset);
        spy_raw_ssz_ptr spy_schema_fulu_decode_ssz_owned(spy_BytesObject *source);
        spy_raw_ssz_ptr spy_schema_fulu_decode_ssz_preset_owned(
            spy_BytesObject *source, int32_t preset);
        spy_raw_ssz_ptr spy_schema_deneb_decode_attestation_owned(
            spy_BytesObject *source);
        spy_raw_ssz_ptr spy_schema_gloas_decode_attestation_owned(
            spy_BytesObject *source);
        spy_raw_ssz_ptr spy_schema_gloas_decode_attestation_ssz_owned(
            spy_BytesObject *source);
        spy_raw_ssz_ptr spy_schema_signing_decode_json_owned(
            spy_BytesObject *source, int32_t kind, int32_t schema,
            int32_t preset);
        spy_raw_ssz_ptr spy_schema_signing_decode_ssz_owned(
            spy_BytesObject *source, int32_t kind, int32_t schema,
            int32_t preset);
        spy_raw_ssz_ptr spy_schema_block_containers_decode_json_owned(
            spy_BytesObject *source, int32_t kind, int32_t preset);
        spy_raw_ssz_ptr spy_schema_block_containers_decode_ssz_owned(
            spy_BytesObject *source, int32_t kind, int32_t preset);
        int32_t spy_ssz_object_hash_tree_root(
            spy_raw_ssz_ptr object, spy_BytesObject *output);
        int32_t spy_ssz_object_is_valid(spy_raw_ssz_ptr object);
        int32_t spy_ssz_object_fork(spy_raw_ssz_ptr object);
        int32_t spy_ssz_object_preset(spy_raw_ssz_ptr object);
        int32_t spy_ssz_object_kind(spy_raw_ssz_ptr object);
        int32_t spy_ssz_object_schema(spy_raw_ssz_ptr object);
        int32_t spy_ssz_object_node_count(spy_raw_ssz_ptr object);
        int32_t spy_ssz_object_hash_tree_root_path(
            spy_raw_ssz_ptr object, int32_t first, int32_t second,
            int32_t depth, spy_BytesObject *output);
        int32_t spy_schema_electra_ssz_size(spy_raw_ssz_ptr object);
        int32_t spy_schema_electra_encode_ssz(
            spy_raw_ssz_ptr object, spy_BytesObject *output);
        int32_t spy_schema_electra_json_size(spy_raw_ssz_ptr object);
        int32_t spy_schema_electra_encode_json(
            spy_raw_ssz_ptr object, spy_BytesObject *output);
        int32_t spy_schema_signing_ssz_size(spy_raw_ssz_ptr object);
        int32_t spy_schema_signing_encode_ssz(
            spy_raw_ssz_ptr object, spy_BytesObject *output);
        int32_t spy_schema_signing_json_size(spy_raw_ssz_ptr object);
        int32_t spy_schema_signing_encode_json(
            spy_raw_ssz_ptr object, spy_BytesObject *output);
        int32_t spy_schema_block_containers_ssz_size(spy_raw_ssz_ptr object);
        int32_t spy_schema_block_containers_encode_ssz(
            spy_raw_ssz_ptr object, spy_BytesObject *output);
        int32_t spy_schema_block_containers_json_size(spy_raw_ssz_ptr object);
        int32_t spy_schema_block_containers_encode_json(
            spy_raw_ssz_ptr object, spy_BytesObject *output);
        void spy_ssz_object_destroy(spy_raw_ssz_ptr object);
        """
    )
    ffi.set_source(
        "spy_ssz._spy",
        '#include "bridge.c"',
        sources=[str(path) for path in sources],
        include_dirs=[str(SOURCE), str(BUILD / "src"), str(libspy / "include")],
        library_dirs=[str(libspy / "build" / "native" / "release")],
        libraries=["spy", "m"],
        extra_compile_args=[
            "-fPIC",
            "-DSPY_GC_NONE",
            "-DSPY_TARGET_NATIVE",
            "-DSPY_RELEASE",
            "-O3",
            "-flto",
            "--std=c99",
            "-w",
        ],
        extra_link_args=["-flto"],
    )
    compiled = Path(
        ffi.compile(tmpdir=str(BUILD / "extension"), verbose=True)
    ).resolve()
    artifact = ROOT / "spy_ssz" / compiled.name
    shutil.copy2(compiled, artifact)
    print(artifact)
    return artifact


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--spy-root",
        type=Path,
        default=os.environ.get("SPY_ROOT"),
        help="optional SPy git checkout (or set SPY_ROOT)",
    )
    args = parser.parse_args()
    build(resolve_spy_root(args.spy_root))


if __name__ == "__main__":
    main()
