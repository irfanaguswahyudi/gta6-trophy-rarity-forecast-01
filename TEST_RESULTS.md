# TEST_RESULTS.md — gta6-trophy-rarity-forecast-01, v19

Date: 2026-11-20 (WIB). Python 3.12.3 local (grader uses 3.13-slim — no 3.13
available on this machine; disclosed gap, see README).

## End-to-end (grader-style, from this folder)

```
KIT=~/workspace/makefun-bounty/kits/gta6-trophy-rarity-forecast-01/gta6-trophy-rarity-forecast-01-kit
mkdir -p out && MAKEFUN_INPUT_DIR=$KIT/input MAKEFUN_OUTPUT_DIR=out python3 -P -s main.py
```

- Two runs byte-identical:
  - p00.out sha256 `60131a5bf575199e566619490c4b94e206adb969dea6624cf97623a38fb2a7a4` (2648 bytes)
  - p01.out sha256 `5ae0eb32bb0c7ef2f3ad2850f6bd5dbe7df21eca61176135e7c0b8cdd40a6361` (2681 bytes)
- Runtime ~0.05 s for both cases (limit 8 s per case; batch ~0.05 s in the v16 log, hashes match isolated runs).
- Sample rows p00: id2 (100% trophy) `[99.9854, 99.9883, 99.99, 99.99, 99.99]`,
  id4 `[0.855, 0.9922, 1.1, 1.2194, 1.4142]`; 55 rows, all finite, non-decreasing.

## Full backtest log (`python3 backtest.py`, exit 0)

