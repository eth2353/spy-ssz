"""Preset variants shared by the fork and signing modules."""

from typing import Any

from .preset import Preset
from .schema import SchemaDefinition
from .ssz import SszObject


def export_preset_types(
    namespace: dict[str, Any],
    base: type[SszObject],
    definition: SchemaDefinition,
    *,
    alias_mainnet: bool = True,
) -> None:
    """Export preset subclasses, preserving the historical mainnet aliases."""
    # type() otherwise assigns dynamically created classes to this helper's
    # module, breaking introspection and import-based class lookup.
    base.__module__ = namespace["__name__"]
    namespace[definition.python_type] = base
    for preset_name in definition.presets:
        preset = Preset[preset_name.upper()]
        name = f"{definition.python_type}{preset.name.title()}"
        namespace[name] = (
            base
            if alias_mainnet and preset is Preset.MAINNET
            else type(
                name,
                (base,),
                {"expected_preset": preset, "__module__": namespace["__name__"]},
            )
        )
