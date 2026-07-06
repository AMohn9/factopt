# Benders candidate: 1/s production-science-pack

**Feasible:** True
**Budget:** 900s total, 40s per master solve, 40 iterations max
**Used:** 963s over 14 iteration(s)
**Bounding box:** 26 x 46 = 1196 tiles
**Routing:** 170 belt tiles, 3 undergrounds, 2 splitters, 31 turns, converged in 4 round(s)
**Static validation:** ok

## Rate plan

```
Plan: 1/s production-science-pack using assembling-machine-2
  machines: 26 total
      3 x electric-furnace       (2.22 exact, 0.333 crafts/s)
      2 x iron-stick             (1.67 exact, 2.500 crafts/s)
     10 x production-science-pack (9.33 exact, 0.333 crafts/s)
      7 x productivity-module    (6.67 exact, 0.333 crafts/s)
      4 x rail                   (3.33 exact, 5.000 crafts/s)
  raw inputs:
       3.333/s advanced-circuit
       1.667/s electronic-circuit
       2.500/s iron-plate
       8.333/s steel-plate
       5.000/s stone
       3.333/s stone-brick
```

## Placement

| macro | position | size |
|---|---|---|
| electric-furnace | (1, 12) | 9 x 9 |
| in-advanced-circuit | (0, 23) | 2 x 1 |
| in-electronic-circuit | (0, 43) | 2 x 1 |
| in-iron-plate | (0, 6) | 2 x 1 |
| in-steel-plate | (0, 9) | 2 x 1 |
| in-stone | (0, 2) | 2 x 1 |
| in-stone-brick | (0, 26) | 2 x 1 |
| iron-stick | (18, 1) | 6 x 7 |
| out | (24, 10) | 2 x 1 |
| production-science-pack | (14, 13) | 9 x 30 |
| productivity-module | (4, 23) | 8 x 21 |
| rail | (4, 1) | 12 x 9 |

## Coarse routing

13 x 13 cells of 4 tiles; max boundary utilization 0.50

## Iterations

