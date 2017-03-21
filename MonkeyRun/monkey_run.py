# coding: utf-8

import time
import random
import logging
import os
import subprocess
import platform
import traceback
import threading
from ConfigParser import ConfigParser


logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(name)s:%(levelname)s: %(message)s"
)
wkdir = os.getcwd()

def mkdir(path):
    # 去除首位空格
    path = path.strip()
    # 去除尾部 \ 符号
    path = path.rstrip("\\")
 
    # 判断路径是否存在
    # 存在     True
    # 不存在   False
    isExists = os.path.exists(path)
 
    # 判断结果
    if not isExists:
        # 创建目录操作函数
        os.makedirs(path)
        return True
    else:
        return False

def get_config(config_file):
    if os.path.exists(config_file) is True:
        config_parser = ConfigParser()
        config_parser.read(config_file)

        package = config_parser.get('config', 'package')
        count = config_parser.get('config', 'count')
        seed = config_parser.get('config', 'seed')
    else:
        logging.error('No {0} file found'.format(config_file))

    return package, count, seed

def start_adb():
    cmd = "adb devices"
    logging.debug('cmd:{}'.format(cmd))
    if platform.system() == 'Windows':
        subprocess.check_output(cmd, shell=True)
    time.sleep(2)

def get_device_id():
    '''返回 device id'''
    device_dict = {}
    get_device_id_cmd = "adb devices | findstr /e device"   # /e 对一行的结尾进行匹配

    try:
        output = subprocess.check_output(get_device_id_cmd, shell=True)
        logging.debug('connected devices:\r{0}'.format(output))
        if output is not None:
            output = output.split("\n")
            logging.debug('split connect devices id: {0}'.format(output))
            device_id_list = []

            for device_id in output:
                if device_id == "":
                    continue
                device_id = device_id.replace("\tdevice\r", "")
                logging.debug('device_id: {0}'.format(device_id))
                device_id_list.append(device_id)
            logging.debug('device_id_list: {0}'.format(device_id_list))

        return device_id_list

    except Exception:
        #traceback.print_exc()
        logging.info('All device lost, @{0} line:{1}'.format(__file__, sys._getframe().f_lineno))
        output = None



def get_device_model(device_id):
    device_model = ""
    get_device_model_cmd = "adb -s {0} shell getprop ro.product.model".format(device_id)
    logging.debug(get_device_model_cmd)

    try:
        output_model = subprocess.check_output(get_device_model_cmd, shell=True)
        logging.debug("output_model: {0}".format(output_model))
    except Exception:
        logging.error('get device model error, @{0} line:{1}'.format(__file__, sys._getframe().f_lineno))
        traceback.print_exc()
        output_model = None

    if output_model is not None:
        output_model = output_model.strip("\r\r\n") # 去除行尾的换行光标
        logging.debug(output_model)
        output_model = output_model.split(' ')
        logging.debug(output_model)

    for i in output_model:
        device_model += i

    return device_model


def follow(thefile):
    thefile.seek(0,2)
    while True:
        line = thefile.readline()
        if not line:
            time.sleep(0.1)
            continue
        yield line


def screenshot(error_type, device_id, device_model):    
    logging.info("screenshot_start")
    img_path = wkdir + "\img"
    img_tmp_path = "/data/local/tmp/tmp.png"
    timestamp = time.strftime('%Y-%m-%d-%H-%M-%S',time.localtime(time.time()))
    if error_type == 'NOT RESPONDING':
        error_type = 'NOT-RESPONDING'
    img_name = device_model + '-Error-[' + error_type + ']-' + timestamp
    cmd_screenshot = "adb -s {0} shell screencap -p ".format(device_id) + img_tmp_path
    logging.info("cmd_screenshot: {0}".format(cmd_screenshot))

    output = subprocess.check_output(cmd_screenshot, shell=True)

    cmd_pull_screenshot = "adb -s {0} pull {1} {2}\\{3}.png".format(device_id, img_tmp_path, img_path, img_name)
    logging.info("cmd_pull_screenshot: {0}".format(cmd_pull_screenshot))

    output = subprocess.check_output(cmd_pull_screenshot, shell=True)
    logging.info("screenshot output:".format(output))
    
    logging.info("screenshot success")


