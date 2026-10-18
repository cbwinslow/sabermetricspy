## Decisions

1. **Source**: Hardegree, "Base-Advance Average" (2005), https://www.retrosheet.org/Research/HardegreeG/Base-Advance-Average.pdf. Bases advanced counts every runner's bases gained, the batter's own bases, and negative bases for an erased runner (the runner's original base); opportunities are, for each plate appearance, the maximum bases each runner including the batter could advance (4 for the batter, 3 from first, 2 from second, 1 from third).
2. **Closed form from states.** With runs R on the play (batter and runners reaching home), Pb and Pa the sums of occupied-base numbers before and after: bases advanced = 4R + Pa - Pb (a scoring runner gains 4 minus his base, an erased runner loses his base, the batter starts at 0); opportunities = 4 + 4n - Pb for n runners on base. This reproduces every row of the paper's sample inning.
3. Per-PA helper columns are summed before dividing (project rule); steals and other non-PA events are outside this version.
4. The paper prints .245 for 14/57 = .2456, a truncation; the test asserts the counts and the ratio to three decimals with that note.
