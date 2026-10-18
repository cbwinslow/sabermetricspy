"""Open modeled sabermetric estimators: ExpectedOutcomeModel (xBA/xSLG/xwOBA), PitchQualityModel (Stuff+/Location+/Pitching+), CatcherFramingModel, and OutsAboveAverageModel."""

from __future__ import annotations

from typing import Any, Self

import narwhals as nw
import numpy as np
import polars as pl
from narwhals.typing import IntoFrame
from pydantic import BaseModel, ConfigDict, Field

from sabermetricspy.constants import resolve_context
from sabermetricspy.schema import normalize_columns, to_polars_df
from sabermetricspy.telemetry import profiled
from sabermetricspy.types.context import SeasonContext


def _roundtrip_df(out_pl: pl.DataFrame, original_df: Any) -> Any:
    if isinstance(original_df, pl.DataFrame):
        return out_pl
    arrow_tbl = out_pl.to_arrow()
    if type(original_df).__module__.startswith("pandas"):
        return arrow_tbl.to_pandas()
    return arrow_tbl


class ExpectedOutcomeResults(BaseModel):
    """Frozen statistical diagnostics for the open contact-quality ExpectedOutcomeModel (xBA, xSLG, xwOBA)."""

    model_config = ConfigDict(frozen=True)

    n_batted_balls_fitted: int
    n_neighbors: int
    features_used: tuple[str, ...]
    brier_score_hit: float
    r_squared_woba: float
    mean_xba: float
    mean_xslg: float
    mean_xwoba: float


