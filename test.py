from utils import ConfigDict


if __name__ == '__main__':
    # dd = ConfigDict(dict(a=1, b=dict(d=2)))
    # print(dd.a)
    # print(dd.b)
    # print(dd.b.d)
    pth = r'D:\Program_self\config_learning\test.py'
    import os.path as osp
    print(osp.splitext(pth)[1])