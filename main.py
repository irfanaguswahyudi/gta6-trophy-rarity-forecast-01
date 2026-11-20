"""GTA VI trophy rarity forecast (gta6-trophy-rarity-forecast-01).

Forecasts, for every trophy, five quantiles (5/25/50/75/95%) of its Exophase
earn rate (percent) at the case target, scored by pinball loss on the logit
scale. Standard library only, offline, deterministic.

Model (logit space, per trophy):
  * Median: anchor at the trophy's last rate, plus a shrunk log-time trend.
    logit(rate) is fitted by least squares on x = ln(1 + hours since the
    2026-11-19T00:00Z release -- the same origin the house trend baseline
    uses) over runs ending in the last 24 h (located at run starts, so
    a long run straddling the boundary contributes a point at its start,
    which can be well before the window -- e.g. a run starting at hour 0
    at a 59.5 h checkpoint) and over all history (BLEND_W24 /
    1-BLEND_W24 blend), shrunk 15% toward persistence (x0.85; the
    refresh insurance -- see MEDIAN_SHRINK). Tier pooling was removed
    in v8 (TIER_WEIGHT=0): at fixed shrink it hurts -- held-out 0.2028
    vs 0.1988 at shrink 0.85, and on the seed-7 case at shrink 1.0
    quiet 0.1744 vs 0.1738 and refresh 0.3771 vs 0.3740 -- so 0 was
    chosen on the held-out mean. (The v15 wording compared "tier only"
    against the full model, which also changes shrink; that comparison
    does not isolate tier.) Log-time (not raw time) because story
    progression is fastest right after launch and saturates. Fits use
    per-trophy runs: consecutive reads with the same rounded rate are one
    observation, placed at the run's first timestamp (when that level was
    first established -- a repeated identical read adds no new level, so
    it must not weight the fit). Two clocks, kept separate by design:
    the FIT uses run starts (first-seen times); the MEDIAN ANCHOR and the
    OBSERVATION AGE use the run's END (last confirmation) -- a value
    confirmed an hour ago is fresh knowledge even if it was first seen a
    day ago, so extrapolation starts from the last confirmation, not the
    first sighting. REGIME: Exophase refreshes are feed-wide level
    shifts (all trophies jump together when the player base jumps). A
    level shift inside a fit window corrupts the slope -- a -1.0 logit
    step makes OLS extrapolate steeply down -- so fits use only reads
    since the last large feed-wide step: median |logit change| over the
    large moves (> 0.10) between consecutive distinct snapshots exceeds
    0.25, with at least 80% of the large moves in one direction, at
    least 10 trophies moving, and an abrupt gap (<= 2 h, so a long gap
    with ordinary progression does not false-trigger). The step must
    also be corroborated by a player-count change at that snapshot --
    a refresh changes the player base; a coherent rate jump with an
    unchanged count is a feed catch-up, not dilution -- unless the move
    is very large (> 0.50), in which case it cuts regardless. The gap is
    measured to the last confirmation of the old snapshot, so a feed
    that repeats (caches) one snapshot for hours and then jumps is
    still an abrupt step. The cutoff is
    a snapshot POSITION (index in the read table), and fit runs are
    rebuilt from the post-cutoff slice, so a run that straddles the
    cutoff restarts in the new regime instead of being dropped, and a
    pre-shift read at the same timestamp as the trigger cannot leak in.
    Ties (equal timestamps) keep file order (stable sort); the last read
    at a timestamp wins the anchor. A trophy whose own series is
    perfectly flat, or which has fewer than 3 distinct reads in the
    regime, is EXACT persistence (slope 0 and no dilution adjustment):
    flat means no evidence of movement, and the median does not move on
    no evidence. A downward shift on flat history is NOT applied: one
    launch-night refresh is no evidence of a repeatable negative median
    four days later; staleness is priced into the spread.
  * Spread (logit sigma): random-walk term 0.5*sqrt(days from the trophy's
    last confirmation to the target) + per-trophy residual variance
    (the larger of the 24 h and full-history fits, floored at
    RESID_FLOOR -- the floor applies to every branch, including flat
    history, as a minimum uncertainty, not as a measured residual)
    + slope uncertainty for the blended slope (conservative: 0.85 * max
    of the two window SEs, which ignores their covariance) + disagreement
    between the two window slopes + a refresh floor. Exophase refreshes
    its counts on its own schedule (launch night: players 638 -> 3868 in
    one refresh, every rate but the 100% one fell), so even a flat history
    carries jump risk that no in-sample residual can see; the floor prices
    that in. Only ONE refresh is actually observed (launch night:
    players 638 -> 3868 in one refresh, every rate but the 100% one
    fell); recurrence every few hours is ASSUMED, not established, and
    the floor prices that assumed jump risk. Under that assumption the
    jump probability saturates quickly with horizon; the floor scales
    with the chance a refresh lands inside the horizon (sqrt form, 1.0
    above one day: 90 min -> 0.25x, 1 day -> 1.0x), so short-horizon
    forecasts are not over-widened.
    The quantiles are kept symmetric: an asymmetric downside tested worse
    on final-like holdouts than it gained on practice proxies. A stale
    feed (no whole-snapshot change for a long time) widens the spread
    smoothly. At zero horizon with a fresh read the remaining sigma is
    sqrt(RESID_FLOOR) * SIGMA_SCALE ~= 0.10 -- the irreducible residual
    floor, never zero.
  * High rates: trophies at 85-100% get a dilution cap from the
    extrapolated player count (new players earn them at 95%), smoothly
    phased in from 85% to 95% and smoothly phased out from 99% to 100%.
    Growth is measured from the latest observed count only, and the cap
    weight ramps continuously from 0 at 0.1% projected growth to full at
    1.1%, so there is no cliff at the gate and the adjustment tends to
    zero as projected growth tends to zero; it never fires on
    contraction. The cap weight is also ramped down smoothly as the
    player-count anchor ages (full below 6 h, zero by 24 h). The holder
    base is the TREND median, not the last rate: the trend already embeds
    past dilution, and the cap only binds where the trend implies LESS
    dilution than the count model -- it is a ceiling on the incremental
    effect, not a second dose of the past dilution. The dilution rate
    is compared on the unclipped logit scale (logit_raw): the scorer's
    [0.01, 99.99] clip would cap a count-model rate above 99.99% and
    then pull a trend median above 99.99% down toward it. The cap is
    computed on the RAW (pre-clamp) trend median, and the +-4 logit
    emergency clamp is applied once afterwards as the final invariant:
    clamping first would let the cap lower a forecast whose raw trend
    already implies more dilution than the count model. The blend itself
    is between the two FEASIBLE (clamped) endpoints, so a partial cap
    still shows on a steep trend whose raw median sits above the clamp
    ceiling. The newcomer earn rate F=0.95 is unvalidated (no
    per-trophy newcomer data exists); sensitivity is reported in
    backtest.py (F in {0.85, 0.95, 1.0}).

Clocks: the median extrapolates in TARGET time (x_target); the spread
uses horizon_minutes for the random-walk distance plus the observation
age. The case contract makes them agree (target = at + horizon_minutes);
both are read from the case and no consistency check is applied beyond
that -- a case that violates it is out of contract.

Run: python3 -P -s main.py  (MAKEFUN_INPUT_DIR / MAKEFUN_OUTPUT_DIR
override /input and /output for local runs.)
"""

