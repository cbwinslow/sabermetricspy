# ADR-0032: Extended Pythagorean Head-to-Head Probability

- **Status**: Accepted
- **Date**: 2026-10-18
- **OpenSpec change**: `extended-pythagorean`

## Decision
`Log5Model.extended_pythagorean_home_win_prob` implements equations 1.4 and 1.5 of Cleary et al. (rescale the home team's
runs by the opponent's relative to the league, then apply the Pythagorean form). The exponent is a required argument
because the paper cites Baseball-Reference's 1.87 and notes 1.83 is also common. The two equations agree and the
formula reduces to the Pythagorean win probability against an average opponent (tests). The paper's playoff total was
not reproduced because it needs series data.
