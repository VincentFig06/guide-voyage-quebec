#!/usr/bin/env bash
# Régénère docs/ comme copie exacte et à jour de src/, pour GitHub Pages.
# docs/ ne doit jamais être édité à la main : ce script est la seule source de vérité.
set -euo pipefail
cd "$(dirname "$0")/.."

rm -rf docs
mkdir -p docs
cp -R src/. docs/

echo "docs/ régénéré à partir de src/ ($(find docs -type f | wc -l | tr -d ' ') fichiers)."
