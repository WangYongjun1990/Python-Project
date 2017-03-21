# coding: utf-8

import os
import sys
import time
import logging
import platform
import subprocess
import threading
from xlwt import *


logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(name)s:%(levelname)s: %(message)s"
)
wkdir = os.getcwd()

def OnlyCharNum(s,oth=''):
    fomart = '0123456789s'
    s2 = ''
    for c in s:
        if c in fomart:
            s2 += c
    return s2

def start_adb():
    cmd = "adb devices"
    logging.debug('cmd:{}'.format(cmd))
    if platform.system() == 'Windows':
        subprocess.check_output(cmd, shell=True)
    time.sleep(2)

def get_device_id():
    '''返回 device id'''
    device_dict = {}
    device_id_list = []
    get_device_id_cmd = "adb devices | findstr /e device"   # /e 对一行的结尾进行匹配

    try:
        output = subprocess.check_output(get_device_id_cmd, shell=True)
        logging.debug('connected devices:\r{0}'.format(output))
    except Exception:
        #traceback.print_exc()
        logging.error('All device lost, @{0} line:{1}'.format(__file__, sys._getframe().f_lineno))
        output = None

    if output is not None:
        output = output.split("\n")
        logging.debug('split connect devices id: {0}'.format(output))
        
        for device_id in output:
            if device_id == "":
                continue
            device_id = device_id.replace("\tdevice\r", "")
            logging.debug('device_id: {0}'.format(device_id))
            device_id_list.append(device_id)
        logging.debug('device_id_list: {0}'.format(device_id_list))

    return device_id_list

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


def monitor_log():
    logging.info(unicode('动态处理logcat日志...','utf-8').encode('gbk'))
    time.sleep(1)
    logfile = open("logcat.txt","r")
    loglines = follow(logfile)

    activity_start_mark = 'Displayed cn.memedai.mmd.debug/'
    time_start_mark = ': +'
    time_end_mark = 'ms'

    for line in loglines:
        key_list = ['Displayed cn.memedai.mmd.debug'] #out

        for key in key_list:
            if line.find(key) >= 0:
                logging.info(line)
                #获取activity
                activity = line[line.find(activity_start_mark)+31:line.find(time_start_mark)].split('.')[-1]
                #获取response_time
                response_time = OnlyCharNum(line[line.find(time_start_mark)+3:line.find(time_end_mark)+3]).split('s') #line中提取出'1s45ms' => '1s45s' => ['1','45','']
                response_time.pop() #['1','45',''] => ['1','45']
                if len(response_time) == 1:
                    response_time = int(response_time[0])
                elif len(response_time) == 2:
                    response_time = int(response_time[0])*1000+int(response_time[1]) #['1','45'] => 1045

                logging.debug('activity:{}'.format(activity))
                logging.debug('response_time:{}'.format(response_time))

                set_TABLE(activity, response_time)

        if END_FLAG:
            break


def saving_log(device_id):
    logging.info(unicode('开始保存logcat日志到本地...','utf-8').encode('gbk'))

    saving_log_cmd = 'adb -s {0} logcat ActivityManager:I *:S -v time > logcat.txt'.format(device_id)

    logging.debug('saving_log_cmd:{0}'.format(saving_log_cmd))

    try:
        #子进程child
        child = subprocess.Popen(saving_log_cmd, shell=True)
        #循环判断是否结束
        while not END_FLAG:
            time.sleep(0.1)
        child.kill()

    except Exception:
        logging.error('saving_log ERROR, @{0} line:{1}'.format(__file__, sys._getframe().f_lineno))


def get_input_for_stop():
    global END_FLAG
    raw_input(unicode('手机操作完成后，请按【回车键】保存结果...\n','utf-8').encode('gbk'))
    END_FLAG = True


    
def set_TABLE(activity, response_time):
    global TABLE

    exist = False
    #判断activity是否在TABLE已存在，存在就只添加time
    for col in TABLE:
        if col[0] == activity:
            col.append(response_time)
            exist = True
            break
    #如果不存在，添加activity和time
    if exist == False:
        new_list = []
        new_list.append(activity)
        new_list.append(response_time)
        TABLE.append(new_list)

    logging.debug('TABLE:{}'.format(TABLE))


def write_execl(TABLE, execl_name):
    logging.info(unicode('开始写入execl...','utf-8').encode('gbk'))
    #打开execl        
    file = Workbook(encoding = 'utf-8') 
    sheet1 = file.add_sheet('测试结果')
    sheet1.write(0,0,'加载次数')

    col_num = 0
    row_num = 0
    max_row_num = 1
    max_col_num = len(TABLE)
    #把TABLE循环写入execl
    for col in TABLE:
        col_num += 1
        row_num = 0
        for value in col:
            if row_num == 0:
                sheet1.write(row_num, col_num, value)
            else:
                sheet1.write(row_num, col_num, int(value))
            row_num += 1
        #获取最大行数
        if max_row_num < row_num:
            max_row_num = row_num
    #execl写入第一列
    for i in xrange(1, max_row_num):
        sheet1.write(i, 0 ,'第{}次'.format(i))
    sheet1.write(max_row_num, 0 ,'平均值')
    #execl写入平均值计算公式
    for i in xrange(1, max_col_num + 1):
        average = "AVERAGE({0}2:{0}{1})".format(ALPHABET[i], max_row_num)
        sheet1.write(max_row_num, i ,Formula(average))

    file.save(execl_name)


TABLE = []
ALPHABET = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "D", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z"]
END_FLAG = False


if __name__ == '__main__':
    logging.info(unicode('初始化...','utf-8').encode('gbk'))
    start_adb()
    time.sleep(2)

    device_id_list = []
    device_id_list = get_device_id()
    if len(device_id_list) == 0:
        logging.error(unicode('未找到手机设备','utf-8').encode('gbk'))
    else:
        device_id = device_id_list[0]
        logging.debug('current device id: {0}'.format(device_id))
        device_model = get_device_model(device_id)
        logging.debug('current device model: {0}'.format(device_model))

        threads = []
        t1 = threading.Thread(target=monitor_log,args=())
        threads.append(t1)
        t2 = threading.Thread(target=saving_log,args=(device_id, ))
        threads.append(t2)
        t3 = threading.Thread(target=get_input_for_stop,args=())
        threads.append(t3)

        for t in threads:
            t.setDaemon(True)
            t.start()

        t.join()

    if END_FLAG:
        logging.debug('END=True') 

        timestamp = time.strftime('%Y-%m-%d-%H-%M-%S',time.localtime(time.time()))
        execl_name = device_model + '_result_' + timestamp + '.xls'

        write_execl(TABLE, execl_name)
        raw_input(unicode('测试结果已保存到{},按【回车键】退出'.format(execl_name),'utf-8').encode('gbk'))

    else:
        logging.error('END=False') 
        raw_input(unicode('发生错误, 按【回车键】退出...','utf-8').encode('gbk'))
    


    