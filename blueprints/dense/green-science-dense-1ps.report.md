# Benders candidate: 1/s logistic-science-pack

**Feasible:** True
**Bounding box:** 44 x 28 = 1232 tiles
**Routing:** 286 belt tiles, 6 undergrounds, 45 turns, converged in 24 round(s)
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
| dense-copper-cable | (8, 2) | 7 x 8 |
| in-copper-plate | (0, 2) | 2 x 1 |
| in-iron-plate | (0, 24) | 7 x 4 |
| inserter | (20, 7) | 3 x 9 |
| iron-gear-wheel | (10, 13) | 5 x 8 |
| logistic-science-pack | (18, 20) | 24 x 8 |
| out | (42, 15) | 2 x 1 |
| transport-belt | (27, 13) | 8 x 3 |

## Coarse routing

11 x 11 cells of 4 tiles; max boundary utilization 0.75

## Iterations

```
iter 0: margin=1 slack=0 bbox=18x28 failed (port_conflict, congestion, congestion, congestion, congestion, no_path, no_path, no_path); +8 cuts
iter 1: margin=1 slack=0.15 bbox=34x17 failed (port_conflict, congestion, congestion, congestion, congestion, no_path, no_path, no_path, no_path, no_path); +10 cuts
iter 2: margin=2 slack=0.15 bbox=23x29 failed (congestion, congestion, congestion); +3 cuts
iter 3: margin=2 slack=0.3 bbox=28x27 failed (congestion); +1 cuts
iter 4: margin=3 slack=0.3 bbox=37x26 failed (congestion, congestion); +2 cuts
iter 5: margin=3 slack=0.5 bbox=44x28 routed; +0 cuts
  cut[pin_access] ports ('transport-belt', 'transport-belt-out-0') and ('inserter', 'iron-plate-in') share access tile (8, 19); they must not coincide
  cut[corridor] net iron-plate:in->dense-copper-cable could not converge; contested corridor near []... involves ['dense-copper-cable', 'in-iron-plate']
  cut[corridor] net inserter:inserter->logistic-science-pack could not converge; contested corridor near []... involves ['inserter', 'logistic-science-pack']
  cut[corridor] net transport-belt:transport-belt->logistic-science-pack could not converge; contested corridor near []... involves ['logistic-science-pack', 'transport-belt']
  cut[corridor] net iron-plate:in->transport-belt could not converge; contested corridor near []... involves ['in-iron-plate', 'transport-belt']
  cut[corridor] net electronic-circuit:dense-copper-cable->inserter has no belt path from (1, 9) to (1, 19); blocked by ['dense-copper-cable', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-gear-wheel:iron-gear-wheel->inserter has no belt path from (2, 15) to (0, 19); blocked by ['dense-copper-cable', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-gear-wheel:iron-gear-wheel->transport-belt has no belt path from (1, 15) to (1, 23); blocked by ['dense-copper-cable', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[pin_access] ports ('out', 'logistic-science-pack-in') and ('dense-copper-cable', 'iron-plate-in') share access tile (31, 9); they must not coincide
  cut[corridor] net inserter:inserter->logistic-science-pack could not converge; contested corridor near []... involves ['inserter', 'logistic-science-pack']
  cut[corridor] net transport-belt:transport-belt->logistic-science-pack could not converge; contested corridor near []... involves ['logistic-science-pack', 'transport-belt']
  cut[corridor] net logistic-science-pack:logistic-science-pack->out could not converge; contested corridor near []... involves ['logistic-science-pack', 'out']
  cut[corridor] net iron-plate:in->transport-belt could not converge; contested corridor near []... involves ['in-iron-plate', 'transport-belt']
  cut[corridor] net iron-plate:in->iron-gear-wheel has no belt path from (7, 6) to (2, 9); blocked by ['dense-copper-cable', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-gear-wheel:iron-gear-wheel->inserter has no belt path from (8, 15) to (21, 8); blocked by ['dense-copper-cable', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-plate:in->inserter has no belt path from (7, 5) to (13, 8); blocked by ['dense-copper-cable', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net electronic-circuit:dense-copper-cable->inserter has no belt path from (23, 10) to (20, 8); blocked by ['dense-copper-cable', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-gear-wheel:iron-gear-wheel->transport-belt has no belt path from (8, 16) to (12, 16); blocked by ['dense-copper-cable', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-gear-wheel:iron-gear-wheel->inserter could not converge; contested corridor near []... involves ['inserter', 'iron-gear-wheel']
  cut[corridor] net iron-gear-wheel:iron-gear-wheel->transport-belt could not converge; contested corridor near []... involves ['iron-gear-wheel', 'transport-belt']
  cut[corridor] net iron-plate:in->transport-belt could not converge; contested corridor near []... involves ['in-iron-plate', 'transport-belt']
  cut[corridor] net iron-gear-wheel:iron-gear-wheel->inserter could not converge; contested corridor near [(12, 18)]... involves ['inserter', 'iron-gear-wheel', 'transport-belt']
  cut[corridor] net transport-belt:transport-belt->logistic-science-pack could not converge; contested corridor near []... involves ['logistic-science-pack', 'transport-belt']
  cut[corridor] net iron-gear-wheel:iron-gear-wheel->transport-belt could not converge; contested corridor near []... involves ['iron-gear-wheel', 'transport-belt']
```
