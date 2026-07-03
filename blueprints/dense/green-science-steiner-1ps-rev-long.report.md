# Benders candidate: 1/s logistic-science-pack

**Feasible:** True
**Budget:** 900s total, 60s per master solve, 40 iterations max
**Used:** 917s over 14 iteration(s)
**Bounding box:** 31 x 27 = 837 tiles
**Routing:** 127 belt tiles, 4 undergrounds, 4 splitters, 27 turns, converged in 5 round(s)
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
| dense-copper-cable | (5, 2) | 7 x 8 |
| in-copper-plate | (0, 2) | 2 x 1 |
| in-iron-plate | (0, 9) | 2 x 1 |
| inserter | (1, 13) | 9 x 3 |
| iron-gear-wheel | (13, 13) | 7 x 3 |
| logistic-science-pack | (2, 19) | 24 x 8 |
| out | (29, 26) | 2 x 1 |
| transport-belt | (15, 7) | 8 x 3 |

## Coarse routing

11 x 11 cells of 4 tiles; max boundary utilization 0.50

## Iterations

```
budget: 900s total, 60s/master solve, 40 iteration(s) max; used 917s over 14 iteration(s)
iter 0: margin=1 slack=0 bbox=28x17 failed (port_conflict, port_conflict, no_path); +3 cuts [master 12s, route 0.0s]
iter 1: margin=1 slack=0.15 bbox=19x28 failed (port_conflict, port_conflict); +2 cuts [master 50s, route 0.0s]
iter 2: margin=2 slack=0.15 bbox=21x29 failed (no_path); +1 cuts [master 68s, route 0.0s]
iter 3: margin=2 slack=0.3 bbox=23x30 failed (no_path); +1 cuts [master 68s, route 0.0s]
iter 4: margin=3 slack=0.3 bbox=25x31 failed (congestion); +1 cuts [master 71s, route 0.3s]
iter 5: margin=3 slack=0.5 bbox=31x29 routed; +0 cuts [master 72s, route 0.1s]
iter 6: margin=3 slack=0.5 bbox=27x33 routed; +0 cuts [master 72s, route 0.2s]
iter 7: margin=3 slack=0.5 bbox=28x31 routed; +0 cuts [master 71s, route 0.0s]
iter 8: margin=3 slack=0.5 bbox=32x27 routed; +0 cuts [master 72s, route 0.1s]
iter 9: margin=3 slack=0.5 bbox=22x39 routed; +0 cuts [master 71s, route 0.1s]
iter 10: margin=3 slack=0.5 bbox=31x27 routed; +0 cuts [master 71s, route 0.0s]
iter 11: margin=3 slack=0.5 bbox=31x26 failed (congestion); +1 cuts [master 71s, route 0.8s]
iter 12: margin=3 slack=0.5 bbox=27x30 failed (congestion); +1 cuts [master 73s, route 0.2s]
iter 13: margin=3 slack=0.5 bbox=26x31 failed (congestion); +1 cuts [master 72s, route 0.2s]
  cut[pin_access] ports ('in-iron-plate', 'iron-plate-out-0') and ('transport-belt', 'iron-plate-in') share access tile (2, 15); they must not coincide
  cut[pin_access] ports ('in-copper-plate', 'copper-plate-out-0') and ('transport-belt', 'transport-belt-out-0') share access tile (2, 9); they must not coincide
  cut[corridor] net iron-gear-wheel:iron-gear-wheel-t0 has no belt path from (14, 9) to (6, 16); blocked by ['dense-copper-cable', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[pin_access] ports ('in-copper-plate', 'copper-plate-out-0') and ('dense-copper-cable', 'copper-plate-in') share access tile (2, 3); they must not coincide
  cut[pin_access] ports ('in-iron-plate', 'iron-plate-out-0') and ('dense-copper-cable', 'iron-plate-in') share access tile (2, 10); they must not coincide
  cut[corridor] net iron-plate:in-iron-plate-t0 has no belt path from (2, 18) to (3, 18); blocked by ['dense-copper-cable', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-plate:in-iron-plate-t0 has no belt path from (2, 16) to (7, 19); blocked by ['dense-copper-cable', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-plate:in-iron-plate-t0 could not converge; contested corridor near [(9, 16), (9, 21)]... involves ['in-iron-plate', 'iron-gear-wheel']
  cut[corridor] net iron-plate:in-iron-plate-t0 could not converge; contested corridor near [(5, 9), (6, 9), (7, 9), (7, 10)]... involves ['in-iron-plate', 'inserter', 'iron-gear-wheel', 'transport-belt']
  cut[corridor] net electronic-circuit:dense-copper-cable-t0 could not converge; contested corridor near [(7, 15)]... involves ['dense-copper-cable', 'inserter']
  cut[corridor] net inserter:inserter-t0 could not converge; contested corridor near [(18, 29)]... involves ['inserter', 'logistic-science-pack']
```
