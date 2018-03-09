# -*- coding: utf-8 -*-
import os
import platform
import time
# import logging

from configparser import ConfigParser

import subprocess

__author__ = 'wangyongjun'


# logging.basicConfig(
#     level=logging.DEBUG,
#     format="[%(asctime)s] %(name)s:%(levelname)s: %(message)s"
# )


def follow(thefile):
    thefile.seek(0, 2)
    while True:
        line = thefile.readline()
        if not line:
            time.sleep(0.1)
            continue
        yield line


def only_num(s, oth=''):
    """
    匹配传入字符串中所有数字，并返回
    :param s:
    :param oth:
    :return:
    """
    num = '0123456789'
    s2 = ''
    for c in s:
        if c in num:
            s2 += c
    return s2


def get_config(config):
    """
    获取配置信息，返回配置字典
    :param config:
    :return:
    """
    config_dict = dict()
    if os.path.exists(config):
        config_parser = ConfigParser()
        config_parser.read(config, encoding='UTF-8')

        config_dict['package'] = config_parser.get('config', 'package')
        config_dict['is_monkey_test'] = config_parser.get('config', 'is_monkey_test')
        config_dict['is_front_battery_test'] = config_parser.get('config', 'is_front_battery_test')
        config_dict['is_back_battery_test'] = config_parser.get('config', 'is_back_battery_test')
        config_dict['is_startup_test'] = config_parser.get('config', 'is_startup_test')
        config_dict['monkey_count'] = config_parser.get('config', 'monkey_count')
        config_dict['monkey_seed'] = config_parser.get('config', 'monkey_seed')
        config_dict['startup_times'] = config_parser.get('config', 'startup_times')
        config_dict['activity'] = config_parser.get('config', 'activity')
    else:
        print('No {0} file found'.format(config))

    return config_dict


def start_adb():
    """
    初始化adb
    :return:
    """
    cmd = "adb devices"
    print('cmd: {}'.format(cmd))
    if platform.system() == 'Windows':
        subprocess.check_output(cmd, shell=True)
    time.sleep(2)


def get_device_id_list():
    """返回 device id"""
    time.sleep(1)
    cmd = "adb devices | findstr /e device"  # /e 对一行的结尾进行匹配
    print('cmd:{0}'.format(cmd))
    try:
        output = subprocess.check_output(cmd, shell=True).decode()
        print(output)
        print('connected devices:\r{0}'.format(output))
        if output is not None:
            output = output.split("\n")
            print('split connect devices id: {0}'.format(output))
            device_id_list = []

            for row in output:
                if row == "":
                    continue
                device_id = row.replace("\tdevice\r", "")
                device_id_list.append(device_id)
                print('device_id_list: {0}'.format(device_id_list))

        return device_id_list

    except Exception as err:
        # traceback.print_exc()
        print('All device lost, @{0}'.format(__file__))
        print(err)


def start_monkey(device_id, package, count, seed):
    """
    执行monkey测试
    :param device_id: 设备号
    :param package: 被测包名
    :param count: 随机事件次数
    :param seed: 随机种子
    :return:
    """
    print('Start Monkey...')

    monkey_cmd = 'adb -s {0} shell monkey -p {1} --pct-touch 35 --pct-motion 15 --pct-appswitch 5 --pct-rotation 5 --pct-trackball 25 --pct-nav 0 --pct-syskeys 15 --pct-flip 0 --pct-majornav 0 --throttle 300 --ignore-crashes --ignore-timeouts --ignore-security-exceptions --ignore-native-crashes --monitor-native-crashes -s {2} -v -v -v {3} > info.txt'.format(
        device_id, package, seed, count)

    print('monkey_cmd:{0}'.format(monkey_cmd))

    try:
        output = subprocess.check_output(monkey_cmd, shell=True).decode()
        print(output)

    except Exception as err:
        print('start_monkey ERROR, @{0}'.format(__file__))
        print(err)


def reset_battery(device_id):
    """
    重置手机电量信息
    :param device_id:
    :return:
    """
    cmd = "adb -s {0} shell dumpsys batterystats --reset".format(device_id)
    print('cmd:{0}'.format(cmd))
    succ_flag = False
    try:
        output = subprocess.check_output(cmd, shell=True).decode()
        print(output)
        if "Battery stats reset" in output:
            succ_flag = True

    except Exception as err:
        print(err)
    return succ_flag


def dump_battery_log(device_id):
    """
    下载batterystats日志到logs\battery.log
    :param device_id:
    :return:
    """
    cmd = r"adb -s {0} shell dumpsys batterystats > logs\battery.log".format(device_id)
    print('cmd:{0}'.format(cmd))

    try:
        output = subprocess.check_output(cmd, shell=True).decode()
        print(output)
    except Exception as err:
        print(err)


