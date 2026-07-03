# Benders candidate: 1/s logistic-science-pack

**Feasible:** True
**Budget:** 1000s total, 30s per master solve, 40 iterations max
**Used:** 1016s over 26 iteration(s)
**Bounding box:** 18 x 37 = 666 tiles
**Routing:** 100 belt tiles, 2 undergrounds, 4 splitters, 26 turns, converged in 2 round(s)
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
| dense-copper-cable | (5, 0) | 7 x 8 |
| in-copper-plate | (0, 0) | 2 x 1 |
| in-iron-plate | (0, 7) | 2 x 1 |
| inserter | (4, 11) | 3 x 9 |
| iron-gear-wheel | (0, 23) | 7 x 3 |
| logistic-science-pack | (10, 11) | 8 x 24 |
| out | (16, 7) | 2 x 1 |
| transport-belt | (4, 29) | 3 x 8 |

## Coarse routing

11 x 11 cells of 4 tiles; max boundary utilization 0.50

## Iterations

```
budget: 1000s total, 30s/master solve, 40 iteration(s) max; used 1016s over 26 iteration(s)
iter 0: margin=1 slack=0 bbox=28x17 failed (port_conflict, port_conflict, no_path); +3 cuts [master 10s, route 0.0s]
iter 1: margin=1 slack=0.15 bbox=19x28 failed (port_conflict, port_conflict, port_conflict); +3 cuts [master 33s, route 0.0s]
iter 2: margin=2 slack=0.15 bbox=21x29 failed (no_path); +1 cuts [master 38s, route 0.0s]
iter 3: margin=2 slack=0.3 bbox=23x29 failed (no_path, no_path); +2 cuts [master 39s, route 0.0s]
iter 4: margin=3 slack=0.3 bbox=28x27 routed; +0 cuts [master 44s, route 0.0s]
iter 5: margin=3 slack=0.3 bbox=25x30 routed; +0 cuts [master 40s, route 0.4s]
iter 6: margin=3 slack=0.3 bbox=28x26 routed; +0 cuts [master 42s, route 0.0s]
iter 7: margin=3 slack=0.3 bbox=24x30 routed; +0 cuts [master 40s, route 0.2s]
iter 8: margin=3 slack=0.3 bbox=23x31 routed; +0 cuts [master 41s, route 0.1s]
iter 9: margin=3 slack=0.3 bbox=28x25 routed; +0 cuts [master 41s, route 0.1s]
iter 10: margin=3 slack=0.3 bbox=23x30 failed (congestion); +1 cuts [master 40s, route 0.3s]
iter 11: margin=3 slack=0.3 bbox=23x30 routed; +0 cuts [master 40s, route 0.0s]
iter 12: margin=3 slack=0.3 bbox=18x38 routed; +0 cuts [master 40s, route 0.0s]
iter 13: margin=3 slack=0.3 bbox=22x31 failed (no_path); +1 cuts [master 40s, route 0.4s]
iter 14: margin=3 slack=0.3 bbox=19x35 failed (congestion); +1 cuts [master 41s, route 0.1s]
iter 15: margin=3 slack=0.3 bbox=22x31 routed; +0 cuts [master 40s, route 0.2s]
iter 16: margin=3 slack=0.3 bbox=28x24 failed (congestion, congestion); +2 cuts [master 40s, route 0.3s]
iter 17: margin=3 slack=0.3 bbox=18x37 routed; +0 cuts [master 41s, route 0.0s]
iter 18: margin=3 slack=0.3 bbox=19x35 failed (no_path); +1 cuts [master 40s, route 0.1s]
iter 19: margin=3 slack=0.3 bbox=19x35 failed (no_path, congestion); +2 cuts [master 40s, route 0.5s]
iter 20: margin=3 slack=0.3 bbox=22x30 failed (congestion); +1 cuts [master 40s, route 0.1s]
iter 21: margin=3 slack=0.3 bbox=33x20 failed (no_path); +1 cuts [master 41s, route 0.1s]
iter 22: margin=3 slack=0.3 bbox=41x16 failed (congestion); +1 cuts [master 40s, route 0.1s]
iter 23: margin=3 slack=0.3 bbox=20x33 failed (congestion); +1 cuts [master 41s, route 0.2s]
iter 24: margin=3 slack=0.3 bbox=22x30 failed (no_path); +1 cuts [master 40s, route 0.6s]
iter 25: margin=3 slack=0.3 bbox=22x30 failed (congestion); +1 cuts [master 40s, route 0.3s]
  cut[pin_access] ports ('transport-belt', 'iron-gear-wheel-in') and ('dense-copper-cable', 'iron-plate-in') share access tile (6, 16); they must not coincide
  cut[pin_access] ports ('in-copper-plate', 'copper-plate-out-0') and ('transport-belt', 'transport-belt-out-0') share access tile (2, 9); they must not coincide
  cut[corridor] net iron-gear-wheel:iron-gear-wheel-t0 has no belt path from (14, 9) to (6, 16); blocked by ['dense-copper-cable', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[pin_access] ports ('in-copper-plate', 'copper-plate-out-0') and ('dense-copper-cable', 'copper-plate-in') share access tile (2, 3); they must not coincide
  cut[pin_access] ports ('iron-gear-wheel', 'iron-gear-wheel-out-0') and ('inserter', 'iron-gear-wheel-in') share access tile (9, 15); they must not coincide
  cut[pin_access] ports ('iron-gear-wheel', 'iron-plate-in') and ('transport-belt', 'iron-plate-in') share access tile (3, 19); they must not coincide
  cut[corridor] net iron-plate:in-iron-plate-t0 has no belt path from (2, 18) to (3, 18); blocked by ['dense-copper-cable', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-plate:in-iron-plate-t0 has no belt path from (2, 18) to (3, 18); blocked by ['dense-copper-cable', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-gear-wheel:iron-gear-wheel-t0 has no belt path from (0, 11) to (1, 12); blocked by ['dense-copper-cable', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net inserter:inserter-t0 could not converge; contested corridor near [(16, 28)]... involves ['inserter', 'logistic-science-pack']
  cut[corridor] net transport-belt:transport-belt-t0 has no belt path from (1, 3) to (14, 4); blocked by ['dense-copper-cable', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-plate:in-iron-plate-t0 could not converge; contested corridor near [(1, 15), (8, 16)]... involves ['in-iron-plate', 'iron-gear-wheel']
  cut[corridor] net iron-gear-wheel:iron-gear-wheel-t0 could not converge; contested corridor near [(10, 8), (10, 9), (10, 10)]... involves ['inserter', 'iron-gear-wheel']
  cut[corridor] net inserter:inserter-t0 could not converge; contested corridor near [(1, 17)]... involves ['inserter', 'logistic-science-pack']
  cut[corridor] net inserter:inserter-t0 has no belt path from (6, 6) to (12, 8); blocked by ['dense-copper-cable', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net inserter:inserter-t0 has no belt path from (6, 5) to (12, 8); blocked by ['dense-copper-cable', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net transport-belt:transport-belt-t0 could not converge; contested corridor near [(0, 11)]... involves ['logistic-science-pack', 'transport-belt']
  cut[corridor] net transport-belt:transport-belt-t0 could not converge; contested corridor near [(1, 0), (2, 0), (3, 0), (4, 0)]... involves ['inserter', 'logistic-science-pack', 'transport-belt']
  cut[corridor] net iron-plate:in-iron-plate-t0 has no belt path from (2, 18) to (8, 18); blocked by ['dense-copper-cable', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-plate:in-iron-plate-t0 could not converge; contested corridor near [(7, 14)]... involves ['in-iron-plate', 'iron-gear-wheel']
  cut[corridor] net iron-plate:in-iron-plate-t0 could not converge; contested corridor near [(7, 8), (7, 13), (8, 8), (9, 8)]... involves ['in-iron-plate', 'iron-gear-wheel', 'transport-belt']
  cut[corridor] net electronic-circuit:dense-copper-cable-t0 has no belt path from (7, 20) to (5, 2); blocked by ['dense-copper-cable', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net electronic-circuit:dense-copper-cable-t0 could not converge; contested corridor near [(1, 5)]... involves ['dense-copper-cable', 'inserter']
```
