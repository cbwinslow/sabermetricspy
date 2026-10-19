# ADR-0037: Position-Player WAR Components Follow FanGraphs (Opt-In)

Status: Accepted

## Context
Position-player WAR used a flat 20 replacement runs per 600 PA and a positional adjustment scaled by PA / 600. The
FanGraphs article (read 2026-10-18) prints replacement runs as 570 * (G / 2430) * (RPW / lgPA) * PA, positional runs
as innings / 9 / 162 times the per-162 value (the table is per 1,458 innings, not 1,350 as a code comment said), and
RPW = 9 * (R / IP) * 1.5 + 3.

## Decision
Add `value/position_war.py` (runs_per_win, replacement_runs, positional_runs, league_adjustment). `WARFramework`
uses them when given `league_pa` and a `defensive_innings` column; the old defaults remain for callers without that
data, so existing results do not change.

## Evidence
Eight 2024 leaderboard rows (`tests/golden/position_war_2024.yaml`): RPW from MLB R and IP is 9.6826 and the
published rows imply 9.683; replacement runs match within 0.01 runs (with 2,429 games played that season); WAR =
(Offense + Defense + wLeague + Replacement) / RPW holds within 0.005, where Offense includes baserunning and Defense is
Fielding + Positional; Ohtani's DH adjustment equals 159/162 of -17.5, and the framework gives 8.9259 against 8.9261.

## Limits
Fielding (UZR), UBR, wGDP and the league adjustment inputs are caller-supplied. The entry stays `approximate` because
the defaults are the flat approximations. Making the FanGraphs path the default needs bundled league PA and games.