class ExpectedOutcomeModel:
    """Open Statcast contact-quality estimator (`xBA`, `xSLG`, `xwOBA`) using k-NN kernel smoothing.

    Fits a standardized `KNeighborsRegressor` over batted-ball launch kinematics
    (`launch_speed`, `launch_angle`, and optional `sprint_speed`) to estimate expected
    per-batted-ball probabilities `P(1B)`, `P(2B)`, `P(3B)`, and `P(HR)`, then transforms
    batted-ball or plate-appearance tables with `xba_est`, `xslg_est`, and `xwoba_est`.
    """

    def __init__(
        self,
        *,
        n_neighbors: int = 15,
        season: int = 2024,
        context: SeasonContext | None = None,
        ev_col: str = "launch_speed",
        la_col: str = "launch_angle",
        speed_col: str = "sprint_speed",
    ) -> None:
        self.n_neighbors = n_neighbors
        self.context = resolve_context(context, season=season)
        self.ev_col = ev_col
        self.la_col = la_col
        self.speed_col = speed_col
        self._results: ExpectedOutcomeResults | None = None
        self._knn: Any = None
        self._scaler: Any = None
        self._features: tuple[str, ...] = ()

    @property
    def results(self) -> ExpectedOutcomeResults:
        if self._results is None:
            raise RuntimeError("ExpectedOutcomeModel is not fitted yet. Call .fit(df) first.")
        return self._results

    @profiled(category="modeling")
    def fit(self, df: IntoFrame) -> Self:
        """Fit the k-NN contact-quality probability surface on batted-ball events."""
        from sklearn.metrics import r2_score
        from sklearn.neighbors import KNeighborsRegressor
        from sklearn.preprocessing import StandardScaler

        assert self.context.weights is not None
        w = self.context.weights
        nw_df = normalize_columns(nw.from_native(df))
        pl_df = to_polars_df(nw.to_native(nw_df))

        bbe = pl_df.filter(pl.col(self.ev_col).is_not_null() & pl.col(self.la_col).is_not_null())
        if bbe.is_empty():
            raise ValueError(
                f"ExpectedOutcomeModel requires non-null '{self.ev_col}' and '{self.la_col}' rows."
            )

        feat_cols = [self.ev_col, self.la_col]
        if self.speed_col in bbe.columns and bbe[self.speed_col].null_count() == 0:
            feat_cols.append(self.speed_col)
        self._features = tuple(feat_cols)

        x_raw = bbe.select(feat_cols).to_numpy().astype(np.float64)
        self._scaler = StandardScaler()
        x_scaled = self._scaler.fit_transform(x_raw)

        # Build indicator targets [b1, b2, b3, hr]
        b2 = bbe["b2"].to_numpy().astype(np.float64) if "b2" in bbe.columns else np.zeros(len(bbe))
        b3 = bbe["b3"].to_numpy().astype(np.float64) if "b3" in bbe.columns else np.zeros(len(bbe))
        hr = bbe["hr"].to_numpy().astype(np.float64) if "hr" in bbe.columns else np.zeros(len(bbe))
        if "b1" in bbe.columns:
            b1 = bbe["b1"].to_numpy().astype(np.float64)
        elif "h" in bbe.columns:
            b1 = bbe["h"].to_numpy().astype(np.float64) - b2 - b3 - hr
        else:
            b1 = np.zeros(len(bbe))

        y_mat = np.column_stack([b1, b2, b3, hr])
        k_eff = min(self.n_neighbors, len(bbe))
        self._knn = KNeighborsRegressor(n_neighbors=k_eff, weights="distance")
        self._knn.fit(x_scaled, y_mat)

        pred_probs = self._knn.predict(x_scaled)
        p1, p2, p3, phr = pred_probs[:, 0], pred_probs[:, 1], pred_probs[:, 2], pred_probs[:, 3]
        xba = np.clip(p1 + p2 + p3 + phr, 0.0, 1.0)
        xslg = np.clip(p1 + 2.0 * p2 + 3.0 * p3 + 4.0 * phr, 0.0, 4.0)
        xwoba = p1 * w.w_1b + p2 * w.w_2b + p3 * w.w_3b + phr * w.w_hr

        actual_hit = np.clip(b1 + b2 + b3 + hr, 0.0, 1.0)
        actual_woba = b1 * w.w_1b + b2 * w.w_2b + b3 * w.w_3b + hr * w.w_hr
        brier = float(np.mean((xba - actual_hit) ** 2))
        r2_val = float(r2_score(actual_woba, xwoba)) if np.var(actual_woba) > 0 else 0.0

        self._results = ExpectedOutcomeResults(
            n_batted_balls_fitted=len(bbe),
            n_neighbors=k_eff,
            features_used=self._features,
            brier_score_hit=brier,
            r_squared_woba=r2_val,
            mean_xba=float(np.mean(xba)),
            mean_xslg=float(np.mean(xslg)),
            mean_xwoba=float(np.mean(xwoba)),
        )
        return self

    @profiled(category="modeling")
    def transform(self, df: IntoFrame) -> Any:
        """Predict `xba_est`, `xslg_est`, and `xwoba_est` for batted balls and plate appearances."""
        if self._knn is None or self._scaler is None:
            raise RuntimeError("ExpectedOutcomeModel is not fitted yet. Call .fit(df) first.")
        assert self.context.weights is not None
        w = self.context.weights

        nw_df = normalize_columns(nw.from_native(df))
        pl_df = to_polars_df(nw.to_native(nw_df))

        n = len(pl_df)
        xba_out = np.zeros(n, dtype=np.float64)
        xslg_out = np.zeros(n, dtype=np.float64)
        xwoba_out = np.zeros(n, dtype=np.float64)

        ev_arr = pl_df[self.ev_col].to_numpy()
        la_arr = pl_df[self.la_col].to_numpy()
        valid_mask = ~np.isnan(ev_arr.astype(np.float64)) & ~np.isnan(la_arr.astype(np.float64))

        if np.any(valid_mask):
            feat_mat = pl_df.select(list(self._features)).to_numpy().astype(np.float64)[valid_mask]
            scaled = self._scaler.transform(feat_mat)
            probs = self._knn.predict(scaled)
            p1, p2, p3, phr = probs[:, 0], probs[:, 1], probs[:, 2], probs[:, 3]
            xba_out[valid_mask] = np.clip(p1 + p2 + p3 + phr, 0.0, 1.0)
            xslg_out[valid_mask] = np.clip(p1 + 2.0 * p2 + 3.0 * p3 + 4.0 * phr, 0.0, 4.0)
            xwoba_out[valid_mask] = p1 * w.w_1b + p2 * w.w_2b + p3 * w.w_3b + phr * w.w_hr

        # Handle non-BBE plate appearances (walks / HBP) for xwOBA
        if "bb" in pl_df.columns:
            bb_arr = pl_df["bb"].to_numpy().astype(np.float64)
            ibb_arr = (
                pl_df["ibb"].to_numpy().astype(np.float64)
                if "ibb" in pl_df.columns
                else np.zeros(n)
            )
            ubb_mask = (~valid_mask) & ((bb_arr - ibb_arr) > 0)
            xwoba_out[ubb_mask] = w.w_bb
        if "hbp" in pl_df.columns:
            hbp_arr = pl_df["hbp"].to_numpy().astype(np.float64)
            hbp_mask = (~valid_mask) & (hbp_arr > 0)
            xwoba_out[hbp_mask] = w.w_hbp

        out_pl = pl_df.with_columns(
            pl.Series("xba_est", xba_out),
            pl.Series("xslg_est", xslg_out),
            pl.Series("xwoba_est", xwoba_out),
        )
        return _roundtrip_df(out_pl, df)