def get_batterystats_by_pkg(package):
    """
    根据包名，获取所持进程耗电量信息
    :param package:
    :return:
    """
    uid = None
    search_key = None
    use_flag = False
    power_use = None
    with open(r"logs\battery.log", "r") as f:
        for line in f.readlines():
            if not uid and "\"" + package + "\"" in line:
                uid = line[line.find('=') + 1:line.find(':')]
                search_key = "Estimated power use"
            if search_key and search_key in line:
                use_flag = True
            if use_flag and uid in line:
                print(line)
                power_use_list = line.split(' ')
                for i in range(len(power_use_list)):
                    if uid in power_use_list[i]:
                        power_use = power_use_list[i + 1]
                        break
                break
    return power_use


def kill_app(device_id, package):
    """
    关闭app
    :param device_id: 
    :param package: 
    :return: 
    """
    time.sleep(3)
    cmd = 'adb -s {0} shell am force-stop {1}'.format(device_id, package)
    print('cmd:{0}'.format(cmd))
    try:
        subprocess.check_output(cmd, shell=True)
    except Exception as err:
        print(err)


def start_app(device_id, package, activity):
    """
    启动app，返回本次启动时间float型
    :param device_id:
    :param package:
    :param activity:
    :return:
    """
    time.sleep(3)
    elapse_time = None
    cmd = "adb -s {0} shell am start -W {1}/{2}".format(device_id, package, activity)
    print('cmd:{0}'.format(cmd))
    try:
        output = subprocess.check_output(cmd, shell=True).decode()
        # 如果启动app有错误
        if output.find('Error') >= 0:
            print('Start APP Error, @{0}'.format(__file__))
        else:
            wait_time_key = 'WaitTime:'
            total_time_key = 'TotalTime:'
            this_time_key = 'ThisTime:'
            if output.find(total_time_key) >= 0:
                flag = output.find(total_time_key)
                elapse_time = only_num(output[flag + 10:flag + 16])
            elif output.find(wait_time_key) >= 0:
                flag = output.find(wait_time_key)
                elapse_time = only_num(output[flag + 10:flag + 16])
            elif output.find(this_time_key) >= 0:
                flag = output.find(this_time_key)
                elapse_time = only_num(output[flag + 9:flag + 15])

    except Exception as err:
        print(err)
    return float(elapse_time)


def cold_startup(device_id, package, activity, times=5):
    """
    冷启动耗时测试,返回平均启动时间
    :param device_id:
    :param package:
    :param activity:
    :param times:
    :return:
    """
    times = int(times)
    time_list = list()
    average_time = 0
    for i in range(times):
        kill_app(device_id, package)
        elapse_time = start_app(device_id, package, activity)
        if elapse_time:
            time_list.append(elapse_time)

    if time_list:
        print(time_list)
        average_time = smart_average(time_list)

    return average_time


def smart_average(num_list):
    """
    科学求平均方法
    :param num_list:
    :return:
    """
    max_time = 0
    min_time = 99999
    sum_time = 0.0
    for i in range(len(num_list)):
        tmp = num_list[i]
        if tmp > max_time:
            max_time = tmp
        if tmp < min_time:
            min_time = tmp
    num_list.remove(max_time)
    num_list.remove(min_time)
    for i in num_list:
        sum_time += i
    average_time = sum_time / len(num_list)
    return average_time


def back_home(device_id):
    """
    返回主界面
    :param device_id:
    :return:
    """
    time.sleep(3)
    # 返回主菜单
    cmd = 'adb -s {0} shell input keyevent 3'.format(device_id)
    print('cmd:{0}'.format(cmd))
    try:
        subprocess.check_output(cmd, shell=True)
    except Exception as err:
        print(err)


def backstage_app(device_id, package, activity):
    """
    让被测app处于后台运行
    :param device_id: 
    :param package: 
    :param activity: 
    :return: 
    """
    time.sleep(3)
    cmd = "adb -s {0} shell am start -W {1}/{2}".format(device_id, package, activity)
    print('cmd:{0}'.format(cmd))
    try:
        output = subprocess.check_output(cmd, shell=True).decode()

        # 如果启动app有错误
        if output.find('Error') >= 0:
            print('backstage_app error, @{0}'.format(__file__))
        else:
            time.sleep(10)
            back_home(device_id)

    except Exception as err:
        print(err)


def hot_startup(device_id, package, activity, times=5):
    """
    热启动耗时测试，返回平均启动时间
    :param device_id:
    :param package:
    :param activity:
    :param times:
    :return:
    """
    # 确保被测app处于后台运行状态
    backstage_app(device_id, package, activity)

    times = int(times)
    time_list = list()
    average_time = 0
    for i in range(times):
        elapse_time = start_app(device_id, package, activity)
        back_home(device_id)
        if elapse_time:
            time_list.append(elapse_time)

    if time_list:
        print(time_list)
        average_time = smart_average(time_list)

    return average_time
    
if __name__ == "__main__":
    # is_ok = reset_battery('172.26.27.7:5555')
    # print(is_ok)
    # dump_battery_log('172.26.27.7:5555')
    # power_use = get_batterystats_by_pkg('cn.memedai.mmd.debug')
    # print(power_use)
    get_device_id_list()
