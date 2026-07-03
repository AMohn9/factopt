# Benders candidate: 1/s logistic-science-pack

**Feasible:** True
**Budget:** 600s total, 20s per master solve, 40 iterations max
**Used:** 480s over 40 iteration(s)
**Bounding box:** 15 x 31 = 465 tiles
**Routing:** 116 belt tiles, 6 undergrounds, 3 splitters, 25 turns, converged in 24 round(s)
**Static validation:** ok

## Rate plan

```
Plan: 1/s logistic-science-pack using assembling-machine-2
  machines: 11 total
      1 x inserter               (0.67 exact, 1.000 crafts/s)
      1 x iron-gear-wheel        (1.00 exact, 1.500 crafts/s)
      8 x logistic-science-pack  (8.00 exact, 1.000 crafts/s)
      1 x transport-belt         (0.33 exact, 0.500 crafts/s)
  raw inputs:
       1.000/s electronic-circuit
       4.500/s iron-plate
```

## Placement

| macro | position | size |
|---|---|---|
| in-electronic-circuit | (0, 30) | 2 x 1 |
| in-iron-plate | (0, 0) | 2 x 1 |
| inserter | (10, 19) | 3 x 9 |
| iron-gear-wheel | (10, 0) | 3 x 7 |
| logistic-science-pack | (0, 4) | 8 x 24 |
| out | (13, 30) | 2 x 1 |
| transport-belt | (10, 9) | 3 x 8 |

## Coarse routing

9 x 9 cells of 4 tiles; max boundary utilization 0.50

## Iterations

