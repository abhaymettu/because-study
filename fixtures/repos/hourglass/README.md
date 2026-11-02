# hourglass

Parse time ranges, merge the overlapping ones, and work with weekly shift
schedules. It is plain Python with no dependencies, written for the small jobs
that come up around rotas and opening hours.

Times are stored as minutes since midnight and a span stays within one day, so
an overnight shift is written as two shifts. Schedules are CSV files with
`worker`, `day` and `span` columns.

## Install

```
pip install .
```

## Quick usage

```python
from hourglass import day_coverage, format_span, load_schedule, worker_minutes

shifts = load_schedule("rota.csv")

for span in day_coverage(shifts, "Monday"):
    print(format_span(span))

print(worker_minutes(shifts))
```

For a rota with an overlap around lunch this prints something like

```
09:00-17:00
{'Brisa': 540, 'Odell': 390, 'Quill': 450}
```
