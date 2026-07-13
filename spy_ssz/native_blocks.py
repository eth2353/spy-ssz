"""Native Electra block contents and blinded block types."""

from . import _native
from .native_object import (
    Fork,
    NativeSszObject,
    ObjectKind,
    register_json_decoder,
    register_json_encoder,
    register_ssz_decoder,
    register_ssz_encoder,
)
from .preset import Preset


def _signature_hex(signature: str | bytes) -> str:
    if isinstance(signature, bytes):
        if len(signature) != 96:
            raise ValueError("BLS signature must contain 96 bytes")
        return f"0x{signature.hex()}"
    value = signature if signature.startswith("0x") else f"0x{signature}"
    if len(value) != 194:
        raise ValueError("BLS signature must contain 96 bytes")
    return value


class _BlockProjection(NativeSszObject):
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
    expected_fork = Fork.ELECTRA
    expected_kind = ObjectKind.BEACON_BLOCK_CONTENTS

    def sign(self, signature: str | bytes) -> "ElectraSignedBeaconBlockContents":
        raw = self.to_json()
        marker = b',"kzg_proofs":'
        boundary = raw.rfind(marker)
        if boundary < 0 or not raw.startswith(b'{"block":'):
            raise ValueError("invalid native block contents JSON")
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


class ElectraSignedBeaconBlockContents(NativeSszObject):
    expected_fork = Fork.ELECTRA
    expected_kind = ObjectKind.SIGNED_BEACON_BLOCK_CONTENTS
    json_input_envelope_key = "data"
    json_output_envelope_key = None


class ElectraBlindedBeaconBlock(_BlockProjection):
    expected_fork = Fork.ELECTRA
    expected_kind = ObjectKind.BLINDED_BEACON_BLOCK

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


class ElectraSignedBlindedBeaconBlock(NativeSszObject):
    expected_fork = Fork.ELECTRA
    expected_kind = ObjectKind.SIGNED_BLINDED_BEACON_BLOCK
    json_input_envelope_key = "data"
    json_output_envelope_key = None


def _variant(name: str, base: type[NativeSszObject], preset: Preset):
    return type(name, (base,), {"expected_preset": preset})


_BASES = (
    ElectraBeaconBlockContents,
    ElectraSignedBeaconBlockContents,
    ElectraBlindedBeaconBlock,
    ElectraSignedBlindedBeaconBlock,
)
for _base in _BASES:
    for _preset in Preset:
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


for _kind in (
    ObjectKind.BEACON_BLOCK_CONTENTS,
    ObjectKind.SIGNED_BEACON_BLOCK_CONTENTS,
    ObjectKind.BLINDED_BEACON_BLOCK,
    ObjectKind.SIGNED_BLINDED_BEACON_BLOCK,
):
    for _preset in Preset:
        register_json_decoder(
            Fork.ELECTRA,
            _kind,
            lambda source, kind=_kind, preset=_preset: (
                _native.lib.spy_schema_block_containers_decode_json_owned(source, kind, preset)
            ),
            _preset,
        )
        register_ssz_decoder(
            Fork.ELECTRA,
            _kind,
            lambda source, kind=_kind, preset=_preset: (
                _native.lib.spy_schema_block_containers_decode_ssz_owned(source, kind, preset)
            ),
            _preset,
        )
        register_json_encoder(
            Fork.ELECTRA,
            _kind,
            _native.lib.spy_schema_block_containers_json_size,
            _native.lib.spy_schema_block_containers_encode_json,
            _preset,
        )
        register_ssz_encoder(
            Fork.ELECTRA,
            _kind,
            _native.lib.spy_schema_block_containers_ssz_size,
            _native.lib.spy_schema_block_containers_encode_ssz,
            _preset,
        )