class PitchQualityResults(BaseModel):
    """Frozen statsmodels / regression diagnostics for open Stuff+, Location+, and Pitching+."""

    model_config = ConfigDict(frozen=True)

    n_pitches_fitted: int
    stuff_r_squared: float
    stuff_f_statistic: float
    stuff_f_pvalue: float
    pitching_r_squared: float
    pitching_f_statistic: float
    pitching_f_pvalue: float
    stuff_coefficients: dict[str, float] = Field(default_factory=dict)
    stuff_pvalues: dict[str, float] = Field(default_factory=dict)
    mean_pitch_rv: float
    std_stuff_rv: float
    std_location_rv: float
    std_pitching_rv: float


class PitchQualityModel:
    """Open `Stuff+`, `Location+`, and `Pitching+` estimator (mean = 100, SD = 10, higher is better).

    Fits linear/polynomial response surfaces using `statsmodels.api.OLS` predicting per-pitch
    run value (`pitch_rv`, where negative run value is good for the pitcher) from:
    - **Stuff features**: `release_speed`, `ivb`, `hb`, `release_extension`, `spin_rate`, `vaa`, `haa`
    - **Location features**: `plate_x`, `plate_z`, radial distance from strike-zone center, and count leverage
    - **Pitching+**: Joint Stuff + Location feature space.

    Predicted run values are z-scored and inverted onto the `100 +/- 10` scale:
        `Plus = 100.0 - 10.0 * ((pred_rv - mean_pred_rv) / std_pred_rv)`
    """

    DEFAULT_STUFF_COLS: tuple[str, ...] = (
        "release_speed",
        "ivb",
        "hb",
        "release_extension",
        "spin_rate",
        "vaa",
        "haa",
    )

    def __init__(
        self,
        *,
        target_col: str = "pitch_rv",
        stuff_cols: tuple[str, ...] | None = None,
    ) -> None:
        self.target_col = target_col
        self.stuff_cols = stuff_cols or self.DEFAULT_STUFF_COLS
        self._results: PitchQualityResults | None = None
        self._stuff_ols: Any = None
        self._loc_ols: Any = None
        self._pit_ols: Any = None
        self._active_stuff_cols: list[str] = []
        self._has_location: bool = False
        self._stuff_mean_std: tuple[float, float] = (0.0, 1.0)
        self._loc_mean_std: tuple[float, float] = (0.0, 1.0)
        self._pit_mean_std: tuple[float, float] = (0.0, 1.0)

    @property
    def results(self) -> PitchQualityResults:
        if self._results is None:
            raise RuntimeError("PitchQualityModel is not fitted yet. Call .fit(df) first.")
        return self._results

    @staticmethod
    def _build_location_features(pl_df: pl.DataFrame) -> np.ndarray[Any, Any]:
        px = pl_df["plate_x"].to_numpy().astype(np.float64)
        pz = pl_df["plate_z"].to_numpy().astype(np.float64)
        # Distance from strike-zone center (x=0, z=2.5 ft) and shadow-zone edge distance (~0.83 ft horizontal)
        radial_dist = np.sqrt(px * px + (pz - 2.5) ** 2)
        edge_dist = np.abs(np.abs(px) - 0.83) + np.abs(np.abs(pz - 2.5) - 1.0)
        cols = [px, pz, px * px, (pz - 2.5) ** 2, radial_dist, edge_dist]
        if "balls" in pl_df.columns and "strikes" in pl_df.columns:
            balls = pl_df["balls"].to_numpy().astype(np.float64)
            strikes = pl_df["strikes"].to_numpy().astype(np.float64)
            cols.append(strikes - balls)
        return np.column_stack(cols)

    @profiled(category="modeling")
    def fit(self, df: IntoFrame) -> Self:
        """Fit Stuff+, Location+, and Pitching+ models using statsmodels OLS and store diagnostics."""
        import statsmodels.api as sm

        nw_df = normalize_columns(nw.from_native(df))
        pl_df = to_polars_df(nw.to_native(nw_df))

        if self.target_col not in pl_df.columns:
            raise ValueError(f"PitchQualityModel requires target column {self.target_col!r}.")

        self._active_stuff_cols = [c for c in self.stuff_cols if c in pl_df.columns]
        if not self._active_stuff_cols:
            raise ValueError(
                f"PitchQualityModel requires at least one stuff feature column from {self.stuff_cols}."
            )

        y = pl_df[self.target_col].to_numpy().astype(np.float64)
        x_stuff_raw = pl_df.select(self._active_stuff_cols).to_numpy().astype(np.float64)
        x_stuff = sm.add_constant(x_stuff_raw, has_constant="add")
        self._stuff_ols = sm.OLS(y, x_stuff).fit()
        stuff_pred = np.asarray(self._stuff_ols.predict(x_stuff), dtype=np.float64)
        self._stuff_mean_std = (
            float(np.mean(stuff_pred)),
            max(float(np.std(stuff_pred, ddof=1)), 1e-6),
        )

        self._has_location = "plate_x" in pl_df.columns and "plate_z" in pl_df.columns
        if self._has_location:
            x_loc_raw = self._build_location_features(pl_df)
            x_loc = sm.add_constant(x_loc_raw, has_constant="add")
            self._loc_ols = sm.OLS(y, x_loc).fit()
            loc_pred = np.asarray(self._loc_ols.predict(x_loc), dtype=np.float64)
            self._loc_mean_std = (
                float(np.mean(loc_pred)),
                max(float(np.std(loc_pred, ddof=1)), 1e-6),
            )

            x_pit_raw = np.column_stack([x_stuff_raw, x_loc_raw])
            x_pit = sm.add_constant(x_pit_raw, has_constant="add")
            self._pit_ols = sm.OLS(y, x_pit).fit()
            pit_pred = np.asarray(self._pit_ols.predict(x_pit), dtype=np.float64)
            self._pit_mean_std = (
                float(np.mean(pit_pred)),
                max(float(np.std(pit_pred, ddof=1)), 1e-6),
            )
            pit_r2 = float(self._pit_ols.rsquared)
            pit_f = float(self._pit_ols.fvalue) if not np.isnan(self._pit_ols.fvalue) else 0.0
            pit_fp = float(self._pit_ols.f_pvalue) if not np.isnan(self._pit_ols.f_pvalue) else 1.0
        else:
            self._loc_ols = None
            self._pit_ols = self._stuff_ols
            self._loc_mean_std = self._stuff_mean_std
            self._pit_mean_std = self._stuff_mean_std
            pit_r2 = float(self._stuff_ols.rsquared)
            pit_f = float(self._stuff_ols.fvalue) if not np.isnan(self._stuff_ols.fvalue) else 0.0
            pit_fp = (
                float(self._stuff_ols.f_pvalue) if not np.isnan(self._stuff_ols.f_pvalue) else 1.0
            )

        names = ["intercept", *self._active_stuff_cols]
        coef_dict = {k: float(v) for k, v in zip(names, self._stuff_ols.params, strict=False)}
        pval_dict = {
            k: float(v) if not np.isnan(v) else 1.0
            for k, v in zip(names, self._stuff_ols.pvalues, strict=False)
        }

        self._results = PitchQualityResults(
            n_pitches_fitted=len(pl_df),
            stuff_r_squared=float(self._stuff_ols.rsquared),
            stuff_f_statistic=float(self._stuff_ols.fvalue)
            if not np.isnan(self._stuff_ols.fvalue)
            else 0.0,
            stuff_f_pvalue=float(self._stuff_ols.f_pvalue)
            if not np.isnan(self._stuff_ols.f_pvalue)
            else 1.0,
            pitching_r_squared=pit_r2,
            pitching_f_statistic=pit_f,
            pitching_f_pvalue=pit_fp,
            stuff_coefficients=coef_dict,
            stuff_pvalues=pval_dict,
            mean_pitch_rv=float(np.mean(y)),
            std_stuff_rv=self._stuff_mean_std[1],
            std_location_rv=self._loc_mean_std[1],
            std_pitching_rv=self._pit_mean_std[1],
        )
        return self

    @profiled(category="modeling")
    def transform(self, df: IntoFrame) -> Any:
        """Attach `stuff_plus`, `location_plus`, and `pitching_plus` (mean 100, SD 10) to `df`."""
        import statsmodels.api as sm

        if self._stuff_ols is None:
            raise RuntimeError("PitchQualityModel is not fitted yet. Call .fit(df) first.")

        nw_df = normalize_columns(nw.from_native(df))
        pl_df = to_polars_df(nw.to_native(nw_df))

        x_stuff_raw = pl_df.select(self._active_stuff_cols).to_numpy().astype(np.float64)
        x_stuff = sm.add_constant(x_stuff_raw, has_constant="add")
        s_pred = np.asarray(self._stuff_ols.predict(x_stuff), dtype=np.float64)
        s_mu, s_sd = self._stuff_mean_std
        stuff_plus = 100.0 - 10.0 * ((s_pred - s_mu) / s_sd)

        if self._has_location and self._loc_ols is not None and self._pit_ols is not None:
            x_loc_raw = self._build_location_features(pl_df)
            x_loc = sm.add_constant(x_loc_raw, has_constant="add")
            l_pred = np.asarray(self._loc_ols.predict(x_loc), dtype=np.float64)
            l_mu, l_sd = self._loc_mean_std
            location_plus = 100.0 - 10.0 * ((l_pred - l_mu) / l_sd)

            x_pit_raw = np.column_stack([x_stuff_raw, x_loc_raw])
            x_pit = sm.add_constant(x_pit_raw, has_constant="add")
            p_pred = np.asarray(self._pit_ols.predict(x_pit), dtype=np.float64)
            p_mu, p_sd = self._pit_mean_std
            pitching_plus = 100.0 - 10.0 * ((p_pred - p_mu) / p_sd)
        else:
            location_plus = np.full(len(pl_df), 100.0, dtype=np.float64)
            pitching_plus = stuff_plus.copy()

        out_pl = pl_df.with_columns(
            pl.Series("stuff_plus", stuff_plus),
            pl.Series("location_plus", location_plus),
            pl.Series("pitching_plus", pitching_plus),
        )
        return _roundtrip_df(out_pl, df)


