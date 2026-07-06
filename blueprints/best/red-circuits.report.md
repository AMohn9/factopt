# Benders candidate: 1/s advanced-circuit

**Feasible:** True
**Budget:** 300s total, 20s per master solve, 40 iterations max
**Used:** 248s over 35 iteration(s)
**Bounding box:** 18 x 28 = 504 tiles
**Routing:** 87 belt tiles, 2 undergrounds, 0 splitters, 22 turns, converged in 24 round(s)
**Static validation:** ok

## Rate plan

```
Plan: 1/s advanced-circuit using assembling-machine-2
  machines: 14 total
      8 x advanced-circuit       (8.00 exact, 1.000 crafts/s)
      4 x copper-cable           (3.33 exact, 5.000 crafts/s)
      2 x electronic-circuit     (1.33 exact, 2.000 crafts/s)
  raw inputs:
       5.000/s copper-plate
       2.000/s iron-plate
       2.000/s plastic-bar
```

## Placement

| macro | position | size |
|---|---|---|
| advanced-circuit | (9, 2) | 9 x 24 |
| copper-cable | (1, 10) | 7 x 12 |
| electronic-circuit | (0, 2) | 8 x 6 |
| in-copper-plate | (0, 23) | 2 x 1 |
| in-iron-plate | (0, 0) | 2 x 1 |
| in-plastic-bar | (0, 25) | 2 x 1 |
| out | (16, 0) | 2 x 1 |

## Coarse routing

9 x 9 cells of 4 tiles; max boundary utilization 1.00

## Iterations