```
budget: 900s total, 40s/master solve, 40 iteration(s) max; used 963s over 14 iteration(s)
iter 0: margin=1 slack=0 bbox=45x19 failed (port_conflict, port_conflict, no_path, no_path, no_path); +5 cuts [master 33s, route 0.1s]
iter 1: margin=1 slack=0.15 bbox=19x47 failed (port_conflict, port_conflict, no_path, no_path, no_path); +5 cuts [master 59s, route 0.1s]
iter 2: margin=2 slack=0.15 bbox=50x22 failed (no_path, no_path, congestion, congestion); +4 cuts [master 67s, route 0.7s]
iter 3: margin=2 slack=0.3 bbox=25x49 routed; +0 cuts [master 75s, route 0.1s]
iter 4: margin=2 slack=0.3 bbox=34x36 failed (congestion); +1 cuts [master 71s, route 0.4s]
iter 5: margin=2 slack=0.3 bbox=31x37 failed (no_path); +1 cuts [master 75s, route 0.2s]
iter 6: margin=2 slack=0.3 bbox=26x47 failed (no_path, congestion); +2 cuts [master 70s, route 0.0s]
iter 7: margin=2 slack=0.3 bbox=29x42 failed (no_path, congestion); +2 cuts [master 71s, route 0.4s]
iter 8: margin=2 slack=0.3 bbox=25x48 failed (no_path, congestion); +2 cuts [master 75s, route 0.2s]
iter 9: margin=2 slack=0.3 bbox=26x46 failed (no_path, congestion); +2 cuts [master 73s, route 0.3s]
iter 10: margin=2 slack=0.3 bbox=25x48 failed (no_path, no_path); +2 cuts [master 74s, route 0.0s]
iter 11: margin=2 slack=0.3 bbox=25x48 failed (no_path, congestion); +2 cuts [master 73s, route 0.4s]
iter 12: margin=2 slack=0.3 bbox=26x44 failed (no_path, congestion); +2 cuts [master 68s, route 0.1s]
iter 13: margin=2 slack=0.3 bbox=26x46 routed; +0 cuts [master 76s, route 0.0s]
  cut[pin_access] ports ('in-advanced-circuit', 'advanced-circuit-out-0') and ('electric-furnace', 'advanced-circuit-in') share access tile (2, 18); they must not coincide
  cut[pin_access] ports ('in-steel-plate', 'steel-plate-out-0') and ('electric-furnace', 'steel-plate-in') share access tile (2, 11); they must not coincide
  cut[corridor] net production-science-pack:production-science-pack-t0 has no belt path from (43, 17) to (42, 8); blocked by ['electric-furnace', 'in-advanced-circuit', 'in-electronic-circuit', 'in-iron-plate', 'in-steel-plate', 'in-stone', 'in-stone-brick', 'iron-stick', 'out', 'production-science-pack', 'productivity-module', 'rail']
  cut[corridor] net stone:in-stone-t0 has no belt path from (2, 0) to (7, 1); blocked by ['electric-furnace', 'in-advanced-circuit', 'in-electronic-circuit', 'in-iron-plate', 'in-steel-plate', 'in-stone', 'in-stone-brick', 'iron-stick', 'out', 'production-science-pack', 'productivity-module', 'rail']
  cut[corridor] net electronic-circuit:in-electronic-circuit-t0 has no belt path from (2, 15) to (42, 0); blocked by ['electric-furnace', 'in-advanced-circuit', 'in-electronic-circuit', 'in-iron-plate', 'in-steel-plate', 'in-stone', 'in-stone-brick', 'iron-stick', 'out', 'production-science-pack', 'productivity-module', 'rail']
  cut[pin_access] ports ('rail', 'rail-out-0') and ('production-science-pack', 'rail-in') share access tile (17, 32); they must not coincide
  cut[pin_access] ports ('iron-stick', 'iron-plate-in') and ('in-stone-brick', 'stone-brick-out-0') share access tile (2, 38); they must not coincide
  cut[corridor] net production-science-pack:production-science-pack-t0 has no belt path from (11, 32) to (16, 46); blocked by ['electric-furnace', 'in-advanced-circuit', 'in-electronic-circuit', 'in-iron-plate', 'in-steel-plate', 'in-stone', 'in-stone-brick', 'iron-stick', 'out', 'production-science-pack', 'productivity-module', 'rail']
  cut[corridor] net steel-plate:in-steel-plate-t0 has no belt path from (2, 36) to (1, 35); blocked by ['electric-furnace', 'in-advanced-circuit', 'in-electronic-circuit', 'in-iron-plate', 'in-steel-plate', 'in-stone', 'in-stone-brick', 'iron-stick', 'out', 'production-science-pack', 'productivity-module', 'rail']
  cut[corridor] net advanced-circuit:in-advanced-circuit-t0 has no belt path from (2, 24) to (1, 23); blocked by ['electric-furnace', 'in-advanced-circuit', 'in-electronic-circuit', 'in-iron-plate', 'in-steel-plate', 'in-stone', 'in-stone-brick', 'iron-stick', 'out', 'production-science-pack', 'productivity-module', 'rail']
  cut[corridor] net productivity-module:productivity-module-t0 has no belt path from (25, 0) to (17, 18); blocked by ['electric-furnace', 'in-advanced-circuit', 'in-electronic-circuit', 'in-iron-plate', 'in-steel-plate', 'in-stone', 'in-stone-brick', 'iron-stick', 'out', 'production-science-pack', 'productivity-module', 'rail']
  cut[corridor] net steel-plate:in-steel-plate-t0 has no belt path from (2, 10) to (3, 10); blocked by ['electric-furnace', 'in-advanced-circuit', 'in-electronic-circuit', 'in-iron-plate', 'in-steel-plate', 'in-stone', 'in-stone-brick', 'iron-stick', 'out', 'production-science-pack', 'productivity-module', 'rail']
  cut[corridor] net rail:rail-t0 could not converge; contested corridor near [(17, 12)]... involves ['production-science-pack', 'rail']
  cut[corridor] net advanced-circuit:in-advanced-circuit-t0 could not converge; contested corridor near [(25, 5)]... involves ['electric-furnace', 'in-advanced-circuit', 'productivity-module']
  cut[corridor] net advanced-circuit:in-advanced-circuit-t0 could not converge; contested corridor near [(1, 26)]... involves ['electric-furnace', 'in-advanced-circuit', 'productivity-module']
  cut[corridor] net iron-stick:iron-stick-t0 has no belt path from (6, 13) to (3, 0); blocked by ['electric-furnace', 'in-advanced-circuit', 'in-electronic-circuit', 'in-iron-plate', 'in-steel-plate', 'in-stone', 'in-stone-brick', 'iron-stick', 'out', 'production-science-pack', 'productivity-module', 'rail']
  cut[corridor] net steel-plate:in-steel-plate-t0 has no belt path from (2, 10) to (3, 10); blocked by ['electric-furnace', 'in-advanced-circuit', 'in-electronic-circuit', 'in-iron-plate', 'in-steel-plate', 'in-stone', 'in-stone-brick', 'iron-stick', 'out', 'production-science-pack', 'productivity-module', 'rail']
  cut[corridor] net advanced-circuit:in-advanced-circuit-t0 could not converge; contested corridor near [(3, 23), (4, 23), (7, 23)]... involves ['electric-furnace', 'in-advanced-circuit', 'productivity-module']
  cut[corridor] net electronic-circuit:in-electronic-circuit-t0 has no belt path from (2, 40) to (4, 34); blocked by ['electric-furnace', 'in-advanced-circuit', 'in-electronic-circuit', 'in-iron-plate', 'in-steel-plate', 'in-stone', 'in-stone-brick', 'iron-stick', 'out', 'production-science-pack', 'productivity-module', 'rail']
  cut[corridor] net rail:rail-t0 could not converge; contested corridor near [(17, 32)]... involves ['production-science-pack', 'rail']
  cut[corridor] net advanced-circuit:in-advanced-circuit-t0 has no belt path from (2, 37) to (3, 37); blocked by ['electric-furnace', 'in-advanced-circuit', 'in-electronic-circuit', 'in-iron-plate', 'in-steel-plate', 'in-stone', 'in-stone-brick', 'iron-stick', 'out', 'production-science-pack', 'productivity-module', 'rail']
  cut[corridor] net steel-plate:in-steel-plate-t0 could not converge; contested corridor near [(3, 27)]... involves ['in-steel-plate', 'rail']
  cut[corridor] net steel-plate:in-steel-plate-t0 has no belt path from (2, 8) to (3, 8); blocked by ['electric-furnace', 'in-advanced-circuit', 'in-electronic-circuit', 'in-iron-plate', 'in-steel-plate', 'in-stone', 'in-stone-brick', 'iron-stick', 'out', 'production-science-pack', 'productivity-module', 'rail']
  cut[corridor] net advanced-circuit:in-advanced-circuit-t0 could not converge; contested corridor near [(3, 20)]... involves ['electric-furnace', 'in-advanced-circuit']
  cut[corridor] net steel-plate:in-steel-plate-t0 has no belt path from (2, 31) to (3, 30); blocked by ['electric-furnace', 'in-advanced-circuit', 'in-electronic-circuit', 'in-iron-plate', 'in-steel-plate', 'in-stone', 'in-stone-brick', 'iron-stick', 'out', 'production-science-pack', 'productivity-module', 'rail']
  cut[corridor] net advanced-circuit:in-advanced-circuit-t0 has no belt path from (2, 37) to (3, 37); blocked by ['electric-furnace', 'in-advanced-circuit', 'in-electronic-circuit', 'in-iron-plate', 'in-steel-plate', 'in-stone', 'in-stone-brick', 'iron-stick', 'out', 'production-science-pack', 'productivity-module', 'rail']
  cut[corridor] net productivity-module:productivity-module-t0 has no belt path from (13, 24) to (24, 12); blocked by ['electric-furnace', 'in-advanced-circuit', 'in-electronic-circuit', 'in-iron-plate', 'in-steel-plate', 'in-stone', 'in-stone-brick', 'iron-stick', 'out', 'production-science-pack', 'productivity-module', 'rail']
  cut[corridor] net electric-furnace:electric-furnace-t0 could not converge; contested corridor near [(0, 8), (0, 9), (0, 10), (0, 11)]... involves ['electric-furnace', 'in-steel-plate', 'production-science-pack']
  cut[corridor] net advanced-circuit:in-advanced-circuit-t0 has no belt path from (2, 33) to (3, 33); blocked by ['electric-furnace', 'in-advanced-circuit', 'in-electronic-circuit', 'in-iron-plate', 'in-steel-plate', 'in-stone', 'in-stone-brick', 'iron-stick', 'out', 'production-science-pack', 'productivity-module', 'rail']
  cut[corridor] net steel-plate:in-steel-plate-t0 could not converge; contested corridor near [(3, 23)]... involves ['in-steel-plate', 'rail']
```
