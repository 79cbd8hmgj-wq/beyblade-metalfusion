# Migration and recovery foundation

## Implemented

The tooling model falls back to sanitized defaults when both extension slots are invalid and preserves original save bytes outside the edited extension slot. Corrupt newest-slot tests verify fallback to the older slot.

## Unknown / unexecuted

Original-save validity integration and native stale-extension clearing behavior remain unimplemented until load/save hook sites and EEPROM-tail safety are confirmed.