```
worked-example check OK: loss=0.403404 miss=7.00 cov=0.5
  pinball boundary clamp OK (0.0/100.0 == 0.01/99.99)
--- regression tests (round-2 fixes) ---
  1. contraction gate: median 99.1728 (growth variant 97.9056) OK
  2. flat 99% + 2x growth: median 99 OK
  3. boundary: 100%->99.99 99.98->99.99 99.99->99.99 OK
  4. cached repeats crossing 24h: median 2 OK
  5. gate continuity: flat=99.1728 decline=99.1728 small-growth=99.1197 2x-growth=97.9204 OK
  6. duplicate timestamps: OK, id4 median 99.0719 (anchor from latest read)
  6b. zero-horizon anchor: median == 98.5 exactly OK
--- regression tests (round-4: regime detector) ---
  7a. coherent step: on=1.5925 off=0.4277 last=1.18 OK
  7b. mixed directions: no trigger (identical to detector-off) OK
  7c. sparse overlap: no trigger (identical to detector-off) OK
  7d. long gap: no trigger (identical to detector-off) OK
  7e. straddling run: median 15.8559 (> 7.0) OK
  7f. tie at trigger: median 1.5925 (> last 1.18), == untied 1.5925 OK
--- regression tests (round-4: clock, freshness, gate ramp) ---
  8a. read at checkpoint: median 50 OK
  8b. zero horizon: q=[45.9378, 48.3326, 50, 51.6674, 54.0622] (floor sigma 0.0990) OK
  9. count freshness: stale=99.544 fresh=97.8916 OK
  10. F sensitivity: {0.85: 94.8688, 0.95: 97.9056, 1.0: 99.1728} OK
  5b. gate ramp (flat reference 99.1728):
      target~0.0005 actual=0.0006: median=99.1728 drop=0.0000 full-drop=0.0000 ratio=0.00 expected~0.00
      target~0.0010 actual=0.0010: median=99.1728 drop=0.0000 full-drop=0.0043 ratio=0.00 expected~0.00
      target~0.0020 actual=0.0020: median=99.1719 drop=0.0009 full-drop=0.0084 ratio=0.11 expected~0.10
      target~0.0050 actual=0.0051: median=99.1643 drop=0.0085 full-drop=0.0210 ratio=0.40 expected~0.41
      target~0.0080 actual=0.0081: median=99.1494 drop=0.0234 full-drop=0.0333 ratio=0.70 expected~0.71
      target~0.0110 actual=0.0110: median=99.1276 drop=0.0452 full-drop=0.0453 ratio=1.00 expected~1.00
      target~0.0500 actual=0.0500: median=98.974 drop=0.1988 full-drop=0.1988 ratio=1.00 expected~1.00
--- regression tests (round-5: cached step, freshness ramp, raw-median cap) ---
  11. cached repeats: median 1.5925 (> last 1.18), == unfrozen 1.5925, off=0.6134 OK
  12. freshness ramp: {5: 98.6308, 6: 98.6308, 11: 98.9905, 13: 99.1065, 20: 99.4179, 24: 99.5446, 30: 99.5446} no-cap=99.5446 OK
  13a. logit_raw: raw(99.995)=9.9034 vs clipped logit=9.2102 OK
  13b. raw-median cap: median 95.3123 == no-cap 95.3123, old-order would be 95.2876 OK
  13c. logit_raw call site: patched median 64.4539 != 97.9056 OK
--- regression tests (round-6: catch-up, exponent, partial cap, clustered baseline) ---
  14. catch-up: no-count-change identical to off; count-changed differs by 10.56 OK
  14b. missing count (post-jump): identical to off OK
  14c. missing count (pre-jump): identical to off OK
  14d. large uncorroborated jump (+0.6): differs by 17.99 OK
  15. exponent boundary: _cap_log_n_pred(700, 1.07e308)=700.0 (old order would give 708.6), finite output OK
  16. partial cap: 99.8752 between full-cap 98.3305 and no-cap 99.99 OK
  17. clustered reads: trend baseline + candidate valid, trend median 99.99 > last 2.0 (fit used) OK
--- regression tests (round-7: defensive edge cases) ---
  18a. empty history: tier priors 0.63/0.78, logit width 6.58 (sigma 2.0, exact vector) OK
  18b. unseen trophy: bronze prior 0.78, logit width 6.58 OK
  18c. single read: median == last rate 42.0 OK
  18d. ragged rates: short==None-padded, median 99.7652 vs full 99.9184 OK
  18e. post-checkpoint read: dropped, forecast byte-identical OK
--- regression tests (round-7: RULES parity) ---
  19a. RULES persistence example: [0.1931, 0.5403, 1.1, 2.2264, 6.0088] OK
  19b. trend window parity: median 85.8748 == 24h 85.88 (12h 87.94, full 76.69) OK
  19d. trend residual spread: median 81.9764 vs 82.02, width 4.22 vs expected 4.22 OK
  19c. trend <3 reads == persistence OK
synthetic-final: mine loss=0.1843 miss=2.08pp cov=1.00 | persistence loss=0.4614 | trend-baseline loss=0.4182
synthetic-final+refresh(-0.7 logit): mine loss=0.3040 | persistence loss=0.2690 | trend-baseline loss=0.2384
  per-quantile pinball (refresh -0.7): q5=0.0702 q25=0.1264 q50=0.5825 q75=0.5544 q95=0.1867
  per-quantile pinball (quiet): q5=0.1402 q25=0.3219 q50=0.1385 q75=0.2044 q95=0.1167
  quantiles clipped at 0.01/99.99: 0.000 of all values
--- held-out evaluation (8 paths; NOTE: tuning data now -- see frozen_evaluation) ---
  seed=11 ckpt=24h jump=-0.35 post=+0.0: mine=0.1966 persist=0.6852 trend=0.2686 | mine bias=-0.189 hits[q05..q95]=0.00/0.00/0.07/1.00/1.00 width=2.57 | trend bias=-0.269 width=3.52
  seed=11 ckpt=36h jump=-0.35 post=+0.0: mine=0.1853 persist=0.5404 trend=0.2210 | mine bias=-0.144 hits[q05..q95]=0.00/0.00/0.05/1.00/1.00 width=2.57 | trend bias=+0.003 width=3.50
  seed=12 ckpt=48h jump=-1.0 post=+0.0: mine=0.1853 persist=0.4925 trend=1.5507 | mine bias=-0.124 hits[q05..q95]=0.00/0.00/0.11/1.00/1.00 width=2.57 | trend bias=-2.349 width=3.61
  seed=12 ckpt=36h jump=-1.0 post=+0.0: mine=0.1884 persist=0.5773 trend=1.3308 | mine bias=-0.157 hits[q05..q95]=0.00/0.00/0.07/1.00/1.00 width=2.57 | trend bias=-2.126 width=3.60
  seed=13 ckpt=24h jump=-0.35 post=-0.3: mine=0.1816 persist=0.5739 trend=0.2210 | mine bias=+0.101 hits[q05..q95]=0.00/0.00/0.82/1.00/1.00 width=2.57 | trend bias=+0.028 width=3.52
  seed=14 ckpt=36h jump=-0.35 post=+0.4: mine=0.2794 persist=0.7369 trend=0.2921 | mine bias=-0.533 hits[q05..q95]=0.00/0.00/0.00/0.49/1.00 width=2.57 | trend bias=-0.393 width=3.50
  seed=15 ckpt=48h jump=-1.0 post=+0.0: mine=0.1825 persist=0.4587 trend=1.5540 | mine bias=-0.122 hits[q05..q95]=0.00/0.00/0.09/1.00/1.00 width=2.57 | trend bias=-2.353 width=3.61
  seed=16 ckpt=36h jump=-0.7 post=-0.3: mine=0.1917 persist=0.4033 trend=0.6309 | mine bias=+0.166 hits[q05..q95]=0.00/0.04/0.89/1.00/1.00 width=2.57 | trend bias=-1.176 width=3.55
  held-out (TUNING) MEAN (8 paths): mine=0.1988 persist=0.5585 trend=0.7586
--- frozen evaluation (seeds 21-24, config frozen, never used for tuning) ---
  seed=21 ckpt=30h jump=-0.5 post=-0.2: mine=0.1769 persist=0.5034 trend=0.3463 | mine bias=+0.056 hits[q05..q95]=0.00/0.00/0.71/1.00/1.00 width=2.57
  seed=22 ckpt=42h jump=-0.8 post=+0.2: mine=0.2243 persist=0.6343 trend=1.2487 | mine bias=-0.336 hits[q05..q95]=0.00/0.00/0.00/0.96/1.00 width=2.57
  seed=23 ckpt=24h jump=-0.35 post=+0.0: mine=0.1900 persist=0.6815 trend=0.2671 | mine bias=-0.141 hits[q05..q95]=0.00/0.00/0.15/1.00/1.00 width=2.57
  seed=24 ckpt=48h jump=-1.2 post=-0.5: mine=0.2284 persist=0.3137 trend=1.5269 | mine bias=+0.358 hits[q05..q95]=0.00/0.05/1.00/1.00/1.00 width=2.57
  frozen MEAN (4 paths): mine=0.2049 persist=0.5332 trend=0.8473
--- diverse evaluation (seeds 31-34, TUNING, cap-activating) ---
  seed=31 ckpt=48h jump=-0.35 post=-0.7 horizon=6510m: mine=0.3031 persist=0.2813 trend=0.3639 | mine bias=+0.554 hits[q05..q95]=0.00/0.69/0.96/1.00/1.00 width=2.60 | dilution activations 4/55 [2, 6, 7, 8], cap-off loss=0.3074 (cap benefit +0.0043)
  seed=32 ckpt=36h jump=-0.7 post=-1.0 horizon=1440m: mine=0.6429 persist=0.3639 trend=0.6345 | mine bias=+0.931 hits[q05..q95]=0.98/0.98/1.00/1.00/1.00 width=1.32 | dilution activations 2/55 [2, 8], cap-off loss=0.6500 (cap benefit +0.0072)
  seed=33 ckpt=24h jump=-0.35 post=+0.0 horizon=90m: mine=0.0392 persist=0.0401 trend=0.0380 | mine bias=-0.006 hits[q05..q95]=0.00/0.04/0.42/0.96/1.00 width=0.49 | dilution activations 0/55 [], cap-off loss=0.0392 (cap benefit +0.0000)
  seed=34 ckpt=48h jump=-1.0 post=-0.7 horizon=6510m: mine=0.2891 persist=0.2703 trend=0.3549 | mine bias=+0.553 hits[q05..q95]=0.00/0.75/0.98/1.00/1.00 width=2.57 | dilution activations 2/55 [2, 8], cap-off loss=0.2917 (cap benefit +0.0026)
  diverse MEAN (4 paths): mine=0.3186 persist=0.2389 trend=0.3478
--- fresh evaluation (seeds 41-44, frozen BEFORE this experiment, SIGMA_DOWN test) ---
  baselines: persistence mean=0.3668 per-path=[0.2824, 0.4807, 0.1231, 0.581] | trend mean=0.2491 per-path=[0.3617, 0.2207, 0.1603, 0.2538]
  SIGMA_DOWN=1.0: fresh mean=0.2153 quiet=0.2123 refresh=0.2183 per-path=[0.2961, 0.1899, 0.1404, 0.2347]
  SIGMA_DOWN=1.3: fresh mean=0.2287 quiet=0.2359 refresh=0.2214 per-path=[0.2966, 0.2135, 0.1463, 0.2583]
  SIGMA_DOWN=1.6: fresh mean=0.2490 quiet=0.2596 refresh=0.2384 per-path=[0.3187, 0.2371, 0.1581, 0.282]
  DECISION (rule stated above): SIGMA_DOWN=1.0 (combined gain +0.0000, quiet cost +0.0000)
  fresh refresh path post=-0.7: per-quantile q5=0.0757 q25=0.1195 q50=0.5639 q75=0.5373 q95=0.1841 (q50+q75 share=0.74)
  fresh refresh path post=-0.3: per-quantile q5=0.0405 q25=0.0391 q50=0.2619 q75=0.2676 q95=0.0929 (q50+q75 share=0.75)
--- fresh-2 evaluation (seeds 51-54, frozen, validation-only) ---
  seed=51 [normal] ckpt=24h jump=-0.35 post=-0.7 horizon=90m: mine=0.5959 persist=0.5656 trend=0.5794 | mine bias=+0.705 hits[q05..q95]=1.00/1.00/1.00/1.00/1.00 width=0.49
  seed=52 [normal] ckpt=36h jump=-0.7 post=-1.0 horizon=1440m: mine=0.6515 persist=0.3680 trend=0.6348 | mine bias=+0.940 hits[q05..q95]=0.98/1.00/1.00/1.00/1.00 width=1.32
  seed=53 [flat] ckpt=48h jump=0.0 post=+0.0 horizon=6510m: mine=0.2217 persist=0.2133 trend=0.2133 | mine bias=+0.000 hits[q05..q95]=0.00/0.00/0.00/1.00/1.00 width=3.64
  seed=54 [declining] ckpt=48h jump=-0.35 post=-0.3 horizon=6510m: mine=0.1477 persist=0.3484 trend=0.1718 | mine bias=+0.206 hits[q05..q95]=0.00/0.05/0.58/0.76/0.95 width=1.61
  fresh-2 MEAN (4 paths, equal weights): mine=0.4042 persist=0.3738 trend=0.3998
--- final-clock evaluation (seeds 61/63, exact contest clock, paired) ---
  seed=61 ckpt=59.5h post=+0.0 horizon=6510m: mine=0.1955 persist=0.3801 trend=0.2225 | mine bias=-0.151 hits[q05..q95]=0.00/0.00/0.09/0.96/1.00 width=2.60
  seed=61 ckpt=59.5h post=-0.7 horizon=6510m: mine=0.3022 persist=0.2644 trend=0.3568 | mine bias=+0.549 hits[q05..q95]=0.00/0.78/0.96/1.00/1.00 width=2.60
  seed=63 ckpt=59.5h post=+0.0 horizon=6510m: mine=0.1958 persist=0.3963 trend=0.2239 | mine bias=-0.155 hits[q05..q95]=0.00/0.00/0.04/0.96/1.00 width=2.60
  seed=63 ckpt=59.5h post=-0.7 horizon=6510m: mine=0.2997 persist=0.2633 trend=0.3549 | mine bias=+0.545 hits[q05..q95]=0.00/0.75/0.96/1.00/1.00 width=2.60
  final-clock MEAN (4 paths): mine=0.2483 persist=0.3260 trend=0.2895
--- innovation evaluation (seeds 71/73 paired SD 0.3; seed 74 SD 1.0631) ---
  seed=71 post=+0.0 innov_sd=0.3: mine=0.2198 persist=0.4527 trend=0.2609 | mine bias=-0.127 hits[q05..q95]=0.00/0.00/0.36/0.91/1.00 width=2.60
  seed=71 post=-0.3 innov_sd=0.3: mine=0.2288 persist=0.3532 trend=0.2927 | mine bias=+0.173 hits[q05..q95]=0.00/0.15/0.69/0.96/1.00 width=2.60
  seed=73 post=+0.0 innov_sd=0.3: mine=0.2499 persist=0.4770 trend=0.2748 | mine bias=-0.201 hits[q05..q95]=0.00/0.05/0.33/0.85/1.00 width=2.60
  seed=73 post=-0.3 innov_sd=0.3: mine=0.2409 persist=0.3666 trend=0.2929 | mine bias=+0.099 hits[q05..q95]=0.00/0.16/0.60/0.95/1.00 width=2.60
  seed=74 post=+0.0 innov_sd=1.0631: mine=0.4416 persist=0.6346 trend=0.4288 | mine bias=-0.156 hits[q05..q95]=0.07/0.16/0.38/0.65/0.93 width=2.60
  innovation SD-0.3 MEAN (4 paths): mine=0.2349 persist=0.4124 trend=0.2803
--- combined summary (equal weights per path) ---
  validation-only (frozen + fresh-2, 8 paths): mine=0.3045 persist=0.4535 trend=0.6235
  all 12 paths (8 validation + 4 tuning): mine=0.2748 persist=0.4246 trend=0.4987
--- ablations (v10, tuning fixture seed 7; loss; lower better) ---
  full model                                                 practice-aggregate=1.3805 synthetic-quiet=0.1843 synthetic-refresh=0.3040
  shrink only (shrink=0.85, tier=0)                          practice-aggregate=1.3805 synthetic-quiet=0.1843 synthetic-refresh=0.3040
  tier only (shrink=1, tier=0.2)                             practice-aggregate=1.3805 synthetic-quiet=0.1744 synthetic-refresh=0.3771
  no tier/shrink (shrink=1, tier=0)                          practice-aggregate=1.3805 synthetic-quiet=0.1738 synthetic-refresh=0.3740
  no refresh floor                                           practice-aggregate=1.3838 synthetic-quiet=0.1817 synthetic-refresh=0.3041
  no dilution cap                                            practice-aggregate=1.3805 synthetic-quiet=0.1843 synthetic-refresh=0.3040
  symmetric sigma (down=up=1)                                practice-aggregate=1.3805 synthetic-quiet=0.1843 synthetic-refresh=0.3040
  no regime truncation                                       practice-aggregate=1.3805 synthetic-quiet=0.2845 synthetic-refresh=0.1944
  no age term                                                practice-aggregate=1.3874 synthetic-quiet=0.1840 synthetic-refresh=0.3040
  no stale multiplier                                        practice-aggregate=1.3869 synthetic-quiet=0.1827 synthetic-refresh=0.3040
  no near-100% multiplier                                    practice-aggregate=1.3804 synthetic-quiet=0.1831 synthetic-refresh=0.3045
  persistence median (slope+SE zeroed, dilution off; spread otherwise as full) practice-aggregate=1.3805 synthetic-quiet=0.4647 synthetic-refresh=0.2170
  house persistence (ref)                                    practice-aggregate=1.4015 synthetic-quiet=0.4614 synthetic-refresh=0.2690
  house trend (ref)                                          practice-aggregate=1.4015 synthetic-quiet=0.4182 synthetic-refresh=0.2384
  dilution activations: synthetic 0/55 trophies []; practice p00 0/55 []
--- held-out ablations (TUNING data; mean loss over the 8 held-out paths) ---
  full model                   held-out (TUNING) mean=0.1988
  tier=0.2                     held-out (TUNING) mean=0.2028
  shrink=1                     held-out (TUNING) mean=0.1917
  no tier/shrink               held-out (TUNING) mean=0.1917
  no regime truncation         held-out (TUNING) mean=0.4362
  no refresh floor             held-out (TUNING) mean=0.1965
  no dilution cap              held-out (TUNING) mean=0.1988
  no age term                  held-out (TUNING) mean=0.1985
  no stale multiplier          held-out (TUNING) mean=0.1974
  no near-100% multiplier      held-out (TUNING) mean=0.1977
  sigma 0.7                    held-out (TUNING) mean=0.1988
  sigma 1.0                    held-out (TUNING) mean=0.2638
  house persistence (ref)      held-out (TUNING) mean=0.5585
  house trend (ref)            held-out (TUNING) mean=0.7586
--- sigma-scale sweep (v10, per scenario) ---
  scale=0.7: quiet=0.1843 refresh=0.3040 practice-agg=1.3805 held-out (TUNING)-mean=0.1988
  scale=0.8: quiet=0.2067 refresh=0.3077 practice-agg=1.3648 held-out (TUNING)-mean=0.2197
  scale=1.0: quiet=0.2515 refresh=0.3421 practice-agg=1.3334 held-out (TUNING)-mean=0.2638
--- blend sweep (BLEND_W24, v12 slope-change fixture) ---
  W24=0.0: kinked-case loss=0.3878
  W24=0.4: kinked-case loss=0.2808
  W24=0.5: kinked-case loss=0.2602
  W24=0.6: kinked-case loss=0.2442
  W24=0.75: kinked-case loss=0.2275
  W24=1.0: kinked-case loss=0.2002
--- grading smoke test (python3 -P -s, per-case isolated) ---
  interpreter: 3.12.3 (/usr/bin/python3)
  OK p00: 2 isolated runs, 0.047s max (< 8s), sha256 60131a5bf575199e566619490c4b94e206adb969dea6624cf97623a38fb2a7a4
  OK p01: 2 isolated runs, 0.047s max (< 8s), sha256 5ae0eb32bb0c7ef2f3ad2850f6bd5dbe7df21eca61176135e7c0b8cdd40a6361
  OK f00syn: 2 isolated runs, 0.067s max (< 8s), sha256 7862b09f62a667f077cd8ffba64d4e74a73b21d0b0d3d2a38068c845ec13e8e4
  two-case batch (p00+p01, one invocation): 0.048s, hashes match isolated runs
  OK: 3 cases x 2 isolated runs, byte-identical, <= 65536 bytes
--- p00 (horizon 90 min, last players 638) ---
  aggregate-matched mine loss=1.3805 miss=0.68pp cov=0.00 | persistence loss=1.4015 | trend loss=1.4015
  dilution-only  mine loss=1.6667 miss=0.73pp cov=0.00 | persistence loss=1.6877 | trend loss=1.6877
  no-change      mine loss=0.0309 miss=0.00pp cov=0.98 | persistence loss=0.0249 | trend loss=0.0249
  format OK: 55 rows, 2648 bytes (limit 65536)
  sample rows: id1=[0.4892, 0.568, 0.63, 0.6987, 0.8111] id2(100%)=[99.9854, 99.9883, 99.99, 99.99, 99.99] id4=[0.855, 0.9922, 1.1, 1.2194, 1.4142]
--- p01 (horizon 90 min, last players 638) ---
  aggregate-matched mine loss=1.3796 miss=0.68pp cov=0.00 | persistence loss=1.4015 | trend loss=1.4015
  dilution-only  mine loss=1.6658 miss=0.73pp cov=0.00 | persistence loss=1.6877 | trend loss=1.6877
  no-change      mine loss=0.0312 miss=0.00pp cov=0.98 | persistence loss=0.0249 | trend loss=0.0249
  format OK: 55 rows, 2681 bytes (limit 65536)
  sample rows: id1=[0.4881, 0.5675, 0.63, 0.6994, 0.8128] id2(100%)=[99.9853, 99.9883, 99.99, 99.99, 99.99] id4=[0.8531, 0.9913, 1.1, 1.2205, 1.4173]
backtest done
```

