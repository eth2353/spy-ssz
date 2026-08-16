"""Shared native beacon-block projection and signing support."""

from typing import TypeVar

from . import _spy
from .preset import Preset
from .schema import ObjectKind
from .ssz import SszObject, _spy_bytes


_SignedObject = TypeVar("_SignedObject", bound=SszObject)


def signature_bytes(signature: str | bytes) -> bytes:
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


class BlockProjection(SszObject):
    json_input_envelope_key = "data"
    json_output_envelope_key = None
    signed_schema_id: int
    signed_types_by_preset: dict[Preset, type[SszObject]]

    def header_dict(self) -> dict[str, str]:
        output = bytearray(112)
        output_obj, output_view = _spy_bytes(output)
        with self._use_handle() as handle:
            valid = _spy.lib.spy_ssz_object_block_header(handle, output_obj)
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
        signature_obj, signature_view = _spy_bytes(signature_bytes(signature))
        with self._use_handle() as source_handle:
            handle = _spy.lib.spy_ssz_object_clone_and_sign_block(
                source_handle,
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

    def sign(self, signature: str | bytes) -> SszObject:
        return self._sign(signature, self.signed_type(), self.signed_schema_id)

    @classmethod
    def signed_type(cls) -> type[SszObject]:
        return cls.signed_types_by_preset[cls.expected_preset]

    def block_hash_tree_root(self) -> str:
        if self.object_kind is ObjectKind.BEACON_BLOCK_CONTENTS:
            root = self._hash_tree_root_path(0, 0, 1)
        else:
            root = self.hash_tree_root()
        return f"0x{root.hex()}"
