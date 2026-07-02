from factopt.codec import decode, encode, decode_json, encode_json
from factopt.model import Blueprint, Entity, Position
from factopt.model.blueprint import EAST


def _sample_blueprint() -> Blueprint:
    return Blueprint(
        label="test",
        entities=[
            Entity(
                name="assembling-machine-2",
                position=Position(0.5, 0.5),
                recipe="electronic-circuit",
            ),
            Entity(name="transport-belt", position=Position(2.5, 0.5), direction=EAST),
            Entity(name="inserter", position=Position(1.5, 0.5), direction=EAST),
        ],
    )


def test_roundtrip_blueprint_object():
    bp = _sample_blueprint()
    s = encode(bp)
    assert s.startswith("0")
    back = decode(s)
    assert len(back.entities) == 3
    assert back.label == "test"
    names = sorted(e.name for e in back.entities)
    assert names == ["assembling-machine-2", "inserter", "transport-belt"]
    am = next(e for e in back.entities if e.name == "assembling-machine-2")
    assert am.recipe == "electronic-circuit"
    assert am.position == Position(0.5, 0.5)


def test_entity_numbers_assigned():
    bp = _sample_blueprint()
    obj = decode_json(encode(bp))
    nums = [e["entity_number"] for e in obj["blueprint"]["entities"]]
    assert nums == [1, 2, 3]


def test_extra_fields_captured_in_dto():
    # Fields we don't model first-class (e.g. control_behavior) land in extra.
    raw = {
        "blueprint": {
            "item": "blueprint",
            "version": 281479275151360,
            "entities": [
                {
                    "entity_number": 1,
                    "name": "fast-inserter",
                    "position": {"x": 0.5, "y": 0.5},
                    "direction": 2,
                    "control_behavior": {"circuit_mode_of_operation": 0},
                }
            ],
        }
    }
    bp = decode(encode_json(raw))
    ent = bp.entities[0]
    assert ent.extra.get("control_behavior") == {"circuit_mode_of_operation": 0}


def test_raw_dict_roundtrip_is_lossless():
    # The dict-level codec (Draftsman's string <-> JSON) preserves everything,
    # which is where arbitrary community-blueprint data survives untouched.
    raw = {
        "blueprint": {
            "item": "blueprint",
            "version": 281479275151360,
            "entities": [
                {
                    "entity_number": 1,
                    "name": "fast-inserter",
                    "position": {"x": 0.5, "y": 0.5},
                    "direction": 2,
                    "control_behavior": {"circuit_mode_of_operation": 0},
                }
            ],
        }
    }
    out = decode_json(encode_json(raw))
    assert out["blueprint"]["entities"][0]["control_behavior"] == {"circuit_mode_of_operation": 0}


def test_exports_factorio_2_0_format():
    # A 2.0 target: version stamp is major 2, directions use the 16-way enum.
    s = encode(_sample_blueprint())
    obj = decode_json(s)
    assert (obj["blueprint"]["version"] >> 48) == 2
    dirs = {e.get("direction") for e in obj["blueprint"]["entities"] if e.get("direction")}
    assert dirs <= {4, 8, 12}  # E / S / W in the 2.0 16-way enum (N=0 omitted)


def test_rejects_malformed_string():
    import pytest

    with pytest.raises(ValueError):
        decode("Xabcdef")
