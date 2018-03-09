# -*- coding: utf-8 -*-

from functions import *

__author__ = 'wangyongjun'

wkdir = os.getcwd()


class AdbClient:
    # 初始化
    def __init__(self, device_id):
        config_file = "{0}\default.conf".format(wkdir)
        config_parser = ConfigParser()
        config_parser.read(config_file, encoding='UTF-8')

        self.device_id = device_id
        self.is_front_battery_test = True if config_parser.get('config', 'is_front_battery_test') == '1' else False
        self.is_back_battery_test = True if config_parser.get('config', 'is_back_battery_test') == '1' else False
        self.is_monkey_test = True if config_parser.get('config', 'is_monkey_test') == '1' else False
        self.is_startup_test = True if config_parser.get('config', 'is_startup_test') == '1' else False
        self.package = config_parser.get('config', 'package')
        self.activity = config_parser.get('config', 'activity')
        self.monkey_count = config_parser.get('config', 'monkey_count')
        self.monkey_seed = config_parser.get('config', 'monkey_seed')
        self.startup_times = config_parser.get('config', 'startup_times')
        self.backstage_sleep_minutes = config_parser.get('config', 'backstage_sleep_minutes')

        print('GOT CONFIG INFO:\n'
              '==================================================\n'
              'package = {0}\n'
              'activity = {1}\n'
              'monkey_count = {2}\n'
              'monkey_seed = {3}\n'
              'startup_times = {4}\n'
              'is_front_battery_test = {5}\n'
              'is_back_battery_test = {6}\n'
              'is_monkey_test = {7}\n'
              'is_startup_test = {8}\n'
              'backstage_sleep_minutes = {9}\n'
              '==================================================\n'
              'DEVICE ID = {10}\n'
              '==================================================\n'
              .format(self.package,
                      self.activity,
                      self.monkey_count,
                      self.monkey_seed,
                      self.startup_times,
                      self.is_front_battery_test,
                      self.is_back_battery_test,
                      self.is_monkey_test,
                      self.is_startup_test,
                      self.backstage_sleep_minutes,
                      self.device_id))

        # # 获取device信息
        # start_adb()
        # time.sleep(1)
        # self.device_id = get_device_id_list()[0]
        # print('DEVICE ID: \n{0}'.format(self.device_id))

        self.all_stats = dict()

    def startup_test(self):
        """
        启动时间测试
        :return:
        """
        # 冷启动
        cold_startup_time = cold_startup(self.device_id, self.package, self.activity, times=self.startup_times)
        if cold_startup_time:
            self.all_stats['ColdStartupTime'] = cold_startup_time

        # 热启动
        hot_startup_time = hot_startup(self.device_id, self.package, self.activity, times=self.startup_times)
        if hot_startup_time:
            self.all_stats['HotStartupTime'] = hot_startup_time

    def monkey_test(self):
        """
        monkey测试
        :return:
        """
        start_monkey(self.device_id, self.package, self.monkey_count, self.monkey_seed)

    def front_battery_test(self):
        """
        前台运行耗电测试
        :return:
        """
        # 重置电量信息
        is_reset = reset_battery(self.device_id)
        if not is_reset:
            print("重置手机电量出现错误")

        self.monkey_test()

        # todo 精确控制时间

        # 下载、收集电量信息
        dump_battery_log(self.device_id)
        front_power_use = get_batterystats_by_pkg(self.package)
        if front_power_use:
            self.all_stats['FrontPowerUse'] = front_power_use

    def back_battery_test(self):
        """
        后台静默耗电测试
        :return:
        """
        # 重置电量信息
        reset_battery(self.device_id)
        backstage_app(self.device_id, self.package, self.activity)

        # 等待5分钟
        time.sleep(60 * int(self.backstage_sleep_minutes))
        print("后台静默{0}分钟".format(self.backstage_sleep_minutes))

        # 下载、收集电量信息
        dump_battery_log(self.device_id)
        front_power_use = get_batterystats_by_pkg(self.package)
        if front_power_use:
            self.all_stats['BackPowerUse'] = front_power_use


def auto():
    wkdir = os.getcwd()
    all_stats = dict()

    # 获取monkey配置信息
    config_file = "{0}\default.conf".format(wkdir)
    config = get_config(config_file)
    print('Get Config:\nPackage = {0}\nCount = {1}\nSeed = {2}'.format(config['package'], config['monkey_count'], config['monkey_seed']))
    is_front_battery_test = True if config['is_front_battery_test'] == '1' else False
    is_back_battery_test = True if config['is_back_battery_test'] == '1' else False
    is_monkey_test = True if config['is_monkey_test'] == '1' else False
    is_startup_test = True if config['is_startup_test'] == '1' else False

    # 获取device信息
    start_adb()
    time.sleep(1)
    device_id = get_device_id_list()[0]
    print('current device id: {0}'.format(device_id))

    # 重置电量信息
    if is_front_battery_test:
        is_reset = reset_battery(device_id=device_id)
        if not is_reset:
            print("重置手机电量出现错误")

    # 执行monkey测试
    if is_monkey_test:
        start_monkey(device_id, config['package'], config['monkey_count'], config['monkey_seed'])

    # 下载、收集电量信息
    if is_front_battery_test:
        dump_battery_log(device_id=device_id)
        front_power_use = get_batterystats_by_pkg(package=config['package'])
        if front_power_use:
            all_stats['FrontPowerUse'] = front_power_use

    # 后台静默耗电测试
    if is_back_battery_test:
        backstage_app(device_id, config['package'], config['activity'])
        reset_battery(device_id=device_id)
        time.sleep(seconds=300)


    # 启动耗时测试
    if is_startup_test:
        # 冷启动
        cold_startup_time = cold_startup(device_id, config['package'], config['activity'], times=config['startup_times'])
        if cold_startup_time:
            all_stats['ColdStartupTime'] = cold_startup_time

        # 热启动
        hot_startup_time = hot_startup(device_id, config['package'], config['activity'], times=config['startup_times'])
        if hot_startup_time:
            all_stats['HotStartupTime'] = hot_startup_time

    print(all_stats)