import json
import math
import os
from datetime import datetime, timezone
from pathlib import Path

INPUT_DIR = Path(os.environ.get("MAKEFUN_INPUT_DIR", "/input"))
OUTPUT_DIR = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))

LEVELS = [0.05, 0.25, 0.5, 0.75, 0.95]
Z = [-1.645, -0.674, 0.0, 0.674, 1.645]

# Release-day origin for the log-time axis (2026-11-19T00:00:00Z).
RELEASE = datetime(2026, 11, 19, 0, 0, 0, tzinfo=timezone.utc)

# --- tuned constants (see backtest; all in logit units unless noted) ---
RW_SIGMA = 0.5        # random-walk spread per sqrt(day), as the house baseline
AGE_WEIGHT = 1.0      # weight of the observation age in the random-walk
                      # term (age_days + horizon_days); 0 = age ignored
                      # (ablation knob; default keeps the full term)
STALE_GAIN = 0.5      # gain of the stale-feed spread multiplier
                      # (1 + gain * (1 - exp(-stale_hours/24))); 0 = off
NEAR100_GAIN = 0.5    # gain of the near-100% spread multiplier
                      # (1 + gain * clip((last_rate-90)/10)); 0 = off
RESID_FLOOR = 0.02    # minimum residual variance: a FLOOR on uncertainty,
                      # applied to every branch including flat history
                      # (flat history has no measured residual, but the
                      # floor is a minimum, not a measurement)
RESID_CAP = 1.0       # cap on residual variance
REFRESH_FLOOR = 0.20  # jump risk from Exophase refreshes unseen in-sample
                      # (v5-fixture sweep: 0.0 -> final-mean 0.2994,
                      # 0.20 -> 0.3029, 0.35 -> 0.3100; 0.20 keeps
                      # insurance against a launch-night-size jump at
                      # small final cost)
