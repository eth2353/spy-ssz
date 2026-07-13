"""Electra SSZ block, block-contents, and blinded-block types."""

from typing import TypeVar

from .. import _spy
from ..preset import Preset
from ..schema import get_schema, schema_for, schemas_for
from ..ssz import (
    Fork,
    ObjectKind,
    SszObject,
    _spy_bytes,
    bind_decoder,
    register_json_decoder,
    register_json_encoder,
    register_ssz_decoder,
    register_ssz_encoder,
)


_SIGNED_BLOCK = schema_for("electra_block")
ElectraSignedBeaconBlock = type(
    _SIGNED_BLOCK.python_type,
    (SszObject,),
    {"expected_fork": _SIGNED_BLOCK.fork, "expected_kind": _SIGNED_BLOCK.kind},
)
for _preset_name in _SIGNED_BLOCK.presets:
    _preset = Preset[_preset_name.upper()]
    _name = f"{_SIGNED_BLOCK.python_type}{_preset.name.title()}"
    globals()[_name] = (
        ElectraSignedBeaconBlock
        if _preset is Preset.MAINNET
        else type(_name, (ElectraSignedBeaconBlock,), {"expected_preset": _preset})
    )

for _preset_name in _SIGNED_BLOCK.presets:
    _preset = Preset[_preset_name.upper()]
    register_json_decoder(
        _SIGNED_BLOCK.fork,
        _SIGNED_BLOCK.kind,
        bind_decoder(_spy.lib.spy_schema_electra_decode_preset_owned, _preset),
        _preset,
    )
    register_ssz_decoder(
        _SIGNED_BLOCK.fork,
        _SIGNED_BLOCK.kind,
        bind_decoder(_spy.lib.spy_schema_electra_decode_ssz_preset_owned, _preset),
        _preset,
    )
    register_ssz_encoder(
        _SIGNED_BLOCK.fork,
        _SIGNED_BLOCK.kind,
        _spy.lib.spy_schema_electra_ssz_size,
        _spy.lib.spy_schema_electra_encode_ssz,
        _preset,
    )
    register_json_encoder(
        _SIGNED_BLOCK.fork,
        _SIGNED_BLOCK.kind,
        _spy.lib.spy_schema_electra_json_size,
        _spy.lib.spy_schema_electra_encode_json,
        _preset,
    )


_CONTENTS = get_schema(Fork.ELECTRA, ObjectKind.BEACON_BLOCK_CONTENTS)
_SIGNED_CONTENTS = get_schema(Fork.ELECTRA, ObjectKind.SIGNED_BEACON_BLOCK_CONTENTS)
_BLINDED = get_schema(Fork.ELECTRA, ObjectKind.BLINDED_BEACON_BLOCK)
_SIGNED_BLINDED = get_schema(Fork.ELECTRA, ObjectKind.SIGNED_BLINDED_BEACON_BLOCK)
_SignedObject = TypeVar("_SignedObject", bound=SszObject)


def _signature_bytes(signature: str | bytes) -> bytes:
    if isinstance(signature, bytes):
        if len(signature) != 96:
            raise ValueError("BLS signature must contain 96 bytes")
        return signature
    value = signature if signature.startswith("0x") else f"0x{signature}"
    if len(value) != 194:
        raise ValueError("BLS signature must contain 96 bytes")
    try:
        return bytes.fromhex(value[2:])
    except ValueError:
        raise ValueError("BLS signature must be hexadecimal") from None


class _BlockProjection(SszObject):
    json_input_envelope_key = "data"
    json_output_envelope_key = None

    def header_dict(self) -> dict[str, str]:
        output = bytearray(112)
        output_obj, output_view = _spy_bytes(output)
        valid = _spy.lib.spy_ssz_object_block_header(self._require_handle(), output_obj)
        assert output_view
        if not valid:
            raise ValueError("SPy block header extraction failed")
        return {
            "slot": str(int.from_bytes(output[0:8], "little")),
            "proposer_index": str(int.from_bytes(output[8:16], "little")),
            "parent_root": f"0x{output[16:48].hex()}",
            "state_root": f"0x{output[48:80].hex()}",
            "body_root": f"0x{output[80:112].hex()}",
        }

    def _sign(
        self,
        signature: str | bytes,
        signed_type: type[_SignedObject],
        signed_schema: int,
    ) -> _SignedObject:
        signature_bytes = _signature_bytes(signature)
        signature_obj, signature_view = _spy_bytes(signature_bytes)
        handle = _spy.lib.spy_ssz_object_clone_and_sign_block(
            self._require_handle(),
            signature_obj,
            signed_type.expected_kind,
            signed_schema,
            self.object_kind is ObjectKind.BEACON_BLOCK_CONTENTS,
        )
        assert signature_view
        if not handle.p or not _spy.lib.spy_ssz_object_is_valid(handle):
            if handle.p:
                _spy.lib.spy_ssz_object_destroy(handle)
            raise ValueError("SPy block signing failed")
        return signed_type(handle)

    def block_hash_tree_root(self) -> str:
        if self.object_kind is ObjectKind.BEACON_BLOCK_CONTENTS:
            root = self._hash_tree_root_path(0, 0, 1)
        else:
            root = self.hash_tree_root()
        return f"0x{root.hex()}"


