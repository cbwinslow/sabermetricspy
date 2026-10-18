"""Frozen Pydantic value objects for seasonal context, weights, and entities."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class WOBAWeights(BaseModel):
    """Linear weights and scaling constants for wOBA, wRAA, and wRC+ in a given season."""

    model_config = ConfigDict(frozen=True)

    season: int
    league: str = "MLB"
    lg_woba: float = Field(..., description="League average wOBA")
    woba_scale: float = Field(..., description="wOBA scale factor to convert to runs")
    w_bb: float = Field(..., description="Unintentional walk linear weight")
    w_hbp: float = Field(..., description="Hit by pitch linear weight")
    w_1b: float = Field(..., description="Single linear weight")
    w_2b: float = Field(..., description="Double linear weight")
    w_3b: float = Field(..., description="Triple linear weight")
    w_hr: float = Field(..., description="Home run linear weight")
    r_sb: float = Field(default=0.20, description="Stolen base run value")
    r_cs: float = Field(default=-0.42, description="Caught stealing run value")
    lg_r_per_pa: float = Field(..., description="League runs per plate appearance")
    lg_r_per_w: float = Field(..., description="League runs per win (RPW)")
    c_fip: float = Field(..., description="Seasonal FIP constant")
    lg_era: float = Field(default=4.15, description="League average ERA")
    lg_fip: float = Field(default=4.15, description="League average FIP")
    lg_xfip: float = Field(default=4.15, description="League average xFIP")
    lg_hr_per_fb: float = Field(default=0.115, description="League HR/FB ratio for xFIP")
    lg_obp: float = Field(default=0.315, description="League average OBP for OPS+")
    lg_slg: float = Field(default=0.410, description="League average SLG for OPS+")
    lg_k_pct: float = Field(default=0.226, description="League average strikeout rate (SO/PA)")
    lg_bb_pct: float = Field(default=0.083, description="League average walk rate (BB/PA)")
    lg_gidp_rate: float = Field(
        default=0.105, description="League average GIDP rate per GIDP opportunity"
    )
    r_gidp: float = Field(default=0.44, description="Run value of avoiding a GIDP")
    lg_wsb: float = Field(
        default=0.0, description="League stolen base runs per opportunity (1B + uBB + HBP)"
    )
    source: str = Field(default="FanGraphs Guts!", description="Provenance source")


class SIERACoefficients(BaseModel):
    """Regression coefficients for SIERA (Skill-Interactive ERA)."""

    model_config = ConfigDict(frozen=True)

    version: str = "fangraphs_standard"
    intercept: float = 6.145
    so_per_pa: float = -16.986
    bb_per_pa: float = 11.434
    net_gb_per_pa: float = -1.858
    so_per_pa_sq: float = 7.653
    net_gb_per_pa_sq: float = -6.664
    so_x_net_gb: float = 10.130
    bb_x_net_gb: float = -5.195
    so_x_bb: float = 0.0


class ParkFactor(BaseModel):
    """Ballpark run environment adjustment factor (100 = neutral)."""

    model_config = ConfigDict(frozen=True)

    park_id: str
    team_id: str
    season: int
    basic_5yr: float = Field(default=100.0, description="5-year regressed park factor (100=neutral)")
    basic_1yr: float = Field(default=100.0, description="1-year park factor (100=neutral)")
    hr_factor: float = Field(default=100.0, description="Home run park factor (100=neutral)")
    source: str = "FanGraphs"

    @property
    def multiplier(self) -> float:
        """Convert 100-indexed park factor to a half-home/half-road player multiplier.

        In FanGraphs wRC+ and FIP-, a park factor of 104 means `pf = 1.04` (or half-effect
        already baked into published 5yr basic factors). Here `basic_5yr / 100.0` is returned.
        """
        return self.basic_5yr / 100.0


class SeasonContext(BaseModel):
    """Contextual configuration supplied to contextual metric calculations."""

    model_config = ConfigDict(frozen=True)

    season: int = 2024
    league: str = "MLB"
    park_factor: float = Field(
        default=100.0,
        description="Park factor on 100-scale (100.0 = neutral park). Used for wRC+, OPS+, ERA+, FIP-.",
    )
    pythag_exponent: float = Field(
        default=1.83,
        description="Exponent gamma for Pythagorean winning percentage.",
    )
    weights: WOBAWeights | None = None
    siera_coeffs: SIERACoefficients = Field(default_factory=SIERACoefficients)
