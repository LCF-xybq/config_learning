from addict import Dict
from yapf.yapflib.yapf_api import FormatCode


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


def pretty_text(_cfg_dict):
    indent = 4

    def _indent(s_, num_spaces):
        s = s_.split('\n')
        if len(s) == 1:
            return s_
        first = s.pop(0)
        s = [(num_spaces * ' ') + line for line in s]
        s = '\n'.join(s)
        s = first + '\n' + s
        return s

    def _format_basic_types(k, v, use_mapping=False):
        if isinstance(v, str):
            v_str = f"'{v}'"
        else:
            v_str = str(v)
        if use_mapping:
            k_str = f"'{k}'" if isinstance(k, str) else str(k)
            attr_str = f'{k_str}: {v_str}'
        else:
            attr_str = f'{str(k)}={v_str}'
        attr_str = _indent(attr_str, indent)

        return attr_str

    def _format_list(k, v, use_mapping=False):
        # check if all items in the list are dict
        if all(isinstance(_, dict) for _ in v):
            v_str = '[\n'
            v_str += '\n'.join(
                f'dict({_indent(_format_dict(v), indent)}),'
                for v_ in v).rstrip(',')
            if use_mapping:
                k_str = f"'{k}'" if isinstance(k, str) else str(k)
                attr_str = f'{k_str}: {v_str}'
            else:
                attr_str = f'{str(k)}={v_str}'
            attr_str = _indent(attr_str, indent) + ']'
        else:
            attr_str = _format_basic_types(k, v, use_mapping)
        return attr_str

    def _contain_invalid_identifier(dict_str):
        contain_invalid_identifier = False
        for key_name in dict_str:
            contain_invalid_identifier |= \
                (not str(key_name).isidentifier())
        return contain_invalid_identifier

    def _format_dict(input_dict, outest_level=False):
        r = ''
        s = []

        use_mapping = _contain_invalid_identifier(input_dict)
        if use_mapping:
            r += '{'
        for idx, (k, v) in enumerate(input_dict.items()):
            is_last = idx >= len(input_dict) - 1
            end = '' if outest_level or is_last else ','
            if isinstance(v, dict):
                v_str = '\n' + _format_dict(v)
                if use_mapping:
                    k_str = f"'{k}'" if isinstance(k, str) else str(k)
                    attr_str = f'{k_str}: dict{v_str}'
                else:
                    attr_str = f'{str(k)}=dict({v_str}'
                attr_str = _indent(attr_str, indent) + ')' + end
            elif isinstance(v, list):
                attr_str = _format_list(k, v, use_mapping) + end
            else:
                attr_str = _format_basic_types(k, v, use_mapping) + end

            s.append(attr_str)
        r += '\n'.join(s)
        if use_mapping:
            r += '}'
        return r

    cfg_dict = _cfg_dict.to_dict()
    text = _format_dict(cfg_dict, outest_level=True)
    yapf_style = dict(
        based_on_style='pep8',
        blank_line_before_nested_class_or_def=True,
        split_before_expression_after_opening_paren=True
    )
    text, _ = FormatCode(text, style_config=yapf_style, verify=True)

    return text

if __name__ == '__main__':
    model = dict(
        type='Test',
        perc_loss=dict(
            style_weight=       0,
            sacle=[224, 224],
            size=(256,       256)
        )
    )

    model = ConfigDict(model)
    text = pretty_text(model)
    print(text)
