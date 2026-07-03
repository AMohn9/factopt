# Benders candidate: 1/s logistic-science-pack

**Feasible:** True
**Budget:** 800s total, 20s per master solve, 40 iterations max
**Used:** 805s over 27 iteration(s)
**Bounding box:** 21 x 29 = 609 tiles
**Routing:** 120 belt tiles, 7 undergrounds, 2 splitters, 27 turns, converged in 4 round(s)
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
| dense-copper-cable | (4, 19) | 7 x 8 |
| in-copper-plate | (0, 26) | 2 x 1 |
| in-iron-plate | (0, 19) | 2 x 1 |
| inserter | (1, 4) | 9 x 3 |
| iron-gear-wheel | (3, 14) | 7 x 3 |
| logistic-science-pack | (13, 3) | 8 x 24 |
| out | (19, 0) | 2 x 1 |
| transport-belt | (3, 9) | 8 x 3 |

## Coarse routing

10 x 10 cells of 4 tiles; max boundary utilization 0.75

## Iterations

```
budget: 800s total, 20s/master solve, 40 iteration(s) max; used 805s over 27 iteration(s)
iter 0: margin=1 slack=0 bbox=28x17 failed (port_conflict, port_conflict, no_path); +3 cuts [master 13s, route 0.0s]
iter 1: margin=1 slack=0.15 bbox=19x28 failed (port_conflict, port_conflict, no_path); +3 cuts [master 24s, route 0.0s]
iter 2: margin=2 slack=0.15 bbox=21x29 failed (no_path, no_path); +2 cuts [master 27s, route 0.0s]
iter 3: margin=2 slack=0.3 bbox=22x31 routed; +0 cuts [master 27s, route 0.0s]
iter 4: margin=2 slack=0.3 bbox=23x29 routed; +0 cuts [master 31s, route 0.3s]
iter 5: margin=2 slack=0.3 bbox=22x29 failed (no_path); +1 cuts [master 31s, route 0.2s]
iter 6: margin=2 slack=0.3 bbox=30x22 failed (no_path); +1 cuts [master 32s, route 0.0s]
iter 7: margin=2 slack=0.3 bbox=19x35 failed (no_path, no_path); +2 cuts [master 31s, route 0.2s]
iter 8: margin=2 slack=0.3 bbox=19x35 failed (no_path, no_path); +2 cuts [master 31s, route 0.3s]
iter 9: margin=2 slack=0.3 bbox=21x31 failed (no_path, congestion); +2 cuts [master 32s, route 0.2s]
iter 10: margin=2 slack=0.3 bbox=20x33 routed; +0 cuts [master 32s, route 0.2s]
iter 11: margin=2 slack=0.3 bbox=28x23 failed (no_path); +1 cuts [master 29s, route 0.1s]
iter 12: margin=2 slack=0.3 bbox=21x31 failed (no_path, congestion); +2 cuts [master 29s, route 0.1s]
iter 13: margin=2 slack=0.3 bbox=21x31 failed (no_path); +1 cuts [master 30s, route 0.1s]
iter 14: margin=2 slack=0.3 bbox=22x29 failed (no_path); +1 cuts [master 30s, route 0.1s]
iter 15: margin=2 slack=0.3 bbox=21x31 failed (no_path, congestion, congestion); +3 cuts [master 31s, route 0.8s]
iter 16: margin=2 slack=0.3 bbox=18x36 failed (no_path, no_path, congestion); +3 cuts [master 29s, route 0.3s]
iter 17: margin=2 slack=0.3 bbox=21x31 routed; +0 cuts [master 33s, route 0.0s]
iter 18: margin=2 slack=0.3 bbox=28x23 failed (no_path, no_path, congestion); +3 cuts [master 31s, route 0.5s]
iter 19: margin=2 slack=0.3 bbox=22x29 routed; +0 cuts [master 31s, route 0.2s]
iter 20: margin=2 slack=0.3 bbox=21x29 routed; +0 cuts [master 31s, route 0.0s]
iter 21: margin=2 slack=0.3 bbox=20x30 failed (no_path); +1 cuts [master 31s, route 0.0s]
iter 22: margin=2 slack=0.3 bbox=19x32 failed (no_path); +1 cuts [master 30s, route 0.0s]
iter 23: margin=2 slack=0.3 bbox=19x32 failed (no_path); +1 cuts [master 31s, route 0.1s]
iter 24: margin=2 slack=0.3 bbox=18x33 failed (no_path, no_path); +2 cuts [master 31s, route 0.1s]
iter 25: margin=2 slack=0.3 bbox=19x32 failed (no_path); +1 cuts [master 31s, route 0.3s]
iter 26: margin=2 slack=0.3 bbox=19x32 failed (congestion, congestion); +2 cuts [master 32s, route 0.2s]
  cut[pin_access] ports ('transport-belt', 'iron-gear-wheel-in') and ('dense-copper-cable', 'iron-plate-in') share access tile (6, 16); they must not coincide
  cut[pin_access] ports ('in-copper-plate', 'copper-plate-out-0') and ('transport-belt', 'transport-belt-out-0') share access tile (2, 9); they must not coincide
  cut[corridor] net iron-gear-wheel:iron-gear-wheel-t0 has no belt path from (14, 9) to (6, 16); blocked by ['dense-copper-cable', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[pin_access] ports ('in-copper-plate', 'copper-plate-out-0') and ('dense-copper-cable', 'copper-plate-in') share access tile (2, 24); they must not coincide
  cut[pin_access] ports ('in-iron-plate', 'iron-plate-out-0') and ('dense-copper-cable', 'iron-plate-in') share access tile (2, 17); they must not coincide
  cut[corridor] net electronic-circuit:dense-copper-cable-t0 has no belt path from (2, 18) to (8, 16); blocked by ['dense-copper-cable', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-plate:in-iron-plate-t0 has no belt path from (2, 18) to (3, 18); blocked by ['dense-copper-cable', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-gear-wheel:iron-gear-wheel-t0 has no belt path from (8, 12) to (9, 7); blocked by ['dense-copper-cable', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-plate:in-iron-plate-t0 has no belt path from (2, 18) to (9, 16); blocked by ['dense-copper-cable', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-gear-wheel:iron-gear-wheel-t0 has no belt path from (10, 3) to (12, 4); blocked by ['dense-copper-cable', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net inserter:inserter-t0 has no belt path from (10, 7) to (12, 8); blocked by ['dense-copper-cable', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-gear-wheel:iron-gear-wheel-t0 has no belt path from (8, 9) to (7, 7); blocked by ['dense-copper-cable', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-plate:in-iron-plate-t0 has no belt path from (2, 6) to (5, 7); blocked by ['dense-copper-cable', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-gear-wheel:iron-gear-wheel-t0 has no belt path from (8, 13) to (8, 8); blocked by ['dense-copper-cable', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net inserter:inserter-t0 has no belt path from (2, 6) to (14, 4); blocked by ['dense-copper-cable', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-plate:in-iron-plate-t0 could not converge; contested corridor near [(3, 17), (6, 11), (6, 12), (6, 16)]... involves ['dense-copper-cable', 'in-iron-plate', 'iron-gear-wheel', 'transport-belt']
  cut[corridor] net iron-plate:in-iron-plate-t0 has no belt path from (2, 15) to (11, 15); blocked by ['dense-copper-cable', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-plate:in-iron-plate-t0 has no belt path from (2, 18) to (3, 18); blocked by ['dense-copper-cable', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net inserter:inserter-t0 could not converge; contested corridor near [(8, 12), (8, 13), (8, 14)]... involves ['inserter', 'iron-gear-wheel', 'logistic-science-pack']
  cut[corridor] net iron-plate:in-iron-plate-t0 has no belt path from (2, 13) to (2, 15); blocked by ['dense-copper-cable', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-gear-wheel:iron-gear-wheel-t0 has no belt path from (6, 11) to (7, 9); blocked by ['dense-copper-cable', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net inserter:inserter-t0 has no belt path from (2, 23) to (14, 29); blocked by ['dense-copper-cable', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-plate:in-iron-plate-t0 could not converge; contested corridor near [(1, 16), (2, 16), (7, 16), (8, 16)]... involves ['in-iron-plate', 'iron-gear-wheel']
  cut[corridor] net electronic-circuit:dense-copper-cable-t0 could not converge; contested corridor near [(6, 29)]... involves ['dense-copper-cable', 'inserter']
  cut[corridor] net iron-gear-wheel:iron-gear-wheel-t0 has no belt path from (7, 11) to (8, 7); blocked by ['dense-copper-cable', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net electronic-circuit:dense-copper-cable-t0 has no belt path from (6, 16) to (7, 2); blocked by ['dense-copper-cable', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net transport-belt:transport-belt-t0 could not converge; contested corridor near [(9, 9), (9, 10), (9, 11), (9, 12)]... involves ['logistic-science-pack', 'transport-belt']
  cut[corridor] net iron-gear-wheel:iron-gear-wheel-t0 has no belt path from (12, 1) to (10, 9); blocked by ['dense-copper-cable', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net electronic-circuit:dense-copper-cable-t0 has no belt path from (11, 6) to (9, 9); blocked by ['dense-copper-cable', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-plate:in-iron-plate-t0 could not converge; contested corridor near [(1, 8), (2, 8), (3, 8), (14, 9)]... involves ['dense-copper-cable', 'in-iron-plate', 'iron-gear-wheel', 'transport-belt']
  cut[corridor] net iron-plate:in-iron-plate-t0 has no belt path from (2, 1) to (2, 7); blocked by ['dense-copper-cable', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-plate:in-iron-plate-t0 has no belt path from (2, 23) to (1, 17); blocked by ['dense-copper-cable', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net electronic-circuit:dense-copper-cable-t0 has no belt path from (1, 22) to (7, 19); blocked by ['dense-copper-cable', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-plate:in-iron-plate-t0 has no belt path from (2, 5) to (1, 16); blocked by ['dense-copper-cable', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-gear-wheel:iron-gear-wheel-t0 has no belt path from (7, 12) to (7, 7); blocked by ['dense-copper-cable', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net inserter:inserter-t0 has no belt path from (1, 19) to (12, 27); blocked by ['dense-copper-cable', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-plate:in-iron-plate-t0 could not converge; contested corridor near [(3, 9)]... involves ['in-iron-plate', 'iron-gear-wheel', 'transport-belt']
  cut[corridor] net iron-gear-wheel:iron-gear-wheel-t0 could not converge; contested corridor near [(10, 14), (10, 15), (10, 16)]... involves ['inserter', 'iron-gear-wheel', 'logistic-science-pack']
```
