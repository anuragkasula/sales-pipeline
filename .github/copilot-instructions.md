# Copilot instructions for this repo

- Python 3.12, standard library only in `src/`. No pandas.
- Every change to `src/pipeline/transform.py` needs a matching test in `tests/`.
- Environment-specific values belong in `config/<env>.json`, never hard-coded.
- Never print or log secret values; only whether they are set.
- When reviewing PRs, flag: missing tests, hard-coded env values, and changes to
  `.github/workflows/` that touch the `prod` environment.
