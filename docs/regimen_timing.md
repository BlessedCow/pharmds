# Regimen timing model

PharmDS keeps regimen timing separate from dose amount. A frequency code is
normalized into timing semantics only when its meaning is sufficiently clear.
Unknown values are preserved as custom text rather than guessed.

## Timing categories

- `daypart`: QAM, QPM, QHS/HS
- `daily_count`: QD/daily, BID, TID, QID
- `fixed_interval`: Q2H, Q3H, Q4H, Q5H, Q6H, Q8H, Q12H, Q24H, Q48H,
  and other `Q<number>H` values
- `weekly`: QWK/weekly, TIW
- `calendar_interval`: QOD, QMONTH
- `meal_relative`: AC/QAC, PC/QPC
- `custom`: preserved input that is not safely normalized

`BIW` is deliberately preserved as an ambiguous custom frequency because it
can be interpreted inconsistently.

## Important distinctions

`TID` and `Q8H` both commonly result in three administrations in a day, but
PharmDS does not treat them as the same schedule. TID is a daily-count
schedule. Q8H is a fixed eight-hour interval.

Likewise, QAM and QHS both have one administration per day while preserving
different dayparts (`morning` and `bedtime`). This allows future deterministic
PK/PD timing rules to reason about overlap without reducing both regimens to
`1/day`.

PRN fixed-interval orders are not treated as actual around-the-clock exposure.
For example, `2 mg Q4H PRN` can expose a maximum permitted administration
ceiling, but PharmDS does not assume that the patient actually takes 12 mg/day.

Weekly and calendar schedules are not converted into artificial average daily
doses.

## Deterministic rule guards

Dose-aware rules may optionally constrain:

- `schedule_type`: scheduled or PRN
- `frequency_code`
- `timing_type`
- `daypart`
- `interval_hours`
- `around_the_clock`
- minimum dose per administration
- minimum scheduled daily dose
- minimum PRN maximum daily dose

No current interaction rule is automatically changed merely because regimen
metadata is present. Dose/timing behavior must be explicitly curated into a
rule.
