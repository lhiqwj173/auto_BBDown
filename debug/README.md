# auto_BBDown
使用docker进行b站视频自动下载
订阅rsshub关于哔哩哔哩，然后进行愉快的下载
https://docs.rsshub.app/social-media.html#bilibili

下载部分使用：https://github.com/nilaoda/BBDown  
参考项目：https://github.com/LJason77/bilibili-webhook

## 使用步骤：
创建挂载目录
```shell
cd ~
```
```shell
mkdir bilibili
```
```shell
mkdir bilibili_downloads
```
根据自己的需求

拉取镜像
```shell
docker pull registry.cn-hangzhou.aliyuncs.com/lhiiqwj/auto_bbdown:latest
```
运行镜像
```shell
docker run --restart=always --name bbdown -itd -v ${PWD}/bilibili:/app/config -v /mnt/HARD_DRIVE:/app/downloads registry.cn-hangzhou.aliyuncs.com/lhiiqwj/auto_bbdown
```
其中/mnt/HARD_DRIVE/bilibili改为本地的下载目录，也就是上面创建的bilibili_downloads  
首次运行会初始化config，自行修改bilibili中的config.ini文件

再次运行
```shell
docker start bbdown
```

## 日志文件：
~/bilibili/log/


## docker 命令提示：

停止容器
```shell
docker stop bbdown
```
删除容器
```shell
docker rm bbdown
```
删除无用镜像
```shell
docker image rm $(docker image ls -a -q)
```
进入容器
```shell
docker exec -it bbdown /bin/bash
```
