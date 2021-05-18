import configparser
import os, sys
import shutil
import requests
from xml.dom.minidom import parseString
import subprocess
import time, datetime
import logging
import re
#TODO 订阅请求失败
class TestLog(object):
    def __init__(self,log_path,log_name, logger=None):
        self.logger = logging.getLogger(logger)
        self.logger.setLevel(logging.DEBUG)

        log_time = time.strftime("%Y_%m_%d_")
        log_path = log_path
        log_name = os.path.join(log_path, log_time + log_name)

        fh = logging.FileHandler(log_name, 'a', encoding='utf-8')  # 这个是python3的
        fh.setLevel(logging.DEBUG)

        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)

        formatter = logging.Formatter(
            # '[%(asctime)s] %(filename)s->%(funcName)s line:%(lineno)d [%(levelname)s]%(message)s')
            '[%(asctime)s]%(message)s')

        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        self.logger.addHandler(fh)
        self.logger.addHandler(ch)
        fh.close()
        ch.close()

    def getlog(self):
        return self.logger

if not os.path.exists(r'/app/config/log'):
    os.mkdir(r'/app/config/log')

log = TestLog(r'/app/config/log','auto_bbdown.log').getlog()

def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    log.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

sys.excepthook = handle_exception

class auto_bbdown():
    def __init__(self):
        #self.abs_path = self.get_py_path()
        # log = TestLog(self.abs_path,'auto_bbdown.log').getlog()

        # 删除5天前的日志
        log.info('[COMMON]清理日志')
        five_day = datetime.datetime.now() - datetime.timedelta(days=5)
        # for i in os.listdir(self.abs_path):
        for i in os.listdir(r'/app/config/log'):
            if '.log' in i:
                log_txt = re.search(r'\d{4}_\d{2}_\d{2}', i).group(0)
                log_date = datetime.datetime.strptime(log_txt, '%Y_%m_%d')
                log.debug('[COMMON]log_date:{}'.format(log_date))
                if log_date < five_day:
                    # log_path = os.path.join(self.abs_path, i)
                    log_path = os.path.join(r'/app/config/log', i)
                    log.debug('[COMMON]del_log:{}'.format(log_path))
                    os.remove(log_path)

        log.info('[COMMON]读取设置')
        self.conf = self.read_config()
        log.debug('[COMMON]config_info:{}'.format(self.conf))
        sleep_time = int(self.conf.get("common", "sleep_time"))
        log.debug('[COMMON]休眠时间：{}'.format(sleep_time))
        while True:
            if self.check_time():
                log.info('[COMMON]开始运行')
                try:
                    self.rss_data = self.get_rss_data()
                except:
                    time.sleep(30)
                    continue
                self.local_data = self.get_local_data()
                self.local_title = []
                for i in self.local_data:
                    self.local_title.append(i.replace('.mp4',''))
                self.del_items()
                self.download()
                log.info('[COMMON]下载完成等待{}秒后再次运行'.format(sleep_time))
                time.sleep(sleep_time)
            else:
                log.info('[COMMON]非运行时段')
                time.sleep(sleep_time)
    def get_py_path(self):
        return os.path.split(os.path.abspath(__file__))[0]

    def read_config(self,path: str = ''):
        if not path:
            path = os.path.join(r'/app/config', 'config.ini')
        log.info("[COMMON]config_path:{}".format(path))
        if os.path.exists(path):
            conf = configparser.ConfigParser()
            try:
                conf.read(path, encoding="utf-8-sig")
            except:
                conf.read(path, encoding="utf-8")
            return conf
        else:
            log.info("[COMMON]Config file not found!")
            log.info("[COMMON]初始化空白 config.ini，请修改后再运行：docker start bbdown")
            with open(path,'w')as f:
                f.write(r'[common]' + '\n')
                f.write(r'#rss链接，具体查看 https://docs.rsshub.app/social-media.html#bilibili' + '\n')
                f.write(r'rss=' + '\n')
                f.write(r"#运行时间段" + '\n')
                f.write(r"#run_time='03:30-06:00','12:00-13:00'" + '\n')
                f.write(r'run_time=all' + '\n')
                f.write(r'#运行间隔 秒' + '\n')
                f.write(r'sleep_time=300' + '\n')

            sys.exit(2)

    def check_time(self):
        run_time = self.conf.get("common", "run_time")
        if ',' in run_time:
            run_time_list = run_time.split(',')
        elif 'all' == run_time or 'ALL' == run_time:
            run_time_list = ['00:00-23:59']
        else:
            run_time_list = [run_time]
        log.debug('[CHECKTIME]运行时间设定：{}'.format(str(run_time_list)))
        n_time = datetime.datetime.now()
        log.debug('[CHECKTIME]now_time：{}'.format(n_time))
        for i in run_time_list:
            l = i.split('-')
            log.debug('str(l)')
            time_b = datetime.datetime.strptime(str(datetime.datetime.now().date()) + l[0].replace("'",''), '%Y-%m-%d%H:%M')
            time_e = datetime.datetime.strptime(str(datetime.datetime.now().date()) + l[1].replace("'",''), '%Y-%m-%d%H:%M')
            if time_b < n_time < time_e:
                return True

        return False


    def get_rss_data(self):
        dict = {}
        url = self.conf.get("common", "rss")
        result = requests.get(str(url))
        if 200 != result.status_code:
            log.info('[RSS_DATA]请求异常')
            return None
        r = result.content
        DOMTree = parseString(r)
        collection = DOMTree.documentElement
        VariationChilds = collection.getElementsByTagName("item")
        # 进行遍历取值
        for VariationChild in VariationChilds:
            log.info('=' * 30)
            title = VariationChild.getElementsByTagName('title')[0].childNodes[0].data

            link = VariationChild.getElementsByTagName('link')[0].childNodes[0].data
            #     description = description.getElementsByTagName('link')

            author = VariationChild.getElementsByTagName('author')[0].childNodes[0].data

            dict[title] = link

            log.info('[RSS_DATA]title:{}'.format(title))
            log.info('[RSS_DATA]link:{}'.format(link))
            log.info('[RSS_DATA]author:{}'.format(author))

        return dict

    def get_local_data(self):
        #path = self.conf.get("common", "download_path")
        path = r'/app/downloads'
        files = os.listdir(path)
        if len(files) > 0:
            for i in files:
                log.info('[LOCAL_DATA]{}'.format(i))
            return files
        else:
            return []

    def del_items(self):
        #path = self.conf.get("common", "download_path")
        path = r'/app/downloads'

        for i in self.local_data:
            title = i.replace('.mp4', '')
            if title not in self.rss_data.keys():
                log.debug('[DEL]{}'.format(title))
                file_path = os.path.join(path,i)
                log.info('[DEL]删除文件:{}'.format(file_path))
                if os.path.isdir(file_path):
                    shutil.rmtree(file_path)
                elif os.path.isfile(file_path):
                    os.remove(file_path)

    def download(self):
        # BBDown_path = self.conf.get("common", "BBDown_path")
        BBDown_path = r'/app/BBDown'
        # download_path = self.conf.get("common", "download_path")
        download_path = r'/app/downloads'
        for i in self.rss_data:
            if i not in self.local_title:
                link = self.rss_data[i]
                log.info('[DOWNLOAD]下载:{}'.format(i))
                command = str(BBDown_path) + ' -p ALL "' + str(link) + '"'
                log.info('[DOWNLOAD]command:{}'.format(command))
                self.run_cmd(command)
                file_path = os.path.join(os.getcwd(),i)
                path_d = os.path.join(download_path,i)
                if not os.path.exists(file_path):
                    file_path = os.path.join(os.getcwd(), i + '.mp4')
                    path_d = os.path.join(download_path, i + '.mp4')
                log.info('[DOWNLOAD]移动:{} --> {}'.format(file_path,path_d))
                shutil.move(file_path,path_d)
    @staticmethod
    def run_cmd(command):
        exitcode, output = subprocess.getstatusoutput(command)
        if exitcode == 0:
            return output
        os._exit(0)

if __name__ == '__main__':
    a = auto_bbdown()
