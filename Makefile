.PHONY: check test web export secrets

# Run this after: uv sync --dev
# On Windows: use Git Bash or install make via `winget install GnuWin32.Make`

check: secrets
	uv run ruff check src/ tests/ scripts/
	uv run pyright src/
	uv run pytest tests/ -q
	uv run python scripts/check_claims.py

test:
	uv run pytest tests/ -x --tb=short

web:
	cd web && npm run dev

export:
	uv run python scripts/export_web_data.py

secrets:
	@if grep -rn \
		-e "sk-ant-api" \
		-e "sk-[a-zA-Z0-9]\{20\}" \
		-e "ANTHROPIC_API_KEY\s*=\s*['\"]" \
		-e "OPENAI_API_KEY\s*=\s*['\"]" \
		src/ tests/ scripts/ cassettes/ results/ runs/ 2>/dev/null; then \
		echo "ERROR: possible API key literal in source"; exit 1; \
	fi
	@echo "secrets scan: ok"
