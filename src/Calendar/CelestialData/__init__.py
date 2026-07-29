# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

'''
Pre-generated calendar tables sourced from celestial-calendar, plus the loader that reads
them.  See `SCHEMA.md` for the frozen data contract.

`Generator.py` is an offline tool: it loads the celestial-calendar dynamic library through
`ctypes` and regenerates `data/`.  It is deliberately not imported from here -- the runtime
path must stay pure Python (the CI matrix includes PyPy, where the dylib does not exist).
Same split as `HkoData/Encoder.py` (offline) vs `HkoData/Decoder.py` (runtime).
'''