WINDOW_HOURS = 24.0   # short fit window before the checkpoint
STEP_THRESHOLD = 0.25  # median |logit change| over the LARGE moves
                      # between consecutive distinct snapshots that marks
                      # a refresh (see below)
STEP_BIG = 0.10        # a move counts as "large" above this |logit change|
STEP_COHERENT_SHARE = 0.80  # ... provided at least this share of the large
                      # moves share one direction: a 50/50 split (median
                      # signed change can still be large there) is noise,
                      # not a feed-wide shift
STEP_UNCORROBORATED_MAX = 0.50  # an ambiguous jump (player count
                      # UNCHANGED at that snapshot -- a feed catch-up,
                      # not a refresh) only cuts the regime when it is
                      # larger than this; smaller rate-only jumps keep
                      # the full history (a refresh is defined by a
                      # player-base change -- that is what dilution is)
STEP_MAX_GAP_H = 2.0   # ... and abrupt: the two snapshots must be within
                      # 2 h, so a long gap with ordinary progression
                      # cannot false-trigger
STEP_MIN_OVERLAP = 10  # ... over at least 10 trophies with a large move:
                      # one trophy cannot declare a feed-wide shift
BLEND_W24 = 0.6     # weight of the 24 h slope vs the full-history slope
                    # (v5-fixture sweep on quiet+refresh holdouts:
                    # 0.6 -> final-mean 0.3029, 0.75 -> 0.3064,
                    # 0.9 -> 0.3142, 1.0 -> 0.3229; on the v6/v7 fixtures
                    # the sweep is degenerate -- the regime lies inside
                    # 24 h, so both windows hold the same data -- and
                    # 0.6 is kept as a prior for regimes longer than 24 h)
MEDIAN_SHRINK = 0.85  # shrink the trend toward persistence. Held-out
                      # ablations cost it ~3.7% on the held-out mean
                      # (0.1988 vs 0.1917 without, v12), but it is the
                      # refresh insurance: tuning refresh holdout 0.3040
                      # with shrink vs 0.3740 without. The final case may
                      # contain further refreshes (assumed, not
                      # established), so the insurance is kept.
TIER_WEIGHT = 0.0     # weight of the tier-median slope in the blend.
                      # REMOVED in v8: v12 ablations show tier pooling
                      # hurts slightly (held-out mean 0.2028 with tier
                      # 0.2 vs 0.1988 without; tuning fixture quiet
                      # 0.1744 vs 0.1738, refresh 0.3771 vs 0.3740).
                      # Per-trophy fits are already stable (runs +
                      # regime + shrink); pooling adds nothing. Kept as
                      # a zero-weight knob so the blend code stays intact.
MAX_LOGIT_MOVE = 4.0  # emergency clamp on |median logit - last logit|
SIGMA_DOWN = 1.0      # downside sigma multiplier (kept symmetric: the
SIGMA_UP = 1.0        # fresh evaluation, seeds 41-44, decision (v11):
                      # decision (v11): 1.0 mean 0.2153 vs 1.3: 0.2287
                      # and 1.6: 0.2490 -- widening the downside worsens
                      # BOTH quiet and refresh paths, so it stays 1.0)
SIGMA_SCALE = 0.7     # global sigma multiplier: per-scenario sweep (v12)
                      # quiet 0.1843 / refresh(-0.7) 0.3040 / practice-
                      # agg 1.3805 / held-out mean 0.1988 at 0.7 vs
                      # 0.2067 / 0.3077 / 1.3648 / 0.2197 at 0.8 and
                      # 0.2515 / 0.3421 / 1.3334 / 0.2638 at 1.0.
                      # 0.8/1.0 win only on the practice aggregate proxy
                      # (1.3648/1.3334 vs 1.3805), whose truth is itself
                      # a guess; 0.7 wins quiet, refresh, and held-out.
                      # 0.7 is the preponderance-of-evidence choice.
DILUTION_LO = 85.0    # dilution cap phases in from this rate
DILUTION_HI = 95.0    # ... to full strength at this rate
DILUTION_OUT_LO = 99.0  # ... and phases out from this rate (100% exempt)
DILUTION_F = 0.95     # share of new players assumed to earn a high-rate trophy
GATE_TOL = 0.001      # dilution gate: no cap below 0.1% projected growth
GATE_RAMP = 0.01      # ... and the cap weight ramps linearly from 0 at
                      # GATE_TOL to full at GATE_TOL + GATE_RAMP (1.1%
                      # growth), so there is no cliff at the gate
