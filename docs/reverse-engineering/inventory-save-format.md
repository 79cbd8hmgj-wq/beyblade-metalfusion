# Inventory, collection, and equipped Bey persistence

The string `removeBladeFromTysonsCollection` at ROM `0x0033D358` and candidate code near runtime `0x0803E1F4` anchor collection behavior. Category cardinalities remain Spin Gears 22, Attack Rings 77, Blade Bases 42, Weight Disks 19. The exact serialized representation—quantity array, ownership bits, component records, or inventory indices—is **unknown** without controlled acquisitions. Accordingly no complete-template-ID interpretation is asserted and invalid IDs are rejected by tooling APIs.

Equipped custom Bey representation (template, five IDs, copied runtime record, or hybrid) is **unknown**. The serializer/deserializer boundary is confirmed in the payload report. `save_diff` plus watchpoints in `task5-save.gdb` is the required resolution path.
