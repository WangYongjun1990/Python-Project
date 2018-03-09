# Vinsmoke使用说明


### 一、前置配置

在调试Android程序时我们需要通过adb工具在手机和电脑之间建立连接，
通常情况我们都是使用数据线，其实adb还提供了另外一种方式通过tcpip建立连接。
也就是可以通过Wifi调试程序。

**注意**：使用wifi调试程序首先确保你的电脑和手机在同一个wifi环境下。

这种方法不需要手机有root权限，但是在第一次连接时需要数据线连接电脑，配置好之后数据线则可以断开。

使用```adb devices```查看手机是否连接成功

 ![Image text](https://raw.githubusercontent.com/WangYongjun1990/Test/master/img/adbDevices.png)

使用命令```adb -s [device_id] tcpip [port]```让手机的某个端口处于监听状态。

 ![Image text](https://raw.githubusercontent.com/WangYongjun1990/Test/master/img/adbTcpip.png)

如上图所示，即端口已经处于监听状态。**现在可以断开手机与电脑的USB线了。**

在手机的Wifi设置中查看你的ip地址[ip-address],使用命令行```adb connect [ip-address]:[port]```连接手机

 ![Image text](https://raw.githubusercontent.com/WangYongjun1990/Test/master/img/adbConnect.png)

返回```connected to [ip-address]:[port]```表示成功连接了手机

测试一下，使用命令```adb devices```

 ![Image text](https://raw.githubusercontent.com/WangYongjun1990/Test/master/img/adbDevices2.png)

可以看到连接的设备ID是手机的ip地址，说明通过Wifi调试adb成功



### 关于device offline的解决方法
1. 进入手机->设置->开发者选项->撤销USB调试授权

2. 关闭 USB调试

3. PC Terminal 输入 adb kill-server

4. PC Terminal 输入 adb start-server

5. 手机打开 USB调试

6. PC Terminal 输入 adb connect xx.xx.xx.xx:5555 (the devices ip)
