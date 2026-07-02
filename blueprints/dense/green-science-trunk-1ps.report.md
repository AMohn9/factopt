# Benders candidate: 1/s logistic-science-pack

**Feasible:** True
**Bounding box:** 22 x 42 = 924 tiles
**Routing:** 151 belt tiles, 5 undergrounds, 39 turns, converged in 4 round(s)
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
| dense-copper-cable | (5, 34) | 7 x 8 |
| in-copper-plate | (0, 38) | 2 x 1 |
| in-iron-plate | (0, 34) | 2 x 1 |
| inserter | (16, 33) | 3 x 9 |
| iron-gear-wheel | (1, 28) | 7 x 3 |
| logistic-science-pack | (14, 5) | 8 x 24 |
| out | (20, 1) | 2 x 1 |
| transport-belt | (8, 17) | 3 x 8 |

## Coarse routing

11 x 11 cells of 4 tiles; max boundary utilization 1.00

## Iterations

```
iter 0: margin=1 slack=0 bbox=28x17 failed (port_conflict, congestion, congestion, no_path, no_path, no_path, congestion); +7 cuts
iter 1: margin=1 slack=0.15 bbox=19x28 failed (congestion, no_path, congestion); +3 cuts
iter 2: margin=2 slack=0.15 bbox=18x34 failed (congestion); +1 cuts
iter 3: margin=2 slack=0.3 bbox=18x36 failed (congestion, congestion); +2 cuts
iter 4: margin=3 slack=0.3 bbox=22x42 routed; +0 cuts
  cut[pin_access] ports ('iron-gear-wheel', 'iron-gear-wheel-out-0') and ('dense-copper-cable', 'iron-plate-in') share access tile (6, 16); they must not coincide
  cut[corridor] net inserter:inserter->logistic-science-pack could not converge; contested corridor near []... involves ['inserter', 'logistic-science-pack']
  cut[corridor] net transport-belt:transport-belt->logistic-science-pack could not converge; contested corridor near []... involves ['logistic-science-pack', 'transport-belt']
  cut[corridor] net iron-gear-wheel:iron-gear-wheel->inserter has no belt path from (6, 16) to (19, 15); blocked by ['dense-copper-cable', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-plate:dense-copper-cable->inserter has no belt path from (14, 16) to (27, 15); blocked by ['dense-copper-cable', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net electronic-circuit:dense-copper-cable->inserter has no belt path from (14, 15) to (20, 15); blocked by ['dense-copper-cable', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net copper-plate:in-copper-plate->dense-copper-cable could not converge; contested corridor near [(0, 7), (0, 8)]... involves ['dense-copper-cable', 'in-copper-plate']
  cut[corridor] net copper-plate:in-copper-plate->dense-copper-cable could not converge; contested corridor near []... involves ['dense-copper-cable', 'in-copper-plate']
  cut[corridor] net electronic-circuit:dense-copper-cable->inserter has no belt path from (9, 9) to (8, 15); blocked by ['dense-copper-cable', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-plate:dense-copper-cable->inserter could not converge; contested corridor near [(0, 18), (0, 19), (0, 20), (0, 21)]... involves ['dense-copper-cable', 'inserter']
  cut[corridor] net transport-belt:transport-belt->logistic-science-pack could not converge; contested corridor near [(9, 27)]... involves ['logistic-science-pack', 'transport-belt']
  cut[corridor] net electronic-circuit:dense-copper-cable->inserter could not converge; contested corridor near []... involves ['dense-copper-cable', 'inserter']
  cut[corridor] net transport-belt:transport-belt->logistic-science-pack could not converge; contested corridor near [(17, 3)]... involves ['logistic-science-pack', 'transport-belt']
```
