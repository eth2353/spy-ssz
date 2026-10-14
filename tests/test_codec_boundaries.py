import subprocess
import sys
from dataclasses import FrozenInstanceError
from unittest import mock

import pytest

from spy_ssz._codecs import _CODECS, get_codec
from spy_ssz.preset import Preset
from spy_ssz.schema import schema_definitions
from spy_ssz.ssz import SszObject


def test_codec_descriptors_cover_schema_matrix_and_are_immutable() -> None:
    expected = {
        (definition.fork, definition.kind, Preset[preset.upper()])
        for definition in schema_definitions()
        for preset in definition.presets
    }
    assert set(_CODECS) == expected
    for key in expected:
        codec = get_codec(key)
        assert callable(codec.json_decoder)
        assert callable(codec.ssz_decoder)
        assert all(callable(operation) for operation in codec.json_encoder)
        assert all(callable(operation) for operation in codec.ssz_encoder)
        with pytest.raises(FrozenInstanceError):
            codec.json_decoder = codec.ssz_decoder


def test_codec_loading_does_not_import_public_type_modules() -> None:
    subprocess.run(
        [
            sys.executable,
            "-c",
            """
import sys
import spy_ssz._codecs
assert not any(name in sys.modules for name in (
    'spy_ssz.signing', 'spy_ssz.electra', 'spy_ssz.fulu', 'spy_ssz.gloas',
))
""",
        ],
        check=True,
    )


def test_owned_adoption_bypasses_public_constructor() -> None:
    class CustomOwner(SszObject):
        __slots__ = ()

        def __init__(self, *args, **kwargs):
            raise AssertionError("public constructor must not adopt native handles")

    handle = object()
    with mock.patch("spy_ssz.ssz._spy") as native:
        owner = CustomOwner._from_owned_handle(handle)
        assert owner._handle is handle
        owner.close()
        owner.close()
        native.lib.spy_ssz_object_destroy.assert_called_once_with(handle)


@pytest.mark.parametrize("after_adoption", [False, True])
def test_failed_owned_adoption_destroys_exactly_once(after_adoption) -> None:
    handle = object()
    initialize = SszObject._initialize_owner

    def fail(owner, adopted):
        if after_adoption:
            initialize(owner, adopted)
        raise RuntimeError("initialization failed")

    with (
        mock.patch("spy_ssz.ssz._spy") as native,
        mock.patch.object(SszObject, "_initialize_owner", fail),
    ):
        with pytest.raises(RuntimeError, match="initialization failed"):
            SszObject._from_owned_handle(handle)
        native.lib.spy_ssz_object_destroy.assert_called_once_with(handle)
