"""Encode/decode Factorio blueprint strings via Draftsman.

factopt targets Factorio **2.0**, which is also Draftsman's native version, so
directions share the 16-way enum (N/E/S/W = 0/4/8/12) end to end -- no conversion
is needed between factopt's :class:`~factopt.model.blueprint.Entity` DTO and
Draftsman.

Draftsman does the heavy lifting we used to hand-roll (base64 + zlib + JSON,
version stamping, prototype validation, and collision modeling). We keep the
lightweight internal DTO because the placement/routing stages do their own
integer-tile math against it; Draftsman is used purely at the serialization
boundary here.
"""

from __future__ import annotations

import warnings

from draftsman.blueprintable import Blueprint as _DBlueprint
from draftsman.entity import new_entity
from draftsman.utils import JSON_to_string, string_to_JSON
from draftsman.warning import DraftsmanWarning

from factopt.model.blueprint import Blueprint, Entity, Position


def decode_json(s: str) -> dict:
    """Decode a blueprint string to its raw JSON dict (lossless)."""
    s = s.strip()
    if not s:
        raise ValueError("empty blueprint string")
    try:
        return string_to_JSON(s)
    except Exception as exc:  # malformed base64/zlib/json -> clean ValueError
        raise ValueError(f"malformed blueprint string: {exc}") from exc


def encode_json(obj: dict) -> str:
    """Encode a raw JSON dict to a blueprint string (lossless)."""
    return JSON_to_string(obj)


def _to_draftsman(bp: Blueprint) -> _DBlueprint:
    d = _DBlueprint()
    if bp.label is not None:
        d.label = bp.label
    built = []
    # factopt guarantees non-overlapping layouts itself; silence Draftsman's
    # spatial/prototype chatter so the codec stays a quiet serialization step.
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DraftsmanWarning)
        for e in bp.entities:
            kwargs: dict = {"position": (e.position.x, e.position.y)}
            if e.direction:
                kwargs["direction"] = e.direction
            if e.recipe is not None:
                kwargs["recipe"] = e.recipe
            ent = new_entity(e.name, **kwargs)
            io_type = e.extra.get("type")
            if io_type is not None and hasattr(ent, "io_type"):
                ent.io_type = io_type
            built.append(ent)
        d.entities = built
    return d


# Entity JSON keys the DTO models as first-class; everything else round-trips
# through ``Entity.extra``.
_CORE_KEYS = {"entity_number", "name", "position", "direction", "recipe"}


def _entity_from_json(d: dict) -> Entity:
    extra = {k: v for k, v in d.items() if k not in _CORE_KEYS}
    # Draftsman/Factorio omit an underground belt's ``type`` when it's the
    # default ("input"); make the DTO explicit so routing sees a real io side.
    if "underground-belt" in d["name"] and "type" not in extra:
        extra["type"] = "input"
    return Entity(
        name=d["name"],
        position=Position(float(d["position"]["x"]), float(d["position"]["y"])),
        direction=int(d.get("direction", 0)),
        recipe=d.get("recipe"),
        extra=extra,
    )


def decode(s: str) -> Blueprint:
    """Decode a blueprint string to a :class:`Blueprint`.

    Only plain blueprints are supported (not blueprint books). We parse the raw
    JSON (via Draftsman's string codec) into the DTO directly; directions are the
    16-way enum the DTO already uses, so no conversion is needed.
    """
    obj = decode_json(s)
    if "blueprint" not in obj:
        kind = next(iter(obj), "<empty>")
        raise ValueError(f"expected a 'blueprint', got {kind!r} (books unsupported)")
    bp = obj["blueprint"]
    return Blueprint(
        label=bp.get("label"),
        entities=[_entity_from_json(e) for e in bp.get("entities", [])],
    )


def encode(bp: Blueprint) -> str:
    """Encode a :class:`Blueprint` to a Factorio 2.0 blueprint string."""
    return _to_draftsman(bp).to_string()