COUNT_FRESHNESS_H = 24.0  # the cap weight ramps to zero by this age of
                      # the latest player count (see FRESHNESS_RAMP_LO):
                      # beyond it the projection is unanchored and the
                      # cap is skipped entirely
FRESHNESS_RAMP_LO = 6.0   # full cap weight while the count is fresher
                      # than this; ramps linearly to 0 at
                      # COUNT_FRESHNESS_H, so there is no cliff at any
                      # single age -- a count 11 h old and one 13 h old
                      # get nearly the same weight
TIER_PRIOR = {"platinum": 0.63, "gold": 0.78, "silver": 0.78, "bronze": 0.78}
UNSEEN_SIGMA = 2.0    # spread for a trophy never observed in history


def clamp_pct(x):
    return min(99.99, max(0.01, x))


def logit(pct):
    p = clamp_pct(pct) / 100.0
    return math.log(p / (1.0 - p))


def logit_raw(pct):
    """Logit WITHOUT the scorer's [0.01, 99.99] clip, for internal
    arithmetic only: the dilution mix must compare the count-model rate
    against the trend median on the same unclipped scale. Using logit()
    here would clip a count-model rate above 99.99% down to 99.99% and
    then cap a trend median above 99.99% down toward it -- lowering a
    forecast the count model says should stay up. Only call it with a
    rate strictly inside (0, 100), which inv_logit produces for finite
    inputs in exact arithmetic (in floating point it can round to
    exactly 0 or 100 at extremes; callers must guard -- the dilution
    path's dil >= 100 check does)."""
    p = pct / 100.0
    return math.log(p / (1.0 - p))


def inv_logit(lg):
    if lg >= 0:
        return 100.0 / (1.0 + math.exp(-lg))
    e = math.exp(lg)
    return 100.0 * e / (1.0 + e)


def round4(x):
    """Round to 4 decimals, half up (as JavaScript Math.round does it)."""
    scaled = x * 10000
    whole = math.floor(scaled)
    if scaled - whole >= 0.5:
        whole += 1
    value = whole / 10000
    return int(value) if value == int(value) else value


def parse_time(s):
    dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=timezone.utc)


def hours_since_release(t):
    return max(0.0, (t - RELEASE).total_seconds() / 3600.0)


def log_time(t):
    return math.log1p(hours_since_release(t))


def ols(xs, ys):
    """Least squares y ~ a + b*x. Returns (a, b, resid_var, se_b, n), or
    None when the x-values span too little time for a usable slope: three
    clustered reads are not a trend, however distinct their timestamps."""
    n = len(xs)
    if n < 2 or max(xs) - min(xs) < 0.05:
        return None
    mx = sum(xs) / n
    my = sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    if sxx <= 1e-12:
        return None
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    b = sxy / sxx
    a = my - b * mx
    resid = sum((y - (a + b * x)) ** 2 for x, y in zip(xs, ys))
    dof = max(n - 2, 1)
    var = resid / dof
    se_b = math.sqrt(var / sxx) if sxx > 0 else 0.0
    return a, b, var, se_b, n