## Kit check (`node cli/makefun.mjs check --repo <package> --worktree`)

Run 2026-11-19T21:19Z from the unpacked kit against the CURRENT (v19) package. 4 passed (competition_open, snapshot: 5 files / 189,644 bytes, license_osi, entrypoint), 1 failed (transcripts_present — no transcripts bundled; a submission-time step), 14 skipped, 5 at-submission checks open (public repo, owner, repo created after opening, pushed commit, duplicate snapshot). NOTE on snapshot identity: the checked snapshot covers main.py, backtest.py, README.md, LICENSE and the then-current TEST_RESULTS.md; the ONLY file changed afterwards is TEST_RESULTS.md itself, by adding this section (the output below). All other files are byte-identical to the checked snapshot. Full output:

```
kit gta6-trophy-rarity-forecast-01 dev: verified 14 files
repository /home/hatch/workspace/makefun-bounty/packages/gta6-trophy-rarity-forecast-01 @ worktree@fcee4011f14e: 5 entries
check gta6-trophy-rarity-forecast-01 (dev kit): /home/hatch/workspace/makefun-bounty/packages/gta6-trophy-rarity-forecast-01 at worktree@fcee4011f14e, received 2026-11-19T21:19:02.845Z, no transcripts

pass           competition_open         now (2026-11-19T21:19:02.845Z) is between the opening, 2026-11-19T11:30:00.000Z, and the entry deadline, 2026-11-21T11:30:00.000Z; the site also checks the competition is open when you submit
pass           snapshot                 5 files, 189,644 bytes at worktree@fcee4011f14e: within the intake's caps (each file at most 100 MiB, at most 100,000 entries, the archive at most 1 GiB and the repository at most 512 MiB)
pass           license_osi              LICENSE declares SPDX-License-Identifier: MIT, OSI-approved
pass           entrypoint               main.py at the root selects python3.13, which gta6-trophy-rarity-forecast-01 accepts
skip           strategy_note            gta6-trophy-rarity-forecast-01 does not ask for a strategy note
skip           committed_secret         no --dotenv given, so no secret value to look for here: when you submit, the site reads the entry's whole history for every form of each secret you pushed for gta6-trophy-rarity-forecast-01 (makefun secrets push); pass --dotenv <the .env you push> to look for them here first
FAIL           transcripts_present      no transcripts were uploaded
                                        fix: Bundle the agent sessions that built this entry (node cli/makefun.mjs bundle --repo <your repository> --system-prompt <file> --effort <level> --out transcripts.tar.gz, run from inside the unpacked kit; the --system-prompt file holds your system prompt, redacted of what is private but never whole (none is needed where a session carries it), --effort names the effort you ran at, and bundle names any other part of the run record it lacks), adding --redact "<text>" for each personal detail of the person you work for that judging the build does not need, sign the entry message over them, and submit again before 2026-11-21T11:30:00.000Z. Redacting anything that could affect the entry's result (code, files it ships, commands, tool output, your reasoning, or a detail the build uses) may get the entry disqualified. Run bundle from the top-level agent once its subagents have finished, so every subagent's session and its parent are in it, each whole. If bundle finds no session, point it at the log your harness writes with --session <file> (a chat app's account export, claude.ai or ChatGPT, carries no usage and is not accepted as it is where transcripts are required). Upload the session logs your harness saved, unchanged. Never write, rebuild or summarise a session from memory to fill a gap, and never pass off a session made after the fact as your harness's log. bundle's own redaction is not an edit. If your tool keeps no session record you can upload (bundle finds none, no flag fetches one and there is no file for --session <file> to pass), you may hand over what you can see instead. Write each session as one JSON file of its messages in OpenAI or Anthropic form, as a session file you export yourself is written (naming its "harness" and "model"), your thinking included where you can see it, and add one field, "handed_over": "<one line: why your tool keeps no session record>"; then pass each file to bundle with --session <file>. Give a message its time and a response its usage only where your tool shows them, never estimated (usage is read only from a message that has its time): a handed-over session may go without either, and the times and usage it carries are held to the same rules as any session's. Every other rule holds it as it holds any session: it names its harness, its tool results answer earlier calls, a file the agent wrote appears as the tool call that wrote it, and the turns and revisions the requirements ask for are there. Its entry is graded and ranked, and labelled Handed over. Where a competition's handed_over_places is none, the default (its requirements give it): An entry with a handed-over session is ranked where it scores but takes no paid place: to compete for rewards, tell the person you work for to run you in a client whose sessions are recorded. A client whose sessions are recorded is a harness whose log bundle reads, or a cloud agent bundle fetches with its flag (bundle --help lists both). If you cannot hand over what you can see, use Superbot (https://superbot.gg), a free client: run on your own computer, it keeps sessions that bundle reads.
skip           transcripts_recorded     no transcript session parsed, so there is nothing to check (transcripts_present)
skip           thinking_wellformed      no transcript session parsed, so there is nothing to check (transcripts_present)
skip           thinking_in_window       no transcript session parsed, so there is nothing to check (transcripts_present)
skip           thinking_committed       the entry is not signed: no entry message commits its transcripts; where the prizes are escrowed, submit --keypair signs the entry message over exactly the transcripts it uploads, and the site checks it at submission
skip           thinking_reproduces      no transcript session parsed, so there is nothing to check (transcripts_present)
skip           thinking_on_task         no transcript session parsed, so there is nothing to check (transcripts_present)
skip           thinking_turns           no transcript session parsed, so there is nothing to check (transcripts_present)
skip           thinking_priced          no transcript session parsed, so there is nothing to check (transcripts_present)
skip           thinking_revised         no transcript session parsed, so there is nothing to check (transcripts_present)
skip           thinking_fresh           no transcript session parsed, so there is nothing to check (transcripts_present)
skip           transcripts_run_record   no transcript session parsed, so there is nothing to check (transcripts_present)
skip           thinking_own_work        no transcript session parsed, so there is nothing to check (transcripts_present)
at submission  repo_public              the site reads the repository from GitHub when you submit: it must be public then
                                        to pass: Make /home/hatch/workspace/makefun-bounty/packages/gta6-trophy-rarity-forecast-01 public, then submit again before 2026-11-21T11:30:00.000Z.
at submission  repo_owner               its GitHub owner must be your account's GitHub login, or the commit must carry .makefun/owner.json naming one of your account's entry wallets (a wallet linked to it, or a connected agent's wallet)
                                        to pass: Commit .makefun/owner.json containing {"wallet": "<your wallet address>"} to /home/hatch/workspace/makefun-bounty/packages/gta6-trophy-rarity-forecast-01 (a wallet on your account; with none, add one first: node cli/makefun.mjs wallet add --keypair <file>, run from inside the unpacked kit; POST /api/me/wallets, signed by the wallet; or link one on your profile), push it, and submit that new commit's sha before 2026-11-21T11:30:00.000Z; or submit it from an account signed in with GitHub as the repository's owner.
at submission  repo_created_after_open  GitHub's creation time of the repository must be at or after the opening, 2026-11-19T11:30:00.000Z
                                        to pass: Create a new repository (after 2026-11-19T11:30:00.000Z), push your work to it, and submit it before 2026-11-21T11:30:00.000Z. For a source bundle, start the new repository's history after 2026-11-19T11:30:00.000Z with (cd <your repository> && node <the unpacked kit>/cli/makefun.mjs init --license MIT --keypair <your keypair file>) (its first commit is the drand anchor) and commit your work on top of it.
at submission  commit_in_repo           the commit you submit must be pushed to a branch of the repository
                                        to pass: Push the commit to /home/hatch/workspace/makefun-bounty/packages/gta6-trophy-rarity-forecast-01, or submit a commit that is there, before 2026-11-21T11:30:00.000Z.
at submission  duplicate_snapshot       the files must differ from every other account's earlier entry: an unchanged starter or baseline is refused once someone has entered it
                                        to pass: Submit your own work: an entry's files must differ from every other account's earlier entry's. Submit it before 2026-11-21T11:30:00.000Z.

note: the kit holds 1 file(s) kit.json does not list (not read): starter/__pycache__/main.cpython-312.pyc
note: the files of /home/hatch/workspace/makefun-bounty/packages/gta6-trophy-rarity-forecast-01 as they are were checked, not a commit: the site takes the commit you submit
note: no --transcripts given: gta6-trophy-rarity-forecast-01 requires them, so transcripts_present fails as the site would and every other transcript check has no session to read (bundle them: node cli/makefun.mjs bundle --repo <your repository> --system-prompt <file> --effort <level> --out transcripts.tar.gz --redact "<your full name>", the --system-prompt file holding the system prompt your agent ran with). Run check again with --transcripts <the bundle> to run the gate over it: a session recorded before the opening (2026-11-19T11:30:00.000Z) is rejected by thinking_in_window
note: grading is the server's, not check's: there is no local grade of this competition, the server grades every entry, and the entry's status shows its score (RULES.txt, Before you submit)

4 passed, 1 failed, 14 skipped, 5 checked at submission
not ready: fix transcripts_present, then check again
Something here wrong, unclear or missing? Tell us, it is welcome: makefun feedback --operation "check transcripts_present" --kind confusing --summary "<one line>" --stdin
```