```
budget: 600s total, 20s/master solve, 40 iteration(s) max; used 480s over 40 iteration(s)
iter 0: margin=1 slack=0 bbox=14x28 failed (no_path, no_path, no_path); +3 cuts [master 5s, route 0.1s]
iter 1: margin=1 slack=0.15 bbox=16x28 failed (no_path); +1 cuts [master 8s, route 0.0s]
iter 2: margin=2 slack=0.15 bbox=18x29 routed; +0 cuts [master 17s, route 0.0s]
iter 3: margin=2 slack=0.15 bbox=17x30 routed; +0 cuts [master 17s, route 0.2s]
iter 4: margin=2 slack=0.15 bbox=17x29 failed (congestion); +1 cuts [master 16s, route 0.2s]
iter 5: margin=2 slack=0.15 bbox=17x29 routed; +0 cuts [master 17s, route 0.1s]
iter 6: margin=2 slack=0.15 bbox=28x17 failed (congestion, congestion); +2 cuts [master 13s, route 0.1s]
iter 7: margin=2 slack=0.15 bbox=32x15 failed (no_path, congestion, congestion); +3 cuts [master 14s, route 0.1s]
iter 8: margin=2 slack=0.15 bbox=30x16 routed; +0 cuts [master 13s, route 0.0s]
iter 9: margin=2 slack=0.15 bbox=28x17 routed; +0 cuts [master 13s, route 0.0s]
iter 10: margin=2 slack=0.15 bbox=15x31 failed (no_path, no_path, congestion); +3 cuts [master 11s, route 0.1s]
iter 11: margin=2 slack=0.15 bbox=15x31 failed (no_path, congestion); +2 cuts [master 11s, route 0.2s]
iter 12: margin=2 slack=0.15 bbox=15x31 failed (congestion); +1 cuts [master 11s, route 0.1s]
iter 13: margin=2 slack=0.15 bbox=15x31 routed; +0 cuts [master 11s, route 0.1s]
iter 14: margin=2 slack=0.15 bbox=0x0 unsolved; +0 cuts [master 5s, route 0.0s]
iter 15: margin=1 slack=0.15 bbox=16x28 failed (no_path, no_path); +2 cuts [master 12s, route 0.0s]
iter 16: margin=1 slack=0.15 bbox=16x28 failed (no_path, congestion); +2 cuts [master 11s, route 0.0s]
iter 17: margin=1 slack=0.15 bbox=16x28 failed (no_path); +1 cuts [master 12s, route 0.0s]
iter 18: margin=1 slack=0.15 bbox=16x28 failed (no_path, no_path); +2 cuts [master 12s, route 0.0s]
iter 19: margin=1 slack=0.15 bbox=16x28 failed (no_path, congestion); +2 cuts [master 12s, route 0.0s]
iter 20: margin=1 slack=0.15 bbox=16x28 failed (no_path, no_path); +2 cuts [master 12s, route 0.0s]
iter 21: margin=1 slack=0.15 bbox=16x28 failed (no_path, no_path); +2 cuts [master 13s, route 0.0s]
iter 22: margin=1 slack=0.15 bbox=16x28 failed (no_path, no_path); +2 cuts [master 13s, route 0.0s]
iter 23: margin=1 slack=0.15 bbox=16x28 failed (no_path); +1 cuts [master 12s, route 0.0s]
iter 24: margin=1 slack=0.15 bbox=16x28 failed (no_path, no_path); +2 cuts [master 11s, route 0.0s]
iter 25: margin=1 slack=0.15 bbox=16x28 failed (no_path, no_path); +2 cuts [master 12s, route 0.0s]
iter 26: margin=1 slack=0.15 bbox=16x28 failed (no_path, no_path); +2 cuts [master 12s, route 0.0s]
iter 27: margin=1 slack=0.15 bbox=16x28 failed (no_path, no_path); +2 cuts [master 11s, route 0.0s]
iter 28: margin=1 slack=0.15 bbox=16x28 failed (no_path); +1 cuts [master 12s, route 0.0s]
iter 29: margin=1 slack=0.15 bbox=16x28 failed (no_path, no_path); +2 cuts [master 11s, route 0.0s]
iter 30: margin=1 slack=0.15 bbox=16x28 failed (no_path, no_path); +2 cuts [master 11s, route 0.0s]
iter 31: margin=1 slack=0.15 bbox=16x28 failed (no_path, no_path); +2 cuts [master 11s, route 0.0s]
iter 32: margin=1 slack=0.15 bbox=16x28 failed (no_path, no_path); +2 cuts [master 12s, route 0.0s]
iter 33: margin=1 slack=0.15 bbox=16x28 failed (no_path, no_path); +2 cuts [master 12s, route 0.0s]
iter 34: margin=1 slack=0.15 bbox=16x28 failed (no_path, no_path); +2 cuts [master 11s, route 0.0s]
iter 35: margin=1 slack=0.15 bbox=16x28 failed (no_path, no_path); +2 cuts [master 13s, route 0.0s]
iter 36: margin=1 slack=0.15 bbox=16x28 failed (no_path, no_path); +2 cuts [master 12s, route 0.0s]
iter 37: margin=1 slack=0.15 bbox=16x28 failed (no_path, no_path); +2 cuts [master 12s, route 0.0s]
iter 38: margin=1 slack=0.15 bbox=16x28 failed (no_path, no_path); +2 cuts [master 12s, route 0.0s]
iter 39: margin=1 slack=0.15 bbox=16x28 failed (no_path, no_path); +2 cuts [master 12s, route 0.0s]
  cut[corridor] net inserter:inserter-t0 has no belt path from (8, 18) to (6, 26); blocked by ['in-electronic-circuit', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-plate:in-iron-plate-t0 has no belt path from (2, 0) to (8, 15); blocked by ['in-electronic-circuit', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net electronic-circuit:in-electronic-circuit-t0 has no belt path from (2, 27) to (8, 24); blocked by ['in-electronic-circuit', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-gear-wheel:iron-gear-wheel-t0 has no belt path from (6, 12) to (7, 17); blocked by ['in-electronic-circuit', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-gear-wheel:iron-gear-wheel-t0 could not converge; contested corridor near [(3, 4)]... involves ['inserter', 'iron-gear-wheel']
  cut[corridor] net iron-plate:in-iron-plate-t0 could not converge; contested corridor near [(0, 7), (0, 8), (0, 9), (0, 10)]... involves ['in-iron-plate', 'iron-gear-wheel']
  cut[corridor] net transport-belt:transport-belt-t0 could not converge; contested corridor near [(27, 3)]... involves ['logistic-science-pack', 'transport-belt']
  cut[corridor] net electronic-circuit:in-electronic-circuit-t0 has no belt path from (2, 10) to (8, 5); blocked by ['in-electronic-circuit', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-plate:in-iron-plate-t0 could not converge; contested corridor near [(17, 6), (18, 6), (23, 6), (24, 6)]... involves ['in-iron-plate', 'iron-gear-wheel', 'logistic-science-pack']
  cut[corridor] net iron-gear-wheel:iron-gear-wheel-t0 could not converge; contested corridor near [(11, 1)]... involves ['inserter', 'iron-gear-wheel']
  cut[corridor] net iron-gear-wheel:iron-gear-wheel-t0 has no belt path from (13, 16) to (13, 27); blocked by ['in-electronic-circuit', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net electronic-circuit:in-electronic-circuit-t0 has no belt path from (2, 30) to (9, 26); blocked by ['in-electronic-circuit', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-plate:in-iron-plate-t0 could not converge; contested corridor near [(1, 2)]... involves ['in-iron-plate', 'iron-gear-wheel']
  cut[corridor] net electronic-circuit:in-electronic-circuit-t0 has no belt path from (2, 30) to (9, 26); blocked by ['in-electronic-circuit', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-gear-wheel:iron-gear-wheel-t0 could not converge; contested corridor near [(13, 8)]... involves ['inserter', 'iron-gear-wheel', 'transport-belt']
  cut[corridor] net iron-gear-wheel:iron-gear-wheel-t0 could not converge; contested corridor near [(14, 9), (14, 10), (14, 11)]... involves ['inserter', 'iron-gear-wheel']
  cut[corridor] net iron-plate:in-iron-plate-t0 has no belt path from (2, 17) to (3, 11); blocked by ['in-electronic-circuit', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-gear-wheel:iron-gear-wheel-t0 has no belt path from (6, 12) to (7, 17); blocked by ['in-electronic-circuit', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-gear-wheel:iron-gear-wheel-t0 has no belt path from (6, 12) to (7, 17); blocked by ['in-electronic-circuit', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-plate:in-iron-plate-t0 could not converge; contested corridor near [(3, 16), (3, 17)]... involves ['in-iron-plate', 'iron-gear-wheel', 'transport-belt']
  cut[corridor] net iron-gear-wheel:iron-gear-wheel-t0 has no belt path from (6, 11) to (7, 16); blocked by ['in-electronic-circuit', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-plate:in-iron-plate-t0 has no belt path from (2, 16) to (3, 17); blocked by ['in-electronic-circuit', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-gear-wheel:iron-gear-wheel-t0 has no belt path from (6, 11) to (7, 16); blocked by ['in-electronic-circuit', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-gear-wheel:iron-gear-wheel-t0 has no belt path from (6, 11) to (7, 16); blocked by ['in-electronic-circuit', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-plate:in-iron-plate-t0 could not converge; contested corridor near [(3, 15), (3, 16)]... involves ['in-iron-plate', 'iron-gear-wheel', 'transport-belt']
  cut[corridor] net iron-plate:in-iron-plate-t0 has no belt path from (2, 11) to (3, 11); blocked by ['in-electronic-circuit', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-gear-wheel:iron-gear-wheel-t0 has no belt path from (6, 12) to (7, 17); blocked by ['in-electronic-circuit', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-plate:in-iron-plate-t0 has no belt path from (2, 17) to (3, 18); blocked by ['in-electronic-circuit', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-gear-wheel:iron-gear-wheel-t0 has no belt path from (6, 12) to (7, 17); blocked by ['in-electronic-circuit', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-plate:in-iron-plate-t0 has no belt path from (2, 11) to (3, 11); blocked by ['in-electronic-circuit', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-gear-wheel:iron-gear-wheel-t0 has no belt path from (6, 12) to (7, 17); blocked by ['in-electronic-circuit', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-gear-wheel:iron-gear-wheel-t0 has no belt path from (6, 11) to (7, 16); blocked by ['in-electronic-circuit', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-plate:in-iron-plate-t0 has no belt path from (2, 16) to (3, 17); blocked by ['in-electronic-circuit', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-gear-wheel:iron-gear-wheel-t0 has no belt path from (6, 11) to (7, 16); blocked by ['in-electronic-circuit', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-plate:in-iron-plate-t0 has no belt path from (2, 17) to (3, 18); blocked by ['in-electronic-circuit', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-gear-wheel:iron-gear-wheel-t0 has no belt path from (6, 12) to (7, 17); blocked by ['in-electronic-circuit', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-plate:in-iron-plate-t0 has no belt path from (2, 10) to (3, 10); blocked by ['in-electronic-circuit', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-gear-wheel:iron-gear-wheel-t0 has no belt path from (6, 11) to (7, 16); blocked by ['in-electronic-circuit', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-plate:in-iron-plate-t0 has no belt path from (2, 16) to (3, 17); blocked by ['in-electronic-circuit', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-gear-wheel:iron-gear-wheel-t0 has no belt path from (6, 11) to (7, 16); blocked by ['in-electronic-circuit', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-gear-wheel:iron-gear-wheel-t0 has no belt path from (6, 12) to (7, 17); blocked by ['in-electronic-circuit', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-plate:in-iron-plate-t0 has no belt path from (2, 17) to (3, 18); blocked by ['in-electronic-circuit', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-gear-wheel:iron-gear-wheel-t0 has no belt path from (6, 12) to (7, 17); blocked by ['in-electronic-circuit', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-plate:in-iron-plate-t0 has no belt path from (2, 16) to (3, 17); blocked by ['in-electronic-circuit', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-gear-wheel:iron-gear-wheel-t0 has no belt path from (6, 11) to (7, 16); blocked by ['in-electronic-circuit', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-plate:in-iron-plate-t0 has no belt path from (2, 10) to (3, 10); blocked by ['in-electronic-circuit', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-gear-wheel:iron-gear-wheel-t0 has no belt path from (6, 11) to (7, 16); blocked by ['in-electronic-circuit', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-plate:in-iron-plate-t0 has no belt path from (2, 11) to (3, 11); blocked by ['in-electronic-circuit', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-gear-wheel:iron-gear-wheel-t0 has no belt path from (6, 12) to (7, 17); blocked by ['in-electronic-circuit', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-plate:in-iron-plate-t0 has no belt path from (2, 17) to (3, 18); blocked by ['in-electronic-circuit', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-gear-wheel:iron-gear-wheel-t0 has no belt path from (6, 12) to (7, 17); blocked by ['in-electronic-circuit', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-plate:in-iron-plate-t0 has no belt path from (2, 10) to (3, 10); blocked by ['in-electronic-circuit', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-gear-wheel:iron-gear-wheel-t0 has no belt path from (6, 11) to (7, 16); blocked by ['in-electronic-circuit', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-plate:in-iron-plate-t0 has no belt path from (2, 16) to (3, 17); blocked by ['in-electronic-circuit', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-gear-wheel:iron-gear-wheel-t0 has no belt path from (6, 11) to (7, 16); blocked by ['in-electronic-circuit', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-plate:in-iron-plate-t0 has no belt path from (2, 11) to (3, 11); blocked by ['in-electronic-circuit', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-gear-wheel:iron-gear-wheel-t0 has no belt path from (6, 12) to (7, 17); blocked by ['in-electronic-circuit', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-plate:in-iron-plate-t0 has no belt path from (2, 17) to (3, 18); blocked by ['in-electronic-circuit', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-gear-wheel:iron-gear-wheel-t0 has no belt path from (6, 12) to (7, 17); blocked by ['in-electronic-circuit', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-plate:in-iron-plate-t0 has no belt path from (2, 10) to (3, 10); blocked by ['in-electronic-circuit', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-gear-wheel:iron-gear-wheel-t0 has no belt path from (6, 11) to (7, 16); blocked by ['in-electronic-circuit', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-plate:in-iron-plate-t0 has no belt path from (2, 16) to (3, 17); blocked by ['in-electronic-circuit', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-gear-wheel:iron-gear-wheel-t0 has no belt path from (6, 11) to (7, 16); blocked by ['in-electronic-circuit', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
```
