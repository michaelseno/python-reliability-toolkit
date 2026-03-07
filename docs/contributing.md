# Contributing

## Test Architecture Rules

The e2e suite uses a Page Object Model structure and should remain layered:

- `tests/e2e/pages/`: page-level actions and selectors
- `tests/e2e/components/`: shared UI blocks (header, language, notification)
- `tests/e2e/flows/`: reusable multi-step behaviors
- `tests/e2e/assertions/`: shared assertions
- `tests/e2e/data/`: test datasets and parametrize inputs
- `tests/e2e/tests/`: test intent only (no low-level selector plumbing)

## Engineering Principles

- **SOLID**: one responsibility per page/flow/component, avoid god objects
- **DRY**: centralize selectors and repeated behavior
- **KISS**: keep page methods short and explicit
- **SMART**: each test should have a single, measurable intent

## E2E Authoring Checklist

- Add selectors in page/component classes, not test modules
- Reuse flow helpers for repeated steps
- Keep assertions domain-focused and deterministic
- Prefer `data-test` selectors in pages/components
- Avoid sleeps/timeouts in tests unless there is no reliable event
- Keep chaos tests explicitly marked with `@pytest.mark.chaos`

## Validation Before PR

```bash
make test-unit
python -m pytest tests/e2e
make run
```
