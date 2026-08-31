# Inference model artifacts

The repository includes the four TorchScript checkpoints used by the archived AIpick/DiTing inference workflow, plus the matching `.pt` files retained for provenance:

- `regional/diting.eqt.jit` / `regional/diting.eqt.pt`
- `regional/diting.rnn.jit` / `regional/diting.rnn.pt`
- `regional/diting.unet.jit` / `regional/diting.unet.pt`
- `regional/diting.lppnl.jit` / `regional/diting.lppnl.pt`

The eight files supplied for this release are byte-identical to the checkpoint snapshot already present in the historical working archive. The TorchScript files were additionally verified with `torch.jit.load(..., map_location="cpu")` during release preparation.

| Model | TorchScript SHA-256 | PyTorch SHA-256 |
|---|---|---|
| EQT | `0951EA097CA23953D0BC74059738DCCBB4892A096FE6E44555EF378C674CADAA` | `EE8BDD1B892F20C019934459C94CDA105D5C7FD489DD2E9EAED96D76CA803EBC` |
| RNN | `04399FDD925D7C779A8FC8D94DCD5E01D406D037CC076C4A580CBE5ED129C784` | `FEFD44008FB36D919089A6148AF5EC435628CD8C172823479586A197BFD7AD07` |
| U-Net | `5CA74668292BC81DBB8BCB5497A73EC8EB7ACBFFE963AA1A5A4E7A1F27CFE561` | `B78ACB9EEA703E634AF00117E83A3B72958BF0F9D0773048432E283E90AF0E61` |
| LPPNL | `CCF823196E280D4387F48C6361A2ED3D2F4F87A86304CF1F96F13918718B7A0C` | `CE83EB50EF79666A7CEB40CB3E44FD90A7E136192018B0AF0D4490E742CC4550` |

Verify the inference checkpoints with:

```bash
python scripts/00_verify_models.py --model-dir models/regional --prefix diting --check-companion-pt --load
```

Run phase picking with:

```bash
python scripts/02_pick_phases.py \
  --ym-path /path/to/prepared/waveforms \
  --ckpt-dir models/regional \
  --checkpoint-prefix diting \
  --out-pick-dir build/picks \
  --out-cnt-dir build/pick-counts \
  --models eqt,rnn,unet,lppnl \
  --year 2018 --months 1-12 --device cpu
```

The file names retain the historical `diting` prefix; they are not renamed to `SX.*`. `scripts/02_pick_phases.py` still accepts another prefix through `--checkpoint-prefix` if an alternate checkpoint set must be tested.

These artifacts support **inference reproducibility**. The supplied materials do not contain a complete manuscript-specific fine-tuning program, training split manifest, random seeds, and environment lock sufficient to claim training-from-scratch reproducibility. Technical verification is complete. Public redistribution of the checkpoints still requires approval by the repository owners and relevant model/data providers; see `models/LICENSE.md`.
