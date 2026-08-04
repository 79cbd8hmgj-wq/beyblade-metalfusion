# Compact story graph

The tracked graph contains only evidenced named nodes. A candidate adjacency
connects `atDojo` and `atExitToStreets`; `TriggerBattle` and the native
tournament subsystem are separately represented. Main-path chapters, optional
rewards, endings, dead branches, and postgame remain unknown rather than being
inferred from identifier order. The generator validates unique node IDs and all
edge references, and emits stable sorted JSON.
