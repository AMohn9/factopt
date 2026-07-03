# Benders candidate: 1/s logistic-science-pack

**Feasible:** True
**Budget:** 600s total, 20s per master solve, 40 iterations max
**Used:** 619s over 20 iteration(s)
**Bounding box:** 19 x 33 = 627 tiles
**Routing:** 119 belt tiles, 6 undergrounds, 2 splitters, 26 turns, converged in 24 round(s)
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
| dense-copper-cable | (0, 12) | 8 x 7 |
| in-copper-plate | (0, 4) | 2 x 1 |
| in-iron-plate | (0, 8) | 2 x 1 |
| inserter | (5, 0) | 3 x 9 |
| iron-gear-wheel | (1, 22) | 7 x 3 |
| logistic-science-pack | (11, 7) | 8 x 24 |
| out | (17, 3) | 2 x 1 |
| transport-belt | (0, 28) | 8 x 3 |

## Coarse routing

11 x 11 cells of 4 tiles; max boundary utilization 0.67

## Iterations

```
budget: 600s total, 20s/master solve, 40 iteration(s) max; used 619s over 20 iteration(s)
iter 0: margin=1 slack=0 bbox=28x17 failed (port_conflict, no_path, no_path, no_path); +4 cuts [master 12s, route 0.0s]
iter 1: margin=1 slack=0.15 bbox=19x28 failed (port_conflict, port_conflict); +2 cuts [master 24s, route 0.0s]
iter 2: margin=2 slack=0.15 bbox=21x29 failed (congestion); +1 cuts [master 28s, route 0.1s]
iter 3: margin=2 slack=0.3 bbox=28x25 routed; +0 cuts [master 28s, route 0.0s]
iter 4: margin=2 slack=0.15 bbox=21x29 failed (no_path); +1 cuts [master 31s, route 0.0s]
iter 5: margin=2 slack=0.3 bbox=22x31 failed (no_path); +1 cuts [master 31s, route 0.0s]
iter 6: margin=3 slack=0.3 bbox=41x17 failed (no_path); +1 cuts [master 34s, route 0.4s]
iter 7: margin=3 slack=0.5 bbox=23x30 routed; +0 cuts [master 34s, route 0.0s]
iter 8: margin=3 slack=0.3 bbox=19x35 routed; +0 cuts [master 34s, route 0.0s]
iter 9: margin=2 slack=0.3 bbox=18x36 routed; +0 cuts [master 32s, route 0.0s]
iter 10: margin=2 slack=0.15 bbox=31x20 failed (congestion, congestion); +2 cuts [master 32s, route 0.2s]
iter 11: margin=2 slack=0.3 bbox=19x34 routed; +0 cuts [master 32s, route 0.0s]
iter 12: margin=2 slack=0.15 bbox=21x29 failed (no_path); +1 cuts [master 32s, route 0.0s]
iter 13: margin=2 slack=0.3 bbox=22x29 failed (no_path); +1 cuts [master 32s, route 0.1s]
iter 14: margin=3 slack=0.3 bbox=20x32 failed (congestion); +1 cuts [master 35s, route 0.3s]
iter 15: margin=3 slack=0.5 bbox=32x20 routed; +0 cuts [master 34s, route 0.2s]
iter 16: margin=3 slack=0.3 bbox=19x33 routed; +0 cuts [master 34s, route 0.1s]
iter 17: margin=2 slack=0.3 bbox=19x32 failed (no_path); +1 cuts [master 31s, route 0.2s]
iter 18: margin=3 slack=0.3 bbox=20x31 failed (no_path, congestion); +2 cuts [master 33s, route 0.5s]
iter 19: margin=3 slack=0.5 bbox=20x31 failed (no_path, congestion); +2 cuts [master 34s, route 0.6s]
  cut[pin_access] ports ('in-copper-plate', 'copper-plate-out-0') and ('transport-belt', 'transport-belt-out-0') share access tile (2, 9); they must not coincide
  cut[corridor] net iron-plate:in-iron-plate-t0 has no belt path from (2, 14) to (2, 15); blocked by ['dense-copper-cable', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-gear-wheel:iron-gear-wheel-t0 has no belt path from (14, 9) to (6, 16); blocked by ['dense-copper-cable', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net electronic-circuit:dense-copper-cable-t0 has no belt path from (14, 15) to (26, 15); blocked by ['dense-copper-cable', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[pin_access] ports ('in-copper-plate', 'copper-plate-out-0') and ('dense-copper-cable', 'copper-plate-in') share access tile (2, 3); they must not coincide
  cut[pin_access] ports ('in-iron-plate', 'iron-plate-out-0') and ('dense-copper-cable', 'iron-plate-in') share access tile (2, 10); they must not coincide
  cut[corridor] net iron-plate:in-iron-plate-t0 could not converge; contested corridor near [(6, 21), (6, 22), (6, 23)]... involves ['in-iron-plate', 'iron-gear-wheel']
  cut[corridor] net iron-plate:in-iron-plate-t0 has no belt path from (2, 17) to (3, 17); blocked by ['dense-copper-cable', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-plate:in-iron-plate-t0 has no belt path from (2, 22) to (3, 22); blocked by ['dense-copper-cable', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net electronic-circuit:dense-copper-cable-t0 has no belt path from (12, 7) to (8, 11); blocked by ['dense-copper-cable', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-plate:in-iron-plate-t0 could not converge; contested corridor near [(11, 7)]... involves ['dense-copper-cable', 'in-iron-plate', 'iron-gear-wheel']
  cut[corridor] net iron-gear-wheel:iron-gear-wheel-t0 could not converge; contested corridor near [(21, 1)]... involves ['inserter', 'iron-gear-wheel']
  cut[corridor] net iron-plate:in-iron-plate-t0 has no belt path from (2, 18) to (3, 18); blocked by ['dense-copper-cable', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-plate:in-iron-plate-t0 has no belt path from (2, 18) to (3, 18); blocked by ['dense-copper-cable', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-plate:in-iron-plate-t0 could not converge; contested corridor near [(0, 1), (0, 5), (0, 6), (8, 6)]... involves ['in-iron-plate', 'iron-gear-wheel', 'transport-belt']
  cut[corridor] net electronic-circuit:dense-copper-cable-t0 has no belt path from (1, 22) to (7, 19); blocked by ['dense-copper-cable', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net electronic-circuit:dense-copper-cable-t0 has no belt path from (1, 24) to (7, 20); blocked by ['dense-copper-cable', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-plate:in-iron-plate-t0 could not converge; contested corridor near [(7, 14)]... involves ['in-iron-plate', 'iron-gear-wheel']
  cut[corridor] net copper-plate:in-copper-plate-t0 has no belt path from (2, 27) to (1, 0); blocked by ['dense-copper-cable', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-plate:in-iron-plate-t0 could not converge; contested corridor near [(0, 6), (0, 7), (0, 8), (1, 4)]... involves ['dense-copper-cable', 'in-iron-plate', 'iron-gear-wheel']
```
