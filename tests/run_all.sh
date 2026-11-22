#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
GODOT="${GODOT:-./.tools/godot}"

"$GODOT" --headless --path . --import

for suite in \
	tests/test_runner.gd \
	tests/scenarios/regression_runner.gd \
	tests/scenarios/light_runner.gd \
	tests/scenarios/basement_runner.gd
do
	echo "== $suite"
	"$GODOT" --headless --path . --script "res://$suite"
done