class CatcherFramingResults(BaseModel):
    """Frozen statistical diagnostics for the shadow-zone CatcherFramingModel."""

    model_config = ConfigDict(frozen=True)

    n_taken_pitches_fitted: int
    mean_called_strike_rate: float
    brier_score: float
    run_value_per_called_strike: float


class CatcherFramingModel:
    """Catcher framing shadow-zone called-strike probability estimator (`StrikesAboveAvg`, `FramingRuns`).

    Fits a regularized logistic regression over taken pitch coordinates (`plate_x`, `plate_z`)
    and count state (`balls`, `strikes`) to estimate expected called-strike probability `cs_prob`,
    then computes:
    - `strikes_above_avg = is_called_strike - cs_prob`
    - `framing_runs = strikes_above_avg * run_value_per_called_strike` (default `0.125` runs).
    """

    def __init__(self, *, run_value_per_called_strike: float = 0.125) -> None:
        self.run_value_per_called_strike = run_value_per_called_strike
        self._results: CatcherFramingResults | None = None
        self._clf: Any = None
        self._scaler: Any = None

    @property
    def results(self) -> CatcherFramingResults:
        if self._results is None:
            raise RuntimeError("CatcherFramingModel is not fitted yet. Call .fit(df) first.")
        return self._results

    @staticmethod
    def _extract_features(pl_df: pl.DataFrame) -> np.ndarray[Any, Any]:
        px = pl_df["plate_x"].to_numpy().astype(np.float64)
        pz = pl_df["plate_z"].to_numpy().astype(np.float64)
        # Rectangular strike zone normalized distance: max(|x|/0.833, |z - 2.5|/1.0)
        norm_rect = np.maximum(np.abs(px) / 0.833, np.abs(pz - 2.5) / 1.0)
        radial = np.sqrt(px * px + (pz - 2.5) ** 2)
        balls = (
            pl_df["balls"].to_numpy().astype(np.float64)
            if "balls" in pl_df.columns
            else np.zeros(len(pl_df))
        )
        strikes = (
            pl_df["strikes"].to_numpy().astype(np.float64)
            if "strikes" in pl_df.columns
            else np.zeros(len(pl_df))
        )
        return np.column_stack(
            [px, pz, px * px, (pz - 2.5) ** 2, norm_rect, radial, balls, strikes]
        )

    @profiled(category="modeling")
    def fit(self, df: IntoFrame) -> Self:
        """Fit the called-strike probability surface on taken pitches."""
        from sklearn.linear_model import LogisticRegression
        from sklearn.preprocessing import StandardScaler

        nw_df = normalize_columns(nw.from_native(df))
        pl_df = to_polars_df(nw.to_native(nw_df))

        for req in ("plate_x", "plate_z", "called_strikes"):
            if req not in pl_df.columns:
                raise ValueError(f"CatcherFramingModel requires column {req!r}.")

        x_mat = self._extract_features(pl_df)
        y = (pl_df["called_strikes"].to_numpy().astype(np.float64) > 0).astype(np.int64)

        self._scaler = StandardScaler()
        x_scaled = self._scaler.fit_transform(x_mat)
        self._clf = LogisticRegression(C=1.0, max_iter=500)
        self._clf.fit(x_scaled, y)

        probs = self._clf.predict_proba(x_scaled)[:, 1]
        brier = float(np.mean((probs - y) ** 2))
        self._results = CatcherFramingResults(
            n_taken_pitches_fitted=len(pl_df),
            mean_called_strike_rate=float(np.mean(y)),
            brier_score=brier,
            run_value_per_called_strike=self.run_value_per_called_strike,
        )
        return self

    @profiled(category="modeling")
    def transform(self, df: IntoFrame) -> Any:
        """Attach `cs_prob`, `strikes_above_avg`, and `framing_runs` to taken pitches."""
        if self._clf is None or self._scaler is None:
            raise RuntimeError("CatcherFramingModel is not fitted yet. Call .fit(df) first.")

        nw_df = normalize_columns(nw.from_native(df))
        pl_df = to_polars_df(nw.to_native(nw_df))

        x_mat = self._extract_features(pl_df)
        x_scaled = self._scaler.transform(x_mat)
        probs = self._clf.predict_proba(x_scaled)[:, 1]
        actual = (pl_df["called_strikes"].to_numpy().astype(np.float64) > 0).astype(np.float64)
        saa = actual - probs
        fr_runs = saa * self.run_value_per_called_strike

        out_pl = pl_df.with_columns(
            pl.Series("cs_prob", probs),
            pl.Series("strikes_above_avg", saa),
            pl.Series("framing_runs", fr_runs),
        )
        return _roundtrip_df(out_pl, df)


