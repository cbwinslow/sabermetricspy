"""Glicko-2 rating update (Glickman), scalar form.

Source: Glickman, "Example of the Glicko-2 system" (2022), https://www.glicko.net/glicko/glicko2.pdf. The rating period
is the caller's choice; one call applies one rating period to one player. Home advantage and any baseball-specific
adjustment are not part of the method and are not applied (ADR-0077).
"""

from __future__ import annotations

import math
from collections.abc import Sequence

from pydantic import BaseModel, ConfigDict

from sabermetricspy.telemetry import profiled

# glicko2.pdf step 2: mu = (r - 1500) / 173.7178 (the exact 400 / ln(10) is 173.7177928...).
GLICKO2_SCALE = 173.7178
_CENTRE = 1500.0
_SCORES = (0.0, 0.5, 1.0)


class Glicko2Rating(BaseModel):
    """A Glicko-2 rating on the familiar 1500-centred scale."""

    model_config = ConfigDict(frozen=True)

    rating: float
    rd: float
    volatility: float


def _g(phi: float) -> float:
    return 1.0 / math.sqrt(1.0 + 3.0 * phi * phi / math.pi**2)


def _expected(mu: float, mu_j: float, phi_j: float) -> float:
    return 1.0 / (1.0 + math.exp(-_g(phi_j) * (mu - mu_j)))


def glicko2_expected_score(rating: float, opponent_rating: float, opponent_rd: float) -> float:
    """Expected score `E` of a player against one opponent, from the player's side (the opponent's RD enters via g)."""
    if not all(math.isfinite(x) for x in (rating, opponent_rating, opponent_rd)):
        raise ValueError("Ratings and rating deviations must be finite numbers.")
    if opponent_rd <= 0.0:
        raise ValueError("opponent_rd must be positive.")
    mu = (rating - _CENTRE) / GLICKO2_SCALE
    mu_j = (opponent_rating - _CENTRE) / GLICKO2_SCALE
    return _expected(mu, mu_j, opponent_rd / GLICKO2_SCALE)


def _new_volatility(
    delta: float, phi: float, v: float, sigma: float, tau: float, epsilon: float
) -> float:
    """Step 5: the Illinois-algorithm solution for the new volatility, exactly as printed (revised 2012 version)."""
    a = math.log(sigma * sigma)

    def f(x: float) -> float:
        ex = math.exp(x)
        return ex * (delta * delta - phi * phi - v - ex) / (2.0 * (phi * phi + v + ex) ** 2) - (
            x - a
        ) / (tau * tau)

    big_a = a
    if delta * delta > phi * phi + v:
        big_b = math.log(delta * delta - phi * phi - v)
    else:
        k = 1
        while f(a - k * tau) < 0.0:
            k += 1
        big_b = a - k * tau
    f_a, f_b = f(big_a), f(big_b)
    while abs(big_b - big_a) > epsilon:
        big_c = big_a + (big_a - big_b) * f_a / (f_b - f_a)
        f_c = f(big_c)
        if f_c * f_b <= 0.0:
            big_a, f_a = big_b, f_b
        else:
            f_a = f_a / 2.0
        big_b, f_b = big_c, f_c
    return math.exp(big_a / 2.0)


@profiled(category="models")
def glicko2_update(
    rating: float = 1500.0,
    rd: float = 350.0,
    volatility: float = 0.06,
    games: Sequence[tuple[float, float, float]] = (),
    *,
    tau: float,
    epsilon: float = 1e-6,
) -> Glicko2Rating:
    """Update one player's Glicko-2 rating after one rating period.

    `games` holds `(opponent_rating, opponent_rd, score)` per game, with score 0 (loss), 0.5 (draw) or 1 (win). With no
    games only the rating deviation grows, to `sqrt(phi**2 + volatility**2)` on the Glicko-2 scale. `tau`, the system
    constant that constrains the change in volatility, has no default: Glickman calls 0.3 to 1.2 reasonable and says
    it should be tested for the application. Raises `ValueError` for invalid input.
    """
    numbers = [rating, rd, volatility, tau, epsilon]
    for o_rating, o_rd, score in games:
        numbers += [o_rating, o_rd, score]
    if not all(math.isfinite(x) for x in numbers):
        raise ValueError("All inputs must be finite numbers.")
    if rd <= 0.0 or volatility <= 0.0 or tau <= 0.0 or epsilon <= 0.0:
        raise ValueError("rd, volatility, tau and epsilon must be positive.")
    if any(o_rd <= 0.0 for _, o_rd, _ in games):
        raise ValueError("opponent rating deviations must be positive.")
    if any(score not in _SCORES for _, _, score in games):
        raise ValueError("Scores must be 0, 0.5 or 1.")

    mu = (rating - _CENTRE) / GLICKO2_SCALE
    phi = rd / GLICKO2_SCALE
    if not games:
        phi_star = math.sqrt(phi * phi + volatility * volatility)
        return Glicko2Rating(rating=rating, rd=GLICKO2_SCALE * phi_star, volatility=volatility)

    mu_j = [(o_rating - _CENTRE) / GLICKO2_SCALE for o_rating, _, _ in games]
    phi_j = [o_rd / GLICKO2_SCALE for _, o_rd, _ in games]
    scores = [score for _, _, score in games]
    g = [_g(p) for p in phi_j]
    e = [_expected(mu, m, p) for m, p in zip(mu_j, phi_j, strict=True)]
    v = 1.0 / sum(gi * gi * ei * (1.0 - ei) for gi, ei in zip(g, e, strict=True))
    score_sum = sum(gi * (si - ei) for gi, si, ei in zip(g, scores, e, strict=True))
    delta = v * score_sum
    sigma_new = _new_volatility(delta, phi, v, volatility, tau, epsilon)
    phi_star = math.sqrt(phi * phi + sigma_new * sigma_new)
    phi_new = 1.0 / math.sqrt(1.0 / (phi_star * phi_star) + 1.0 / v)
    mu_new = mu + phi_new * phi_new * score_sum
    return Glicko2Rating(
        rating=GLICKO2_SCALE * mu_new + _CENTRE, rd=GLICKO2_SCALE * phi_new, volatility=sigma_new
    )


__all__ = ["GLICKO2_SCALE", "Glicko2Rating", "glicko2_expected_score", "glicko2_update"]
