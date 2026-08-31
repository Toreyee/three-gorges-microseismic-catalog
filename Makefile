.PHONY: models audit test manuscript-catalog figures release-audit manifest verify-core verify

models:
	python scripts/00_verify_models.py --model-dir models/regional --prefix diting --check-companion-pt

audit:
	python scripts/08_catalog_quality.py --repo-root . --output docs/catalog_quality_metrics.json --fail-on-structural-error

test:
	python -m pytest

manuscript-catalog:
	python scripts/10_verify_manuscript_catalog.py --repo-root . --output-dir build/manuscript-catalog --report docs/manuscript_catalog_verification.json

figures:
	python scripts/reproduce_figures.py --repo-root . --catalog-mode manuscript --report docs/figure_reproduction_report.json

release-audit:
	python scripts/11_release_audit.py --repo-root . --output docs/release_audit.json

manifest:
	python scripts/09_write_manifest.py --repo-root . --output SHA256SUMS

verify-core: models release-audit audit test manuscript-catalog
verify: verify-core figures manifest
