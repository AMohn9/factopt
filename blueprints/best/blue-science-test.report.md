# Benders candidate: 1/s chemical-science-pack

**Feasible:** True
**Budget:** 900s total, 60s per master solve, 40 iterations max
**Used:** 757s over 7 iteration(s)
**Bounding box:** 70 x 35 = 2450 tiles
**Routing:** 293 belt tiles, 11 undergrounds, 3 splitters, 43 turns, converged in 24 round(s)
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
| advanced-circuit | (26, 0) | 36 x 9 |
| chemical-science-pack | (18, 26) | 48 x 9 |
| copper-cable | (7, 10) | 7 x 15 |
| electronic-circuit | (16, 2) | 8 x 6 |
| engine-unit | (25, 11) | 42 x 9 |
| in-copper-plate | (0, 24) | 2 x 1 |
| in-iron-plate | (0, 12) | 2 x 1 |
| in-plastic-bar | (0, 0) | 2 x 1 |
| in-steel-plate | (0, 19) | 2 x 1 |
| in-sulfur | (0, 34) | 2 x 1 |
| iron-gear-wheel | (2, 3) | 3 x 7 |
| out | (68, 27) | 2 x 1 |
| pipe | (16, 16) | 6 x 7 |

## Coarse routing

18 x 18 cells of 4 tiles; max boundary utilization 0.75

## Iterations

