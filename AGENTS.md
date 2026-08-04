# Reverse-engineering rules

* Never modify the source ROM and never commit patched ROMs or extracted assets.
* Put large reproducible output in ignored `work/`, `dumps/`, `analysis/generated/`, or `analysis/runtime/` directories.
* Give every finding one of: `confirmed`, `strongly_supported`, `candidate`, or `unknown`.
* Keep direct binary/runtime evidence distinguishable from inference and hypothesis.
* Write exact offsets in hexadecimal and check every ROM-offset/runtime-address conversion.
* Keep future Codex Cloud tracked diffs small and reviewable; retain generators rather than bulky output.

