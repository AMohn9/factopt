# Benders candidate: 1/s chemical-science-pack

**Feasible:** True
**Budget:** 900s total, 60s per master solve, 40 iterations max
**Used:** 969s over 8 iteration(s)
**Bounding box:** 74 x 75 = 5550 tiles
**Routing:** 534 belt tiles, 9 undergrounds, 3 splitters, 64 turns, converged in 24 round(s)
**Static validation:** ok

## Rate plan

```
Plan: 1/s chemical-science-pack using assembling-machine-2
  machines: 52 total
     12 x advanced-circuit       (12.00 exact, 1.500 crafts/s)
     16 x chemical-science-pack  (16.00 exact, 0.500 crafts/s)
      5 x copper-cable           (5.00 exact, 7.500 crafts/s)
      2 x electronic-circuit     (2.00 exact, 3.000 crafts/s)
     14 x engine-unit            (13.33 exact, 1.000 crafts/s)
      1 x iron-gear-wheel        (0.67 exact, 1.000 crafts/s)
      2 x pipe                   (1.33 exact, 2.000 crafts/s)
  raw inputs:
       7.500/s copper-plate
       7.000/s iron-plate
       3.000/s plastic-bar
       1.000/s steel-plate
       0.500/s sulfur
```

## Placement

| macro | position | size |
|---|---|---|
| advanced-circuit | (2, 54) | 36 x 9 |
| chemical-science-pack | (24, 13) | 48 x 9 |
| copper-cable | (44, 42) | 7 x 15 |
| electronic-circuit | (33, 43) | 6 x 8 |
| engine-unit | (12, 9) | 9 x 42 |
| in-copper-plate | (0, 42) | 2 x 1 |
| in-iron-plate | (0, 72) | 2 x 1 |
| in-plastic-bar | (0, 66) | 2 x 1 |
| in-steel-plate | (0, 9) | 2 x 1 |
| in-sulfur | (0, 21) | 2 x 1 |
| iron-gear-wheel | (17, 68) | 3 x 7 |
| out | (72, 9) | 2 x 1 |
| pipe | (41, 64) | 6 x 7 |

## Coarse routing

19 x 19 cells of 4 tiles; max boundary utilization 0.75

## Iterations

