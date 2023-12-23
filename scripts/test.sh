#!/bin/bash
set -euxo pipefail

poetry run pytest -s --cov=wallgarden/ --cov=tests --cov-report=term-missing ${@-} --cov-report html
