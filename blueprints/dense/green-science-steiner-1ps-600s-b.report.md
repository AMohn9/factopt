# Benders candidate: 1/s logistic-science-pack

**Feasible:** True
**Budget:** 600s total, 20s per master solve, 40 iterations max
**Used:** 609s over 20 iteration(s)
**Bounding box:** 28 x 24 = 672 tiles
**Routing:** 143 belt tiles, 11 undergrounds, 4 splitters, 35 turns, converged in 9 round(s)
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
| dense-copper-cable | (18, 1) | 7 x 8 |
| in-copper-plate | (0, 0) | 2 x 1 |
| in-iron-plate | (0, 10) | 2 x 1 |
| inserter | (6, 10) | 9 x 3 |
| iron-gear-wheel | (12, 0) | 3 x 7 |
| logistic-science-pack | (2, 16) | 24 x 8 |
| out | (26, 12) | 2 x 1 |
| transport-belt | (1, 4) | 8 x 3 |

## Coarse routing

11 x 11 cells of 4 tiles; max boundary utilization 0.50

## Iterations

```
budget: 600s total, 20s/master solve, 40 iteration(s) max; used 609s over 20 iteration(s)
iter 0: margin=1 slack=0 bbox=28x17 failed (no_path, no_path, no_path, no_path); +4 cuts [master 11s, route 0.1s]
iter 1: margin=1 slack=0.15 bbox=19x28 failed (port_conflict, port_conflict, no_path, no_path, congestion); +5 cuts [master 24s, route 0.2s]
iter 2: margin=2 slack=0.15 bbox=17x36 failed (no_path, congestion); +2 cuts [master 31s, route 0.4s]
iter 3: margin=2 slack=0.3 bbox=23x30 failed (congestion); +1 cuts [master 29s, route 0.2s]
iter 4: margin=3 slack=0.3 bbox=26x30 routed; +0 cuts [master 31s, route 0.4s]
iter 5: margin=3 slack=0.3 bbox=23x33 routed; +0 cuts [master 32s, route 0.5s]
iter 6: margin=3 slack=0.3 bbox=28x27 routed; +0 cuts [master 32s, route 0.4s]
iter 7: margin=3 slack=0.3 bbox=28x26 failed (congestion); +1 cuts [master 34s, route 0.2s]
iter 8: margin=3 slack=0.3 bbox=28x26 failed (congestion); +1 cuts [master 33s, route 0.4s]
iter 9: margin=3 slack=0.3 bbox=20x37 failed (no_path); +1 cuts [master 32s, route 0.6s]
iter 10: margin=3 slack=0.3 bbox=24x31 routed; +0 cuts [master 32s, route 0.0s]
iter 11: margin=3 slack=0.3 bbox=28x26 failed (congestion); +1 cuts [master 31s, route 0.2s]
iter 12: margin=3 slack=0.3 bbox=28x26 routed; +0 cuts [master 32s, route 0.1s]
iter 13: margin=3 slack=0.3 bbox=28x25 routed; +0 cuts [master 32s, route 0.1s]
iter 14: margin=3 slack=0.3 bbox=23x30 routed; +0 cuts [master 31s, route 0.0s]
iter 15: margin=3 slack=0.3 bbox=31x22 routed; +0 cuts [master 33s, route 0.4s]
iter 16: margin=3 slack=0.3 bbox=28x24 failed (congestion); +1 cuts [master 31s, route 0.3s]
iter 17: margin=3 slack=0.3 bbox=28x24 failed (congestion, congestion); +2 cuts [master 31s, route 0.3s]
iter 18: margin=3 slack=0.3 bbox=28x24 routed; +0 cuts [master 30s, route 0.1s]
iter 19: margin=3 slack=0.3 bbox=37x18 failed (no_path, no_path, no_path, congestion); +4 cuts [master 32s, route 0.6s]
  cut[corridor] net electronic-circuit:dense-copper-cable-t0 has no belt path from (25, 15) to (7, 11); blocked by ['dense-copper-cable', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net inserter:inserter-t0 has no belt path from (1, 15) to (1, 1); blocked by ['dense-copper-cable', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-plate:in-iron-plate-t0 has no belt path from (2, 16) to (17, 15); blocked by ['dense-copper-cable', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-gear-wheel:iron-gear-wheel-t0 has no belt path from (13, 9) to (13, 16); blocked by ['dense-copper-cable', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[pin_access] ports ('in-copper-plate', 'copper-plate-out-0') and ('dense-copper-cable', 'copper-plate-in') share access tile (2, 3); they must not coincide
  cut[pin_access] ports ('in-iron-plate', 'iron-plate-out-0') and ('dense-copper-cable', 'iron-plate-in') share access tile (2, 10); they must not coincide
  cut[corridor] net transport-belt:transport-belt-t0 has no belt path from (9, 15) to (11, 26); blocked by ['dense-copper-cable', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net electronic-circuit:dense-copper-cable-t0 has no belt path from (10, 9) to (8, 19); blocked by ['dense-copper-cable', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-gear-wheel:iron-gear-wheel-t0 could not converge; contested corridor near [(1, 17), (1, 18), (1, 23), (1, 24)]... involves ['inserter', 'iron-gear-wheel', 'transport-belt']
  cut[corridor] net inserter:inserter-t0 has no belt path from (7, 17) to (10, 34); blocked by ['dense-copper-cable', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-plate:in-iron-plate-t0 could not converge; contested corridor near [(3, 18), (7, 16)]... involves ['in-iron-plate', 'inserter', 'iron-gear-wheel']
  cut[corridor] net inserter:inserter-t0 could not converge; contested corridor near [(15, 27)]... involves ['inserter', 'logistic-science-pack']
  cut[corridor] net inserter:inserter-t0 could not converge; contested corridor near [(1, 19)]... involves ['inserter', 'logistic-science-pack']
  cut[corridor] net iron-gear-wheel:iron-gear-wheel-t0 could not converge; contested corridor near [(14, 0)]... involves ['inserter', 'iron-gear-wheel']
  cut[corridor] net electronic-circuit:dense-copper-cable-t0 has no belt path from (9, 19) to (18, 31); blocked by ['dense-copper-cable', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net inserter:inserter-t0 could not converge; contested corridor near [(1, 19)]... involves ['inserter', 'logistic-science-pack']
  cut[corridor] net inserter:inserter-t0 could not converge; contested corridor near [(1, 17)]... involves ['inserter', 'logistic-science-pack']
  cut[corridor] net inserter:inserter-t0 could not converge; contested corridor near [(1, 17)]... involves ['inserter', 'logistic-science-pack']
  cut[corridor] net electronic-circuit:dense-copper-cable-t0 could not converge; contested corridor near [(14, 4)]... involves ['dense-copper-cable', 'inserter']
  cut[corridor] net copper-plate:in-copper-plate-t0 has no belt path from (2, 0) to (7, 7); blocked by ['dense-copper-cable', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net inserter:inserter-t0 has no belt path from (23, 7) to (10, 11); blocked by ['dense-copper-cable', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net transport-belt:transport-belt-t0 has no belt path from (12, 1) to (10, 10); blocked by ['dense-copper-cable', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-gear-wheel:iron-gear-wheel-t0 could not converge; contested corridor near [(5, 6)]... involves ['inserter', 'iron-gear-wheel']
```
