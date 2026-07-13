"""Electra block contents and blinded block types."""

from . import _spy
from .ssz import (
    Fork,
    SszObject,
    ObjectKind,
    register_json_decoder,
    register_json_encoder,
    register_ssz_decoder,
    register_ssz_encoder,
)
from .preset import Preset
from .schema import get_schema, schemas_for


_CONTENTS = get_schema(Fork.ELECTRA, ObjectKind.BEACON_BLOCK_CONTENTS)
_SIGNED_CONTENTS = get_schema(Fork.ELECTRA, ObjectKind.SIGNED_BEACON_BLOCK_CONTENTS)
_BLINDED = get_schema(Fork.ELECTRA, ObjectKind.BLINDED_BEACON_BLOCK)
_SIGNED_BLINDED = get_schema(Fork.ELECTRA, ObjectKind.SIGNED_BLINDED_BEACON_BLOCK)


def _signature_hex(signature: str | bytes) -> str:
    if isinstance(signature, bytes):
        if len(signature) != 96:
            raise ValueError("BLS signature must contain 96 bytes")
        return f"0x{signature.hex()}"
    value = signature if signature.startswith("0x") else f"0x{signature}"
    if len(value) != 194:
        raise ValueError("BLS signature must contain 96 bytes")
    return value


class _BlockProjection(SszObject):
    json_input_envelope_key = "data"
    json_output_envelope_key = None

    def header_dict(self) -> dict[str, str]:
        value = self.to_obj()
        if self.object_kind is ObjectKind.BEACON_BLOCK_CONTENTS:
            block = value["block"]
            body_root = self._hash_tree_root_path(0, 4, 2)
        else:
            block = value
            body_root = self._hash_tree_root_path(4, 0, 1)
        return {
            "slot": str(block["slot"]),
            "proposer_index": str(block["proposer_index"]),
            "parent_root": block["parent_root"],
            "state_root": block["state_root"],
            "body_root": f"0x{body_root.hex()}",
        }

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
        raw = self.to_json()
        marker = b',"kzg_proofs":'
        boundary = raw.rfind(marker)
        if boundary < 0 or not raw.startswith(b'{"block":'):
            raise ValueError("invalid SPy block contents JSON")
        signature_bytes = _signature_hex(signature).encode()
        signed = (
            b'{"signed_block":{"message":'
            + raw[len(b'{"block":') : boundary]
            + b',"signature":"'
            + signature_bytes
            + b'"}'
            + raw[boundary:]
        )
        return self.signed_type().from_json(b'{"data":' + signed + b"}")

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
        signature_bytes = _signature_hex(signature).encode()
        signed = (
            b'{"message":'
            + self.to_json()
            + b',"signature":"'
            + signature_bytes
            + b'"}'
        )
        return self.signed_type().from_json(b'{"data":' + signed + b"}")

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
            lambda source, kind=_kind, preset=_preset: (
                _spy.lib.spy_schema_block_containers_decode_json_owned(
                    source, kind, preset
                )
            ),
            _preset,
        )
        register_ssz_decoder(
            _definition.fork,
            _kind,
            lambda source, kind=_kind, preset=_preset: (
                _spy.lib.spy_schema_block_containers_decode_ssz_owned(
                    source, kind, preset
                )
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
