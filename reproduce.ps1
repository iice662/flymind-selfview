# One-command reproduction of every number in the paper.
#
#   pwsh -File reproduce.ps1 -Tier figures     # seconds: redraw all figures from the deposited CSVs
#   pwsh -File reproduce.ps1 -Tier stats       # ~1 min: re-run every statistic and the Bayes self-check
#   pwsh -File reproduce.ps1 -Tier sims        # ~45 min: re-run every simulation family (needs the blob)
#   pwsh -File reproduce.ps1 -Tier all         # sims + stats + figures
#
# Nothing here needs the 3 GB source data: the circuit blob flymind.brain (21 MB, in the
# repository) is the single source of truth, and the CSVs in results/raw/ are the deposited
# per-trial outputs.  Only -Tier source needs the MaleCNS v1.0 feathers (see README).

param(
    [ValidateSet('figures', 'stats', 'sims', 'all', 'source')]
    [string]$Tier = 'figures'
)

$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
$raw = Join-Path $root 'results\raw'
$blob = Join-Path $root 'flymind.brain'
$cp = Join-Path $root 'tools\CircuitPreview'

function Step($msg) { Write-Host "`n=== $msg ===" -ForegroundColor Cyan }

function Sims {
    Step 'simulation families (I/J/K/L/M are the families reported in the paper)'
    Push-Location $cp
    try {
        # primary heading experiment, corrected body-lock drive (n = 10, kappa = 300)
        dotnet run -c Release -- $blob --exp --heading --conflict --kappa 300 --trials 10 --secs 6 --odor 0.05 --csv "$raw\I-heading"
        # n = 20 replication (raises the Bayes-factor ceiling to 3.24)
        dotnet run -c Release -- $blob --exp --heading --kappa 300 --trials 20 --secs 6 --odor 0.05 --csv "$raw\J-n20"
        # gain replication
        dotnet run -c Release -- $blob --exp --heading --conflict --kappa 150 --trials 6 --secs 6 --odor 0.05 --csv "$raw\K-k150"
        dotnet run -c Release -- $blob --exp --heading --conflict --kappa 600 --trials 6 --secs 6 --odor 0.05 --csv "$raw\L-k600"
        # patch-size dose
        dotnet run -c Release -- $blob --dose --heading --kappa 300 --trials 10 --secs 6 --odor 0.05 --fracs 0,0.125,0.25,0.5 --csv "$raw\M-dose"
        # optic flow (unchanged by the body-lock correction)
        dotnet run -c Release -- $blob --exp --kappa 300 --trials 10 --secs 3 --odor 0.05 --csv "$raw\A3-flow"
        # positive controls and propagation
        dotnet run -c Release -- $blob --exp --heading --controls --kappa 300 --trials 10 --secs 6 --odor 0.05 --csv "$raw\D-controls"
        dotnet run -c Release -- $blob --propagate --kappa 300 --kappas 100,300,1000 --odor 0.05
    }
    finally { Pop-Location }
}

function Stats {
    Step 'statistics, equivalence tests and Bayes factors'
    python (Join-Path $root 'tools\compare_trials.py') --selftest
    foreach ($fam in 'I-heading', 'J-n20', 'K-k150', 'L-k600', 'M-dose', 'A3-flow', 'D-controls') {
        $trials = Join-Path $raw "$fam-trials.csv"
        if (Test-Path $trials) {
            Write-Host "  $fam"
            python (Join-Path $root 'tools\compare_trials.py') $trials
        }
    }
    foreach ($fam in 'I-heading', 'K-k150', 'L-k600', 'M-dose') {
        $trials = Join-Path $raw "$fam-trials.csv"
        if (Test-Path $trials) { python (Join-Path $root 'tools\conflict_trend.py') $trials }
    }
    Step 'checking the manuscript numbers against the deposited data'
    python (Join-Path $root 'tools\verify_headline_numbers.py')
}

function Figures {
    Step 'figures'
    python (Join-Path $root 'tools\make_main_figures.py')
    python (Join-Path $root 'tools\make_figures.py')
}

function Source {
    Step 'rebuilding the circuit blob from the released MaleCNS v1.0 feathers (needs ~4 GB of downloads)'
    Push-Location (Join-Path $root 'tools\CircuitBuilder')
    try { dotnet run -c Release -- (Join-Path $root 'malecns\edges.bin') (Join-Path $root 'malecns\annotations.tsv') $blob 12000 1 (Join-Path $root 'malecns\transmitters.tsv') }
    finally { Pop-Location }
}

switch ($Tier) {
    'figures' { Figures }
    'stats' { Stats }
    'sims' { Sims }
    'source' { Source }
    'all' { Sims; Stats; Figures }
}
Step 'done'
