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
    lg_era: float | None = Field(
        default=None, description="League average ERA (None when unsourced)"
    )
    lg_era_nl: float | None = Field(
        default=None, description="NL ERA, all pitchers (27 ER / outs; None when unsourced)"
    )
    lg_era_al: float | None = Field(
        default=None, description="AL ERA, all pitchers (27 ER / outs; None when unsourced)"
    )
    siera_constant: float | None = Field(
        default=None,
        description="Per-season constant of FanGraphs' SIERA, measured from its leaderboard (None when unsourced; 2002 on)",
    )
    kwera_constant: float | None = Field(
        default=None,
        description="FanGraphs kwERA constant C in C - 12 (SO - BB) / TBF (None when unsourced; Tango's original is 5.40)",
    )
    lg_fip: float | None = Field(
        default=None, description="League average FIP (None when unsourced)"
    )
    lg_fip_al: float | None = Field(
        default=None,
        description="AL FIP, all pitchers: (13 HR + 3 (BB + HBP) - 2 SO) / IP + cFIP (None when unsourced)",
    )
    lg_fip_nl: float | None = Field(
        default=None,
        description="NL FIP, all pitchers: (13 HR + 3 (BB + HBP) - 2 SO) / IP + cFIP (None when unsourced)",
    )
    lg_xfip: float | None = Field(
        default=None, description="League average xFIP (None when unsourced)"
    )
    lg_hr_per_fb: float | None = Field(
        default=None, description="League HR/FB ratio for xFIP (None when unsourced; 2002+ only)"
    )
    lg_wrc_per_pa: float | None = Field(
        default=None,
        description="MLB-wide wRC/PA excluding pitchers, the wRC+ denominator (None when unsourced)",
    )
    lg_wrc_per_pa_nl: float | None = Field(
        default=None, description="NL wRC/PA excluding pitchers (None when unsourced)"
    )
    lg_wrc_per_pa_al: float | None = Field(
        default=None, description="AL wRC/PA excluding pitchers (None when unsourced)"
    )
    lg_obp: float = Field(default=0.315, description="League average OBP for OPS+")
    lg_slg: float = Field(default=0.410, description="League average SLG for OPS+")
    lg_k_pct: float = Field(default=0.226, description="League average strikeout rate (SO/PA)")
    lg_bb_pct: float = Field(default=0.083, description="League average walk rate (BB/PA)")
    lg_bb_pct_nl: float | None = Field(
        default=None,
        description="NL walk rate excluding pitchers, the BB%+ denominator (None when unsourced)",
    )
    lg_bb_pct_al: float | None = Field(
        default=None,
        description="AL walk rate excluding pitchers, the BB%+ denominator (None when unsourced)",
    )
    lg_k_pct_nl: float | None = Field(
        default=None,
        description="NL strikeout rate excluding pitchers, the K%+ denominator (None when unsourced)",
    )
    lg_k_pct_al: float | None = Field(
        default=None,
        description="AL strikeout rate excluding pitchers, the K%+ denominator (None when unsourced)",
    )
    lg_pit_bb_pct_nl: float | None = Field(
        default=None,
        description="NL walks per batter faced, all pitchers, the pitcher BB%+ denominator (None when unsourced)",
    )
    lg_pit_bb_pct_al: float | None = Field(
        default=None,
        description="AL walks per batter faced, all pitchers, the pitcher BB%+ denominator (None when unsourced)",
    )
    lg_pit_k_pct_nl: float | None = Field(
        default=None,
        description="NL strikeouts per batter faced, all pitchers, the pitcher K%+ denominator (None when unsourced)",
    )
    lg_pit_k_pct_al: float | None = Field(
        default=None,
        description="AL strikeouts per batter faced, all pitchers, the pitcher K%+ denominator (None when unsourced)",
    )
    lg_wsb: float = Field(
        default=0.0, description="League stolen base runs per opportunity (1B + uBB + HBP)"
    )
    source: str = Field(default="FanGraphs Guts!", description="Provenance source")
    retrieved: str | None = Field(default=None, description="Date the values were retrieved (ISO)")

    def wrc_per_pa_for(self, league: str) -> float | None:
        """Non-pitcher wRC/PA for `league` ("AL", "NL", otherwise MLB-wide); None when unsourced."""
        key = league.upper()
        if key == "NL" and self.lg_wrc_per_pa_nl is not None:
            return self.lg_wrc_per_pa_nl
        if key == "AL" and self.lg_wrc_per_pa_al is not None:
            return self.lg_wrc_per_pa_al
        return self.lg_wrc_per_pa

    def era_for(self, league: str) -> float | None:
        """League ERA for `league` ("AL", "NL", otherwise the MLB-wide `lg_era`); None when unsourced."""
        key = league.upper()
        if key == "NL" and self.lg_era_nl is not None:
            return self.lg_era_nl
        if key == "AL" and self.lg_era_al is not None:
            return self.lg_era_al
        return self.lg_era

    def fip_for(self, league: str) -> float | None:
        """League FIP for `league` ("AL", "NL", otherwise the MLB-wide `lg_fip`); None when unsourced."""
        key = league.upper()
        if key == "NL" and self.lg_fip_nl is not None:
            return self.lg_fip_nl
        if key == "AL" and self.lg_fip_al is not None:
            return self.lg_fip_al
        return self.lg_fip

    def bb_pct_for(self, league: str) -> float:
        """Walk rate for `league` ("AL", "NL", otherwise the MLB-wide `lg_bb_pct`)."""
        key = league.upper()
        if key == "NL" and self.lg_bb_pct_nl is not None:
            return self.lg_bb_pct_nl
        if key == "AL" and self.lg_bb_pct_al is not None:
            return self.lg_bb_pct_al
        return self.lg_bb_pct

    def k_pct_for(self, league: str) -> float:
        """Strikeout rate for `league` ("AL", "NL", otherwise the MLB-wide `lg_k_pct`)."""
        key = league.upper()
        if key == "NL" and self.lg_k_pct_nl is not None:
            return self.lg_k_pct_nl
        if key == "AL" and self.lg_k_pct_al is not None:
            return self.lg_k_pct_al
        return self.lg_k_pct

    def pit_bb_pct_for(self, league: str) -> float:
        """Pitcher walk rate per batter faced for `league` ("AL", "NL", otherwise the MLB-wide `lg_bb_pct`)."""
        key = league.upper()
        if key == "NL" and self.lg_pit_bb_pct_nl is not None:
            return self.lg_pit_bb_pct_nl
        if key == "AL" and self.lg_pit_bb_pct_al is not None:
            return self.lg_pit_bb_pct_al
        return self.lg_bb_pct

    def pit_k_pct_for(self, league: str) -> float:
        """Pitcher strikeout rate per batter faced for `league` ("AL", "NL", otherwise the MLB-wide `lg_k_pct`)."""
        key = league.upper()
        if key == "NL" and self.lg_pit_k_pct_nl is not None:
            return self.lg_pit_k_pct_nl
        if key == "AL" and self.lg_pit_k_pct_al is not None:
            return self.lg_pit_k_pct_al
        return self.lg_k_pct


