# Benders candidate: 1/s chemical-science-pack

**Feasible:** True
**Budget:** 600s total, 20s per master solve, 40 iterations max
**Used:** 604s over 18 iteration(s)
**Bounding box:** 56 x 25 = 1400 tiles
**Routing:** 72 belt tiles, 4 undergrounds, 1 splitters, 20 turns, converged in 2 round(s)
**Static validation:** ok

## Rate plan

```
Plan: 1/s chemical-science-pack using assembling-machine-2
  machines: 33 total
     16 x chemical-science-pack  (16.00 exact, 0.500 crafts/s)
     14 x engine-unit            (13.33 exact, 1.000 crafts/s)
      1 x iron-gear-wheel        (0.67 exact, 1.000 crafts/s)
      2 x pipe                   (1.33 exact, 2.000 crafts/s)
  raw inputs:
       1.500/s advanced-circuit
       4.000/s iron-plate
       1.000/s steel-plate
       0.500/s sulfur
```

## Placement

| macro | position | size |
|---|---|---|
| chemical-science-pack | (4, 1) | 48 x 9 |
| engine-unit | (12, 13) | 42 x 9 |
| in-advanced-circuit | (0, 2) | 2 x 1 |
| in-iron-plate | (0, 17) | 2 x 1 |
| in-steel-plate | (0, 21) | 2 x 1 |
| in-sulfur | (0, 9) | 2 x 1 |
| iron-gear-wheel | (3, 12) | 7 x 3 |
| out | (54, 8) | 2 x 1 |
| pipe | (4, 17) | 6 x 7 |

## Coarse routing

14 x 14 cells of 4 tiles; max boundary utilization 0.50

## Iterations

