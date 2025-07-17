#!/bin/bash

# Patch audiolazy for Python 3.10+ compatibility (Iterable/Iterator imports)

# Manually specify the audiolazy installation directory for garden environment
AUDIOLAZY_DIR="/Users/audible-garden/miniconda3/envs/garden/lib/python3.12/site-packages/audiolazy"

echo "Patching audiolazy in: $AUDIOLAZY_DIR"

# Check if directory exists
if [ ! -d "$AUDIOLAZY_DIR" ]; then
    echo "Error: audiolazy directory not found at $AUDIOLAZY_DIR"
    exit 1
fi

# Patch lazy_analysis.py (the main issue causing the error)
echo "Patching lazy_analysis.py..."
sed -i '' 's/from collections import deque, Sequence, Iterable/from collections import deque\
from collections.abc import Sequence, Iterable/' "$AUDIOLAZY_DIR/lazy_analysis.py"

# Patch lazy_core.py
echo "Patching lazy_core.py..."
if [ -f "$AUDIOLAZY_DIR/lazy_core.py" ]; then
    sed -i '' 's/from collections import Iterable/from collections.abc import Iterable/' "$AUDIOLAZY_DIR/lazy_core.py"
fi

# Patch lazy_stream.py
echo "Patching lazy_stream.py..."
if [ -f "$AUDIOLAZY_DIR/lazy_stream.py" ]; then
    sed -i '' 's/from collections import Iterable, deque/from collections.abc import Iterable\
from collections import deque/' "$AUDIOLAZY_DIR/lazy_stream.py"
fi

# Patch lazy_misc.py
echo "Patching lazy_misc.py..."
if [ -f "$AUDIOLAZY_DIR/lazy_misc.py" ]; then
    sed -i '' 's/from collections import deque, Iterable/from collections import deque\
from collections.abc import Iterable/' "$AUDIOLAZY_DIR/lazy_misc.py"
fi

# Patch lazy_filters.py
echo "Patching lazy_filters.py..."
if [ -f "$AUDIOLAZY_DIR/lazy_filters.py" ]; then
    sed -i '' 's/from collections import Iterable, OrderedDict/from collections.abc import Iterable\
from collections import OrderedDict/' "$AUDIOLAZY_DIR/lazy_filters.py"
fi

# Patch lazy_poly.py
echo "Patching lazy_poly.py..."
if [ -f "$AUDIOLAZY_DIR/lazy_poly.py" ]; then
    sed -i '' 's/from collections import Iterable, deque, OrderedDict/from collections.abc import Iterable\
from collections import deque, OrderedDict/' "$AUDIOLAZY_DIR/lazy_poly.py"
fi

# Patch lazy_itertools.py
echo "Patching lazy_itertools.py..."
if [ -f "$AUDIOLAZY_DIR/lazy_itertools.py" ]; then
    sed -i '' 's/from collections import Iterator/from collections.abc import Iterator/' "$AUDIOLAZY_DIR/lazy_itertools.py"
fi

echo "audiolazy patch complete."
echo "You can now try importing audiolazy again."