# -*- coding:utf-8 -*-

from functools import wraps

def login_require_test(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        '''内层函数'''
        pass
    return wrapper


@login_require_test
def logout():
    '''logout'''
    pass

if __name__ == '__main__':
    print logout.__name__
    print logout.__doc__