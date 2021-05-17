# auto_BBDown
使用docker进行b站视频自动下载

下载部分使用：https://github.com/nilaoda/BBDown
参考项目：https://github.com/LJason77/bilibili-webhook

## 使用步骤：
```shell
cd ~
```
```shell
git clone https://github.com/lhiqwj173/auto_BBDown.git
```
```shell
cd auto_BBDown
```
修改config文件夹中的config.ini
```shell
docker build -t bbdown .
```
```shell
docker run --name bbdown -itd -v ${PWD}/config:/app/config -v /mnt/HARD_DRIVE/bilibili:/app/downloads bbdown
```


docker 命令提示

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
删除项目目录
```shell
rm -rf ~/auto_BBDown/
```
