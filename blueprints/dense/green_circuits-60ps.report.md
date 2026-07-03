# Benders candidate: 20/s electronic-circuit

**Feasible:** True
**Budget:** 120s total, 10s per master solve, 40 iterations max
**Used:** 22s over 7 iteration(s)
**Bounding box:** 64 x 17 = 1088 tiles
**Routing:** 35 belt tiles, 0 undergrounds, 0 splitters, 4 turns, converged in 1 round(s)
**Static validation:** ok

## Rate plan

```
Plan: 20/s electronic-circuit using assembling-machine-2
  machines: 34 total
     20 x copper-cable           (20.00 exact, 30.000 crafts/s)
     14 x electronic-circuit     (13.33 exact, 20.000 crafts/s)
  raw inputs:
      30.000/s copper-plate
      20.000/s iron-plate
```

## Placement

| macro | position | size |
|---|---|---|
| copper-cable | (2, 0) | 60 x 7 |
| electronic-circuit | (18, 9) | 42 x 8 |
| in-copper-plate | (0, 9) | 2 x 1 |
| in-iron-plate | (0, 16) | 2 x 1 |
| out | (62, 15) | 2 x 1 |

## Coarse routing

16 x 16 cells of 4 tiles; max boundary utilization 0.50

## Iterations

```
budget: 120s total, 10s/master solve, 40 iteration(s) max; used 22s over 7 iteration(s)
iter 0: margin=1 slack=0 bbox=0x0 unsolved; +0 cuts [master 0s, route 0.0s]
iter 1: margin=1 slack=0.15 bbox=0x0 unsolved; +0 cuts [master 0s, route 0.0s]
iter 2: margin=2 slack=0.15 bbox=64x19 routed; +0 cuts [master 12s, route 0.0s]
iter 3: margin=2 slack=0.15 bbox=64x18 routed; +0 cuts [master 4s, route 0.0s]
iter 4: margin=2 slack=0.15 bbox=64x17 routed; +0 cuts [master 4s, route 0.0s]
iter 5: margin=2 slack=0.15 bbox=0x0 unsolved; +0 cuts [master 1s, route 0.0s]
iter 6: margin=1 slack=0.15 bbox=0x0 unsolved; +0 cuts [master 0s, route 0.0s]
```
