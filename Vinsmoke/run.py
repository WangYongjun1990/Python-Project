# -*- coding: utf-8 -*-
import time
import traceback

from auto_start import auto_start

__author__ = 'wangyongjun'


if __name__ == '__main__':
    try:
        auto_start()
    except Exception as err:
        traceback.print_exc()
        print(err)
        time.sleep(3)
        input('ERROR:发生错误, 按【回车键】退出...')


