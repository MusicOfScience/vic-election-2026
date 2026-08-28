# Reproducible experimental model bundle

This is the compact, runnable subset used to generate the website’s forecast artefacts. The full research repository contains the upstream acquisition, geography, census and historical-validation pipelines; this bundle contains the frozen inputs required by the public forecast layer.

```bash
python -m pip install -e '.[dev]'
python scripts/run_experimental_forecast.py
python -m pytest -q
```

Material poll-of-polls and Assembly assumptions live in `config/experimental_forecast.yml`; the output manifest records that file's SHA-256 fingerprint. The district output also includes its 2022-anchored starting shares, changes to the 2026 average, effective-contender count, win entropy and guarded by-election signal.

The model is experimental and `production_compatible` remains false. The sealed demographic challenger receives zero central weight because it failed the four-cycle promotion test.
