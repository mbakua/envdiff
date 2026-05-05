# envdiff

> Utility to diff environment variable sets across deployment stages and flag mismatches.

---

## Installation

```bash
pip install envdiff
```

Or install from source:

```bash
pip install git+https://github.com/yourname/envdiff.git
```

---

## Usage

Compare environment variable files across stages:

```bash
envdiff staging.env production.env
```

**Example output:**

```
[MISSING in production]  DATABASE_POOL_SIZE
[MISSING in staging]     NEW_RELIC_LICENSE_KEY
[MISMATCH]               LOG_LEVEL  staging=DEBUG  production=INFO
```

You can also compare more than two files at once:

```bash
envdiff dev.env staging.env production.env
```

Use `--strict` to exit with a non-zero status code if any mismatches are found (useful in CI pipelines):

```bash
envdiff staging.env production.env --strict
```

Use `--ignore` to skip specific keys:

```bash
envdiff staging.env production.env --ignore SECRET_KEY,DEBUG
```

---

## Supported Formats

- `.env` files (key=value pairs)
- Exported shell variables
- JSON key-value maps

---

## License

This project is licensed under the [MIT License](LICENSE).