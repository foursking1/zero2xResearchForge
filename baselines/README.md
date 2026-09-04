# Historical Baselines

`baselines/<domain>/<card_id>/` contains a checked-in historical agent
submission for a task. It is reference material for maintainers and internal
members, not the directory for new work.

Each baseline contains source code, a claim, and a report. Generated `results/`,
`evidence/`, and figure artifacts live in the separate private ModelScope
dataset `foursking1/zero2xResearchForge-baselines`; download them only when
auditing a historical submission with `python3 paperbench.py fetch-baselines`.
They are not needed to run a new task. Historical score reports do not live
here; use `evaluations/<protocol>/`.
