# Benders candidate: 1/s logistic-science-pack

**Feasible:** True
**Bounding box:** 30 x 45 = 1350 tiles
**Routing:** 335 belt tiles, 11 undergrounds, 60 turns, converged in 24 round(s)
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
| copper-cable | (1, 5) | 7 x 3 |
| electronic-circuit | (0, 18) | 8 x 3 |
| in-copper-plate | (0, 1) | 2 x 1 |
| in-iron-plate | (0, 27) | 7 x 4 |
| inserter | (11, 21) | 9 x 3 |
| iron-gear-wheel | (13, 10) | 8 x 5 |
| logistic-science-pack | (4, 37) | 24 x 8 |
| out | (28, 19) | 2 x 1 |
| transport-belt | (0, 12) | 8 x 3 |

## Coarse routing

12 x 12 cells of 4 tiles; max boundary utilization 0.75

## Iterations

```
iter 0: margin=1 slack=0 bbox=18x28 failed (port_conflict, congestion, congestion, congestion, congestion, no_path, no_path, no_path, congestion); +9 cuts
iter 1: margin=1 slack=0.15 bbox=16x35 failed (congestion, congestion, no_path, no_path, no_path, congestion, congestion); +7 cuts
iter 2: margin=2 slack=0.15 bbox=40x19 failed (congestion, congestion, congestion, congestion); +4 cuts
iter 3: margin=2 slack=0.3 bbox=22x40 failed (congestion, congestion); +2 cuts
iter 4: margin=3 slack=0.3 bbox=30x45 routed; +0 cuts
  cut[pin_access] ports ('transport-belt', 'transport-belt-out-0') and ('inserter', 'iron-plate-in') share access tile (8, 19); they must not coincide
  cut[corridor] net iron-plate:in->electronic-circuit could not converge; contested corridor near []... involves ['electronic-circuit', 'in-iron-plate']
  cut[corridor] net inserter:inserter->logistic-science-pack could not converge; contested corridor near []... involves ['inserter', 'logistic-science-pack']
  cut[corridor] net transport-belt:transport-belt->logistic-science-pack could not converge; contested corridor near []... involves ['logistic-science-pack', 'transport-belt']
  cut[corridor] net iron-plate:in->transport-belt could not converge; contested corridor near []... involves ['in-iron-plate', 'transport-belt']
  cut[corridor] net copper-plate:in->copper-cable has no belt path from (2, 0) to (2, 5); blocked by ['copper-cable', 'electronic-circuit', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net electronic-circuit:electronic-circuit->inserter has no belt path from (2, 9) to (1, 19); blocked by ['copper-cable', 'electronic-circuit', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-gear-wheel:iron-gear-wheel->inserter has no belt path from (2, 15) to (0, 19); blocked by ['copper-cable', 'electronic-circuit', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-gear-wheel:iron-gear-wheel->transport-belt could not converge; contested corridor near [(0, 4), (0, 5), (0, 6), (0, 7)]... involves ['electronic-circuit', 'inserter', 'iron-gear-wheel', 'transport-belt']
  cut[corridor] net iron-plate:in->inserter could not converge; contested corridor near []... involves ['in-iron-plate', 'inserter']
  cut[corridor] net iron-gear-wheel:iron-gear-wheel->transport-belt could not converge; contested corridor near []... involves ['iron-gear-wheel', 'transport-belt']
  cut[corridor] net iron-plate:in->electronic-circuit has no belt path from (7, 0) to (12, 19); blocked by ['copper-cable', 'electronic-circuit', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net inserter:inserter->logistic-science-pack has no belt path from (8, 10) to (6, 8); blocked by ['copper-cable', 'electronic-circuit', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net iron-plate:in->transport-belt has no belt path from (7, 3) to (6, 4); blocked by ['copper-cable', 'electronic-circuit', 'in-copper-plate', 'in-iron-plate', 'inserter', 'iron-gear-wheel', 'logistic-science-pack', 'out', 'transport-belt']
  cut[corridor] net copper-plate:in->copper-cable could not converge; contested corridor near [(12, 34), (13, 34), (14, 34)]... involves ['copper-cable', 'in-copper-plate']
  cut[corridor] net transport-belt:transport-belt->logistic-science-pack could not converge; contested corridor near [(10, 8), (11, 8), (12, 8), (13, 8)]... involves ['inserter', 'iron-gear-wheel', 'logistic-science-pack', 'transport-belt']
  cut[corridor] net copper-plate:in->copper-cable could not converge; contested corridor near []... involves ['copper-cable', 'in-copper-plate']
  cut[corridor] net iron-plate:in->inserter could not converge; contested corridor near []... involves ['in-iron-plate', 'inserter']
  cut[corridor] net iron-plate:in->transport-belt could not converge; contested corridor near []... involves ['in-iron-plate', 'transport-belt']
  cut[corridor] net iron-plate:in->electronic-circuit could not converge; contested corridor near [(8, 8)]... involves ['electronic-circuit', 'in-iron-plate']
  cut[corridor] net iron-plate:in->electronic-circuit could not converge; contested corridor near []... involves ['electronic-circuit', 'in-iron-plate']
  cut[corridor] net electronic-circuit:electronic-circuit->inserter could not converge; contested corridor near [(11, 23)]... involves ['electronic-circuit', 'inserter', 'transport-belt']
```
