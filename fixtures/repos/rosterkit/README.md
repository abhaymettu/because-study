# rosterkit

A small library for reading class roster CSV files and turning attendance
sheets into summaries a teacher can actually use. It runs on the Python
standard library and has no dependencies.

Rosters need `id`, `last_name`, `first_name` and `section` columns, with an
optional `email`. Attendance files need `student_id`, `date` and `status`.
Status codes can be full words or the usual single letters.

## Install

```
pip install .
```

## Quick usage

```python
from rosterkit import read_attendance, read_roster, render_section, summarize_section

students = read_roster("period3.csv")
marks = read_attendance("period3_attendance.csv")

summaries = summarize_section(students, marks, "A")
print(render_section(summaries, "A"))
```

which prints something like

```
Section A
Quillon, Sefa         33.3%  absent 2
Thistle, Bram         66.7%  absent 1
Varrow, Ines         100.0%  absent 0
```