class OutsAboveAverageResults(BaseModel):
    """Frozen statistical diagnostics for the opportunity-based OutsAboveAverageModel."""

    model_config = ConfigDict(frozen=True)

    n_opportunities_fitted: int
    mean_out_rate: float
    brier_score: float
    run_value_per_out: float


class OutsAboveAverageModel:
    """Opportunity-based fielding catch-probability estimator (`catch_prob`, `oaa`, `fielding_runs`).

    Fits a logistic catch-probability model over `(opportunity_distance, hang_time, sprint_speed)`
    and computes:
    - `oaa = is_out - catch_prob`
    - `fielding_runs = oaa * run_value_per_out` (default `0.75` runs per out).
    """

    def __init__(self, *, run_value_per_out: float = 0.75) -> None:
        self.run_value_per_out = run_value_per_out
        self._results: OutsAboveAverageResults | None = None
        self._clf: Any = None
        self._scaler: Any = None
        self._feature_cols: list[str] = []

    @property
    def results(self) -> OutsAboveAverageResults:
        if self._results is None:
            raise RuntimeError("OutsAboveAverageModel is not fitted yet. Call .fit(df) first.")
        return self._results

    @profiled(category="modeling")
    def fit(self, df: IntoFrame) -> Self:
        """Fit the catch-probability model on batted-ball fielding opportunities."""
        from sklearn.linear_model import LogisticRegression
        from sklearn.preprocessing import StandardScaler

        nw_df = normalize_columns(nw.from_native(df))
        pl_df = to_polars_df(nw.to_native(nw_df))

        for req in ("opportunity_distance", "hang_time", "is_out"):
            if req not in pl_df.columns:
                raise ValueError(f"OutsAboveAverageModel requires column {req!r}.")

        self._feature_cols = ["opportunity_distance", "hang_time"]
        if "sprint_speed" in pl_df.columns:
            self._feature_cols.append("sprint_speed")
        if "going_back" in pl_df.columns:
            self._feature_cols.append("going_back")

        x_mat = pl_df.select(self._feature_cols).to_numpy().astype(np.float64)
        y = (pl_df["is_out"].to_numpy().astype(np.float64) > 0).astype(np.int64)

        self._scaler = StandardScaler()
        x_scaled = self._scaler.fit_transform(x_mat)
        self._clf = LogisticRegression(C=1.0, max_iter=500)
        self._clf.fit(x_scaled, y)

        probs = self._clf.predict_proba(x_scaled)[:, 1]
        brier = float(np.mean((probs - y) ** 2))
        self._results = OutsAboveAverageResults(
            n_opportunities_fitted=len(pl_df),
            mean_out_rate=float(np.mean(y)),
            brier_score=brier,
            run_value_per_out=self.run_value_per_out,
        )
        return self

    @profiled(category="modeling")
    def transform(self, df: IntoFrame) -> Any:
        """Attach `catch_prob`, `oaa`, and `fielding_runs` (`frv`) to fielding opportunities."""
        if self._clf is None or self._scaler is None:
            raise RuntimeError("OutsAboveAverageModel is not fitted yet. Call .fit(df) first.")

        nw_df = normalize_columns(nw.from_native(df))
        pl_df = to_polars_df(nw.to_native(nw_df))

        x_mat = pl_df.select(self._feature_cols).to_numpy().astype(np.float64)
        x_scaled = self._scaler.transform(x_mat)
        probs = self._clf.predict_proba(x_scaled)[:, 1]
        actual = (pl_df["is_out"].to_numpy().astype(np.float64) > 0).astype(np.float64)
        oaa = actual - probs
        frv = oaa * self.run_value_per_out

        out_pl = pl_df.with_columns(
            pl.Series("catch_prob", probs),
            pl.Series("oaa", oaa),
            pl.Series("fielding_runs", frv),
        )
        return _roundtrip_df(out_pl, df)
