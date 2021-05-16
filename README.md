# auto_BBDown
使用docker进行b站视频自动下载

## 使用步骤：
```shell
- cd ~
- git clone https://github.com/lhiqwj173/auto_BBDown.git
- cd auto_BBDown
```
修改config文件夹中的config.ini
```shell
- docker build -t bbdown .
- docker run --restart=unless-stopped --name bbdown -itd -v ~/auto_bbdown/config:/app/config -v /mnt/HARD_DRIVE/bilibili:/app/downloads bbdown
```