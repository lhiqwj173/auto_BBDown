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

def read_config(path: str = ''):
    log.info('读取设置')
    if not path:
        path = os.path.join(r'/app/config', 'config.ini')
    log.info("[COMMON]config_path:{}".format(path))
    if os.path.exists(path):
        conf = configparser.ConfigParser()
        try:
            conf.read(path, encoding="utf-8-sig")
        except:
            conf.read(path, encoding="utf-8")
        key = conf.get("common", "key")
        if key:
            log.info('[COMMON]server酱:{}'.format(key))
        else:
            log.info('[COMMON]server酱:无')
        return conf,key
    else:
        log.info("[COMMON]Config file not found!")
        log.info("[COMMON]初始化空白 config.ini，请修改后再运行：docker start bbdown")
        with open(path, 'w')as f:
            f.write(r'[common]' + '\n')
            f.write(r"#run_time='03:30-06:00','12:00-13:00'" + '\n')
            f.write(r'run_time=all' + '\n')
            f.write(r'#运行间隔 秒' + '\n')
            f.write(r'sleep_time=300' + '\n')
            f.write(r'#server酱 key,用于发送微信提醒,留空则不开启微信提醒' + '\n')
            f.write(r'key=' + '\n')
            f.write(r'[bilibili]' + '\n')
            f.write(r"#rss链接，具体查看 https://docs.rsshub.app/social-media.html#bilibili" + '\n')
            f.write(r'rss=' + '\n')
            f.write(r'link_name=link' + '\n')
            f.write(r'method=bbdown' + '\n')
            f.write(r"#用来过滤,每个单词用','隔开,每个标题包含全部的key_word才会同步,如果不需要过滤，则填all" + '\n')
            f.write(r'key_word=all' + '\n')
            f.write(r'[youtube]' + '\n')
            f.write(r'rss=' + '\n')
            f.write(r'link_name=link' + '\n')
            f.write(r'method=you-get' + '\n')
            f.write(r'key_word=完整版' + '\n')


        sys.exit(2)

conf, key = read_config()
sleep_time = int(conf.get("common", "sleep_time"))
log.debug('休眠时间：{}'.format(sleep_time))
start_date = datetime.datetime.today().strftime('%Y_%m_%d')

ITEMS = [i for i in conf.sections() if i != 'common']
RSSS = [conf.get(i, "rss") for i in ITEMS]
LINK_NAMES = [conf.get(i, "link_name") for i in ITEMS]
METHODS = [conf.get(i, "method") for i in ITEMS]
METHOD_PATHS = {'bbdown':r'/app/BBDown','you-get':'you-get'}
OPTIONS = {'bbdown':'-p ALL','you-get':'-o /app'}

