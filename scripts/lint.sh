#!/bin/bash
set -euo pipefail

# if arg --fix is passed, fix the code
enable_fix=0
black_flag="--check --diff"
isort_flag="--check --diff"
if [[ $# -eq 1 ]] && [[ $1 == "--fix" ]]; then
    enable_fix=1
    black_flag=""
    isort_flag=""
fi

set -x

poetry run mypy --ignore-missing-imports -p gredditwallpaper
poetry run isort $isort_flag gredditwallpaper/ tests/ --line-length 150
poetry run black $black_flag gredditwallpaper/ tests/ --line-length 150
poetry run flake8 gredditwallpaper/ tests/
poetry run safety check
poetry run bandit -r gredditwallpaper/