# Benders candidate: 1/s logistic-science-pack

**Feasible:** True
**Bounding box:** 25 x 31 = 775 tiles
**Routing:** 173 belt tiles, 5 undergrounds, 38 turns, converged in 7 round(s)
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
| dense-copper-cable | (0, 8) | 8 x 7 |
| in-copper-plate | (0, 18) | 2 x 1 |
| in-iron-plate | (0, 22) | 2 x 1 |
| inserter | (5, 2) | 9 x 3 |
| iron-gear-wheel | (5, 20) | 7 x 3 |
| logistic-science-pack | (17, 3) | 8 x 24 |
| out | (23, 30) | 2 x 1 |
| transport-belt | (11, 9) | 3 x 8 |

## Coarse routing

11 x 11 cells of 4 tiles; max boundary utilization 0.75

## Iterations

```
iter 0: margin=1 slack=0 bbox=28x17 failed (port_conflict, congestion, congestion, no_path, no_path, no_path, congestion); +7 cuts
iter 1: margin=1 slack=0.15 bbox=19x28 failed (port_conflict, port_conflict, congestion, congestion); +4 cuts
iter 2: margin=2 slack=0.15 bbox=28x22 failed (congestion, congestion); +2 cuts
iter 3: margin=2 slack=0.3 bbox=30x23 failed (congestion); +1 cuts
iter 4: margin=3 slack=0.3 bbox=25x31 routed; +0 cuts
  cut[pin_access] ports ('iron-gear-wheel', 'iron-gear-wheel-out-0') and ('dense-copper-cable', 'iron-plate-in') share access tile (6, 16); they must not coincide
  cut[corridor] net inserter:inserter->logistic-science-pack could not converge; contested corridor near []... involves ['inserter', 'logistic-science-pack']
  cut[corridor] net transport-belt:transport-belt->logistic-science-pack could not converge; contested corridor near []... involves ['logistic-science-pack', 'transport-belt']
  cut[corridor] net iron-gear-wheel:iron-gear-wheel->inserter has no belt path from (6, 16) to (19, 15); blocked by ['dense-copper-cable', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-plate:dense-copper-cable->inserter has no belt path from (14, 16) to (27, 15); blocked by ['dense-copper-cable', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net electronic-circuit:dense-copper-cable->inserter has no belt path from (14, 15) to (20, 15); blocked by ['dense-copper-cable', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net copper-plate:in-copper-plate->dense-copper-cable could not converge; contested corridor near [(0, 7), (0, 8)]... involves ['dense-copper-cable', 'in-copper-plate']
  cut[pin_access] ports ('inserter', 'electronic-circuit-in') and ('transport-belt', 'iron-gear-wheel-thru') share access tile (8, 19); they must not coincide
  cut[pin_access] ports ('inserter', 'iron-plate-in') and ('transport-belt', 'transport-belt-out-0') share access tile (1, 19); they must not coincide
  cut[corridor] net iron-gear-wheel:iron-gear-wheel->transport-belt could not converge; contested corridor near []... involves ['iron-gear-wheel', 'transport-belt']
  cut[corridor] net electronic-circuit:dense-copper-cable->inserter could not converge; contested corridor near []... involves ['dense-copper-cable', 'inserter']
  cut[corridor] net electronic-circuit:dense-copper-cable->inserter could not converge; contested corridor near []... involves ['dense-copper-cable', 'inserter']
  cut[corridor] net iron-plate:dense-copper-cable->transport-belt could not converge; contested corridor near [(9, 8)]... involves ['dense-copper-cable', 'transport-belt']
  cut[corridor] net inserter:inserter->logistic-science-pack could not converge; contested corridor near [(1, 16)]... involves ['inserter', 'logistic-science-pack']
```
