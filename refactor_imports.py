import os
import re
from pathlib import Path

BASE_DIR = Path('c:/Users/madha/OneDrive/Documents/03.CAPSTONE/NovaNest/NovaNest')
PYTHON_DIR = BASE_DIR / 'python'

# 1. Create __init__.py everywhere in python/
for root, dirs, files in os.walk(PYTHON_DIR):
    init_path = Path(root) / '__init__.py'
    if not init_path.exists():
        with open(init_path, 'w') as f:
            f.write('')

# 2. Map every python file to its absolute package path
# e.g., 'clv.py' -> 'intelligence.customer.clv'
module_map = {}
for root, _, files in os.walk(PYTHON_DIR):
    for file in files:
        if file.endswith('.py') and file != '__init__.py':
            filepath = Path(root) / file
            rel_path = filepath.relative_to(PYTHON_DIR)
            mod_path = '.'.join(rel_path.with_suffix('').parts)
            module_name = rel_path.stem
            module_map[module_name] = mod_path

print('Generated module map:', len(module_map), 'modules found.')

# 3. Refactor all python files in python/ to use absolute imports for local modules
def refactor_imports(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    rel_file = Path(file_path).relative_to(BASE_DIR)
    if 'python' in rel_file.parts:
        pkg_parts = rel_file.relative_to('python').parent.parts
        pkg_prefix = '.'.join(pkg_parts)
        
        # from .module import
        content = re.sub(r'from\s+\.(\w+)\s+import', f'from {pkg_prefix}.\\1 import', content)
        
        # from ..module import
        def replace_double_dot(m):
            parent_pkg = '.'.join(pkg_parts[:-1])
            if parent_pkg:
                return f'from {parent_pkg}.{m.group(1)} import'
            return f'from {m.group(1)} import'
            
        content = re.sub(r'from\s+\.\.(\w+)\s+import', replace_double_dot, content)
        
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

for root, _, files in os.walk(PYTHON_DIR):
    for file in files:
        if file.endswith('.py'):
            refactor_imports(os.path.join(root, file))

# 4. Refactor Streamlit pages
def refactor_streamlit_page(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    new_lines = []
    added_clean_sys_path = False
    
    for line in lines:
        if 'sys.path.append' in line:
            if not added_clean_sys_path:
                new_lines.append('import sys\n')
                new_lines.append('from pathlib import Path\n')
                new_lines.append('BASE_DIR = Path(__file__).resolve().parent.parent.parent if "pages" in str(Path(__file__)) else Path(__file__).resolve().parent.parent\n')
                new_lines.append('if str(BASE_DIR / "python") not in sys.path:\n')
                new_lines.append('    sys.path.append(str(BASE_DIR / "python"))\n')
                new_lines.append('if str(BASE_DIR / "streamlit_app") not in sys.path:\n')
                new_lines.append('    sys.path.append(str(BASE_DIR / "streamlit_app"))\n')
                added_clean_sys_path = True
            continue 
            
        match = re.match(r'^from\s+(\w+)\s+import\s+(.+)$', line.strip())
        if match:
            mod_name = match.group(1)
            imports = match.group(2)
            if mod_name in module_map:
                line = f'from {module_map[mod_name]} import {imports}\n'
                
        new_lines.append(line)
        
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)

for file in os.listdir(BASE_DIR / 'streamlit_app'):
    if file.endswith('.py'):
        refactor_streamlit_page(BASE_DIR / 'streamlit_app' / file)
        
for file in os.listdir(BASE_DIR / 'streamlit_app' / 'pages'):
    if file.endswith('.py'):
        refactor_streamlit_page(BASE_DIR / 'streamlit_app' / 'pages' / file)

print('Refactoring complete.')
