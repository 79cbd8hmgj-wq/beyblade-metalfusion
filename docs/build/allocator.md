# Allocator

The allocator sorts requests by stable ID and uses first-fit, choosing the lowest aligned address. The default confirmed allocation region is `0x00400000–0x007FFFFF`; original `0x00000000–0x003FFFFF` is occupied. Reservations split free extents. Fixed addresses, maximum address, proximity, and branch reach are checked. Internal space is disabled unless a profile explicitly supplies opt-in, exact extent, expected fill, and an evidence reference; use remains a reported warning. Runtime address equals file offset plus `0x08000000`.