class ElectraBeaconBlockContents(_BlockProjection):
    expected_fork = _CONTENTS.fork
    expected_kind = _CONTENTS.kind

    def sign(self, signature: str | bytes) -> "ElectraSignedBeaconBlockContents":
        return self._sign(signature, self.signed_type(), _SIGNED_CONTENTS.schema_id)

    @classmethod
    def signed_type(cls) -> type["ElectraSignedBeaconBlockContents"]:
        return _SIGNED_CONTENTS_BY_PRESET[cls.expected_preset]


class ElectraSignedBeaconBlockContents(SszObject):
    expected_fork = _SIGNED_CONTENTS.fork
    expected_kind = _SIGNED_CONTENTS.kind
    json_input_envelope_key = "data"
    json_output_envelope_key = None


class ElectraBlindedBeaconBlock(_BlockProjection):
    expected_fork = _BLINDED.fork
    expected_kind = _BLINDED.kind

    def sign(self, signature: str | bytes) -> "ElectraSignedBlindedBeaconBlock":
        return self._sign(signature, self.signed_type(), _SIGNED_BLINDED.schema_id)

    @classmethod
    def signed_type(cls) -> type["ElectraSignedBlindedBeaconBlock"]:
        return _SIGNED_BLINDED_BY_PRESET[cls.expected_preset]


class ElectraSignedBlindedBeaconBlock(SszObject):
    expected_fork = _SIGNED_BLINDED.fork
    expected_kind = _SIGNED_BLINDED.kind
    json_input_envelope_key = "data"
    json_output_envelope_key = None


def _variant(name: str, base: type[SszObject], preset: Preset):
    return type(name, (base,), {"expected_preset": preset})


_BASES = (
    (ElectraBeaconBlockContents, _CONTENTS),
    (ElectraSignedBeaconBlockContents, _SIGNED_CONTENTS),
    (ElectraBlindedBeaconBlock, _BLINDED),
    (ElectraSignedBlindedBeaconBlock, _SIGNED_BLINDED),
)
for _base, _definition in _BASES:
    for _preset_name in _definition.presets:
        _preset = Preset[_preset_name.upper()]
        _name = f"{_base.__name__}{_preset.name.title()}"
        globals()[_name] = _variant(_name, _base, _preset)


_SIGNED_CONTENTS_BY_PRESET = {
    preset: globals()[f"ElectraSignedBeaconBlockContents{preset.name.title()}"]
    for preset in Preset
}
_SIGNED_BLINDED_BY_PRESET = {
    preset: globals()[f"ElectraSignedBlindedBeaconBlock{preset.name.title()}"]
    for preset in Preset
}


for _definition in schemas_for("block_containers"):
    _kind = _definition.kind
    for _preset_name in _definition.presets:
        _preset = Preset[_preset_name.upper()]
        register_json_decoder(
            _definition.fork,
            _kind,
            bind_decoder(
                _spy.lib.spy_schema_block_containers_decode_json_owned,
                _kind,
                _preset,
            ),
            _preset,
        )
        register_ssz_decoder(
            _definition.fork,
            _kind,
            bind_decoder(
                _spy.lib.spy_schema_block_containers_decode_ssz_owned,
                _kind,
                _preset,
            ),
            _preset,
        )
        register_json_encoder(
            _definition.fork,
            _kind,
            _spy.lib.spy_schema_block_containers_json_size,
            _spy.lib.spy_schema_block_containers_encode_json,
            _preset,
        )
        register_ssz_encoder(
            _definition.fork,
            _kind,
            _spy.lib.spy_schema_block_containers_ssz_size,
            _spy.lib.spy_schema_block_containers_encode_ssz,
            _preset,
        )
