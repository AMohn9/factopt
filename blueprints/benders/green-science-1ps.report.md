# Benders candidate: 1/s logistic-science-pack

**Feasible:** True
**Bounding box:** 45 x 45 = 2025 tiles
**Routing:** 346 belt tiles, 9 undergrounds, 55 turns, converged in 24 round(s)
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
| copper-cable | (2, 12) | 3 x 7 |
| electronic-circuit | (10, 30) | 3 x 8 |
| in-copper-plate | (0, 22) | 2 x 1 |
| in-iron-plate | (0, 28) | 7 x 4 |
| inserter | (32, 30) | 3 x 9 |
| iron-gear-wheel | (16, 29) | 5 x 8 |
| logistic-science-pack | (10, 18) | 24 x 8 |
| out | (43, 27) | 2 x 1 |
| transport-belt | (37, 19) | 3 x 8 |

## Coarse routing

12 x 12 cells of 4 tiles; max boundary utilization 0.75

## Iterations

```
iter 0: margin=1 slack=0 bbox=32x17 failed (port_conflict, congestion, congestion, congestion, no_path, no_path, no_path, no_path); +8 cuts
iter 1: margin=1 slack=0.15 bbox=35x19 failed (port_conflict, port_conflict, congestion, congestion, no_path, no_path); +6 cuts
iter 2: margin=2 slack=0.15 bbox=40x19 failed (congestion, congestion, congestion, congestion, congestion); +5 cuts
iter 3: margin=2 slack=0.3 bbox=38x29 failed (congestion, no_path); +2 cuts
iter 4: margin=3 slack=0.3 bbox=45x30 failed (congestion); +1 cuts
iter 5: margin=3 slack=0.5 bbox=44x45 failed (congestion, congestion, congestion); +3 cuts
iter 6: margin=3 slack=0.5 bbox=45x45 failed (congestion); +1 cuts
iter 7: margin=3 slack=0.5 bbox=45x45 failed (congestion, congestion); +2 cuts
iter 8: margin=3 slack=0.5 bbox=44x45 failed (congestion); +1 cuts
iter 9: margin=3 slack=0.5 bbox=45x45 failed (congestion, congestion); +2 cuts
iter 10: margin=3 slack=0.5 bbox=45x45 routed; +0 cuts
  cut[pin_access] ports ('copper-cable', 'copper-plate-in') and ('in-iron-plate', 'iron-plate-out-0') share access tile (7, 0); they must not coincide
  cut[corridor] net electronic-circuit:electronic-circuit->inserter could not converge; contested corridor near []... involves ['electronic-circuit', 'inserter']
  cut[corridor] net transport-belt:transport-belt->logistic-science-pack could not converge; contested corridor near []... involves ['logistic-science-pack', 'transport-belt']
  cut[corridor] net iron-plate:in->transport-belt could not converge; contested corridor near []... involves ['in-iron-plate', 'transport-belt']
  cut[corridor] net iron-plate:in->iron-gear-wheel has no belt path from (7, 2) to (21, 0); blocked by ['copper-cable', 'electronic-circuit', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net copper-plate:in->copper-cable has no belt path from (2, 5) to (7, 0); blocked by ['copper-cable', 'electronic-circuit', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-plate:in->inserter has no belt path from (7, 1) to (1, 16); blocked by ['copper-cable', 'electronic-circuit', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-gear-wheel:iron-gear-wheel->transport-belt has no belt path from (27, 7) to (15, 0); blocked by ['copper-cable', 'electronic-circuit', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[pin_access] ports ('copper-cable', 'copper-cable-out-0') and ('inserter', 'iron-gear-wheel-in') share access tile (7, 10); they must not coincide
  cut[pin_access] ports ('inserter', 'inserter-out-0') and ('electronic-circuit', 'iron-plate-in') share access tile (11, 17); they must not coincide
  cut[corridor] net inserter:inserter->logistic-science-pack could not converge; contested corridor near []... involves ['inserter', 'logistic-science-pack']
  cut[corridor] net iron-plate:in->transport-belt could not converge; contested corridor near []... involves ['in-iron-plate', 'transport-belt']
  cut[corridor] net iron-plate:in->iron-gear-wheel has no belt path from (7, 14) to (16, 11); blocked by ['copper-cable', 'electronic-circuit', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-plate:in->inserter has no belt path from (7, 13) to (7, 18); blocked by ['copper-cable', 'electronic-circuit', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net electronic-circuit:electronic-circuit->inserter could not converge; contested corridor near []... involves ['electronic-circuit', 'inserter']
  cut[corridor] net iron-gear-wheel:iron-gear-wheel->transport-belt could not converge; contested corridor near []... involves ['iron-gear-wheel', 'transport-belt']
  cut[corridor] net iron-plate:in->transport-belt could not converge; contested corridor near []... involves ['in-iron-plate', 'transport-belt']
  cut[corridor] net iron-plate:in->inserter could not converge; contested corridor near [(12, 5)]... involves ['in-iron-plate', 'inserter', 'transport-belt']
  cut[corridor] net iron-gear-wheel:iron-gear-wheel->inserter could not converge; contested corridor near [(8, 9), (8, 10), (9, 9)]... involves ['inserter', 'iron-gear-wheel']
  cut[corridor] net iron-plate:in->inserter could not converge; contested corridor near []... involves ['in-iron-plate', 'inserter']
  cut[corridor] net iron-plate:in->iron-gear-wheel has no belt path from (7, 10) to (25, 9); blocked by ['copper-cable', 'electronic-circuit', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-plate:in->inserter could not converge; contested corridor near [(17, 23), (18, 23), (19, 23)]... involves ['in-iron-plate', 'inserter']
  cut[corridor] net transport-belt:transport-belt->logistic-science-pack could not converge; contested corridor near []... involves ['logistic-science-pack', 'transport-belt']
  cut[corridor] net iron-gear-wheel:iron-gear-wheel->transport-belt could not converge; contested corridor near []... involves ['iron-gear-wheel', 'transport-belt']
  cut[corridor] net iron-plate:in->transport-belt could not converge; contested corridor near []... involves ['in-iron-plate', 'transport-belt']
  cut[corridor] net iron-gear-wheel:iron-gear-wheel->transport-belt could not converge; contested corridor near []... involves ['iron-gear-wheel', 'transport-belt']
  cut[corridor] net iron-plate:in->transport-belt could not converge; contested corridor near []... involves ['in-iron-plate', 'transport-belt']
  cut[corridor] net iron-gear-wheel:iron-gear-wheel->transport-belt could not converge; contested corridor near [(9, 30), (9, 36)]... involves ['iron-gear-wheel', 'transport-belt']
  cut[corridor] net iron-plate:in->transport-belt could not converge; contested corridor near []... involves ['in-iron-plate', 'transport-belt']
  cut[corridor] net iron-gear-wheel:iron-gear-wheel->transport-belt could not converge; contested corridor near []... involves ['iron-gear-wheel', 'transport-belt']
  cut[corridor] net iron-plate:in->transport-belt could not converge; contested corridor near []... involves ['in-iron-plate', 'transport-belt']
```
