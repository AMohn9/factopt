# Benders candidate: 1/s logistic-science-pack

**Feasible:** True
**Budget:** 600s total, 60s per master solve, 15 iterations max
**Used:** 537s over 9 iteration(s)
**Bounding box:** 46 x 25 = 1150 tiles
**Routing:** 246 belt tiles, 6 undergrounds, 4 splitters, 37 turns, converged in 7 round(s)
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
| dense-copper-cable | (12, 3) | 7 x 8 |
| in-copper-plate | (0, 3) | 2 x 1 |
| in-iron-plate | (0, 16) | 2 x 1 |
| inserter | (6, 16) | 3 x 9 |
| iron-gear-wheel | (1, 9) | 7 x 3 |
| logistic-science-pack | (20, 16) | 24 x 8 |
| out | (44, 11) | 2 x 1 |
| transport-belt | (13, 15) | 3 x 8 |

## Coarse routing

12 x 12 cells of 4 tiles; max boundary utilization 0.75

## Iterations

```
budget: 600s total, 60s/master solve, 15 iteration(s) max; used 537s over 9 iteration(s)
iter 0: margin=1 slack=0 bbox=28x17 failed (no_path, no_path, no_path, no_path); +4 cuts [master 9s, route 0.1s]
iter 1: margin=1 slack=0.15 bbox=19x28 failed (port_conflict, port_conflict, no_path); +3 cuts [master 22s, route 0.2s]
iter 2: margin=2 slack=0.15 bbox=21x29 failed (no_path); +1 cuts [master 69s, route 0.1s]
iter 3: margin=2 slack=0.3 bbox=24x29 failed (no_path); +1 cuts [master 69s, route 0.1s]
iter 4: margin=3 slack=0.3 bbox=24x31 failed (no_path); +1 cuts [master 72s, route 0.0s]
iter 5: margin=3 slack=0.5 bbox=25x35 failed (no_path); +1 cuts [master 71s, route 0.1s]
iter 6: margin=4 slack=0.5 bbox=31x33 failed (congestion); +1 cuts [master 77s, route 0.3s]
iter 7: margin=4 slack=0.7 bbox=46x25 failed (congestion); +1 cuts [master 74s, route 0.6s]
iter 8: margin=4 slack=0.7 bbox=46x25 routed; +0 cuts [master 73s, route 0.3s]
  cut[corridor] net electronic-circuit:dense-copper-cable-t0 has no belt path from (25, 15) to (7, 11); blocked by ['dense-copper-cable', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net inserter:inserter-t0 has no belt path from (1, 15) to (1, 1); blocked by ['dense-copper-cable', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-plate:in-iron-plate-t0 has no belt path from (2, 16) to (13, 15); blocked by ['dense-copper-cable', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-gear-wheel:iron-gear-wheel-t0 has no belt path from (13, 9) to (13, 16); blocked by ['dense-copper-cable', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[pin_access] ports ('in-copper-plate', 'copper-plate-out-0') and ('dense-copper-cable', 'copper-plate-in') share access tile (2, 3); they must not coincide
  cut[pin_access] ports ('in-iron-plate', 'iron-plate-out-0') and ('dense-copper-cable', 'iron-plate-in') share access tile (2, 10); they must not coincide
  cut[corridor] net iron-gear-wheel:iron-gear-wheel-t0 has no belt path from (7, 11) to (2, 19); blocked by ['dense-copper-cable', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-plate:in-iron-plate-t0 has no belt path from (2, 9) to (2, 16); blocked by ['dense-copper-cable', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-plate:in-iron-plate-t0 has no belt path from (2, 18) to (9, 14); blocked by ['dense-copper-cable', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-plate:in-iron-plate-t0 has no belt path from (2, 13) to (1, 23); blocked by ['dense-copper-cable', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-plate:in-iron-plate-t0 has no belt path from (2, 21) to (1, 27); blocked by ['dense-copper-cable', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net electronic-circuit:dense-copper-cable-t0 could not converge; contested corridor near [(12, 22)]... involves ['dense-copper-cable', 'inserter', 'transport-belt']
  cut[corridor] net iron-gear-wheel:iron-gear-wheel-t0 could not converge; contested corridor near [(11, 0)]... involves ['inserter', 'iron-gear-wheel']
```
