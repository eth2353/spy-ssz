from spy_ssz import Preset, load_preset


def test_checked_in_presets_cover_supported_networks() -> None:
    mainnet = load_preset(Preset.MAINNET)
    minimal = load_preset("minimal")
    gnosis = load_preset(Preset.GNOSIS)

    assert mainnet.sync_committee_size == 512
    assert minimal.sync_committee_size == 32
    assert mainnet.max_committees_per_slot == 64
    assert minimal.max_committees_per_slot == 4
    assert mainnet.max_withdrawals_per_payload == 16
    assert minimal.max_withdrawals_per_payload == 4
    assert gnosis.max_withdrawals_per_payload == 8
