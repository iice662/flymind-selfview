# Receptive-field mapping — status, findings, and what is still needed

## What is running

`python tools/receptive_field.py --full`, detached, logging to `results/raw/receptive-field2.log`
(the earlier attempts at `receptive-field.log` and `receptive-field3.log` were killed by the
environment — detached processes are reaped here, so completion must never be assumed; check
`Get-Process python` and the log's freshness). It streams the 6.8 GB `malecns/syn-partners.feather`
batch by batch (the machine has ~3 GB RAM free, so the table cannot be loaded) and, for each of the
2,689 visual-pool cells, accumulates the centroid of its postsynaptic sites
(`x_post`, `y_post`, `z_post`) — the receptive-field proxy — plus the number of input synapses.
Output lands in one write at the end: `results/receptive-field.csv`.

The scan is not resumable: if it dies, re-running starts from row 0.

## The decoder work this round (`tools/arrow_columns.py`)

`decode_batch` guessed each column's buffer width from the size of the next buffer; one wrong guess
shifted every later column, which is why `primary_post`, `type`, `somaSide` and `somaLocation` all
decoded as empty strings. The replacement reads the width from the schema (`type_id`:
Int/Float 2 buffers, plain Utf8 3) and the *bit width* from the buffer length
(`>= 8n` → int64/float64, else int32/float32). Verified on batch 0 of `syn-partners`:

| column | result |
|---|---|
| `x_pre`, `y_pre`, `z_pre`, `x_post`, `y_post`, `z_post` | correct (int32), e.g. `[36730, 36730, 37603]` |
| `body_pre`, `body_post` | correct (int64), e.g. `[339821567, 405401280, …]` |
| `conf_pre`, `conf_post` | correct (float32), e.g. `[0.798, 0.798, 0.796]` |
| `primary_post` | **still unresolved** |

## Why `primary_post` resists, and why it does not block the mapping

`primary_post` is **dictionary-encoded**: the record batch carries only `[validity, indices]`
(2 buffers, not the 3 a plain Utf8 column has — which is why the schema plan totals 23 buffers
while the batch has 22), and the string values live in a separate DictionaryBatch that the reader
does not parse. Two ways forward:

1. **Parse the DictionaryBatch** (the correct fix): in `iter_batches`, also yield messages with
   `mtype == 2` (DictionaryBatch), decode the dictionary's values buffer, and index into it.
   This also restores the 14-column annotation table (`type`, `somaSide`, `somaLocation`).
2. **Ignore the labels.** The mapping needs *positions*, not names: `x_post/y_post/z_post` decode
   correctly, and the dictionary *index* (if decoded) would group sites into compartments anyway.

**The running scan uses option 2** — it accumulates coordinates and synapse counts only, so its
`top_neuropil` columns will be empty. That is enough for step 1 of the objective (rebuild the body
patch as a visual-field region); it is *not* enough to name the compartments (lobula plate vs
lobula vs medulla), which needs fix 1.

One consequence to remember when reading the CSV: without `primary_post` the sites cannot be
restricted to optic-lobe neuropil, so a cell's centroid includes whatever non-optic input it has.
Pool cells are lobula-plate tangential cells, so this is a second-order effect — but the
`input_synapses` and site-count columns should be used to check for cells whose centroid is an
outlier before they are trusted.

## Next steps (in order)

1. When `results/receptive-field.csv` appears: `tools/patch_from_rf.py` (to be written) selects the
   cells whose RF centroid falls within ±θ₀ of the frontal field, θ₀ chosen to give ≈672 cells
   (same size as the soma-space patch); **the field-of-view assumption must be stated explicitly in
   the script header**, because that is the modelling choice a reviewer will attack.
2. Add `--patchfile` to `tools/CircuitPreview/Program.cs` + a `PatchFromFile` next to
   `CompactPatch` in `Experiment.cs` (~20 lines), then re-run:
   `--exp --heading --conflict --patchfile results/raw/rf-patch.txt --kappa 300 --trials 10 --secs 6`
   → `N-rfpatch`, and compare against `I2-heading` with `python tools\digest.py N-rfpatch I2-heading`.
   Pass condition: `patch_level_ratio ≈ 0.43` (the manipulation still reaches the patch) and effects
   of the same sign and magnitude as the soma-space patch.
3. Fix the DictionaryBatch parsing (option 1) to recover the neuropil labels and the 14-column
   annotation table.
