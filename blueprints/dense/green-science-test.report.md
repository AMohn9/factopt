# Benders candidate: 1/s logistic-science-pack

**Feasible:** True
**Budget:** 500s total, 20s per master solve, 20 iterations max
**Used:** 505s over 16 iteration(s)
**Bounding box:** 20 x 34 = 680 tiles
**Routing:** 184 belt tiles, 6 undergrounds, 4 splitters, 47 turns, converged in 7 round(s)
**Static validation:** ok

## Rate plan

```
Plan: 1/s logistic-science-pack using assembling-machine-2
  machines: 13 total
      1 x copper-cable           (1.00 exact, 1.500 crafts/s)
      1 x electronic-circuit     (0.67 exact, 1.000 crafts/s)
      1 x inserter               (0.67 exact, 1.000 crafts/s)
      1 x iron-gear-wheel        (1.00 exact, 1.500 crafts/s)
      8 x logistic-science-pack  (8.00 exact, 1.000 crafts/s)
      1 x transport-belt         (0.33 exact, 0.500 crafts/s)
  raw inputs:
       1.500/s copper-plate
       5.500/s iron-plate
```

## Placement

| macro | position | size |
|---|---|---|
| dense-copper-cable | (1, 24) | 8 x 7 |
| in-copper-plate | (0, 20) | 2 x 1 |
| in-iron-plate | (0, 16) | 2 x 1 |
| inserter | (0, 8) | 9 x 3 |
| iron-gear-wheel | (5, 14) | 3 x 7 |
| logistic-science-pack | (12, 8) | 8 x 24 |
| out | (18, 4) | 2 x 1 |
| transport-belt | (5, 2) | 8 x 3 |

## Coarse routing

11 x 11 cells of 4 tiles; max boundary utilization 0.75

## Iterations

```
budget: 500s total, 20s/master solve, 20 iteration(s) max; used 505s over 16 iteration(s)
iter 0: margin=1 slack=0 bbox=28x17 failed (port_conflict, port_conflict, no_path); +3 cuts [master 11s, route 0.0s]
iter 1: margin=1 slack=0.15 bbox=19x28 failed (port_conflict, port_conflict, no_path); +3 cuts [master 25s, route 0.0s]
iter 2: margin=2 slack=0.15 bbox=21x29 failed (no_path); +1 cuts [master 27s, route 0.0s]
iter 3: margin=2 slack=0.3 bbox=21x33 failed (no_path); +1 cuts [master 30s, route 0.3s]
iter 4: margin=3 slack=0.3 bbox=30x26 routed; +0 cuts [master 32s, route 0.0s]
iter 5: margin=3 slack=0.3 bbox=20x38 failed (no_path); +1 cuts [master 35s, route 0.0s]
iter 6: margin=3 slack=0.3 bbox=28x27 routed; +0 cuts [master 35s, route 0.3s]
iter 7: margin=3 slack=0.3 bbox=25x30 failed (no_path); +1 cuts [master 35s, route 0.2s]
iter 8: margin=3 slack=0.3 bbox=28x26 failed (congestion); +1 cuts [master 34s, route 0.2s]
iter 9: margin=3 slack=0.3 bbox=25x30 failed (congestion); +1 cuts [master 34s, route 0.3s]
iter 10: margin=3 slack=0.3 bbox=25x30 routed; +0 cuts [master 34s, route 0.3s]
iter 11: margin=3 slack=0.3 bbox=28x26 routed; +0 cuts [master 35s, route 0.0s]
iter 12: margin=3 slack=0.3 bbox=24x30 routed; +0 cuts [master 34s, route 0.0s]
iter 13: margin=3 slack=0.3 bbox=37x19 failed (congestion); +1 cuts [master 34s, route 0.2s]
iter 14: margin=3 slack=0.3 bbox=28x25 routed; +0 cuts [master 34s, route 0.1s]
iter 15: margin=3 slack=0.3 bbox=20x34 routed; +0 cuts [master 33s, route 0.1s]
  cut[pin_access] ports ('transport-belt', 'iron-gear-wheel-in') and ('dense-copper-cable', 'iron-plate-in') share access tile (6, 16); they must not coincide
  cut[pin_access] ports ('in-copper-plate', 'copper-plate-out-0') and ('transport-belt', 'transport-belt-out-0') share access tile (2, 9); they must not coincide
  cut[corridor] net iron-gear-wheel:iron-gear-wheel-t0 has no belt path from (14, 9) to (6, 16); blocked by ['dense-copper-cable', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[pin_access] ports ('in-copper-plate', 'copper-plate-out-0') and ('dense-copper-cable', 'copper-plate-in') share access tile (2, 24); they must not coincide
  cut[pin_access] ports ('in-iron-plate', 'iron-plate-out-0') and ('dense-copper-cable', 'iron-plate-in') share access tile (2, 17); they must not coincide
  cut[corridor] net electronic-circuit:dense-copper-cable-t0 has no belt path from (2, 18) to (8, 16); blocked by ['dense-copper-cable', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-plate:in-iron-plate-t0 has no belt path from (2, 9) to (3, 9); blocked by ['dense-copper-cable', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net electronic-circuit:dense-copper-cable-t0 has no belt path from (3, 22) to (3, 1); blocked by ['dense-copper-cable', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-plate:in-iron-plate-t0 has no belt path from (2, 37) to (1, 28); blocked by ['dense-copper-cable', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-gear-wheel:iron-gear-wheel-t0 has no belt path from (7, 1) to (10, 2); blocked by ['dense-copper-cable', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-plate:in-iron-plate-t0 could not converge; contested corridor near [(11, 16), (13, 20)]... involves ['in-iron-plate', 'iron-gear-wheel']
  cut[corridor] net electronic-circuit:dense-copper-cable-t0 could not converge; contested corridor near [(4, 23)]... involves ['dense-copper-cable', 'inserter']
  cut[corridor] net electronic-circuit:dense-copper-cable-t0 could not converge; contested corridor near [(3, 7), (4, 7), (5, 7)]... involves ['dense-copper-cable', 'inserter']
```
