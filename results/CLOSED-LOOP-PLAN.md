# Closed-loop behaviour experiment — specification and exact patch

Goal: make the fly's turn *caused by* its own descending steering command, so the conflict
manipulation can be scored as behaviour (heading error, drift) instead of only as a readout.
Status: **not yet implemented**; the pre-edit sources are backed up as
`tools/CircuitPreview/Experiment.cs.bak-preclosedloop` and `Program.cs.bak-preclosedloop`.

## Design (frozen-gain, so the result is not circular)

| element | choice |
|---|---|
| Plant | the same model: `headingRad` integrates the turn rate; the visual drive is generated from the **heading error**, not from a scripted yaw |
| Command | `thetaStar(t)` = the existing scripted yaw series (`driveSeries[s]`, i.e. the multi-tone 0.25 Hz waveform) reinterpreted as the *intended* heading |
| Sensory signal | `signal = clamp(thetaStar - headingRad, -1, 1)` — the retinal slip of a fly trying to hold a commanded course |
| Controller | `yaw = clamp(k * lp, -1, 1)` where `lp` is a first-order low-pass of the per-step descending left–right difference |
| Gain `k` | calibrated **once** at alpha = 0, kappa = 300 (bisection on the RMS heading error over a coarse grid of k), then **frozen for every arm, alpha and kappa** |
| Patch | unchanged: `bodySlip = BodySlip * signal`, conflict blends with the shuffled copy, `YawLevel` solves the surround so the expected total is identical |
| Readouts | already recorded: `steer_corr_yaw`, `steer_asym_sd_hz`; **new**: RMS heading error, drift (linear trend of the error), error lag-1 autocorrelation |

Why it is not circular: the loop closes through the *real* circuit, and `k` is fixed before the
manipulation is applied. The prediction is that alpha = 0 tracks (error comparable to the open-loop
baseline), and the error grows monotonically with alpha.

## Exact patch (three edits, ~35 lines)

The yaw site is `Experiment.cs` line ~1097 in `OneTrial`; the DN totals are already maintained at
lines 1193–1194 (per bin) and the step loop calls `c.Step()` at line 1187.

**1. Statics** (next to `Arms`, before `sealed class Trial`):

```csharp
/// <summary>Closed loop: the turn is caused by the circuit's own descending steering command,
/// and the visual drive comes from the heading error rather than from a scripted yaw.</summary>
internal static bool ClosedLoop = false;
internal static float LoopGain = 0f;          // calibrated once at alpha = 0, then frozen
```

**2. Controller inside the step loop** (replace `float signal = driveSeries[s];` … up to
`float bodySlip = BodySlip * signal;`):

```csharp
float signal = driveSeries[s];
if (ClosedLoop && heading)
{
    // per-step descending left-right difference (exact spike counts, not bins)
    long r = 0, l = 0;
    for (int k = 0; k < dnR.Count; k++) { long now = c.SpikeTotal[dnR[k]]; r += now - dnStepPrev[dnL.Count + k]; dnStepPrev[dnL.Count + k] = now; }
    for (int k = 0; k < dnL.Count; k++) { long now = c.SpikeTotal[dnL[k]]; l += now - dnStepPrev[k]; dnStepPrev[k] = now; }
    float steer = (float)(r - l) / Math.Max(1, dnL.Count + dnR.Count);
    lp += (steer - lp) * 0.25f;               // ~2 ms, 4 steps at dt = 0.5 ms
    yawCommand = Math.Clamp(LoopGain * lp, -1f, 1f);
    signal = Math.Clamp(thetaStar(s), -1f, 1f);   // retinal slip of the commanded course
}
```

with, declared next to `float yaw = 0f, headingRad = 0f;` (line 1083):

```csharp
float lp = 0f, yawCommand = 0f, errAcc = 0f, errAcc2 = 0f;
var dnStepPrev = new long[dnL.Count + dnR.Count];
for (int k = 0; k < dnStepPrev.Length; k++) dnStepPrev[k] = 0;
float thetaStar(float s_) => s_;              // the scripted series IS the commanded heading
```

and in the `if (heading)` branch replace `yaw = signal;` with
`yaw = ClosedLoop ? yawCommand : signal;`, accumulating both the error and its square just before
the bin update so the trial record can report `LoopErrRms = sqrt(errAcc2 / n)` and
`LoopErrTrend = errAcc` (slope = Σ t·e / Σ t²).