class SIERACoefficients(BaseModel):
    """Coefficients of FanGraphs' SIERA, the 2011 "New SIERA" (Swartz) as FanGraphs displays it.

    The per-season constant is `WOBAWeights.siera_constant`. Every coefficient is the published 2011 value
    except `bb_per_pa_sq`: the published 27.252 does not reproduce FanGraphs' leaderboard, and 25.264 does
    (maximum error 0.007 over 8,042 pitcher-seasons, 2002-2026; docs/VERIFICATION.md).
    """

    model_config = ConfigDict(frozen=True)

    version: str = "fangraphs_2011_measured"
    so_per_pa: float = -15.518
    so_per_pa_sq: float = 9.146
    bb_per_pa: float = 8.648
    bb_per_pa_sq: float = 25.264
    net_gb_per_pa: float = -2.298
    net_gb_per_pa_sq: float = -4.920
    so_x_bb: float = -4.036
    so_x_net_gb: float = 5.155
    bb_x_net_gb: float = 4.546
    start_share: float = 0.367


class ParkFactor(BaseModel):
    """Ballpark run environment adjustment factor (100 = neutral)."""

    model_config = ConfigDict(frozen=True)

    park_id: str
    team_id: str
    season: int
    basic_5yr: float = Field(
        default=100.0, description="5-year regressed park factor (100=neutral)"
    )
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
    pythagenpat_exponent: float = Field(
        default=0.287,
        description=(
            "Power applied to runs per game to get the Pythagenpat exponent. Sources differ: "
            "0.287 (default) and 0.285 (Baseball-Reference WAR)."
        ),
    )
    weights: WOBAWeights | None = None
    siera_coeffs: SIERACoefficients = Field(default_factory=SIERACoefficients)


