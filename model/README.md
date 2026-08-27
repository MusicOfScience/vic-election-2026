# Reproducible experimental model bundle

This is the compact, runnable subset used to generate the website’s forecast artefacts. The full research repository contains the upstream acquisition, geography, census and historical-validation pipelines; this bundle contains the frozen inputs required by the public forecast layer.

```bash
python -m pip install -e '.[dev]'
python scripts/run_experimental_forecast.py --simulations 5000 --seed 20260826
python -m pytest -q
```

The model is experimental and `production_compatible` remains false. The sealed demographic challenger receives zero central weight because it failed the four-cycle promotion test.