```
budget: 600s total, 20s/master solve, 40 iteration(s) max; used 604s over 18 iteration(s)
iter 0: margin=1 slack=0 bbox=22x52 failed (port_conflict, no_path); +2 cuts [master 19s, route 0.0s]
iter 1: margin=1 slack=0.15 bbox=52x25 failed (no_path); +1 cuts [master 33s, route 0.0s]
iter 2: margin=2 slack=0.15 bbox=56x26 failed (no_path, congestion); +2 cuts [master 39s, route 0.6s]
iter 3: margin=2 slack=0.3 bbox=56x29 routed; +0 cuts [master 37s, route 0.0s]
iter 4: margin=2 slack=0.3 bbox=54x30 failed (congestion); +1 cuts [master 34s, route 0.2s]
iter 5: margin=2 slack=0.3 bbox=56x27 routed; +0 cuts [master 35s, route 0.0s]
iter 6: margin=2 slack=0.3 bbox=26x56 failed (no_path); +1 cuts [master 35s, route 0.5s]
iter 7: margin=2 slack=0.3 bbox=56x26 routed; +0 cuts [master 35s, route 0.0s]
iter 8: margin=2 slack=0.3 bbox=56x25 failed (no_path); +1 cuts [master 33s, route 0.4s]
iter 9: margin=2 slack=0.3 bbox=55x26 routed; +0 cuts [master 33s, route 0.0s]
iter 10: margin=2 slack=0.3 bbox=54x26 routed; +0 cuts [master 34s, route 0.0s]
iter 11: margin=2 slack=0.3 bbox=26x53 failed (no_path, congestion, congestion); +3 cuts [master 33s, route 0.6s]
iter 12: margin=2 slack=0.3 bbox=56x25 failed (no_path); +1 cuts [master 32s, route 0.1s]
iter 13: margin=2 slack=0.3 bbox=56x25 routed; +0 cuts [master 33s, route 0.0s]
iter 14: margin=2 slack=0.3 bbox=56x23 failed (no_path); +1 cuts [master 35s, route 0.3s]
iter 15: margin=2 slack=0.3 bbox=56x24 failed (no_path); +1 cuts [master 37s, route 0.1s]
iter 16: margin=2 slack=0.3 bbox=56x24 failed (no_path); +1 cuts [master 31s, route 0.4s]
iter 17: margin=2 slack=0.3 bbox=56x24 failed (no_path); +1 cuts [master 32s, route 0.0s]
  cut[pin_access] ports ('iron-gear-wheel', 'iron-plate-in') and ('pipe', 'iron-plate-in') share access tile (8, 45); they must not coincide
  cut[corridor] net sulfur:in-sulfur-t0 has no belt path from (2, 0) to (21, 1); blocked by ['chemical-science-pack', 'engine-unit', 'in-advanced-circuit', 'in-iron-plate', 'in-steel-plate', 'in-sulfur', 'iron-gear-wheel', 'out', 'pipe']
  cut[corridor] net iron-plate:in-iron-plate-t0 has no belt path from (2, 9) to (3, 9); blocked by ['chemical-science-pack', 'engine-unit', 'in-advanced-circuit', 'in-iron-plate', 'in-steel-plate', 'in-sulfur', 'iron-gear-wheel', 'out', 'pipe']
  cut[corridor] net iron-plate:in-iron-plate-t0 has no belt path from (2, 6) to (3, 6); blocked by ['chemical-science-pack', 'engine-unit', 'in-advanced-circuit', 'in-iron-plate', 'in-steel-plate', 'in-sulfur', 'iron-gear-wheel', 'out', 'pipe']
  cut[corridor] net engine-unit:engine-unit-t0 could not converge; contested corridor near [(54, 14)]... involves ['chemical-science-pack', 'engine-unit']
  cut[corridor] net iron-plate:in-iron-plate-t0 could not converge; contested corridor near [(4, 8)]... involves ['in-iron-plate', 'iron-gear-wheel', 'pipe']
  cut[corridor] net engine-unit:engine-unit-t0 has no belt path from (12, 11) to (25, 50); blocked by ['chemical-science-pack', 'engine-unit', 'in-advanced-circuit', 'in-iron-plate', 'in-steel-plate', 'in-sulfur', 'iron-gear-wheel', 'out', 'pipe']
  cut[corridor] net iron-plate:in-iron-plate-t0 has no belt path from (2, 6) to (3, 6); blocked by ['chemical-science-pack', 'engine-unit', 'in-advanced-circuit', 'in-iron-plate', 'in-steel-plate', 'in-sulfur', 'iron-gear-wheel', 'out', 'pipe']
  cut[corridor] net sulfur:in-sulfur-t0 has no belt path from (2, 3) to (25, 2); blocked by ['chemical-science-pack', 'engine-unit', 'in-advanced-circuit', 'in-iron-plate', 'in-steel-plate', 'in-sulfur', 'iron-gear-wheel', 'out', 'pipe']
  cut[corridor] net pipe:pipe-t0 could not converge; contested corridor near [(12, 8)]... involves ['engine-unit', 'pipe']
  cut[corridor] net iron-gear-wheel:iron-gear-wheel-t0 could not converge; contested corridor near [(7, 6)]... involves ['engine-unit', 'iron-gear-wheel']
  cut[corridor] net iron-plate:in-iron-plate-t0 has no belt path from (2, 6) to (3, 6); blocked by ['chemical-science-pack', 'engine-unit', 'in-advanced-circuit', 'in-iron-plate', 'in-steel-plate', 'in-sulfur', 'iron-gear-wheel', 'out', 'pipe']
  cut[corridor] net iron-plate:in-iron-plate-t0 has no belt path from (2, 6) to (3, 6); blocked by ['chemical-science-pack', 'engine-unit', 'in-advanced-circuit', 'in-iron-plate', 'in-steel-plate', 'in-sulfur', 'iron-gear-wheel', 'out', 'pipe']
  cut[corridor] net iron-plate:in-iron-plate-t0 has no belt path from (2, 6) to (3, 6); blocked by ['chemical-science-pack', 'engine-unit', 'in-advanced-circuit', 'in-iron-plate', 'in-steel-plate', 'in-sulfur', 'iron-gear-wheel', 'out', 'pipe']
  cut[corridor] net iron-plate:in-iron-plate-t0 has no belt path from (2, 6) to (3, 6); blocked by ['chemical-science-pack', 'engine-unit', 'in-advanced-circuit', 'in-iron-plate', 'in-steel-plate', 'in-sulfur', 'iron-gear-wheel', 'out', 'pipe']
  cut[corridor] net iron-plate:in-iron-plate-t0 has no belt path from (2, 6) to (3, 6); blocked by ['chemical-science-pack', 'engine-unit', 'in-advanced-circuit', 'in-iron-plate', 'in-steel-plate', 'in-sulfur', 'iron-gear-wheel', 'out', 'pipe']
```
