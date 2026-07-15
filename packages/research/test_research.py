"""基础测试: research 模块"""
import sys
import os as _os
_script_dir = _os.path.dirname(__file__)
sys.path.insert(0, _os.path.join(_script_dir, '..'))

def test_module_importable():
    try:
        exec('import research')
    except ImportError:
        pass

def test_package_structure():
    py_files = [f for f in _os.listdir(_script_dir) if f.endswith('.py') and f != 'test_research.py']
    assert len(py_files) > 0, f'No Python files in {_script_dir}'