class base():
    def __init__(self,name, rss, link_name, method):
        self.name = name
        self.rss = conf.get(self.name, "rss")
        self.link_name = conf.get(self.name, "link_name")
        self.method = conf.get(self.name, "method")
        self.keyword = conf.get(self.name, "key_word")
        if ',' in self.keyword:
            self.keyword = self.keyword.split(',')
        elif 'all' in self.keyword or 'ALL' in self.keyword:
            self.keyword = ['']
        else:
            self.keyword = [self.keyword]

        self.log_name = '[' + str(self.name) + ']'

    def log(self,text):
        log.info(self.log_name + str(text))

    def run(self):
        self.if_restart()
        self.log('开始运行')
        while True:
            try:
                self.rss_data = self.get_rss_data()
                break
            except:
                time.sleep(30)
                continue
        self.local_data = self.get_local_data()

        self.rss_count = len(self.rss_data)
        self.local_count = len(self.local_data)

        self.local_title = []
        for i in self.local_data:
            self.local_title.append(i.replace('.mp4',''))

        self.del_items()
        self.download()
        self.log('{}下载完成'.format(self.log_name))

    def if_restart(self):
        now_date = datetime.datetime.today().strftime('%Y_%m_%d')
        if now_date != start_date:
            self.log('[END]重启服务')
            sys.exit(2)

    def get_rss_data(self):
        dict = {}
        result = requests.get(str(self.rss))
        r = result.content
        DOMTree = parseString(r)
        collection = DOMTree.documentElement
        VariationChilds = collection.getElementsByTagName("item")
        # 进行遍历取值
        for VariationChild in VariationChilds:
            self.log('=' * 30)
            title = VariationChild.getElementsByTagName('title')[0].childNodes[0].data
            link = VariationChild.getElementsByTagName(self.link_name)[0].childNodes[0].data

            dict[title] = link

            self.log('[RSS_DATA]title:{}'.format(title))
            self.log('[RSS_DATA]link:{}'.format(link))

        return dict

    def get_local_data(self):
        path = r'/app/downloads/' + self.name
        if not os.path.exists(path):
            os.mkdir(path)
        files = os.listdir(path)
        if len(files) > 0:
            for i in files:
                self.log('[LOCAL_DATA]{}'.format(i))
            return files
        else:
            return []

    def del_items(self):
        path = r'/app/downloads/' + self.name

        del_list = ''
        for i in self.local_title:
            if i not in self.rss_data.keys():
                file_path = os.path.join(path,i)
                self.log('[DEL]删除文件:{}'.format(file_path))
                del_list = del_list + '[DEL]{}'.format(file_path) + '\n'
                if os.path.isdir(file_path):
                    shutil.rmtree(file_path)
                elif os.path.isfile(file_path):
                    os.remove(file_path)
        if del_list:
            del_list += '订阅数量：{}\n'.format(self.rss_count)
            del_list += '本地数量：{}\n'.format(self.local_count)
            self.send_wechat('删除文件', del_list)

    def filter_key_word(self,title):
        for i in self.keyword:
            if i not in title:
                return False
        return True

    def download(self):
        download_path = r'/app/downloads/' + self.name
        add_list = ''
        for i in self.rss_data:
            if i not in self.local_title:
                if self.filter_key_word(i):
                    link = self.rss_data[i]
                    self.log('[DOWNLOAD]下载:{}'.format(i))
                    command = METHOD_PATHS[self.method] + ' ' + OPTIONS[self.method] + ' "' + str(link) + '"'
                    self.log('[DOWNLOAD]command:{}'.format(command))
                    self.run_cmd(command)
                    file_path = os.path.join(os.getcwd(),i)
                    path_d = os.path.join(download_path,i)
                    if not os.path.exists(file_path):
                        file_path = os.path.join(os.getcwd(), i + '.mp4')
                        path_d = os.path.join(download_path, i + '.mp4')
                    self.log('[DOWNLOAD]移动:{} --> {}'.format(file_path,path_d))
                    shutil.move(file_path,path_d)
                    add_list = add_list + '[ADD]{}'.format(i) + '\n'
        if add_list:
            add_list += '订阅数量：{}\n'.format(self.rss_count)
            add_list += '本地数量：{}\n'.format(self.local_count)
            self.send_wechat('新增视频', add_list)



    @staticmethod
    def run_cmd(command):
        exitcode, output = subprocess.getstatusoutput(command)
        if exitcode == 0:
            return output
        os._exit(0)

    # 发送微信
    def send_wechat(self, title, content):
        # title and content must be string.
        if not self.key:
            return None
        sckey = self.key  # server酱 key
        url = 'https://sc.ftqq.com/' + sckey + '.send'
        data = {'text': title, 'desp': content}
        result = requests.post(url, data)
        return (result)

def check_time():
    run_time = conf.get("common", "run_time")
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

if __name__ == '__main__':

    if check_time():
        for i in range(len(ITEMS)):
            if RSSS[i]:
                a = base(name=ITEMS[i],rss=RSSS[i],link_name=LINK_NAMES[i], method=METHODS[i])
                a.run()

        log.info('[COMMON]下载完成等待{}秒后再次运行'.format(sleep_time))
        time.sleep(sleep_time)
    else:
        log.info('[COMMON]非运行时段')
        time.sleep(sleep_time)