**3. `Program.cs`**: `--closedloop` and `--loopgain <k>` next to the other switches, passed through
`Experiment.Run(...)` (add two parameters) or assigned to the statics before calling `Run`.

## Calibration and runs

```powershell
# 1) calibrate k once at alpha = 0, kappa = 300, then freeze it
foreach ($k in 2000,5000,10000,20000,50000) {
  dotnet run -c Release -- ..\..\flymind.brain --exp --heading --closedloop --loopgain $k `
    --trials 3 --secs 6 --odor 0.05 --csv ..\..\results\raw\_cal-$k
}
# 2) the experiment: conflict dose x three gains, n = 10
dotnet run -c Release -- ..\..\flymind.brain --exp --heading --conflict --closedloop --loopgain <k> `
  --kappa 300 --trials 10 --secs 6 --odor 0.05 --csv ..\..\results\raw\Q-closedloop
```

Acceptance: `patch_level_ratio ≈ 0.43` (the manipulation still reaches the patch — this check would
have caught the body-lock bug), delivered events identical across arms, and a monotone rise in
RMS heading error with alpha (rho < 0, P <= 1e-3) that replicates at kappa = 150 and 600.

## Measured (rounds 5-12): five findings that cost several rounds to establish

Everything below is in the code as comments with the numbers, so it does not have to be rediscovered.

1. **The pool must be driven by the visual signal, not the motor command.**
   `profile.YawLevel(yaw, …)` was passing the motor command.  Open loop they are the same variable,
   so nothing showed; in closed loop it creates a *dead fixed point*: `yawCommand = 0` → no rotation
   drive for the surround → descending asymmetry 0 → command 0.  Measured before the fix:
   `turned_deg = 0.0` and byte-identical metrics for `LoopGain` = 500, 2000, 8000.
   Fixed: `YawLevel(ClosedLoop ? signal : yaw, patchSignal, level)`.

2. **`turned_deg = 0.0` is the *correct* closed-loop outcome, not a bug.**  `thetaStar` is a
   zero-mean multi-tone, so a loop that tracks returns to its starting heading.  The closed-loop
   readout must therefore be the tracking error, which is why `loop_err_rms` / `loop_err_mean` were
   added to `Trial` and the CSV.

3. **The stabilising sign is positive.**  The descending asymmetry encodes the rotation the eye
   *senses*, which in closed loop *is* the heading error, so `yaw = +k · error` tracks.
   Measured: `-k` diverges to `loop_err_rms = 2.53 rad` against 0.49-0.50 for `+k`.

4. **The asymmetry is sparse and carries a DC bias unrelated to the error.**  2-8 spikes per 20 ms
   bin across ~59 cells per side (`steer ≈ ±0.03`, sign alternating) around a mean of ≈ −0.01.
   Amplifying the raw value pins the command at full turn (`yaw = −1.000` for every bin at
   k ≥ 2000), which is why every earlier gain looked "insensitive".  The controller now drives the
   *deviation* from a running estimate of its own operating point (`loopDc`, τ ≈ 0.7 s).

5. **The usable gain is ~3 orders of magnitude below the first guesses.**  Calibration (κ = 300,
   α = 0, 1 trial × 3 s; no-control reference = the commanded heading's own RMS = 0.5017 rad):

   | k | `loop_err_rms` (flow) | reading |
   |---|---|---|
   | 5 | 0.6149 | worse than no control (out of phase) |
   | 10 | 0.5586 | still worse |
   | 20 | **0.4914** | first value below the no-control reference — tracking just begins |
   | 200-3000 | 0.49-0.55, sometimes pinned at full turn | saturation / jitter |

   The loop is **stable and monotone in k over 5-20**; the next step is 30-100, bounded above by
   the saturation seen at k ≥ 200.  Note these are single-trial runs: the calibration must be
   repeated with n = 3-5 before a gain is frozen and the full dose series is launched.

## Why this was not done in the round that specified it

Implementing it means editing the same trial loop that every reported number comes from. With the
pre-edit sources backed up and the patch above pinned to exact line anchors, the change is
mechanical — but it needs a build plus a two-command smoke test (manipulation check + drive
matching) before the full runs, and that verification budget was not available. Nothing in the
repository is left half-changed: the backup files are inert, and the harness still builds and runs
the corrected `I2`/`J2`/`K2`/`L2`/`M2` families.