```
budget: 900s total, 60s/master solve, 40 iteration(s) max; used 757s over 7 iteration(s)
iter 0: margin=1 slack=0 bbox=60x65 failed (port_conflict, no_path, no_path, no_path, no_path, no_path, no_path, no_path); +8 cuts [master 123s, route 8.9s]
iter 1: margin=1 slack=0.15 bbox=65x65 failed (port_conflict, port_conflict); +2 cuts [master 123s, route 1.4s]
iter 2: margin=2 slack=0.15 bbox=49x55 failed (no_path, no_path, congestion, congestion); +4 cuts [master 123s, route 4.8s]
iter 3: margin=2 slack=0.3 bbox=70x35 routed; +0 cuts [master 123s, route 1.3s]
iter 4: margin=2 slack=0.3 bbox=0x0 unsolved; +0 cuts [master 62s, route 0.0s]
iter 5: margin=1 slack=0.3 bbox=52x44 failed (no_path, no_path, no_path, no_path, congestion); +5 cuts [master 122s, route 3.1s]
iter 6: margin=1 slack=0.3 bbox=0x0 unsolved; +0 cuts [master 62s, route 0.0s]
  cut[pin_access] ports ('chemical-science-pack', 'chemical-science-pack-out-0') and ('out', 'chemical-science-pack-in') share access tile (57, 53); they must not coincide
  cut[corridor] net electronic-circuit:electronic-circuit-t0 has no belt path from (1, 46) to (8, 38); blocked by ['advanced-circuit', 'chemical-science-pack', 'copper-cable', 'electronic-circuit', 'engine-unit', 'in-copper-plate', 'in-iron-plate', 'in-plastic-bar', 'in-steel-plate', 'in-sulfur', 'iron-gear-wheel', 'out', 'pipe']
  cut[corridor] net advanced-circuit:advanced-circuit-t0 has no belt path from (1, 38) to (8, 47); blocked by ['advanced-circuit', 'chemical-science-pack', 'copper-cable', 'electronic-circuit', 'engine-unit', 'in-copper-plate', 'in-iron-plate', 'in-plastic-bar', 'in-steel-plate', 'in-sulfur', 'iron-gear-wheel', 'out', 'pipe']
  cut[corridor] net engine-unit:engine-unit-t0 has no belt path from (1, 57) to (8, 46); blocked by ['advanced-circuit', 'chemical-science-pack', 'copper-cable', 'electronic-circuit', 'engine-unit', 'in-copper-plate', 'in-iron-plate', 'in-plastic-bar', 'in-steel-plate', 'in-sulfur', 'iron-gear-wheel', 'out', 'pipe']
  cut[corridor] net steel-plate:in-steel-plate-t0 has no belt path from (2, 54) to (1, 64); blocked by ['advanced-circuit', 'chemical-science-pack', 'copper-cable', 'electronic-circuit', 'engine-unit', 'in-copper-plate', 'in-iron-plate', 'in-plastic-bar', 'in-steel-plate', 'in-sulfur', 'iron-gear-wheel', 'out', 'pipe']
  cut[corridor] net iron-gear-wheel:iron-gear-wheel-t0 has no belt path from (7, 54) to (1, 56); blocked by ['advanced-circuit', 'chemical-science-pack', 'copper-cable', 'electronic-circuit', 'engine-unit', 'in-copper-plate', 'in-iron-plate', 'in-plastic-bar', 'in-steel-plate', 'in-sulfur', 'iron-gear-wheel', 'out', 'pipe']
  cut[corridor] net copper-cable:copper-cable-t0 has no belt path from (23, 38) to (7, 38); blocked by ['advanced-circuit', 'chemical-science-pack', 'copper-cable', 'electronic-circuit', 'engine-unit', 'in-copper-plate', 'in-iron-plate', 'in-plastic-bar', 'in-steel-plate', 'in-sulfur', 'iron-gear-wheel', 'out', 'pipe']
  cut[corridor] net iron-plate:in-iron-plate-t0 has no belt path from (2, 49) to (0, 46); blocked by ['advanced-circuit', 'chemical-science-pack', 'copper-cable', 'electronic-circuit', 'engine-unit', 'in-copper-plate', 'in-iron-plate', 'in-plastic-bar', 'in-steel-plate', 'in-sulfur', 'iron-gear-wheel', 'out', 'pipe']
  cut[pin_access] ports ('in-copper-plate', 'copper-plate-out-0') and ('copper-cable', 'copper-plate-in') share access tile (2, 40); they must not coincide
  cut[pin_access] ports ('in-plastic-bar', 'plastic-bar-out-0') and ('advanced-circuit', 'plastic-bar-in') share access tile (2, 32); they must not coincide
  cut[corridor] net electronic-circuit:electronic-circuit-t0 has no belt path from (10, 35) to (1, 46); blocked by ['advanced-circuit', 'chemical-science-pack', 'copper-cable', 'electronic-circuit', 'engine-unit', 'in-copper-plate', 'in-iron-plate', 'in-plastic-bar', 'in-steel-plate', 'in-sulfur', 'iron-gear-wheel', 'out', 'pipe']
  cut[corridor] net sulfur:in-sulfur-t0 has no belt path from (2, 5) to (48, 2); blocked by ['advanced-circuit', 'chemical-science-pack', 'copper-cable', 'electronic-circuit', 'engine-unit', 'in-copper-plate', 'in-iron-plate', 'in-plastic-bar', 'in-steel-plate', 'in-sulfur', 'iron-gear-wheel', 'out', 'pipe']
  cut[corridor] net copper-cable:copper-cable-t0 could not converge; contested corridor near [(1, 48)]... involves ['advanced-circuit', 'copper-cable', 'electronic-circuit']
  cut[corridor] net pipe:pipe-t0 could not converge; contested corridor near [(23, 1)]... involves ['engine-unit', 'pipe']
  cut[corridor] net advanced-circuit:advanced-circuit-t0 has no belt path from (49, 20) to (50, 36); blocked by ['advanced-circuit', 'chemical-science-pack', 'copper-cable', 'electronic-circuit', 'engine-unit', 'in-copper-plate', 'in-iron-plate', 'in-plastic-bar', 'in-steel-plate', 'in-sulfur', 'iron-gear-wheel', 'out', 'pipe']
  cut[corridor] net iron-gear-wheel:iron-gear-wheel-t0 has no belt path from (0, 5) to (7, 33); blocked by ['advanced-circuit', 'chemical-science-pack', 'copper-cable', 'electronic-circuit', 'engine-unit', 'in-copper-plate', 'in-iron-plate', 'in-plastic-bar', 'in-steel-plate', 'in-sulfur', 'iron-gear-wheel', 'out', 'pipe']
  cut[corridor] net steel-plate:in-steel-plate-t0 has no belt path from (2, 29) to (7, 25); blocked by ['advanced-circuit', 'chemical-science-pack', 'copper-cable', 'electronic-circuit', 'engine-unit', 'in-copper-plate', 'in-iron-plate', 'in-plastic-bar', 'in-steel-plate', 'in-sulfur', 'iron-gear-wheel', 'out', 'pipe']
  cut[corridor] net engine-unit:engine-unit-t0 has no belt path from (50, 32) to (50, 35); blocked by ['advanced-circuit', 'chemical-science-pack', 'copper-cable', 'electronic-circuit', 'engine-unit', 'in-copper-plate', 'in-iron-plate', 'in-plastic-bar', 'in-steel-plate', 'in-sulfur', 'iron-gear-wheel', 'out', 'pipe']
  cut[corridor] net pipe:pipe-t0 could not converge; contested corridor near [(30, 2)]... involves ['engine-unit', 'pipe']
```
