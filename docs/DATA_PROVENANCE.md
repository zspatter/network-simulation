# Data Provenance

Every external data source the simulation depends on, with citation and retrieval date. Figures
carried in code cite this file; this file is the single place to update when the underlying data
is refreshed.

## Real hospital network

- **Source**: OPTN membership directory,
  <https://www.hrsa.gov/optn/about/membership/optn-membership-database>
- **Snapshot in repo**: `execute/import/optn_membership/optn_membership_2026-07-02.csv`
- **What is used**: rows of type `Transplant Hospital`, `Independent OPO`, `Hospital Based OPO`
  with `membershipStatus = Approved` - the only member types that are physical locations the
  simulation places patients/organs at.
- **Geocoding**: US Census Bureau batch geocoder (no API key), with a rate-limited Nominatim
  (OpenStreetMap) fallback for institutional-campus addresses Census cannot match. The result
  (297 nodes: 245 transplant hospitals, 52 OPOs) is cached at
  `<csv>.network_cache.pkl` so runs don't re-hit the geocoder. See `execute/import_hospitals.py`.

## National calibration figures - OPTN/SRTR 2024 Annual Data Report

Retrieved **2026-07-08** from <https://srtr.hrsa.gov/adr/2024/> (Overview and Deceased Organ
Donation chapters). These pin the arrival, discard, donor, and living-donor constants.

| Figure | Value | Used in |
|---|---|---|
| New waitlist registrations, total | 70,600 | `scenario_report.NATIONAL_WEEKLY_NEW_PATIENTS` |
| New registrations by organ | Kidney 50,481 · Liver 15,395 · Heart 6,068 · Lung 3,822 · Pancreas 1,979¹ · Intestine 128 | `frequencies.US_WAITLIST_ADDITIONS_ORGAN_WEIGHTS` |
| Deceased donors | 16,989 | `scenario_report.NATIONAL_WEEKLY_DECEASED_DONORS` |
| Donor pathway split | DBD 9,705 · DCD 7,284 (~57% / 43%) | `frequencies.DONOR_TYPE_WEIGHTS` (selects the per-pathway donor-quality distribution that drives discard/graft - see [ADR-0010](adr/0010-continuous-donor-quality-index.md)) |
| Living donors | 7,024 | `scenario_report.NATIONAL_WEEKLY_LIVING_DONORS` (~7,000) |
| Deceased-donor transplants | 42,048 | validation target |
| Organ non-use (discard) rate, overall | 20.7% | validation target |
| Non-use by organ | Kidney 29.3% · Pancreas 25.1% · Liver 11.5% · Lung 11.3% · Intestine 4.9% · Heart 1.9% | `acceptance.BASE_DISCARD_PROB` |
| Re-transplant share of listings | Kidney ~9.6% (first-time 90.4% of DDKT), liver 3.4% of candidates; blended ~9% | `retransplant.RETRANSPLANT_SHARE_OF_LISTINGS` (splits first-time vs endogenous relists - see [ADR-0011](adr/0011-retransplant-loop.md)) |
| Standing wait list (point prevalence) | ~103,000 (~86% kidney) | validation target |

¹ Kidney-pancreas (1,667) folded into Pancreas with pancreas-alone/after-kidney (312), since a
one-organ-per-patient model can't represent the dual need.

> **Note on stock vs. flow.** The ADR also reports 167,230 "candidates on the waiting list
> during 2024" - that is a flow-inclusive count (everyone listed at any point), not the standing
> snapshot. The steady-state validation target is the ~103,000 point-prevalence figure.

**Verification history**: the arrival mix and discard rates were originally documented
approximations flagged `VERIFY`. They were replaced with the exact 2024 ADR figures on
2026-07-08 (commit *"Pin arrival mix and discard rates to verified 2024 OPTN/SRTR figures"*).
The prior estimates were close on the arrival mix but off on discard (kidney 20→29%, lung
6→11%, heart 4→2%).

## Other frequency distributions

| Distribution | Source | Notes |
|---|---|---|
| Blood type (US joint letter × Rh) | American Red Cross / Stanford Blood Center | sampled as a joint table, not letter × polarity independently |
| Per-organ donor recovery | transplant literature (per-organ recovery likelihood) | kidney recovered from nearly every donor and yields two |
| Cold-ischemia times / OR durations | published transplant ranges | see [METHODOLOGY.md](METHODOLOGY.md) §2 |
| Post-transplant life-years by organ | documented approximation | relative "benefit served" proxy only, not a survival model |

## Allocation policy references

Geographic-constraint modeling (regions → distance circles → continuous distribution) follows
HRSA/OPTN policy history:

- Removal of DSA/Region from kidney allocation:
  <https://www.hrsa.gov/optn/professionals/resources/kidney-pancreas/kidney-allocation-system/removal-dsa-region-kidney-allocation-policy>
- Continuous distribution overview:
  <https://www.hrsa.gov/optn/policies-bylaws/policy-issues/continuous-distribution>
- Continuous distribution - heart:
  <https://optn.transplant.hrsa.gov/policies-bylaws/a-closer-look/continuous-distribution/continuous-distribution-heart/>
