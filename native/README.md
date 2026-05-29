# newskoo_native

C++17 acceleration for NewsKoo's hot paths — text normalization, 64-bit SimHash,
and Hamming-distance dedup helpers — exposed to Python via **pybind11** and built
with **CMake** (driven by **scikit-build-core**).

Python never imports this module directly: `newskoo.core.accel` is a facade that
prefers `newskoo_native` when present and otherwise uses pure-Python fallbacks.
So the backend runs with or without this extension built; building it just makes
the hot paths faster.

## API

| Function | Signature | Notes |
|----------|-----------|-------|
| `normalize` | `(str) -> str` | lowercase + whitespace-collapse, UTF-8 byte-safe |
| `simhash64` | `(str) -> int` | 64-bit SimHash over whitespace/alnum tokens |
| `simhash_tokens` | `(list[str]) -> int` | SimHash over caller-supplied tokens |
| `hamming` | `(int, int) -> int` | Hamming distance between two 64-bit hashes |
| `hamming_table` | `(int, list[int]) -> list[int]` | distances from one hash to many |
| `nearest` | `(int, list[int]) -> (int, int)` | `(index, distance)` of the closest hash |

Semantics match the pure-Python fallbacks in `backend/newskoo/core/accel.py`.

## Build

Requires a C++17 compiler and CMake **>= 3.15**. The dev WSL image ships cmake
3.16.3, which is sufficient — no PyPI cmake wheel is pulled.

### As a Python package (recommended)

```bash
# from the repo root
uv pip install ./native
# or, editable (the backend already wires this via [tool.uv.sources])
uv pip install -e ./native
```

The backend's `pyproject.toml` declares `newskoo-native` as an editable path
dependency and an optional extra:

```bash
cd backend && uv sync --extra native   # build + install the extension
```

### Standalone CMake build (for iterating on the C++)

```bash
cd native
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j
# build/ now holds newskoo_native*.so; put it on PYTHONPATH to import it
```

## Verify

```bash
python -c "import newskoo_native as n; \
print(n.normalize('  Hello\tWORLD ')); \
print(n.hamming(n.simhash64('the quick brown fox'), \
                n.simhash64('the quick brown foxes')))"
```

`backend/tests/test_native.py` exercises the module and is skipped automatically
(`pytest.importorskip`) when the extension is not built.
