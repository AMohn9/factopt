# Benders candidate: 1/s logistic-science-pack

**Feasible:** True
**Budget:** 600s total, 60s per master solve, 15 iterations max
**Used:** 671s over 11 iteration(s)
**Bounding box:** 25 x 31 = 775 tiles
**Routing:** 238 belt tiles, 7 undergrounds, 4 splitters, 42 turns, converged in 24 round(s)
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
| dense-copper-cable | (5, 23) | 7 x 8 |
| in-copper-plate | (0, 30) | 2 x 1 |
| in-iron-plate | (0, 23) | 2 x 1 |
| inserter | (3, 17) | 9 x 3 |
| iron-gear-wheel | (3, 7) | 3 x 7 |
| logistic-science-pack | (16, 4) | 8 x 24 |
| out | (23, 0) | 2 x 1 |
| transport-belt | (9, 6) | 3 x 8 |

## Coarse routing

11 x 11 cells of 4 tiles; max boundary utilization 0.75

## Iterations

```
budget: 600s total, 60s/master solve, 15 iteration(s) max; used 671s over 11 iteration(s)
iter 0: margin=1 slack=0 bbox=28x17 failed (no_path, no_path, no_path, no_path); +4 cuts [master 10s, route 0.1s]
iter 1: margin=1 slack=0.15 bbox=19x28 failed (port_conflict, port_conflict, no_path, no_path, congestion); +5 cuts [master 18s, route 0.2s]
iter 2: margin=2 slack=0.15 bbox=21x29 failed (no_path); +1 cuts [master 68s, route 0.0s]
iter 3: margin=2 slack=0.3 bbox=24x29 failed (no_path, congestion); +2 cuts [master 69s, route 0.1s]
iter 4: margin=3 slack=0.3 bbox=25x31 routed; +0 cuts [master 72s, route 0.6s]
iter 5: margin=3 slack=0.3 bbox=28x26 failed (congestion); +1 cuts [master 71s, route 0.2s]
iter 6: margin=3 slack=0.3 bbox=28x27 failed (congestion); +1 cuts [master 73s, route 0.3s]
iter 7: margin=3 slack=0.3 bbox=24x31 failed (congestion); +1 cuts [master 74s, route 0.3s]
iter 8: margin=3 slack=0.3 bbox=28x27 failed (no_path, congestion, congestion); +3 cuts [master 71s, route 1.0s]
iter 9: margin=3 slack=0.3 bbox=29x26 failed (congestion); +1 cuts [master 71s, route 0.2s]
iter 10: margin=3 slack=0.3 bbox=40x19 failed (no_path, congestion); +2 cuts [master 72s, route 0.2s]
  cut[corridor] net electronic-circuit:dense-copper-cable-t0 has no belt path from (25, 15) to (7, 11); blocked by ['dense-copper-cable', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net inserter:inserter-t0 has no belt path from (1, 15) to (1, 1); blocked by ['dense-copper-cable', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-plate:in-iron-plate-t0 has no belt path from (2, 16) to (17, 15); blocked by ['dense-copper-cable', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-gear-wheel:iron-gear-wheel-t0 has no belt path from (13, 9) to (13, 16); blocked by ['dense-copper-cable', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[pin_access] ports ('in-copper-plate', 'copper-plate-out-0') and ('dense-copper-cable', 'copper-plate-in') share access tile (2, 3); they must not coincide
  cut[pin_access] ports ('in-iron-plate', 'iron-plate-out-0') and ('dense-copper-cable', 'iron-plate-in') share access tile (2, 10); they must not coincide
  cut[corridor] net transport-belt:transport-belt-t0 has no belt path from (9, 15) to (11, 26); blocked by ['dense-copper-cable', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net electronic-circuit:dense-copper-cable-t0 has no belt path from (10, 9) to (8, 19); blocked by ['dense-copper-cable', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-gear-wheel:iron-gear-wheel-t0 could not converge; contested corridor near [(1, 17), (1, 18), (1, 23), (1, 24)]... involves ['inserter', 'iron-gear-wheel', 'transport-belt']
  cut[corridor] net iron-plate:in-iron-plate-t0 has no belt path from (2, 13) to (2, 15); blocked by ['dense-copper-cable', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-plate:in-iron-plate-t0 has no belt path from (2, 21) to (8, 22); blocked by ['dense-copper-cable', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net inserter:inserter-t0 could not converge; contested corridor near [(16, 27)]... involves ['inserter', 'logistic-science-pack']
  cut[corridor] net inserter:inserter-t0 could not converge; contested corridor near [(1, 19)]... involves ['inserter', 'logistic-science-pack']
  cut[corridor] net inserter:inserter-t0 could not converge; contested corridor near [(1, 20)]... involves ['inserter', 'logistic-science-pack']
  cut[corridor] net inserter:inserter-t0 could not converge; contested corridor near [(7, 29), (16, 29)]... involves ['inserter', 'logistic-science-pack', 'transport-belt']
  cut[corridor] net iron-gear-wheel:iron-gear-wheel-t0 has no belt path from (17, 11) to (4, 1); blocked by ['dense-copper-cable', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-plate:in-iron-plate-t0 could not converge; contested corridor near [(2, 10)]... involves ['in-iron-plate', 'iron-gear-wheel']
  cut[corridor] net inserter:inserter-t0 could not converge; contested corridor near [(1, 20)]... involves ['inserter', 'logistic-science-pack']
  cut[corridor] net inserter:inserter-t0 could not converge; contested corridor near [(2, 19)]... involves ['inserter', 'logistic-science-pack']
  cut[corridor] net transport-belt:transport-belt-t0 has no belt path from (12, 3) to (13, 11); blocked by ['dense-copper-cable', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-gear-wheel:iron-gear-wheel-t0 could not converge; contested corridor near [(12, 18)]... involves ['inserter', 'iron-gear-wheel']
```