```
budget: 300s total, 20s/master solve, 40 iteration(s) max; used 248s over 35 iteration(s)
iter 0: margin=1 slack=0 bbox=18x28 failed (no_path, no_path); +2 cuts [master 6s, route 0.0s]
iter 1: margin=1 slack=0.15 bbox=18x32 failed (port_conflict); +1 cuts [master 9s, route 0.0s]
iter 2: margin=2 slack=0.15 bbox=19x32 routed; +0 cuts [master 11s, route 0.0s]
iter 3: margin=2 slack=0.15 bbox=19x31 routed; +0 cuts [master 11s, route 0.0s]
iter 4: margin=2 slack=0.15 bbox=19x30 routed; +0 cuts [master 8s, route 0.0s]
iter 5: margin=2 slack=0.15 bbox=19x29 routed; +0 cuts [master 7s, route 0.0s]
iter 6: margin=2 slack=0.15 bbox=28x19 failed (no_path, no_path); +2 cuts [master 5s, route 0.1s]
iter 7: margin=2 slack=0.15 bbox=28x19 routed; +0 cuts [master 5s, route 0.0s]
iter 8: margin=2 slack=0.15 bbox=0x0 unsolved; +0 cuts [master 2s, route 0.0s]
iter 9: margin=1 slack=0.15 bbox=18x29 failed (no_path, no_path); +2 cuts [master 8s, route 0.1s]
iter 10: margin=1 slack=0.15 bbox=18x29 failed (no_path, no_path); +2 cuts [master 8s, route 0.1s]
iter 11: margin=1 slack=0.15 bbox=18x29 failed (no_path); +1 cuts [master 8s, route 0.0s]
iter 12: margin=1 slack=0.15 bbox=18x29 failed (no_path); +1 cuts [master 8s, route 0.0s]
iter 13: margin=1 slack=0.15 bbox=18x29 failed (no_path); +1 cuts [master 8s, route 0.0s]
iter 14: margin=1 slack=0.15 bbox=18x29 failed (no_path); +1 cuts [master 8s, route 0.0s]
iter 15: margin=1 slack=0.15 bbox=18x29 failed (no_path); +1 cuts [master 8s, route 0.1s]
iter 16: margin=1 slack=0.15 bbox=18x29 failed (no_path, congestion); +2 cuts [master 8s, route 0.0s]
iter 17: margin=1 slack=0.15 bbox=18x29 failed (no_path); +1 cuts [master 8s, route 0.1s]
iter 18: margin=1 slack=0.15 bbox=18x29 failed (no_path); +1 cuts [master 8s, route 0.0s]
iter 19: margin=1 slack=0.15 bbox=18x29 failed (no_path); +1 cuts [master 8s, route 0.0s]
iter 20: margin=1 slack=0.15 bbox=18x29 routed; +0 cuts [master 8s, route 0.0s]
iter 21: margin=1 slack=0.15 bbox=18x28 failed (no_path); +1 cuts [master 6s, route 0.0s]
iter 22: margin=1 slack=0.15 bbox=18x28 failed (no_path); +1 cuts [master 6s, route 0.1s]
iter 23: margin=1 slack=0.15 bbox=18x28 failed (no_path, congestion); +2 cuts [master 6s, route 0.0s]
iter 24: margin=1 slack=0.15 bbox=18x28 failed (no_path, congestion); +2 cuts [master 6s, route 0.1s]
iter 25: margin=1 slack=0.15 bbox=18x28 failed (no_path, no_path, no_path); +3 cuts [master 6s, route 0.1s]
iter 26: margin=1 slack=0.15 bbox=18x28 failed (no_path); +1 cuts [master 6s, route 0.1s]
iter 27: margin=1 slack=0.15 bbox=18x28 failed (no_path, no_path); +2 cuts [master 6s, route 0.0s]
iter 28: margin=1 slack=0.15 bbox=18x28 failed (no_path, congestion); +2 cuts [master 6s, route 0.1s]
iter 29: margin=1 slack=0.15 bbox=18x28 failed (no_path, no_path, congestion); +3 cuts [master 6s, route 0.1s]
iter 30: margin=1 slack=0.15 bbox=18x28 failed (no_path); +1 cuts [master 7s, route 0.1s]
iter 31: margin=1 slack=0.15 bbox=18x28 failed (no_path, no_path); +2 cuts [master 6s, route 0.0s]
iter 32: margin=1 slack=0.15 bbox=18x28 failed (no_path); +1 cuts [master 7s, route 0.2s]
iter 33: margin=1 slack=0.15 bbox=18x28 routed; +0 cuts [master 6s, route 0.1s]
iter 34: margin=1 slack=0.15 bbox=0x0 unsolved; +0 cuts [master 1s, route 0.0s]
  cut[corridor] net iron-plate:in-iron-plate-t0 has no belt path from (2, 0) to (1, 2); blocked by ['advanced-circuit', 'copper-cable', 'electronic-circuit', 'in-copper-plate', 'in-iron-plate', 'in-plastic-bar', 'out']
  cut[corridor] net copper-cable:copper-cable-t0 has no belt path from (7, 10) to (8, 9); blocked by ['advanced-circuit', 'copper-cable', 'electronic-circuit', 'in-copper-plate', 'in-iron-plate', 'in-plastic-bar', 'out']
  cut[pin_access] ports ('copper-cable', 'copper-cable-out-0') and ('electronic-circuit', 'copper-cable-in') share access tile (7, 8); they must not coincide
  cut[corridor] net electronic-circuit:electronic-circuit-t0 has no belt path from (17, 1) to (26, 10); blocked by ['advanced-circuit', 'copper-cable', 'electronic-circuit', 'in-copper-plate', 'in-iron-plate', 'in-plastic-bar', 'out']
  cut[corridor] net advanced-circuit:advanced-circuit-t0 has no belt path from (26, 17) to (25, 7); blocked by ['advanced-circuit', 'copper-cable', 'electronic-circuit', 'in-copper-plate', 'in-iron-plate', 'in-plastic-bar', 'out']
  cut[corridor] net electronic-circuit:electronic-circuit-t0 has no belt path from (1, 3) to (9, 2); blocked by ['advanced-circuit', 'copper-cable', 'electronic-circuit', 'in-copper-plate', 'in-iron-plate', 'in-plastic-bar', 'out']
  cut[corridor] net copper-cable:copper-cable-t0 has no belt path from (7, 10) to (8, 9); blocked by ['advanced-circuit', 'copper-cable', 'electronic-circuit', 'in-copper-plate', 'in-iron-plate', 'in-plastic-bar', 'out']
  cut[corridor] net electronic-circuit:electronic-circuit-t0 has no belt path from (1, 3) to (9, 2); blocked by ['advanced-circuit', 'copper-cable', 'electronic-circuit', 'in-copper-plate', 'in-iron-plate', 'in-plastic-bar', 'out']
  cut[corridor] net copper-cable:copper-cable-t0 has no belt path from (7, 10) to (8, 9); blocked by ['advanced-circuit', 'copper-cable', 'electronic-circuit', 'in-copper-plate', 'in-iron-plate', 'in-plastic-bar', 'out']
  cut[corridor] net copper-cable:copper-cable-t0 has no belt path from (7, 10) to (8, 9); blocked by ['advanced-circuit', 'copper-cable', 'electronic-circuit', 'in-copper-plate', 'in-iron-plate', 'in-plastic-bar', 'out']
  cut[corridor] net copper-cable:copper-cable-t0 has no belt path from (7, 10) to (8, 9); blocked by ['advanced-circuit', 'copper-cable', 'electronic-circuit', 'in-copper-plate', 'in-iron-plate', 'in-plastic-bar', 'out']
  cut[corridor] net copper-cable:copper-cable-t0 has no belt path from (7, 10) to (8, 9); blocked by ['advanced-circuit', 'copper-cable', 'electronic-circuit', 'in-copper-plate', 'in-iron-plate', 'in-plastic-bar', 'out']
  cut[corridor] net copper-cable:copper-cable-t0 has no belt path from (7, 10) to (8, 9); blocked by ['advanced-circuit', 'copper-cable', 'electronic-circuit', 'in-copper-plate', 'in-iron-plate', 'in-plastic-bar', 'out']
  cut[corridor] net copper-cable:copper-cable-t0 has no belt path from (7, 10) to (8, 9); blocked by ['advanced-circuit', 'copper-cable', 'electronic-circuit', 'in-copper-plate', 'in-iron-plate', 'in-plastic-bar', 'out']
  cut[corridor] net copper-cable:copper-cable-t0 has no belt path from (7, 11) to (8, 9); blocked by ['advanced-circuit', 'copper-cable', 'electronic-circuit', 'in-copper-plate', 'in-iron-plate', 'in-plastic-bar', 'out']
  cut[corridor] net electronic-circuit:electronic-circuit-t0 could not converge; contested corridor near [(8, 10), (8, 11), (8, 12), (8, 13)]... involves ['advanced-circuit', 'copper-cable', 'electronic-circuit']
  cut[corridor] net copper-cable:copper-cable-t0 has no belt path from (7, 10) to (8, 9); blocked by ['advanced-circuit', 'copper-cable', 'electronic-circuit', 'in-copper-plate', 'in-iron-plate', 'in-plastic-bar', 'out']
  cut[corridor] net copper-cable:copper-cable-t0 has no belt path from (7, 10) to (8, 9); blocked by ['advanced-circuit', 'copper-cable', 'electronic-circuit', 'in-copper-plate', 'in-iron-plate', 'in-plastic-bar', 'out']
  cut[corridor] net copper-cable:copper-cable-t0 has no belt path from (7, 10) to (8, 9); blocked by ['advanced-circuit', 'copper-cable', 'electronic-circuit', 'in-copper-plate', 'in-iron-plate', 'in-plastic-bar', 'out']
  cut[corridor] net copper-cable:copper-cable-t0 has no belt path from (7, 10) to (8, 9); blocked by ['advanced-circuit', 'copper-cable', 'electronic-circuit', 'in-copper-plate', 'in-iron-plate', 'in-plastic-bar', 'out']
  cut[corridor] net copper-cable:copper-cable-t0 has no belt path from (7, 10) to (8, 9); blocked by ['advanced-circuit', 'copper-cable', 'electronic-circuit', 'in-copper-plate', 'in-iron-plate', 'in-plastic-bar', 'out']
  cut[corridor] net copper-cable:copper-cable-t0 has no belt path from (7, 11) to (8, 9); blocked by ['advanced-circuit', 'copper-cable', 'electronic-circuit', 'in-copper-plate', 'in-iron-plate', 'in-plastic-bar', 'out']
  cut[corridor] net electronic-circuit:electronic-circuit-t0 could not converge; contested corridor near [(8, 10), (8, 11), (8, 12), (8, 13)]... involves ['advanced-circuit', 'copper-cable', 'electronic-circuit']
  cut[corridor] net electronic-circuit:electronic-circuit-t0 has no belt path from (1, 8) to (9, 1); blocked by ['advanced-circuit', 'copper-cable', 'electronic-circuit', 'in-copper-plate', 'in-iron-plate', 'in-plastic-bar', 'out']
  cut[corridor] net copper-cable:copper-cable-t0 could not converge; contested corridor near [(7, 1)]... involves ['copper-cable', 'electronic-circuit']
  cut[corridor] net plastic-bar:in-plastic-bar-t0 has no belt path from (2, 24) to (17, 26); blocked by ['advanced-circuit', 'copper-cable', 'electronic-circuit', 'in-copper-plate', 'in-iron-plate', 'in-plastic-bar', 'out']
  cut[corridor] net iron-plate:in-iron-plate-t0 has no belt path from (2, 0) to (1, 2); blocked by ['advanced-circuit', 'copper-cable', 'electronic-circuit', 'in-copper-plate', 'in-iron-plate', 'in-plastic-bar', 'out']
  cut[corridor] net copper-cable:copper-cable-t0 has no belt path from (7, 10) to (8, 9); blocked by ['advanced-circuit', 'copper-cable', 'electronic-circuit', 'in-copper-plate', 'in-iron-plate', 'in-plastic-bar', 'out']
  cut[corridor] net copper-cable:copper-cable-t0 has no belt path from (7, 10) to (8, 9); blocked by ['advanced-circuit', 'copper-cable', 'electronic-circuit', 'in-copper-plate', 'in-iron-plate', 'in-plastic-bar', 'out']
  cut[corridor] net iron-plate:in-iron-plate-t0 has no belt path from (2, 1) to (1, 3); blocked by ['advanced-circuit', 'copper-cable', 'electronic-circuit', 'in-copper-plate', 'in-iron-plate', 'in-plastic-bar', 'out']
  cut[corridor] net copper-cable:copper-cable-t0 has no belt path from (7, 11) to (8, 10); blocked by ['advanced-circuit', 'copper-cable', 'electronic-circuit', 'in-copper-plate', 'in-iron-plate', 'in-plastic-bar', 'out']
  cut[corridor] net electronic-circuit:electronic-circuit-t0 has no belt path from (1, 3) to (9, 1); blocked by ['advanced-circuit', 'copper-cable', 'electronic-circuit', 'in-copper-plate', 'in-iron-plate', 'in-plastic-bar', 'out']
  cut[corridor] net copper-cable:copper-cable-t0 could not converge; contested corridor near [(8, 11), (8, 12)]... involves ['advanced-circuit', 'copper-cable', 'electronic-circuit']
  cut[corridor] net iron-plate:in-iron-plate-t0 has no belt path from (2, 0) to (1, 2); blocked by ['advanced-circuit', 'copper-cable', 'electronic-circuit', 'in-copper-plate', 'in-iron-plate', 'in-plastic-bar', 'out']
  cut[corridor] net copper-cable:copper-cable-t0 has no belt path from (7, 10) to (8, 9); blocked by ['advanced-circuit', 'copper-cable', 'electronic-circuit', 'in-copper-plate', 'in-iron-plate', 'in-plastic-bar', 'out']
  cut[corridor] net copper-plate:in-copper-plate-t0 could not converge; contested corridor near [(0, 10), (0, 11), (0, 12), (0, 13)]... involves ['copper-cable', 'in-copper-plate']
  cut[corridor] net electronic-circuit:electronic-circuit-t0 has no belt path from (1, 3) to (9, 1); blocked by ['advanced-circuit', 'copper-cable', 'electronic-circuit', 'in-copper-plate', 'in-iron-plate', 'in-plastic-bar', 'out']
  cut[corridor] net iron-plate:in-iron-plate-t0 has no belt path from (2, 0) to (1, 3); blocked by ['advanced-circuit', 'copper-cable', 'electronic-circuit', 'in-copper-plate', 'in-iron-plate', 'in-plastic-bar', 'out']
  cut[corridor] net copper-cable:copper-cable-t0 has no belt path from (7, 11) to (8, 10); blocked by ['advanced-circuit', 'copper-cable', 'electronic-circuit', 'in-copper-plate', 'in-iron-plate', 'in-plastic-bar', 'out']
  cut[corridor] net electronic-circuit:electronic-circuit-t0 has no belt path from (1, 3) to (9, 1); blocked by ['advanced-circuit', 'copper-cable', 'electronic-circuit', 'in-copper-plate', 'in-iron-plate', 'in-plastic-bar', 'out']
```
