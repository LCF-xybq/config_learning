import copy


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
                cfg[k] = _substitute_base_vars(v, base_var_dict, base_cfg)
    elif isinstance(cfg, tuple):
        cfg = tuple(
            _substitute_base_vars(c, base_var_dict, base_cfg)
            for c in cfg
        )
    elif isinstance(cfg, list):
        cfg = [
            _substitute_base_vars(c, base_var_dict, base_cfg)
            for c in cfg
        ]
    elif isinstance(cfg, str) and cfg in base_var_dict:
        new_v = base_cfg
        for new_k in base_var_dict[cfg].split('.'):
            new_v = new_v[new_k]
        cfg = new_v
    return cfg


if __name__ == '__main__':
    cfg = dict(
        model=dict(a='place', b='B'),
        body='MSDC',
        key=['lq', 'gt'],
        scale=('width','height')
    )
    base_cfg = dict(
        A=1,
        B=2,
        H=256,
        W=224
    )
    base_var_dict = {
        'place' : 'A',
        'lq' : 'B',
        'height' : "H",
        'width' : 'W',
    }
    cfg = _substitute_base_vars(cfg, base_var_dict, base_cfg)
    print(cfg)