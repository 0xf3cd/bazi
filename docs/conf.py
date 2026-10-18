# Copyright (C) 2026 Ningqi Wang (0xf3cd) <https://github.com/0xf3cd>

import os
import sys
from pathlib import Path

'''构建身份由 run_docs 显式提供；变量缺失即失败，不回退到默认分支或版本。'''
ROOT = Path(os.environ['BAZI_DOC_ROOT']).resolve()
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tests'))
sys.path.insert(0, str(Path(__file__).resolve().parent / '_ext'))

project = 'bazi'
language = 'zh_CN'
extensions = [
  'sphinx.ext.autodoc', 'sphinx.ext.doctest', 'sphinx.ext.linkcode',
  'myst_parser', 'house_docstrings', 'typeddict_fields', 'knowledge_catalog',
]
source_suffix = {'.rst': 'restructuredtext', '.md': 'markdown'}
exclude_patterns = ['_build']
html_theme = 'alabaster'
html_title = 'bazi · ' + os.environ['BAZI_DOC_VERSION']
html_show_sourcelink = False
html_show_copyright = False
html_static_path = ['_static']
html_css_files = ['documentation.css']
html_theme_options = {
  'description': '排盘、关系与独立知识查阅',
  'extra_nav_links': {'全部版本': 'https://0xf3cd.github.io/bazi/versions/'},
}
nitpicky = True
nitpick_ignore = [('py:class', 'DataclassInstance')]
autodoc_preserve_defaults = True
autodoc_typehints = 'description'

from source_links import linkcode_resolve as resolve_source, missing_reference

linkcode_resolve = resolve_source


def setup(app):
  app.connect('missing-reference', missing_reference)
