# Character progression

The Thumb helper at `0x08042F08` iterates 55 records at stride `0x30`, reads a
signed byte selector at `+0x04`, updates a halfword at `+0x0A`, and clamps the
sum to a maximum derived from the function input (`0x3FFF0000` literal masks
that input). This is **strongly supported** as the experience-raise helper due
to the nearby `matchBladerExperience` diagnostic, but level thresholds and stat
changes are unknown. The Python reference implements only unsigned saturating
addition and does not claim the caller's complete reward formula.
