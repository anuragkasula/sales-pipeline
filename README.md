# sales-pipeline — a DataOps promotion practice repo

A deliberately tiny pipeline (CSV -> clean -> revenue by region) whose only job is to
let you practise **code change -> PR -> CI -> dev -> uat -> prod** on GitHub.

```
feature/*  --PR-->  dev  --PR-->  uat  --PR-->  main
                     |             |              |
                 deploys to    deploys to     deploys to prod
                   DEV           UAT        (needs your approval, gets tagged)
```

| Piece | File | What it shows |
|---|---|---|
| CI | `.github/workflows/ci.yml` | Lint + tests on every PR; reused by deploy |
| CD | `.github/workflows/deploy.yml` | Branch -> environment mapping, env-scoped secrets, approval gate, concurrency, prod tags |
| Promotion | `.github/workflows/promote.yml` | One-click promotion PR listing exactly which commits move |
| Config per env | `config/*.json` | Same code, different behaviour (prod filters orders < 5) |
| Copilot | `.github/copilot-instructions.md` | Repo rules Copilot follows when writing/reviewing |
| Governance | `CODEOWNERS`, PR template | Who must approve what |

Run locally:
```bash
pip install -r requirements-dev.txt
pytest -v
APP_ENV=dev  PYTHONPATH=src python -m pipeline.main
APP_ENV=prod PYTHONPATH=src python -m pipeline.main   # notice East drops the 3.00 order
```

---

## One-time setup (~15 min)

1. **Create a public repo** on GitHub (public so environment approvals work on a free plan).
   Replace `YOUR_GITHUB_USERNAME` in `.github/CODEOWNERS`.
2. **Push and create the environment branches:**
   ```bash
   git init && git add . && git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/<you>/sales-pipeline.git
   git push -u origin main
   git checkout -b uat && git push -u origin uat
   git checkout -b dev && git push -u origin dev
   ```
3. **Settings -> Environments:** create `dev`, `uat`, `prod`.
   - Add a secret `DB_PASSWORD` to each with a *different* value.
   - On `prod`: add yourself as a **required reviewer**, and under deployment branches allow only `main`.
4. **Settings -> Rules -> Rulesets** (or Branches -> protection) for `dev`, `uat`, `main`:
   require a pull request, require status check `lint-and-test`, block force pushes.
   (Solo tip: set required approvals to 0 or you'll be stuck unable to approve your own PR.)
5. **Settings -> Actions -> General:** tick *"Allow GitHub Actions to create and approve pull requests"* (needed by `promote.yml`).
6. **Copilot:** if you have access, turn on Copilot code review so you can add Copilot as a PR reviewer.

---

## Drills

### Drill 1 — A normal feature, all the way to prod
Business ask: *"Also report order count per region."*
```bash
git checkout dev && git pull
git checkout -b feature/order-count
```
- Change `revenue_by_region` (or add `orders_by_region`) in `transform.py`. Try having Copilot
  draft it, then ask Copilot Chat to *"write a pytest for this following copilot-instructions.md"*.
- `pytest`, commit, `git push -u origin feature/order-count`.
- Open PR **feature/order-count -> dev**. Watch CI run. Add Copilot as reviewer, read its comments.
- **Squash merge.** Watch *Deploy* run against `dev` (check the Actions log: `SALES_DEV`).
- Actions -> *Promote* -> `dev-to-uat`. Review the PR (it lists the commits). **Merge commit, not squash.**
- Deploy runs against `uat`.
- *Promote* -> `uat-to-main`. Merge. Deploy **pauses** waiting for your approval -> approve -> prod runs -> tag `prod-N` created.

Look at: `git log --oneline --graph --all` after each step. That graph is the answer to "how does promotion work".

### Drill 2 — CI blocks a bad change
Break a test on purpose (e.g. change `.title()` to `.upper()`), open a PR to `dev`. Merge button is blocked.
Fix it in a new commit on the same branch; the PR re-runs automatically.

### Drill 3 — Config-only change
Change `min_amount` in `config/uat.json` only. Promote it. Note that code didn't change but behaviour in UAT did —
that's why config lives in the repo and goes through the same review.

### Drill 4 — Hotfix in prod
Prod bug found while `dev` has unfinished work you *don't* want in prod.
```bash
git checkout main && git pull
git checkout -b hotfix/negative-amounts
# fix, test, push, PR -> main, approve deploy
```
Then **back-merge**: open PRs `main -> uat` and `uat -> dev` (or cherry-pick). Skip this and the next
promotion from dev will "undo" or conflict with your hotfix — try skipping it once to see it happen.

### Drill 5 — Rollback
Something bad reached prod. On the merged PR in GitHub click **Revert**, which opens a revert PR into `main`.
Merge it -> deploy runs -> prod is back. Then decide whether dev/uat need the revert too.

### Drill 6 — Merge conflict during promotion
Edit the same line of `transform.py` differently on `dev` and on `uat` (via a hotfix). Try promoting dev -> uat and resolve:
```bash
git checkout dev && git pull && git merge origin/uat   # resolve, commit, push; the PR updates
```

---

## Gotchas worth saying out loud in an interview

- **Squash into `dev`, merge-commit for promotions.** Squashing dev -> uat makes uat's history differ from dev's,
  so the next promotion shows old commits again and conflicts appear from nowhere.
- **PRs opened with `GITHUB_TOKEN` don't trigger other workflows** (anti-recursion rule), so CI won't
  auto-run on PRs from `promote.yml`. Fixes: use a GitHub App token / PAT, or protection relies on the deploy-time
  `test` job. Knowing this is a strong signal you've actually done it.
- **Build once, deploy many** is the ideal: this repo re-runs from source per environment (simple, common for
  dbt/Airflow code), whereas for containers you'd build an image once in dev and promote the *same digest*.
- **Environment-scoped secrets + required reviewers** are the approval gate; branch protection is the code gate.
- **`concurrency`** prevents two deploys to the same env racing each other.
- **Alternative model:** trunk-based — one `main` branch, deploy the same commit to dev -> uat -> prod via
  environments in a single workflow with approval gates. Fewer long-lived branches, no back-merges.
  Be ready to compare it to branch-per-environment (what this repo does).

## Mapping to real stacks you'd mention
- dbt: `dbt build --target $APP_ENV` with profiles per env; Slim CI with `state:modified+` on PRs.
- Airflow: sync DAGs to an env-specific S3 bucket / MWAA environment in the deploy step.
- Snowflake: deploy to `DB_DEV` / `DB_UAT` / `DB_PROD`, zero-copy clone prod into UAT for realistic tests.
