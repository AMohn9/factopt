# Benders candidate: 1/s logistic-science-pack

**Feasible:** True
**Budget:** 600s total, 20s per master solve, 40 iterations max
**Used:** 615s over 22 iteration(s)
**Bounding box:** 19 x 32 = 608 tiles
**Routing:** 100 belt tiles, 6 undergrounds, 4 splitters, 26 turns, converged in 16 round(s)
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
| dense-copper-cable | (2, 3) | 7 x 8 |
| in-copper-plate | (0, 0) | 2 x 1 |
| in-iron-plate | (0, 24) | 2 x 1 |
| inserter | (0, 13) | 9 x 3 |
| iron-gear-wheel | (2, 18) | 7 x 3 |
| logistic-science-pack | (11, 6) | 8 x 24 |
| out | (17, 3) | 2 x 1 |
| transport-belt | (4, 23) | 3 x 8 |

## Coarse routing

10 x 10 cells of 4 tiles; max boundary utilization 0.67

## Iterations

```
budget: 600s total, 20s/master solve, 40 iteration(s) max; used 615s over 22 iteration(s)
iter 0: margin=1 slack=0 bbox=28x17 failed (port_conflict, no_path, no_path, no_path); +4 cuts [master 10s, route 0.0s]
iter 1: margin=1 slack=0.15 bbox=19x28 failed (port_conflict, port_conflict, port_conflict); +3 cuts [master 24s, route 0.0s]
iter 2: margin=2 slack=0.15 bbox=17x36 routed; +0 cuts [master 28s, route 0.0s]
iter 3: margin=2 slack=0.15 bbox=21x29 failed (no_path); +1 cuts [master 29s, route 0.0s]
iter 4: margin=2 slack=0.15 bbox=21x29 failed (no_path, congestion); +2 cuts [master 29s, route 0.0s]
iter 5: margin=2 slack=0.15 bbox=19x32 failed (no_path); +1 cuts [master 29s, route 0.0s]
iter 6: margin=2 slack=0.15 bbox=21x29 failed (no_path, congestion); +2 cuts [master 29s, route 0.4s]
iter 7: margin=2 slack=0.15 bbox=21x29 failed (no_path); +1 cuts [master 29s, route 0.1s]
iter 8: margin=2 slack=0.15 bbox=21x29 failed (no_path, congestion); +2 cuts [master 29s, route 0.1s]
iter 9: margin=2 slack=0.15 bbox=21x29 failed (no_path); +1 cuts [master 29s, route 0.0s]
iter 10: margin=2 slack=0.15 bbox=21x29 failed (no_path); +1 cuts [master 29s, route 0.0s]
iter 11: margin=2 slack=0.15 bbox=21x29 failed (no_path); +1 cuts [master 29s, route 0.0s]
iter 12: margin=2 slack=0.15 bbox=21x29 failed (no_path); +1 cuts [master 30s, route 0.0s]
iter 13: margin=2 slack=0.15 bbox=21x29 failed (no_path); +1 cuts [master 29s, route 0.0s]
iter 14: margin=2 slack=0.15 bbox=21x29 failed (no_path, no_path); +2 cuts [master 29s, route 0.0s]
iter 15: margin=2 slack=0.15 bbox=21x29 failed (no_path); +1 cuts [master 29s, route 0.0s]
iter 16: margin=2 slack=0.15 bbox=21x29 failed (no_path); +1 cuts [master 29s, route 0.0s]
iter 17: margin=2 slack=0.15 bbox=21x29 failed (no_path); +1 cuts [master 29s, route 0.0s]
iter 18: margin=2 slack=0.15 bbox=21x29 failed (no_path); +1 cuts [master 29s, route 0.0s]
iter 19: margin=2 slack=0.15 bbox=21x29 failed (congestion); +1 cuts [master 29s, route 0.1s]
iter 20: margin=2 slack=0.15 bbox=21x29 routed; +0 cuts [master 29s, route 0.2s]
iter 21: margin=2 slack=0.15 bbox=19x32 routed; +0 cuts [master 29s, route 0.1s]
  cut[pin_access] ports ('in-copper-plate', 'copper-plate-out-0') and ('transport-belt', 'transport-belt-out-0') share access tile (2, 9); they must not coincide
  cut[corridor] net iron-plate:in-iron-plate-t0 has no belt path from (2, 16) to (19, 15); blocked by ['dense-copper-cable', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-gear-wheel:iron-gear-wheel-t0 has no belt path from (14, 9) to (6, 16); blocked by ['dense-copper-cable', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net electronic-circuit:dense-copper-cable-t0 has no belt path from (14, 15) to (26, 15); blocked by ['dense-copper-cable', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[pin_access] ports ('in-copper-plate', 'copper-plate-out-0') and ('dense-copper-cable', 'copper-plate-in') share access tile (2, 3); they must not coincide
  cut[pin_access] ports ('iron-gear-wheel', 'iron-gear-wheel-out-0') and ('inserter', 'iron-gear-wheel-in') share access tile (9, 15); they must not coincide
  cut[pin_access] ports ('iron-gear-wheel', 'iron-plate-in') and ('transport-belt', 'iron-plate-in') share access tile (3, 19); they must not coincide
  cut[corridor] net iron-plate:in-iron-plate-t0 has no belt path from (2, 21) to (6, 13); blocked by ['dense-copper-cable', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-plate:in-iron-plate-t0 has no belt path from (2, 18) to (1, 12); blocked by ['dense-copper-cable', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net electronic-circuit:dense-copper-cable-t0 could not converge; contested corridor near [(3, 19)]... involves ['dense-copper-cable', 'inserter']
  cut[corridor] net iron-plate:in-iron-plate-t0 has no belt path from (2, 17) to (0, 11); blocked by ['dense-copper-cable', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net inserter:inserter-t0 has no belt path from (3, 13) to (14, 27); blocked by ['dense-copper-cable', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-plate:in-iron-plate-t0 could not converge; contested corridor near [(3, 19)]... involves ['in-iron-plate', 'iron-gear-wheel', 'transport-belt']
  cut[corridor] net iron-plate:in-iron-plate-t0 has no belt path from (2, 18) to (3, 18); blocked by ['dense-copper-cable', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-gear-wheel:iron-gear-wheel-t0 has no belt path from (11, 21) to (10, 23); blocked by ['dense-copper-cable', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-plate:in-iron-plate-t0 could not converge; contested corridor near [(2, 21), (2, 22), (3, 22)]... involves ['in-iron-plate', 'iron-gear-wheel', 'transport-belt']
  cut[corridor] net iron-plate:in-iron-plate-t0 has no belt path from (2, 18) to (3, 18); blocked by ['dense-copper-cable', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-plate:in-iron-plate-t0 has no belt path from (2, 17) to (3, 17); blocked by ['dense-copper-cable', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-plate:in-iron-plate-t0 has no belt path from (2, 21) to (3, 21); blocked by ['dense-copper-cable', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-gear-wheel:iron-gear-wheel-t0 has no belt path from (6, 18) to (5, 18); blocked by ['dense-copper-cable', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-plate:in-iron-plate-t0 has no belt path from (2, 18) to (6, 10); blocked by ['dense-copper-cable', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-plate:in-iron-plate-t0 has no belt path from (2, 18) to (3, 18); blocked by ['dense-copper-cable', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-gear-wheel:iron-gear-wheel-t0 has no belt path from (8, 12) to (9, 7); blocked by ['dense-copper-cable', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-gear-wheel:iron-gear-wheel-t0 has no belt path from (1, 9) to (0, 7); blocked by ['dense-copper-cable', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-plate:in-iron-plate-t0 has no belt path from (2, 13) to (6, 21); blocked by ['dense-copper-cable', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-plate:in-iron-plate-t0 has no belt path from (2, 9) to (4, 20); blocked by ['dense-copper-cable', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-plate:in-iron-plate-t0 has no belt path from (2, 17) to (6, 9); blocked by ['dense-copper-cable', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-plate:in-iron-plate-t0 could not converge; contested corridor near [(6, 18), (6, 19), (6, 20)]... involves ['in-iron-plate', 'iron-gear-wheel']
```
