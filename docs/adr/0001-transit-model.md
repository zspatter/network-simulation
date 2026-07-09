# ADR-0001: Door-to-door transit is `min(ground, air)`

**Date**: 2026-07-08 · **Status**: Accepted

## Context

Transit time gates feasibility (an organ must arrive with cold-ischemia budget to spare) and is
the geographic-cost axis of the whole allocation question. The original model used straight-line
distance fed to a single two-tier speed (ground below 400 km, air above) with **zero logistics
overhead**. That produced two defects: mean transit was ~2.5 h so viability/geography almost
never bound (every strategy tied), and the model was **non-monotonic** - a hospital 401 km away
"arrived" faster than one 399 km away, so the distance circles became donut-shaped.

## Decision

Model door-to-door transit as the faster of two competing modes:

```
ground = handling(0.5 h) + circuity(1.25) × great_circle_km / 105 km·h⁻¹
air    = overhead(2.5 h) + great_circle_km / 750 km·h⁻¹
transit = min(ground, air)
```

Ground carries road circuity and packaging; air carries a multi-hour fixed overhead (both
airport ground legs, taxi/climb/descent, coordination). Because ground has low fixed + high
marginal cost and air the reverse, their min is continuous and **monotonic** in distance.

## Consequences

- Mean transit rises to ~4.8 h; geography now binds thoracic organs (heart/lung reach ~50% of
  hospitals within their 6 h window) but not kidney (30 h reaches all). This is what makes the
  geographic-constraint comparison meaningful.
- The operation buffer had to be recut so short-window organs stay transplantable - see
  [ADR-0002](0002-operation-buffer-is-implant-to-reperfusion.md).
- Values are documented simulation approximations, not routing-grade. The sensitivity analysis
  flags air-overhead as the second-largest lever on lives saved, so it is worth revisiting with
  better data if precision matters.
