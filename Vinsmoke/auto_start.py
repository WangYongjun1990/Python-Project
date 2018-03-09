# -*- coding: utf-8 -*-
from adb_client import AdbClient
from functions import *

__author__ = 'wangyongjun'


def auto_start():
    # 获取device信息
    start_adb()

    device_id_list = get_device_id_list()
    print('DEVICE ID LIST: \n{0}'.format(device_id_list))

    for device_id in device_id_list:
        print('CURRENT DEVICE ID: \n{0}'.format(device_id))

        ac = AdbClient(device_id)

        if ac.is_startup_test:
            ac.startup_test()

        if ac.is_monkey_test:
            if ac.is_front_battery_test:
                ac.front_battery_test()
            else:
                ac.monkey_test()

        if ac.is_back_battery_test:
            ac.back_battery_test()

        print(ac.all_stats)

        result_dict = ac.all_stats

        # 保存测试结果到execl
        # sr = SaveResult(result_dict)

    # todo 多台设备多线程运行


if __name__ == '__main__':
    auto_start()