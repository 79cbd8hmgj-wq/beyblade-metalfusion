# Map and entity data

The low ROM through approximately `0x00003D00` combines ROM pointer arrays,
small integer records, and aligned inline ASCII identifiers. At `0x00002CB0`,
three u32 values precede `atExitToStreets`; at `0x00002CD0`, three u32 values
precede `atDojo`. This shape is a **candidate** authored map/event record, not a
confirmed actor coordinate layout. Coordinates, facing, sprites, collision,
and destinations remain unknown because integer range alone is insufficient.

The reusable parser accepts a caller-selected field count, requires ASCII/NUL
termination and four-byte alignment, and preserves padding exactly. It does not
scan or export commercial content in bulk.

## Task 8 avatar/portrait notes

**Unknown:** player overworld actor resource, sprite animation table, palette upload path, and portrait loader sites. Task 8 adds manifests without commercial asset extraction.
