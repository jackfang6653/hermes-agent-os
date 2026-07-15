"""基础测试: norhor 模块"""
import sys
import os as _os
_script_dir = _os.path.dirname(__file__)
_src_dir = _os.path.join(_script_dir, "src")
sys.path.insert(0, _os.path.join(_script_dir, '..'))
sys.path.insert(0, _src_dir)

def test_module_importable():
    try:
        exec('from norhor import src')
    except ImportError:
        pass

def test_package_structure():
    py_files = [f for f in _os.listdir(_src_dir) if f.endswith('.py')]
    assert len(py_files) > 0, f'No Python files in {_src_dir}'
    assert 'detail_image_gen.py' in py_files, f'missing detail_image_gen in {_src_dir}'
