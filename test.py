

if __name__ == '__main__':
    a = dict(b=dict(c=2))
    for k, v in a.items():
        res = v.pop('efef', False)
        print(res)
        print(v)