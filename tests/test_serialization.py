from __future__ import annotations

from pathlib import Path

from quantas_gui.services.serialization import inventory_item, to_json_value


def test_paths_are_reduced_to_display_names() -> None:
    value = to_json_value(Path(r"C:\\Users\\example\\private\\result.hdf5"))
    assert value == {"type": "path", "name": "result.hdf5"}
    assert "Users" not in str(value)
    assert inventory_item("source", Path("/srv/private/result.hdf5"))["summary"] == "result.hdf5"


def test_large_strings_mappings_and_sequences_are_bounded() -> None:
    long_string = "x" * 5000
    assert len(to_json_value(long_string)) == 4096

    mapping = {f"key-{index}": index for index in range(80)}
    serialized_mapping = to_json_value(mapping)
    assert serialized_mapping["length"] == 80
    assert len(serialized_mapping["preview"]) == 12

    sequence = list(range(100))
    serialized_sequence = to_json_value(sequence)
    assert serialized_sequence["length"] == 100
    assert serialized_sequence["preview"] == [0, 1, 2, 3, 4]
