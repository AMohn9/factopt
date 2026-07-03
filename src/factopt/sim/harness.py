"""Headless-Factorio simulation harness: measure a block's true throughput.

The loop's objective is analytical; this harness measures the real thing --
by building the blueprint in a headless Factorio
instance, feeding its raw inputs from infinity chests, powering it from an
electric-energy-interface, running it at high speed, and reading the output
item's production rate from the force's flow statistics. That measured items/sec
is the ground-truth objective an outer search can optimize against.

Data flows through the scenario like this:

* Factorio's Lua sandbox can *write* files (``game.write_file``) but not read
  arbitrary ones, so the job (blueprint string, input sources, output item, run
  length) is injected by writing a ``job.lua`` module into a per-run copy of the
  bundled scenario; ``control.lua`` does ``require("job")``.
* The scenario writes ``factopt_sim_result.json`` into Factorio's
  ``script-output`` directory; this driver polls for it and parses the result.

This module is import-safe and fully unit-testable without Factorio installed:
serialization, parsing, and the "Factorio missing" path have no game dependency.
Only :func:`run_headless` shells out, and it fails fast with
:class:`FactorioNotFound` when the binary isn't there.

In-game verification still needed (documented, since it can't be tested here):
the exact ``control.lua`` entity facing / source wiring and the headless launch
flags for a given Factorio version -- see ``scenario/control.lua``.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path

RESULT_FILENAME = "factopt_sim_result.json"
_SCENARIO_SRC = Path(__file__).parent / "scenario"


class FactorioNotFound(RuntimeError):
    """Raised when the configured Factorio binary cannot be found/executed."""


@dataclass(frozen=True)
class Source:
    """An infinite supply of ``item`` injected onto the belt tile at (x, y)."""

    x: int
    y: int
    item: str


@dataclass
class SimJob:
    """A single simulation request."""

    blueprint_string: str
    output_item: str
    sources: list[Source] = field(default_factory=list)
    # 2 game-minutes at 60 UPS: warm up, then read the trailing one-minute window.
    ticks: int = 7200
    speed: float = 100.0

    def to_lua(self) -> str:
        """Serialize as a Lua module (``return { ... }``) for the scenario.

        The blueprint string uses only the base64 alphabet plus a leading version
        byte (no quotes, backslashes, or ``]]``), so a long-bracket literal is safe.
        """
        src_lines = "\n".join(
            f'    {{ x = {s.x}, y = {s.y}, item = "{s.item}" }},' for s in self.sources
        )
        return (
            "return {\n"
            f"  blueprint = [[{self.blueprint_string}]],\n"
            f'  output = "{self.output_item}",\n'
            f"  ticks = {int(self.ticks)},\n"
            f"  speed = {float(self.speed)},\n"
            "  sources = {\n"
            f"{src_lines}\n"
            "  },\n"
            "}\n"
        )


@dataclass
class SimResult:
    """Parsed outcome of a simulation run."""

    output_item: str
    output_per_sec: float
    ticks: int
    raw: dict = field(default_factory=dict)

    @classmethod
    def from_json(cls, text: str) -> "SimResult":
        obj = json.loads(text)
        if not obj.get("done"):
            raise ValueError("simulation result is not marked done")
        return cls(
            output_item=obj["output_item"],
            output_per_sec=float(obj["output_per_sec"]),
            ticks=int(obj.get("ticks", 0)),
            raw=obj,
        )


def _prepare_scenario(job: SimJob, scenarios_dir: Path, scenario_name: str) -> Path:
    """Copy the bundled scenario into ``scenarios_dir`` and inject ``job.lua``."""
    dst = Path(scenarios_dir) / scenario_name
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(_SCENARIO_SRC, dst)
    (dst / "job.lua").write_text(job.to_lua(), encoding="utf-8")
    return dst


def run_headless(
    job: SimJob,
    factorio_path: str | os.PathLike,
    *,
    scenarios_dir: str | os.PathLike,
    script_output_dir: str | os.PathLike,
    scenario_name: str = "factopt_sim",
    extra_args: tuple[str, ...] = (),
    timeout_s: float = 300.0,
    poll_interval_s: float = 1.0,
) -> SimResult:
    """Build + run ``job`` in headless Factorio and return the measured result.

    ``scenarios_dir`` is Factorio's user scenarios directory (the scenario is
    copied there); ``script_output_dir`` is Factorio's ``script-output`` directory
    (where the result JSON appears). ``extra_args`` is appended to the launch
    command -- typically ``--server-settings`` for ``--start-server-load-scenario``
    on your install.

    Raises :class:`FactorioNotFound` if the binary is missing, or ``TimeoutError``
    if no result appears within ``timeout_s``.

    Note: the exact launch flags and the scenario's in-game wiring should be
    verified against your Factorio version the first time you run this.
    """
    factorio = Path(factorio_path)
    if not factorio.exists():
        raise FactorioNotFound(f"Factorio binary not found at {factorio}")

    _prepare_scenario(job, Path(scenarios_dir), scenario_name)
    result_path = Path(script_output_dir) / RESULT_FILENAME
    if result_path.exists():
        result_path.unlink()

    cmd = [
        str(factorio),
        "--start-server-load-scenario",
        scenario_name,
        *extra_args,
    ]
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        deadline = time.monotonic() + timeout_s
        while time.monotonic() < deadline:
            if result_path.exists():
                # Give the write a beat to flush, then parse.
                time.sleep(poll_interval_s)
                return SimResult.from_json(result_path.read_text(encoding="utf-8"))
            if proc.poll() is not None and not result_path.exists():
                raise RuntimeError(
                    f"Factorio exited (code {proc.returncode}) before writing a result"
                )
            time.sleep(poll_interval_s)
        raise TimeoutError(f"no simulation result after {timeout_s:g}s")
    finally:
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()
