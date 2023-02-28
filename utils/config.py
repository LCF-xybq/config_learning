import ast
import copy
import uuid
import platform
import warnings
import os.path as osp

from addict import Dict
from argparse import Action
from importlib import import_module


def import_modules_from_strings(imports, allow_failed_imports=False):
    """Import modules from the given list of strings.

    Args:
        imports (list | str | None): To be imported module names.
        allow_failed_imports (bool): True => failed import return None.
            False => raise ImportError.

    Returns:
        list[module] | module | None: The imported modules.
    """
    if not imports:
        return
    single_import = False
    if isinstance(imports, str):
        single_import = True
        imports = [imports]
    if not  isinstance(imports, list):
        raise TypeError(f'imports must be list, but got {type(imports)}')
    imported = []
    for imp in imports:
        if not  isinstance(imp, str):
            raise TypeError(f'each to be imported must be str, but got {type(imp)}')
        try:
            imported_tmp = import_module(imp)
        except ImportError:
            if allow_failed_imports:
                warnings.warn(f'failed to import {img}', UserWarning)
                imported_tmp = None
            else:
                raise ImportError
        imported.append(imported_tmp)
    if single_import:
        imported = imported[0]
    return imported


def check_file_exist(filename: str, msg_tmpl='file "{}" does not exist'):
    if not osp.isfile(filename):
        raise FileNotFoundError(msg_tmpl.format(filename))


if platform.system() == 'Windows':
    import regex as re
else:
    import re


BASE_KEY = '_base_'
DELETE_KEY = '_delete_'
DEPRECATION_KEY = '_deprecation_'
RESERVED_KEYS = ['filename', 'text', 'pretty_text']


class ConfigDict(Dict):

    def __missing__(self, key):
        raise KeyError(key)

    def __getattr__(self, item):
        try:
            value = super().__getattr__(item)
        except KeyError:
            ex = AttributeError(f"'{self.__class__.__name__}' has no "
                                f"attribute '{item}'")
        except Exception as e:
            ex = e
        else:
            return value
        raise ex


class Config:
    """A facility for config and config files.

    It supports common file formats as configs: python/json/yaml. The interface
    is the same as a dict object and also allows access config values as
    attributes.

    Example:
        >>> cfg = Config(dict(a=1, b=dict(b1=[0, 1])))
        >>> cfg.a
        1
        >>> cfg.b
        {'b1': [0, 1]}
        >>> cfg.b.b1
        [0, 1]
        >>> cfg = Config.fromfile('tests/data/config/a.py')
        >>> cfg.filename
        "/home/kchen/projects/mmcv/tests/data/config/a.py"
        >>> cfg.item4
        'test'
        >>> cfg
        "Config [path: /home/kchen/projects/mmcv/tests/data/config/a.py]: "
        "{'item1': [1, 2], 'item2': {'a': 0}, 'item3': True, 'item4': 'test'}"
    """
    @staticmethod
    def _validata_py_syntax(filename):
        with open(filename, encoding='utf-8') as f:
            content = f.read()
        try:
            ast.parse(content)
        except SyntaxError as e:
            raise SyntaxError(f'file {filename}: {e}')

    @staticmethod
    def _substitute_predefined_vars(filename, temp_config_name):
        file_dirname = osp.dirname(filename)
        file_basename = osp.basename(filename)
        file_basename_no_ext = osp.splitext(file_basename)[0]
        file_extname = osp.splitext(filename)[1]
        support_templates = dict(
            fileDirname=file_dirname,
            fileBasename=file_basename,
            fileBasenameNoExtension=file_basename_no_ext,
            fileExtname=file_extname
        )
        with open(filename, encoding='utf-8') as f:
            config_file = f.read()
        for key, value in support_templates.items():
            regexp = r'\{\{\s*' + str(key) + r'\s*\}\}'
            value = value.replace('\\', '/')
            config_file = re.sub(regexp, value, config_file)
        with open(temp_config_name, 'w', encoding='utf-8') as tmp_config_file:
            tmp_config_file.write(config_file)

    @staticmethod
    def _pre_substitute_base_vars(filename, temp_config_name):
        """Substitute base variable placehoders to string."""
        with open(filename, encoding='utf-8') as f:
            config_file = f.read()
        base_var_dict = {}
        """
        Explanations from ChatGPT.

        This is a regular expression pattern, 
            written in Python syntax, that can be used to match strings 
            that match a specific pattern. 
            Here's what each part of the pattern means:

        `r` at the beginning of the string indicates 
            that it is a "raw string", meaning that 
            backslashes are treated as literal characters 
            instead of escape characters.

        `\{\{` matches the characters "{{" in the input string.
            The backslashes are used to escape the curly braces, 
            which have special meaning in regular expressions.

        `\s*` matches zero or more whitespace characters (spaces, tabs, newlines, etc.).

        `_base_` matches the literal string "base".

        `\.`` matches a literal period character.

        `([\w\.]+)` matches one or more characters that are either 
            letters, digits, underscores, or periods. 
            The parentheses indicate a capturing group, 
            which means that this part of the pattern can be referred to later.

        `\s*` matches zero or more whitespace characters.

        `\}\}`` matches the characters "}}".

        So this regular expression can be used to match strings 
            that look like "{{ _base_.some_text }}" or 
            "{{ _base_.some.nested.text }}". 
            The part that matches the "some_text" or "some.nested.text" 
            is captured and can be used later in the code.
        """
        regexp = r'\{\{\s*' + BASE_KEY + r'\.([\w\.]+)\s*\}\}'
        base_vars = set(re.findall(regexp, config_file))
        """
        _base_.some_text ==> _.some_text_uuid1
        _base_.some.nested.text ==> _.some.nested.text_uuid2
        """
        for base_var in base_vars:
            randstr = f'_{base_var}_{uuid.uuid4().hex.lower()[:6]}'
            base_var_dict[randstr] = base_var
            regexp = r'\{\{\s*' + BASE_KEY + r'\.' + base_var + r'\s*\}\}'
            config_file = re.sub(regexp, f'"{randstr}"', config_file)
        with open(temp_config_name, 'w', encoding='utf-8') as tmp_config_file:
            tmp_config_file.write(config_file)
        """
        {
            '_.some_text_uuid1': '_base_.some_text',
            '_.some.nested.text_uuid2': '_base_.some.nested.text'
        }
        """
        return base_var_dict

    @staticmethod
    def _substitute_base_vars(cfg, base_var_dict, base_cfg):
        """Substitute variable strings to their actual values."""
        cfg = copy.deepcopy(cfg)

        if isinstance(cfg, dict):
            for k, v in cfg.items():
                if isinstance(v, str) and v in base_var_dict:
                    new_v = base_cfg
                    for new_k in base_var_dict[v].split('.'):
                        new_v = new_v[new_k]
                    cfg[k] = new_v
                elif isinstance(v, (list, tuple, dict)):
                    cfg[k] = Config._substitute_base_vars(v, base_var_dict, base_cfg)
        elif isinstance(cfg, tuple):
            cfg = tuple(
                Config._substitute_base_vars(c, base_var_dict, base_cfg)
                for c in cfg
            )
        elif isinstance(cfg, list):
            cfg = [
                Config._substitute_base_vars(c, base_var_dict, base_cfg)
                for c in cfg
            ]
        elif isinstance(cfg, str) and cfg in base_var_dict:
            new_v = base_cfg
            for new_k in base_var_dict[cfg].split('.'):
                new_v = new_v[new_k]
            cfg = new_v
        return cfg


class DictAction(Action):
    pass