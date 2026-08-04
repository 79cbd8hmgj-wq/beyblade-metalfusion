# Shops, rewards, and unlocks (Task 3)

Shop/reward dialogue and inventory diagnostics are **confirmed strings**, but
they do not by themselves establish a price or availability table. No fixed
stride candidate had both an item-ID correlation and an executable consumer,
so price, resale, quantity, and unlock fields remain **unknown**. The component
name tables contain only pointers and therefore do not store prices directly.

For runtime resolution, stop immediately before buying one Attack Ring, watch
the currency and inventory RAM locations, then break on the name-array base
`0x0807B0D8` being resolved. Log the category/item arguments and the source of
the displayed price. Repeat for one launcher and one ripcord to test whether
equipment shares the namespace.