def random_input_back(device_id, seed):
    random.seed(seed)
    back_cmd = 'adb -s {} shell input keyevent 4'.format(device_id)

    try:
        while not END_FLAG:
            interval = random.randint(2,10)
            time.sleep(interval)
            subprocess.check_output(back_cmd, shell=True)

    except Exception:
        logging.error('random_input_back ERROR, @{0} line:{1}'.format(__file__, sys._getframe().f_lineno))


def monitor_log(device_id, device_model):
    global END_FLAG
    logging.info('Monitoring Monkey Log...')
    time.sleep(1)
    logfile = open("info.txt","r")
    loglines = follow(logfile)

    error_type_list = ['ANR','Exception','CRASH','NOT RESPONDING']
    finish_flag = 'Monkey finished'

    for line in loglines:
        for error_type in error_type_list:
            if line.find(error_type) >= 0:
                logging.info(line)
                screenshot(error_type, device_id, device_model)

        if line.find(finish_flag) >= 0:
            logging.info(line)
            END_FLAG = True
            break
            #os._exit(0)


def start_monkey(device_id, package, count, seed):
    logging.info('Start Monkey...')

    monkey_cmd = 'adb -s {0} shell monkey -p {1} --pct-touch 35 --pct-motion 15 --pct-appswitch 5 --pct-rotation 5 --pct-trackball 25 --pct-nav 0 --pct-syskeys 15 --pct-flip 0 --pct-majornav 0 --throttle 300 --ignore-crashes --ignore-timeouts --ignore-security-exceptions --ignore-native-crashes --monitor-native-crashes -s {2} -v -v -v {3} > info.txt'.format(device_id, package, seed, count)

    logging.info('monkey_cmd:{0}'.format(monkey_cmd))

    try:
        subprocess.check_output(monkey_cmd, shell=True)
    except Exception:
        logging.error('start_monkey ERROR, @{0} line:{1}'.format(__file__, sys._getframe().f_lineno))


END_FLAG = False

if __name__ == '__main__':
    try:
        #获取配置文件
        wkdir = os.getcwd()
        config_file = "{0}\default.conf".format(wkdir)
        package, count, seed = get_config(config_file)
        logging.info('get config:\nPackage = {0}\nCount = {1}\nSeed = {2}'.format(package, count, seed))
    
        #创建img目录
        mkpath = wkdir + "\\img\\"
        mkdir(mkpath)

        #获取device信息
        start_adb()
        time.sleep(1)

        device_id_list = []
        device_id_list = get_device_id()
        device_id = device_id_list[0]
        logging.debug('current device id: {0}'.format(device_id))
        device_model = get_device_model(device_id)
        logging.debug('current device model: {0}'.format(device_model))

        threads = []
        t1 = threading.Thread(target=start_monkey,args=(device_id, package, count, seed,))
        threads.append(t1)
        t2 = threading.Thread(target=monitor_log,args=(device_id, device_model,))
        threads.append(t2)
        t3 = threading.Thread(target=random_input_back,args=(device_id, seed,))
        threads.append(t3)

        for t in threads:
            t.setDaemon(True)
            t.start()

        t.join()

        if END_FLAG:
            logging.debug('END=True')
        else:
            logging.error('END=False') 
            raw_input(unicode('发生错误, 按【回车键】退出...','utf-8').encode('gbk'))

    except Exception:
        traceback.print_exc()
        time.sleep(1)
        raw_input(unicode('发生错误, 按回车键退出...','utf-8').encode('gbk'))
    finally:
        pass

