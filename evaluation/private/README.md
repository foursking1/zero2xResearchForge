# Private Evaluation Material

`cards/<domain>/<card_id>/` contains the maintainer-only paper anchor, scoring
rubric, and calibration notes. Task directories intentionally do not contain
these files.

This directory is an ownership boundary, not an access-control mechanism. Do
not grant Participant Kit users access to this maintainer repository or its Git
history. A judge may instead read an independently mounted copy by setting
`PAPER_BENCH_PRIVATE_CARD_ROOT` to the corresponding `cards/` directory.
