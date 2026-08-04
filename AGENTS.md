# Reverse-engineering rules

* Never modify the source ROM and never commit patched ROMs or extracted assets.
* Put large reproducible output in ignored `work/`, `dumps/`, `analysis/generated/`, or `analysis/runtime/` directories.
* Give every finding one of: `confirmed`, `strongly_supported`, `candidate`, or `unknown`.
* Keep direct binary/runtime evidence distinguishable from inference and hypothesis.
* Write exact offsets in hexadecimal and check every ROM-offset/runtime-address conversion.
* Keep future Codex Cloud tracked diffs small and reviewable; retain generators rather than bulky output.
* All ROM writes flow through `tools.build`; every patch has expected original bytes and every allocation has a stable ID.
* Never make hidden manual hex edits or edit a generated ROM. The source ROM remains immutable and deterministic output is mandatory.
* Questionable internal space is disabled by default. Preserve unknown fields in every compiler and serializer.
