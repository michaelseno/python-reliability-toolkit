# Seed Strategy

Seeds control deterministic randomness for chaos injection.

## Why Seeds Matter

- Same seed + same profile + same test input => reproducible chaos pattern
- Different seed => different injection pattern and broader robustness coverage

## Standard Convention

### 1) Fixed Lane (reproducible)

- `latency_light` => `21`
- `checkout_fault` => `7`

Use fixed seeds for deterministic triage and CI reproducibility.

### 2) Daily Deterministic Lane (exploratory)

Use a UTC date+profile-derived seed so each day explores a different pattern,
while reruns on the same day/profile remain reproducible.

## Recommended Usage

```bash
# fixed lane
reliabilitykit run --chaos latency_light --seed 21 -- tests/e2e -m chaos

# exploratory sweep
reliabilitykit run --chaos latency_light --seed 21 --repeat 3 -- tests/e2e -m chaos
reliabilitykit run --chaos latency_light --seed 22 --repeat 3 -- tests/e2e -m chaos
```

## Related Commands

- `reliabilitykit chaos list`
- `reliabilitykit chaos show <profile>`
- `make run-chaos-ci-latency`
- `make run-chaos-ci-fault`
