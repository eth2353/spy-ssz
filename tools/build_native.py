from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

from cffi import FFI


ROOT = Path(__file__).resolve().parents[1]
NATIVE = ROOT / "native"
BUILD = NATIVE / "build"


def run(command: list[str], *, env: dict[str, str]) -> None:
    subprocess.run(command, cwd=ROOT, env=env, check=True)


def build(spy_root: Path) -> Path:
    spy_root = spy_root.resolve()
    if not (spy_root / "spy" / "libspy" / "Makefile").is_file():
        raise SystemExit(f"not a SPy source checkout: {spy_root}")

    env = os.environ.copy()
    env["PYTHONPATH"] = str(spy_root)
    env["PATH"] = f"{Path(sys.executable).parent}:{env.get('PATH', '')}"
    env.setdefault("ZIG_GLOBAL_CACHE_DIR", "/tmp/spy-zig-global-cache")
    env.setdefault("ZIG_LOCAL_CACHE_DIR", "/tmp/spy-zig-local-cache")

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
            str(NATIVE / "native_api.spy"),
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

        void spy_ssz_kernels_hash_pair_into(
            spy_BytesObject *source, int32_t source_offset,
            spy_BytesObject *output, int32_t output_offset,
            spy_BytesObject *state, spy_BytesObject *schedule);
        void spy_ssz_kernels_merkleize_in_place(
            spy_BytesObject *work, int32_t leaf_count,
            spy_BytesObject *state, spy_BytesObject *schedule);
        spy_raw_ssz_ptr spy_schema_deneb_decode_owned(spy_BytesObject *source);
        spy_raw_ssz_ptr spy_schema_deneb_decode_ssz_owned(
            spy_BytesObject *source);
        spy_raw_ssz_ptr spy_schema_deneb_decode_attestation_ssz_owned(
            spy_BytesObject *source);
        spy_raw_ssz_ptr spy_schema_electra_decode_owned(spy_BytesObject *source);
        spy_raw_ssz_ptr spy_schema_electra_decode_ssz_owned(spy_BytesObject *source);
        spy_raw_ssz_ptr spy_schema_fulu_decode_owned(spy_BytesObject *source);
        spy_raw_ssz_ptr spy_schema_fulu_decode_ssz_owned(spy_BytesObject *source);
        spy_raw_ssz_ptr spy_schema_deneb_decode_attestation_owned(
            spy_BytesObject *source);
        spy_raw_ssz_ptr spy_schema_gloas_decode_attestation_owned(
            spy_BytesObject *source);
        spy_raw_ssz_ptr spy_schema_gloas_decode_attestation_ssz_owned(
            spy_BytesObject *source);
        int32_t spy_ssz_object_hash_tree_root(
            spy_raw_ssz_ptr object, spy_BytesObject *output);
        int32_t spy_ssz_object_is_valid(spy_raw_ssz_ptr object);
        int32_t spy_ssz_object_fork(spy_raw_ssz_ptr object);
        int32_t spy_ssz_object_kind(spy_raw_ssz_ptr object);
        int32_t spy_ssz_object_schema(spy_raw_ssz_ptr object);
        int32_t spy_ssz_object_node_count(spy_raw_ssz_ptr object);
        int32_t spy_schema_electra_ssz_size(spy_raw_ssz_ptr object);
        int32_t spy_schema_electra_encode_ssz(
            spy_raw_ssz_ptr object, spy_BytesObject *output);
        int32_t spy_schema_electra_json_size(spy_raw_ssz_ptr object);
        int32_t spy_schema_electra_encode_json(
            spy_raw_ssz_ptr object, spy_BytesObject *output);
        void spy_ssz_object_destroy(spy_raw_ssz_ptr object);
        """
    )
    ffi.set_source(
        "postpy_ssz._native",
        """
        #include "ssz_kernels.h"
        #include "json_parser.h"
        #include "ssz_reader.h"
        #include "ssz_object.h"
        #include "schema_deneb.h"
        #include "schema_deneb_ssz.h"
        #include "schema_electra.h"
        #include "schema_electra_ssz.h"
        #include "schema_electra_encode.h"
        #include "schema_gloas.h"
        #include "schema_gloas_ssz.h"
        typedef spy_unsafe$raw_ptr__json_parser$JsonDocument spy_raw_json_ptr;
        typedef spy_unsafe$raw_ptr__ssz_reader$SszDocument spy_raw_ssz_document_ptr;
        typedef spy_unsafe$raw_ptr__ssz_object$NativeSszObject spy_raw_ssz_ptr;
        #define spy_ssz_kernels_hash_pair_into spy_ssz_kernels$hash_pair_into
        #define spy_ssz_kernels_merkleize_in_place spy_ssz_kernels$merkleize_in_place

        static void spy_json_document_destroy(spy_raw_json_ptr opaque) {
            spy_json_parser$JsonDocument *document = opaque.p;
            if (document == NULL) return;
            free(document->json.p);
            free(document->tokens.p);
            free(document);
        }

        static void spy_ssz_document_destroy(spy_raw_ssz_document_ptr opaque) {
            spy_ssz_reader$SszDocument *document = opaque.p;
            if (document == NULL) return;
            free(document->data.p);
            free(document);
        }

        spy_raw_ssz_ptr spy_schema_deneb_decode_owned(spy_BytesObject *source) {
            spy_schema_deneb$DenebDecodeResult result =
                spy_schema_deneb$decode_deneb_signed_block(source);
            spy_json_document_destroy(result.temporary);
            return result.object;
        }
        spy_raw_ssz_ptr spy_schema_deneb_decode_ssz_owned(
            spy_BytesObject *source) {
            spy_schema_deneb_ssz$DenebSszDecodeResult result =
                spy_schema_deneb_ssz$decode_deneb_signed_block_ssz(source);
            spy_ssz_document_destroy(result.temporary);
            return result.object;
        }
        spy_raw_ssz_ptr spy_schema_deneb_decode_attestation_ssz_owned(
            spy_BytesObject *source) {
            spy_schema_deneb_ssz$DenebSszDecodeResult result =
                spy_schema_deneb_ssz$decode_deneb_attestation_ssz(source);
            spy_ssz_document_destroy(result.temporary);
            return result.object;
        }
        spy_raw_ssz_ptr spy_schema_electra_decode_owned(spy_BytesObject *source) {
            spy_schema_deneb$DenebDecodeResult result =
                spy_schema_electra$decode_signed_block(source, 2, 201);
            spy_json_document_destroy(result.temporary);
            return result.object;
        }
        spy_raw_ssz_ptr spy_schema_electra_decode_ssz_owned(
            spy_BytesObject *source) {
            spy_schema_deneb_ssz$DenebSszDecodeResult result =
                spy_schema_electra_ssz$decode_signed_block_ssz(source, 2, 201);
            spy_ssz_document_destroy(result.temporary);
            return result.object;
        }
        spy_raw_ssz_ptr spy_schema_fulu_decode_owned(spy_BytesObject *source) {
            spy_schema_deneb$DenebDecodeResult result =
                spy_schema_electra$decode_signed_block(source, 3, 301);
            spy_json_document_destroy(result.temporary);
            return result.object;
        }
        spy_raw_ssz_ptr spy_schema_fulu_decode_ssz_owned(
            spy_BytesObject *source) {
            spy_schema_deneb_ssz$DenebSszDecodeResult result =
                spy_schema_electra_ssz$decode_signed_block_ssz(source, 3, 301);
            spy_ssz_document_destroy(result.temporary);
            return result.object;
        }
        spy_raw_ssz_ptr spy_schema_deneb_decode_attestation_owned(
            spy_BytesObject *source) {
            spy_schema_deneb$DenebDecodeResult result =
                spy_schema_deneb$decode_deneb_attestation(source);
            spy_json_document_destroy(result.temporary);
            return result.object;
        }
        spy_raw_ssz_ptr spy_schema_gloas_decode_attestation_owned(
            spy_BytesObject *source) {
            spy_schema_deneb$DenebDecodeResult result =
                spy_schema_gloas$decode_gloas_attestation(source);
            spy_json_document_destroy(result.temporary);
            return result.object;
        }
        spy_raw_ssz_ptr spy_schema_gloas_decode_attestation_ssz_owned(
            spy_BytesObject *source) {
            spy_schema_deneb_ssz$DenebSszDecodeResult result =
                spy_schema_gloas_ssz$decode_gloas_attestation_ssz(source);
            spy_ssz_document_destroy(result.temporary);
            return result.object;
        }

        #define spy_ssz_object_hash_tree_root spy_ssz_object$object_hash_tree_root
        #define spy_schema_electra_ssz_size spy_schema_electra_encode$electra_ssz_size
        #define spy_schema_electra_encode_ssz spy_schema_electra_encode$electra_encode_ssz
        #define spy_schema_electra_json_size spy_schema_electra_encode$electra_json_size
        #define spy_schema_electra_encode_json spy_schema_electra_encode$electra_encode_json

        int32_t spy_ssz_object_is_valid(spy_raw_ssz_ptr opaque) {
            return opaque.p != NULL && opaque.p->valid;
        }
        int32_t spy_ssz_object_fork(spy_raw_ssz_ptr opaque) {
            return opaque.p->fork;
        }
        int32_t spy_ssz_object_kind(spy_raw_ssz_ptr opaque) {
            return opaque.p->object_kind;
        }
        int32_t spy_ssz_object_schema(spy_raw_ssz_ptr opaque) {
            return opaque.p->schema_id;
        }
        int32_t spy_ssz_object_node_count(spy_raw_ssz_ptr opaque) {
            return opaque.p->node_count;
        }
        void spy_ssz_object_destroy(spy_raw_ssz_ptr opaque) {
            spy_ssz_object$NativeSszObject *obj = opaque.p;
            if (obj == NULL) return;
            free(obj->nodes.p);
            free(obj->edges.p);
            free(obj->arena.p);
            if (obj->work.p != NULL) free(obj->work.p);
            if (obj->zeros.p != NULL) free(obj->zeros.p);
            if (obj->state.p != NULL) free(obj->state.p);
            if (obj->schedule.p != NULL) free(obj->schedule.p);
            if (obj->root.p != NULL) free(obj->root.p);
            free(obj);
        }
        """,
        sources=[str(path) for path in sources],
        include_dirs=[str(BUILD / "src"), str(libspy / "include")],
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
    artifact = ROOT / "postpy_ssz" / compiled.name
    shutil.copy2(compiled, artifact)
    print(artifact)
    return artifact


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--spy-root",
        type=Path,
        default=Path(os.environ["SPY_ROOT"]) if "SPY_ROOT" in os.environ else None,
        required="SPY_ROOT" not in os.environ,
        help="SPy git checkout (or set SPY_ROOT)",
    )
    args = parser.parse_args()
    build(args.spy_root)


if __name__ == "__main__":
    main()