class LeagueRunEnvironment(BaseModel):
    """One league's pitching totals for a season (the inputs to FanGraphs' league FIP)."""

    model_config = ConfigDict(frozen=True)

    outs: int = Field(..., description="Innings pitched x 3")
    r: int = Field(..., description="Runs allowed")
    er: int = Field(..., description="Earned runs allowed")
    hr: int
    bb: int
    hbp: int
    so: int
    iffb: int | None = Field(
        default=None, description="Infield flies; None when not published (before 2002)"
    )

    @property
    def ip(self) -> float:
        """True decimal innings pitched."""
        return self.outs / 3.0

    @property
    def iffip_numerator(self) -> float:
        """13 HR + 3 (BB + HBP) - 2 (K + IFFB), treating unpublished infield flies as zero."""
        return 13.0 * self.hr + 3.0 * (self.bb + self.hbp) - 2.0 * (self.so + (self.iffb or 0))

    def __add__(self, other: LeagueRunEnvironment) -> LeagueRunEnvironment:
        iffb = (
            None
            if self.iffb is None and other.iffb is None
            else (self.iffb or 0) + (other.iffb or 0)
        )
        return LeagueRunEnvironment(
            outs=self.outs + other.outs,
            r=self.r + other.r,
            er=self.er + other.er,
            hr=self.hr + other.hr,
            bb=self.bb + other.bb,
            hbp=self.hbp + other.hbp,
            so=self.so + other.so,
            iffb=iffb,
        )


class PitcherWARConstants(BaseModel):
    """League run environment and derived constants for FanGraphs-method pitcher WAR in one season."""

    model_config = ConfigDict(frozen=True)

    season: int
    al: LeagueRunEnvironment
    nl: LeagueRunEnvironment
    war_ip_correction: float | None = Field(
        default=None,
        description="League correction in wins per inning (published by FanGraphs for 2016 only)",
    )
    source: str = ""
    retrieved: str | None = None

    @property
    def mlb(self) -> LeagueRunEnvironment:
        """MLB-wide totals (AL + NL)."""
        return self.al + self.nl

    @property
    def lg_era(self) -> float:
        """MLB league ERA."""
        return 9.0 * self.mlb.er / self.mlb.ip

    @property
    def lg_ra9(self) -> float:
        """MLB league runs allowed per nine innings."""
        return 9.0 * self.mlb.r / self.mlb.ip

    @property
    def ra9_minus_era(self) -> float:
        """Adjustment that moves an ERA-scale estimator to the RA9 scale."""
        return self.lg_ra9 - self.lg_era

    @property
    def iffip_constant(self) -> float:
        """MLB ifFIP constant: league ERA minus league ifFIP before the constant (not Guts! cFIP)."""
        return self.lg_era - self.mlb.iffip_numerator / self.mlb.ip

    def league_fipr9(self, league: str) -> float:
        """League (AL, NL, or MLB-wide) FIP on the RA9 scale at park factor 100, using the MLB constant."""
        key = league.upper()
        env = self.al if key == "AL" else self.nl if key == "NL" else self.mlb
        return env.iffip_numerator / env.ip + self.iffip_constant + self.ra9_minus_era


class LeagueWARConstants(BaseModel):
    """MLB inputs to the FanGraphs position-player replacement level and runs per win for one season."""

    model_config = ConfigDict(frozen=True)

    season: int
    games: int = Field(description="MLB games played (team games / 2)")
    pa: int = Field(description="MLB plate appearances")
    runs: int = Field(description="MLB runs scored")
    outs: int = Field(description="MLB outs recorded by pitchers (innings x 3)")

    @property
    def runs_per_win(self) -> float:
        """FanGraphs runs per win: 9 * (R / IP) * 1.5 + 3."""
        return 9.0 * self.runs / (self.outs / 3.0) * 1.5 + 3.0

    @property
    def replacement_runs_per_600_pa(self) -> float:
        """Replacement-level runs over 600 plate appearances implied by the FanGraphs formula."""
        return 570.0 * (self.games / 2430.0) * (self.runs_per_win / self.pa) * 600.0
