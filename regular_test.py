import uuid
import platform

if platform.system() == 'Windows':
    import regex as re
else:
    import re

BASE_KEY = '_base_'

regexp = r'\{\{\s*' + BASE_KEY + r'\.([\w\.]+)\s*\}\}'

str = "{{_base_.1.ab}}" \
      "{{  _base_.2.cd}}" \
      "{{_base_.3.ef.gh    }}" \
      "{{_base_.a.yu    }}"

base_vars = set(re.findall(regexp, str))

base_var_dict = {}

for base_var in base_vars:
    randstr = f'_{base_var}_{uuid.uuid4().hex.lower()[:6]}'
    base_var_dict[randstr] = base_var
    regexp = r'\{\{\s*' + BASE_KEY + r'\.' + base_var + r'\s*\}\}'
    str = re.sub(regexp, f'"{randstr}"', str)

print(str)