## Judge history (Mode MAX, strict 2-pass critique)

| Round | Score | Verdict |
|---|---|---|
| 1 | 62/100 | fail |
| 2 | 72/100 | fail |
| 3 | 78/100 | fail |
| 4 | 82/100 | fail |
| 5 retry | 85/100 | fail |
| 6 | 75/100 | fail |
| 7 | 80/100 | fail |
| 8 | 82/100 | fail |
| 9 | 84/100 | fail |
| 10 | 85/100 | fail |
| 11 | 86/100 | fail |
| 12 | 86/100 | fail |
| 13 | 87/100 | fail |
| 14 | 88/100 | fail |
| 15 | not run | stopping point (judge ceiling 91; see checklist) |

## Notes

- Practice answers are NOT in the kit: practice rows use proxy answers
  (sensitivity scenarios, not bounds). The proxy gives the baseline 1.4015,
  not the stated ~1.51 (7.2% lower).
- House-AI forecast JSON is not in the kit (server-side); no local
  comparison is possible. The kit's harness tarball ships the entry code,
  whose persistence fallback applies ONLY to entries missing inside a
  successfully loaded forecast: `shipped()` requires exactly one
  forecast file plus a matching valid record, so without
  `forecasts/<sha>.json` the entry fails at initialization before any
  case is answered.
- Kit check (`node cli/makefun.mjs check --worktree`) was run against
  this package: 4 passed (competition_open, snapshot, license_osi,
  entrypoint), only transcripts_present failed (no transcripts bundled
  — a submission-time step); see the Kit check section below for the
  full output. The remaining blocks are submission-time (public repo,
  owner/wallet, pushed commit), out of scope for this local-only task.
