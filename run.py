import configparser
import os, sys
import shutil
import requests
from xml.dom.minidom import parseString
import subprocess
import time, datetime
import logging
import re

class TestLog(object):
    def __init__(self,log_path,log_name, logger=None):
        self.logger = logging.getLogger(logger)
        self.logger.setLevel(logging.DEBUG)

        self.log_time = time.strftime("%Y_%m_%d_")
        self.log_path = log_path
        self.log_name = os.path.join(self.log_path, self.log_time + log_name)

        fh = logging.FileHandler(self.log_name, 'a', encoding='utf-8')  # 这个是python3的
        fh.setLevel(logging.INFO)

        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)

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

class auto_bbdown():
    def __init__(self):
        if not os.path.exists(r'/app/config/log'):
            os.mkdir(r'/app/config/log')
        self.abs_path = self.get_py_path()
        # self.log = TestLog(self.abs_path,'auto_bbdown.log').getlog()
        self.log = TestLog(r'/app/config/log','auto_bbdown.log').getlog()
        # 删除5天前的日志
        self.log.info('清理日志')
        five_day = datetime.datetime.now() - datetime.timedelta(days=5)
        # for i in os.listdir(self.abs_path):
        for i in os.listdir(r'/app/config/log'):
            if '.log' in i:
                log_txt = re.search(r'\d{4}_\d{2}_\d{2}', i).group(0)
                log_date = datetime.datetime.strptime(log_txt, '%Y_%m_%d')
                if log_date < five_day:
                    # log_path = os.path.join(self.abs_path, i)
                    log_path = os.path.join(r'/app/config/log', i)
                    os.remove(log_path)

        self.log.info('读取设置')
        self.conf = self.read_config()
        sleep_time = int(self.conf.get("common", "sleep_time"))
        while True:
            if self.check_time():
                self.log.info('开始下载')
                self.rss_data = self.get_rss_data()
                self.local_data = self.get_local_data()
                self.del_items()
                self.download()
                time.sleep(sleep_time)
            else:
                self.log.info('等待')
                time.sleep(sleep_time)
    def get_py_path(self):
        return os.path.split(os.path.abspath(__file__))[0]

    def read_config(self,path: str = ''):
        if not path:
            path = os.path.join(self.abs_path, 'config.ini')
        if os.path.exists(path):
            conf = configparser.ConfigParser()
            try:
                conf.read(path, encoding="utf-8-sig")
            except:
                conf.read(path, encoding="utf-8")
            return conf
        else:
            print("[-]Config file not found!")
            sys.exit(2)

    def check_time(self):
        run_time = self.conf.get("common", "run_time")
        if ',' in run_time:
            run_time_list = run_time.split(',')
        elif 'all' == run_time or 'ALL' == run_time:
            run_time_list = ['00:00-24:00']
        else:
            run_time_list = [run_time]

        n_time = datetime.datetime.now()
        for i in run_time_list:
            l = i.split('-')
            time_b = datetime.datetime.strptime(str(datetime.datetime.now().date()) + l[0].replace("'",''), '%Y-%m-%d%H:%M')
            time_e = datetime.datetime.strptime(str(datetime.datetime.now().date()) + l[1].replace("'",''), '%Y-%m-%d%H:%M')
            if time_b < n_time < time_e:
                return True

        return False


    def get_rss_data(self):
        dict = {}
        url = self.conf.get("common", "rss")
        result = requests.get(str(url))
        r = result.content
        DOMTree = parseString(r)
        collection = DOMTree.documentElement
        VariationChilds = collection.getElementsByTagName("item")
        # 进行遍历取值
        for VariationChild in VariationChilds:
            self.log.info('=' * 30)
            title = VariationChild.getElementsByTagName('title')[0].childNodes[0].data

            link = VariationChild.getElementsByTagName('link')[0].childNodes[0].data
            #     description = description.getElementsByTagName('link')

            author = VariationChild.getElementsByTagName('author')[0].childNodes[0].data

            dict[title] = link

            self.log.info(title)
            self.log.info(link)
            self.log.info(author)

        return dict

    def get_local_data(self):
        #path = self.conf.get("common", "download_path")
        path = r'/app/downloads'
        files = os.listdir(path)
        if len(files) > 0:
            return files
        else:
            return []

    def del_items(self):
        #path = self.conf.get("common", "download_path")
        path = r'/app/downloads'
        for i in self.local_data:
            if i not in self.rss_data:
                file_path = os.path.join(path,i)
                self.log.info('删除文件:{}'.format(file_path))
                shutil.rmtree(file_path)

    def download(self):
        # BBDown_path = self.conf.get("common", "BBDown_path")
        BBDown_path = r'/app/BBDown'
        # download_path = self.conf.get("common", "download_path")
        download_path = r'/app/downloads'
        for i in self.rss_data:
            if i not in self.local_data:
                link = self.rss_data[i]
                self.log.info('下载:{}'.format(i))
                command = str(BBDown_path) + ' -p ALL "' + str(link) + '"'
                print(command)
                self.run_cmd(command)
                file_path = os.path.join(os.getcwd(),i)
                path_d = os.path.join(download_path,i)
                if not os.path.exists(file_path):
                    file_path = os.path.join(os.getcwd(), i + '.mp4')
                    path_d = os.path.join(download_path, i + '.mp4')
                shutil.move(file_path,path_d)
    @staticmethod
    def run_cmd(command):
        exitcode, output = subprocess.getstatusoutput(command)
        if exitcode == 0:
            return output
        os._exit(0)

if __name__ == '__main__':
    a = auto_bbdown()