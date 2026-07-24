#!/usr/bin/env bash
set -euo pipefail

# QuantLab Review Package Generator
# Generates a complete ZIP for GPT review

VERSION="${1:-v1.1}"
PHASE="${2:-02}"
ZIP_NAME="QuantLab_Review_Fase_${PHASE}_${VERSION}.zip"

echo "=========================================="
echo "QuantLab Review Package Generator"
echo "Version: ${VERSION}"
echo "Phase: ${PHASE}"
echo "Output: ${ZIP_NAME}"
echo "=========================================="

# Generate tree.txt
echo "Generating tree.txt..."
find . \
  -not -path './.git/*' \
  -not -path './.venv/*' \
  -not -path './__pycache__/*' \
  -not -path './data/*' \
  -not -path './.pytest_cache/*' \
  -not -path './.mypy_cache/*' \
  -not -path './.ruff_cache/*' \
  -not -name '*.pyc' \
  -not -name '.DS_Store' \
  | sort > tree.txt

# Remove old ZIP if exists
rm -f "${ZIP_NAME}" "QuantLab_Review_Fase_${PHASE}_"*.zip

# Create ZIP excluding unwanted files
echo "Creating ZIP..."
zip -r "${ZIP_NAME}" \
  src/ \
  tests/ \
  config/ \
  .github/workflows/ \
  docs/ \
  learning/ \
  reports/ \
  pyproject.toml \
  uv.lock \
  README.md \
  CHANGELOG.md \
  LESSONS_LEARNED.md \
  PROJECT_STATUS.md \
  REVIEW_REQUEST.md \
  tree.txt \
  scripts/generate_review_package.sh \
  .gitleaks.toml \
  -x '*.pyc' \
  -x '__pycache__/*' \
  -x '.pytest_cache/*' \
  -x '.mypy_cache/*' \
  -x '.ruff_cache/*' \
  -x '*.egg-info/*' \
  -x '.venv/*' \
  -x 'data/*' \
  -x '.git/*' \
  -x '.env' \
  -x '*.secret' \
  2>/dev/null || true

echo ""
echo "ZIP created: ${ZIP_NAME}"
echo "Size: $(du -h "${ZIP_NAME}" | cut -f1)"
echo "=========================================="