```
budget: 900s total, 60s/master solve, 40 iteration(s) max; used 969s over 8 iteration(s)
iter 0: margin=1 slack=0 bbox=61x65 failed (no_path, no_path, no_path, no_path); +4 cuts [master 121s, route 21.6s]
iter 1: margin=1 slack=0.15 bbox=65x65 failed (no_path, no_path); +2 cuts [master 121s, route 6.6s]
iter 2: margin=2 slack=0.15 bbox=61x61 failed (no_path); +1 cuts [master 121s, route 3.1s]
iter 3: margin=2 slack=0.3 bbox=70x53 failed (no_path, no_path); +2 cuts [master 121s, route 6.4s]
iter 4: margin=3 slack=0.3 bbox=74x75 routed; +0 cuts [master 122s, route 8.8s]
iter 5: margin=3 slack=0.3 bbox=0x0 unsolved; +0 cuts [master 61s, route 0.0s]
iter 6: margin=2 slack=0.3 bbox=70x65 failed (congestion); +1 cuts [master 122s, route 4.8s]
iter 7: margin=2 slack=0.3 bbox=70x65 failed (no_path, no_path, congestion); +3 cuts [master 121s, route 5.8s]
  cut[corridor] net advanced-circuit:advanced-circuit-t0 has no belt path from (59, 23) to (43, 60); blocked by ['advanced-circuit', 'chemical-science-pack', 'copper-cable', 'electronic-circuit', 'engine-unit', 'in-copper-plate', 'in-iron-plate', 'in-plastic-bar', 'in-steel-plate', 'in-sulfur', 'iron-gear-wheel', 'out', 'pipe']
  cut[corridor] net chemical-science-pack:chemical-science-pack-t0 has no belt path from (49, 11) to (58, 64); blocked by ['advanced-circuit', 'chemical-science-pack', 'copper-cable', 'electronic-circuit', 'engine-unit', 'in-copper-plate', 'in-iron-plate', 'in-plastic-bar', 'in-steel-plate', 'in-sulfur', 'iron-gear-wheel', 'out', 'pipe']
  cut[corridor] net sulfur:in-sulfur-t0 has no belt path from (2, 55) to (50, 60); blocked by ['advanced-circuit', 'chemical-science-pack', 'copper-cable', 'electronic-circuit', 'engine-unit', 'in-copper-plate', 'in-iron-plate', 'in-plastic-bar', 'in-steel-plate', 'in-sulfur', 'iron-gear-wheel', 'out', 'pipe']
  cut[corridor] net iron-plate:in-iron-plate-t0 has no belt path from (2, 57) to (4, 58); blocked by ['advanced-circuit', 'chemical-science-pack', 'copper-cable', 'electronic-circuit', 'engine-unit', 'in-copper-plate', 'in-iron-plate', 'in-plastic-bar', 'in-steel-plate', 'in-sulfur', 'iron-gear-wheel', 'out', 'pipe']
  cut[corridor] net iron-gear-wheel:iron-gear-wheel-t0 has no belt path from (15, 59) to (25, 63); blocked by ['advanced-circuit', 'chemical-science-pack', 'copper-cable', 'electronic-circuit', 'engine-unit', 'in-copper-plate', 'in-iron-plate', 'in-plastic-bar', 'in-steel-plate', 'in-sulfur', 'iron-gear-wheel', 'out', 'pipe']
  cut[corridor] net iron-plate:in-iron-plate-t0 has no belt path from (2, 60) to (9, 59); blocked by ['advanced-circuit', 'chemical-science-pack', 'copper-cable', 'electronic-circuit', 'engine-unit', 'in-copper-plate', 'in-iron-plate', 'in-plastic-bar', 'in-steel-plate', 'in-sulfur', 'iron-gear-wheel', 'out', 'pipe']
  cut[corridor] net engine-unit:engine-unit-t0 has no belt path from (1, 49) to (48, 50); blocked by ['advanced-circuit', 'chemical-science-pack', 'copper-cable', 'electronic-circuit', 'engine-unit', 'in-copper-plate', 'in-iron-plate', 'in-plastic-bar', 'in-steel-plate', 'in-sulfur', 'iron-gear-wheel', 'out', 'pipe']
  cut[corridor] net steel-plate:in-steel-plate-t0 has no belt path from (2, 5) to (1, 11); blocked by ['advanced-circuit', 'chemical-science-pack', 'copper-cable', 'electronic-circuit', 'engine-unit', 'in-copper-plate', 'in-iron-plate', 'in-plastic-bar', 'in-steel-plate', 'in-sulfur', 'iron-gear-wheel', 'out', 'pipe']
  cut[corridor] net sulfur:in-sulfur-t0 has no belt path from (2, 2) to (19, 8); blocked by ['advanced-circuit', 'chemical-science-pack', 'copper-cable', 'electronic-circuit', 'engine-unit', 'in-copper-plate', 'in-iron-plate', 'in-plastic-bar', 'in-steel-plate', 'in-sulfur', 'iron-gear-wheel', 'out', 'pipe']
  cut[corridor] net copper-cable:copper-cable-t0 could not converge; contested corridor near [(11, 7)]... involves ['advanced-circuit', 'copper-cable', 'electronic-circuit']
  cut[corridor] net electronic-circuit:electronic-circuit-t0 has no belt path from (1, 51) to (8, 38); blocked by ['advanced-circuit', 'chemical-science-pack', 'copper-cable', 'electronic-circuit', 'engine-unit', 'in-copper-plate', 'in-iron-plate', 'in-plastic-bar', 'in-steel-plate', 'in-sulfur', 'iron-gear-wheel', 'out', 'pipe']
  cut[corridor] net sulfur:in-sulfur-t0 has no belt path from (2, 59) to (19, 30); blocked by ['advanced-circuit', 'chemical-science-pack', 'copper-cable', 'electronic-circuit', 'engine-unit', 'in-copper-plate', 'in-iron-plate', 'in-plastic-bar', 'in-steel-plate', 'in-sulfur', 'iron-gear-wheel', 'out', 'pipe']
  cut[corridor] net engine-unit:engine-unit-t0 could not converge; contested corridor near [(24, 44)]... involves ['chemical-science-pack', 'engine-unit']
```
