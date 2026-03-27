# Project audit TODO (2026-03-27)

## Critical
- [ ] **URGENT: remove leaked private SSH key from repository history and rotate it immediately**.
  - File: `src/_project/settings/sudo apt-get install -y nginx` (contains full private key material).
  - Actions:
    1. Revoke/rotate compromised key everywhere it was used.
    2. Remove file from git and purge it from history (`git filter-repo`/BFG).
    3. Add secret scanning in CI (`gitleaks`/`trufflehog`).

- [ ] **Move all hardcoded secrets/API keys to environment variables**.
  - Affected examples: Django `SECRET_KEY`, `SECRET_API_TOKEN`, IP geolocation token, payment gateway keys/salts.
  - Actions:
    1. Replace literals with `env()` lookups.
    2. Add `.env.example` without secrets.
    3. Rotate exposed tokens/keys.

## High priority
- [ ] **Fix test architecture: no network calls on import**.
  - `src/moderation/test_paytr.py` executes `requests.post(...)` at module import time.
  - This breaks `python manage.py test` in offline/proxied CI and causes nondeterministic tests.
  - Actions:
    1. Convert this file into proper Django/pytest tests.
    2. Mock external HTTP (`responses`/`requests-mock`).
    3. Keep integration tests behind explicit marker/flag.

- [ ] **Address Django system warnings**.
  - `ManyToManyField(..., null=True)` has no effect and should be removed.
  - Actions:
    1. Remove `null=True` from M2M fields.
    2. Generate and apply migrations.

- [ ] **Stop using unsupported CKEditor 4 package**.
  - `django-ckeditor` warns about unsupported CKEditor 4 and known security issues.
  - Actions:
    1. Plan migration to CKEditor 5 package.
    2. Validate license and data compatibility.

## Medium priority
- [ ] **Harden production settings**.
  - Current settings include `DEBUG = True` and permissive `CORS_ALLOW_ALL_ORIGINS = True`.
  - Actions:
    1. Create strict production profile.
    2. Enforce secure cookie flags and restricted CORS/hosts.

- [ ] **Expand automated tests**.
  - Many app test files are placeholders only.
  - Actions:
    1. Add smoke tests for URLs/views.
    2. Add model validation tests.
    3. Add payment callback signature-validation tests.

- [ ] **Clean repository hygiene issues**.
  - Suspicious file names and legacy duplicate modules (`tasks_old.py`, `product_import_old.py`) increase maintenance risk.
  - Actions:
    1. Archive/remove dead code with changelog note.
    2. Add pre-commit hooks (formatting, import sort, secret scan, lint).

## Nice to have
- [ ] Document local/CI quality gates in README (`check`, `test`, lint, secret scan).
- [ ] Add architecture note for payment providers and callback verification flow.