def median_of(values):
    s = sorted(values)
    m = len(s)
    if m == 0:
        return 0.0
    return s[m // 2] if m % 2 else 0.5 * (s[m // 2 - 1] + s[m // 2])


def _runs(reads, get_value):
    """Collapse consecutive equal values into runs.

    Returns [(t_start, t_end, x_start, value)] with x the log-time axis;
    a run's value is placed at its FIRST timestamp (when it was first
    observed), and it counts as live in a window if its run extends into
    the window (t_end). None values are skipped without breaking a run:
    a missing reading is not a change of value.
    """
    runs = []
    cur = None
    for r in reads:
        v = get_value(r)
        if v is None:
            continue
        if cur is None or v != cur[3]:
            if cur is not None:
                runs.append(cur)
            cur = [r["t"], r["t"], r["x"], v]
        else:
            cur[1] = r["t"]
    if cur is not None:
        runs.append(cur)
    return runs


def _cap_log_n_pred(log_n_pred, last_n):
    """Clamp a projected log player count. Ratio clamps first ([0.5x,
    50x]), then the absolute exponent cap LAST: the lower (0.5x) clamp
    must never be able to raise the exponent above the 700 cap (with a
    huge last_n, max(..., log(last_n) - log 2) alone would return
    ~708.5). Extracted as its own function so the order is directly
    testable (regression 15 calls this, not a reimplementation)."""
    log_n_pred = min(log_n_pred, math.log(last_n) + math.log(50.0))
    log_n_pred = max(log_n_pred, math.log(last_n) - math.log(2.0))
    log_n_pred = min(log_n_pred, 700.0)
    return log_n_pred


def forecast_case(case, name):
    if case["levels"] != LEVELS:
        raise ValueError(f"{name} asks for levels {case['levels']}, not {LEVELS}")
    trophies = case["trophies"]
    history = case["history"]
    if not history:
        # Defensive fallback (cannot happen per spec: reads exist from
        # launch night on). One no-data policy: tier prior, sigma 2.0.
        # A valid, very wide forecast beats crashing into an invalid case.
        rows = []
        for trophy in trophies:
            lg = logit(TIER_PRIOR.get(trophy["tier"], 0.78))
            qs = [round4(clamp_pct(inv_logit(lg + z * UNSEEN_SIGMA))) for z in Z]
            for j in range(1, 5):
                if qs[j] < qs[j - 1]:
                    qs[j] = qs[j - 1]
            rows.append({"id": trophy["id"], "q": qs})
        return {"trophies": rows}

    horizon_days = case["horizon_minutes"] / 1440.0
    at = parse_time(case["at"])
    target = parse_time(case["target"])
    x_target = log_time(target)

    # One parsed read table, sorted by time, reads after the checkpoint
    # dropped (the contract says history is every read before `at`).
    # rates arrays are padded with None where a read is short, so a
    # ragged history cannot raise IndexError.
    n_tr = len(trophies)
    reads = []
    for h in history:
        t = parse_time(h["at"])
        if t > at:
            continue
        rates = list(h["rates"][:n_tr]) + [None] * max(0, n_tr - len(h["rates"]))
        reads.append({"t": t, "x": log_time(t),
                      "players": h.get("players_tracked"), "rates": rates})
    reads.sort(key=lambda r: r["t"])
    if not reads:
        return forecast_case({**case, "history": []}, name)

    # Staleness: hours since the last whole-snapshot change (rates AND
    # player count). Smooth multiplier, bounded, no cliffs.
    prev_sig = None
    last_change_t = reads[0]["t"]
    for r in reads:
        sig = (tuple(r["rates"]), r["players"])
        if sig != prev_sig:
            last_change_t = r["t"]
            prev_sig = sig
    stale_hours = (at - last_change_t).total_seconds() / 3600.0
    stale_mult = 1.0 + STALE_GAIN * (1.0 - math.exp(-stale_hours / 24.0))

    # Regime cutoff: the last feed-wide level shift, as a snapshot
    # POSITION (index into `reads`). Between consecutive distinct whole
    # snapshots, take the logit changes across trophies: a refresh is a
    # large median |change| (over the moves bigger than STEP_BIG) that is
    # also coherent in direction (at least 80% of the large moves share
    # one sign -- the median signed change alone is NOT a coherence
    # measure: a 27/28 split still has median +-1.0), abrupt (<= 2 h
    # gap), and observed on at least 10 trophies. The gap is measured
    # to the LAST confirmation of the old snapshot, not its first
    # sighting: a feed that repeats (caches) one snapshot for hours and
    # then jumps is still an abrupt step -- measuring to the first
    # sighting would false-negative it. Fits are rebuilt from
    # the post-cutoff slice, so a run straddling the cutoff restarts in
    # the new regime instead of being dropped, and a pre-shift read at
    # the same timestamp as the trigger cannot leak in.
    regime_idx = 0
    prev_r = None
    prev_sig2 = None
    prev_last_t = None
    for k, r in enumerate(reads):
        sig = (tuple(r["rates"]), r["players"])
        if sig == prev_sig2:
            # A repeat confirms the old snapshot again: the step gap is
            # measured from here, not from when the snapshot first
            # appeared.
            prev_last_t = r["t"]
            continue
        if prev_r is not None:
            diffs = []
            for i in range(n_tr):
                ra, rb = prev_r["rates"][i], r["rates"][i]
                if ra is not None and rb is not None:
                    diffs.append(logit(rb) - logit(ra))
            big = [d for d in diffs if abs(d) > STEP_BIG]
            up = sum(1 for d in big if d > 0)
            share = max(up, len(big) - up) / len(big) if big else 0.0
            gap_h = (r["t"] - prev_last_t).total_seconds() / 3600.0
            med_big = median_of([abs(d) for d in big]) if big else 0.0
            # Corroboration: a refresh changes the player base. A
            # coherent rate jump with an UNCHANGED player count is a
            # feed catch-up (stale snapshots published at once), not
            # dilution -- it only cuts the regime when it is too large
            # to be a slope artefact (over STEP_UNCORROBORATED_MAX).
            # A MISSING count corroborates nothing: only two KNOWN
            # counts that differ count as a change (None != 638 would
            # otherwise false-positive a refresh on a missing-data
            # read, which the implementation deliberately supports).
            count_changed = (prev_r["players"] is not None
                             and r["players"] is not None
                             and prev_r["players"] != r["players"])
            if (len(big) >= STEP_MIN_OVERLAP
                    and med_big > STEP_THRESHOLD
                    and share >= STEP_COHERENT_SHARE
                    and gap_h <= STEP_MAX_GAP_H
                    and (count_changed or med_big > STEP_UNCORROBORATED_MAX)):
                regime_idx = k
        prev_r, prev_sig2, prev_last_t = r, sig, r["t"]
    regime_reads = reads[regime_idx:]

    # Per-trophy run series: (x_start, logit rate), 24 h window and full
    # history, built from the post-cutoff slice. A run counts for the
    # window when it extends into it.
    window_start_t = at.timestamp() - WINDOW_HOURS * 3600.0
    series_win, series_all, last_obs = [], [], []
    for i in range(n_tr):
        runs = _runs(regime_reads, lambda r, i=i: r["rates"][i])
        pts_all = [(x0, logit(v)) for _, _, x0, v in runs]
        pts_win = [(x0, logit(v)) for _, t1, x0, v in runs
                   if t1.timestamp() >= window_start_t]
        series_all.append(pts_all)
        series_win.append(pts_win)
        # Last distinct observation over ALL reads (the anchor): the last
        # run (start time, end time, log-time of the run start, value).
        # The run carries no player count -- counts live on the reads.
        all_runs = _runs(reads, lambda r, i=i: r["rates"][i])
        last_obs.append(all_runs[-1] if all_runs else None)

    # Per-trophy fits on both windows.
    # blends[i] = (slope_blended, resid_var, se_blend, disagree, flat);
    # dx (extrapolation distance) is computed in the row loop from the
    # anchor run's END (last confirmation), not here.
    blends = []
    for i in range(n_tr):
        f24 = f_all = None
        if len({p[0] for p in series_win[i]}) >= 3:
            f24 = ols([p[0] for p in series_win[i]], [p[1] for p in series_win[i]])
        if len({p[0] for p in series_all[i]}) >= 3:
            f_all = ols([p[0] for p in series_all[i]], [p[1] for p in series_all[i]])
        if f24 is None and f_all is None:
            blends.append(None)
            continue
        flat = len({p[1] for p in series_all[i]}) <= 1
        if f24 is None:
            blended, var, se_b = f_all[1], f_all[2], MEDIAN_SHRINK * f_all[3]
        elif f_all is None:
            blended, var, se_b = f24[1], f24[2], MEDIAN_SHRINK * f24[3]
        else:
            blended = BLEND_W24 * f24[1] + (1.0 - BLEND_W24) * f_all[1]
            var = max(f24[2], f_all[2])
            # Conservative: max SE (the two fits overlap, so their errors
            # are correlated; RSS would understate it), scaled by the
            # shrinkage applied to the median slope.
            se_b = MEDIAN_SHRINK * max(f24[3], f_all[3])
        disagree = abs(f24[1] - f_all[1]) if (f24 is not None and f_all is not None) else 0.0
        blends.append((blended, var, se_b, disagree, flat))

    # Tier-median blended slopes (pooling movers only; tiny tiers fall
    # back to the global median).
    tier_slopes = {}
    for i, trophy in enumerate(trophies):
        if blends[i] is not None and not blends[i][4]:
            tier_slopes.setdefault(trophy["tier"], []).append(blends[i][0])
    global_slope = median_of([b[0] for b in blends if b is not None and not b[4]])
    tier_median = {}
    for t, v in tier_slopes.items():
        tier_median[t] = median_of(v) if len(v) >= 3 else global_slope

    # Player-count trend, anchored at the last observed count: growth is
    # projected from that count with the fitted log slope, clamped to
    # [0.5x, 50x] so the exponential can never overflow, and the log
    # exponent itself is capped at 700 (exp(709) is the float limit) so
    # an extreme input count cannot overflow the projection either.
    # The fit uses runs of the player count from the post-cutoff slice.
    n_runs = _runs(regime_reads, lambda r: r["players"])
    n_pts = [(x0, math.log(max(1, v))) for _, _, x0, v in n_runs]
    last_n = 0
    last_n_x = None
    last_n_t = None
    for r in reversed(reads):
        if r["players"]:
            last_n, last_n_x, last_n_t = r["players"], r["x"], r["t"]
            break
    n_pred = None
    if len({p[0] for p in n_pts}) >= 3 and last_n > 0:
        fit_n = ols([p[0] for p in n_pts], [p[1] for p in n_pts])
        if fit_n is not None:
            b_n = min(2.0, max(-2.0, fit_n[1]))
            log_n_pred = math.log(last_n) + b_n * (x_target - last_n_x)
            log_n_pred = _cap_log_n_pred(log_n_pred, last_n)
            n_pred = math.exp(log_n_pred)
    # Unanchored projection: if the latest count is stale, the cap
    # weight ramps down (see the row loop) and is skipped entirely
    # beyond COUNT_FRESHNESS_H -- projecting growth from an old count
    # would call all the inferred growth incremental.
    if last_n_t is not None and (at - last_n_t).total_seconds() / 3600.0 > COUNT_FRESHNESS_H:
        n_pred = None

    rows = []
    for i, trophy in enumerate(trophies):
        run = last_obs[i]
        unseen = run is None
        if unseen:
            last_rate = TIER_PRIOR.get(trophy["tier"], 0.78)
            last_lg = logit(last_rate)
            age_days = 0.0
            x_last = x_target
        else:
            _, t1, _, last_rate = run
            last_lg = logit(last_rate)
            # Anchor clock: the run's END (last confirmation). The value
            # was confirmed at t1, so extrapolation starts there and the
            # observation age is measured from t1 -- not from the run's
            # first sighting, which can be far older for a long flat run.
            x_last = log_time(t1)
            age_days = (at - t1).total_seconds() / 86400.0
        dx = max(0.0, x_target - x_last) if not unseen else 0.0
        blend = blends[i]
        flat_or_sparse = blend is None or blend[4]
        if flat_or_sparse:
            # EXACT persistence: no slope, no dilution. No evidence of
            # movement means the median does not move.
            slope, var, se_b, disagree = 0.0, 0.0, 0.0, 0.0
        else:
            b_own, var, se_b, disagree, _ = blend
            prior = tier_median.get(trophy["tier"], global_slope)
            slope = MEDIAN_SHRINK * ((1.0 - TIER_WEIGHT) * b_own + TIER_WEIGHT * prior)
        med_lg = last_lg + slope * dx
        # NOTE: the +-4 logit clamp is applied ONCE, AFTER the dilution
        # cap (below). Clamping first and then capping would let the cap
        # lower a forecast whose RAW trend already implies MORE dilution
        # than the count model: e.g. a trophy whose trend extrapolates
        # far below the clamp floor gets clamped up to last-4, and the
        # cap would then pull that clamped value down toward the
        # count-model rate -- even though the unclamped trend already
        # falls below it. Capping the raw median makes the min() guard
        # compare like with like.
        # Dilution cap for high rates (not flat/sparse, not unseen).
        # Growth is measured from the LATEST count only: the rate is
        # already observed, so growth since the trophy's last distinct
        # observation is already reflected in it (or unknown, and the
        # persistence anchor assumes it holds). Only incremental players
        # between now and the target can dilute it further. The cap
        # weight ramps continuously from 0 at 0.1% projected growth to
        # full at 1.1% growth -- no cliff at the gate: the adjustment
        # tends to zero as projected growth tends to zero, and it never
        # fires on contraction. It is ALSO ramped down smoothly as the
        # player-count anchor ages (full weight while the count is
        # fresher than 6 h, zero by 24 h), so no single age is a cliff.
        # The cap is smoothly phased in 85->95% and out 99->100%.
        if (not flat_or_sparse and not unseen and last_rate < 100.0
                and n_pred is not None and last_n > 0):
            growth = n_pred / last_n - 1.0
            w_gate = min(1.0, max(0.0, (growth - GATE_TOL) / GATE_RAMP))
            count_age_h = (at - last_n_t).total_seconds() / 3600.0 \
                if last_n_t is not None else 0.0
            w_fresh = min(1.0, max(0.0, (COUNT_FRESHNESS_H - count_age_h)
                                    / (COUNT_FRESHNESS_H - FRESHNESS_RAMP_LO)))
            w_in = min(1.0, max(0.0, (last_rate - DILUTION_LO) / (DILUTION_HI - DILUTION_LO)))
            w_out = 1.0 - min(1.0, max(0.0, (last_rate - DILUTION_OUT_LO) / (100.0 - DILUTION_OUT_LO)))
            w = w_in * w_out * w_gate * w_fresh
            if w > 0.0:
                # Base the holder count on the TREND median, not the last
                # rate: existing players keep completing (the trend), and
                # only the incremental newcomers dilute. Basing it on the
                # last rate would forbid any completion by existing
                # non-holders and overstate the drop. The dilution rate
                # is compared with logit_raw, NOT logit: the scorer's
                # [0.01, 99.99] clip inside logit() would cap a
                # count-model rate above 99.99% down to 99.99% and then
                # pull a trend median above 99.99% down toward it --
                # lowering a forecast the count model says should stay
                # up. inv_logit output is inside (0, 100) for all
                # finite inputs in exact arithmetic (in floating point
                # it can round to exactly 0 or 100 at extremes, which
                # is why the dil >= 100 guard below exists), so
                # logit_raw is finite here. The cap only binds
                # where the trend implies LESS dilution than the count
                # model: capped = min(trend, count-model rate), so a
                # trend that already falls below the count-model rate
                # is left alone.
                med_rate = inv_logit(med_lg)
                holders_now = med_rate / 100.0 * last_n
                holders_pred = holders_now + DILUTION_F * (n_pred - last_n)
                dil = 100.0 * holders_pred / n_pred
                # Float safety: holders_pred/n_pred is < 1 in exact
                # arithmetic (holders grow by at most F < 1 of the
                # newcomers), but rounding with huge counts could push
                # it to 1.0, where logit_raw would fail. Guard at 1e-9
                # below 100 -- far below any observable effect.
                if dil >= 100.0:
                    dil = 100.0 - 1e-9
                capped = min(med_lg, logit_raw(dil))
                # Blend between the FEASIBLE endpoints (both inside the
                # +-4 clamp): blending the raw values first and then
                # clamping would erase a partial cap whenever the raw
                # trend median sits above the clamp ceiling -- the blend
                # would land above the ceiling and clamp back to exactly
                # the no-cap value.
                lo = last_lg - MAX_LOGIT_MOVE
                hi = last_lg + MAX_LOGIT_MOVE
                med_lg = (1.0 - w) * min(hi, max(lo, med_lg)) \
                    + w * min(hi, max(lo, capped))
        # The +-4 logit emergency clamp, applied ONCE here as the final
        # invariant on the median (whether or not the cap fired).
        med_lg = min(last_lg + MAX_LOGIT_MOVE, max(last_lg - MAX_LOGIT_MOVE, med_lg))

        resid = min(RESID_CAP, max(RESID_FLOOR, var)) if blend is not None else RESID_FLOOR
        u_disagree = 0.5 * dx * disagree
        # The refresh floor scales with the chance a refresh lands inside
        # the horizon: under the assumed recurrence a refresh is
        # near-certain over 4.5 days but unlikely inside 90 minutes, so
        # the floor is horizon-independent only above one day (sqrt form:
        # 90 min -> 0.25x, 1 day -> 1.0x). A horizon-independent floor
        # would over-widen short-horizon forecasts.
        refresh_floor_eff = REFRESH_FLOOR * math.sqrt(min(1.0, horizon_days))
        var_total = (RW_SIGMA ** 2) * (AGE_WEIGHT * age_days + horizon_days) + resid \
            + (se_b * dx) ** 2 + u_disagree ** 2 + refresh_floor_eff ** 2
        sigma = math.sqrt(var_total) * stale_mult * SIGMA_SCALE
        if unseen:
            sigma = max(sigma, UNSEEN_SIGMA)
        # Near-100% spread widens smoothly: 1.0x at 90%, 1.5x at 100%.
        sigma *= 1.0 + NEAR100_GAIN * min(1.0, max(0.0, (last_rate - 90.0) / 10.0))
        qs = []
        for z in Z:
            s = sigma * (SIGMA_DOWN if z < 0 else SIGMA_UP if z > 0 else 1.0)
            q = inv_logit(med_lg + z * s)
            qs.append(round4(clamp_pct(q)))
        # Enforce non-decreasing (rounding can tie, never invert).
        for j in range(1, 5):
            if qs[j] < qs[j - 1]:
                qs[j] = qs[j - 1]
        # Defensive finite validation: every output value must be a
        # finite number in [0.01, 99.99]. A non-finite value (impossible
        # on valid input -- all inputs are clamped and the exponential
        # is capped) falls back to the median.
        for j in range(5):
            if not math.isfinite(qs[j]):
                qs[j] = round4(clamp_pct(inv_logit(med_lg)))
        for j in range(1, 5):
            if qs[j] < qs[j - 1]:
                qs[j] = qs[j - 1]
        rows.append({"id": trophy["id"], "q": qs})
    return {"trophies": rows}


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for path in sorted(INPUT_DIR.glob("*.in")):
        case = json.loads(path.read_text(encoding="utf-8"))
        forecast = forecast_case(case, path.name)
        (OUTPUT_DIR / f"{path.stem}.out").write_text(
            json.dumps(forecast, separators=(",", ":")) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
