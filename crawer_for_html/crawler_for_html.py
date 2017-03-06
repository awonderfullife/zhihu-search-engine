# -*- coding:utf-8 -*-
import urlparse,os, urllib,urllib2, re,robotparser,threading,Queue,time,sys
from string import lower
from bs4 import BeautifulSoup
from gzip import GzipFile
from StringIO import StringIO
from selenium import webdriver
from support import *
import socket
socket.setdefaulttimeout(3000)

# Python爬虫需要设置栈的大小来节约内存
threading.stack_size(32768*16)
# change the default encode way
reload(sys)
sys.setdefaultencoding( "utf-8" )
webdriver.DesiredCapabilities.PHANTOMJS["phantomjs.page.settings.resourceTimeout"] = 3


class Bitarray:
    def __init__(self, size):
        """ Create a bit array of a specific size """
        self.size = size
        self.bitarray = bytearray(size / 8)

    def set(self, n):
        """ Sets the nth element of the bitarray """

        index = n / 8
        position = n % 8
        self.bitarray[index] = self.bitarray[index] | 1 << (7 - position)

    def get(self, n):
        """ Gets the nth element of the bitarray """

        index = n / 8
        position = n % 8
        return (self.bitarray[index] & (1 << (7 - position))) > 0

class Crawer_message:
    page_name = 0

    def __init__(self):
        self.url_class = NORMALHTML  # url网页的类型,是否为html,在知乎内外，知乎内的话，是什么类型
        self.content = ' '
        self.url = ' '
        self.driver = webdriver.PhantomJS(executable_path=PHANTOMJS_EXCUTABLE_PATH)

    def The_BKDRHash(self, key, seed):
        hash = 0
        for i in range(len(key)):
            hash = (hash * seed) + ord(key[i])
        return hash

    def valid_filename(self, s):
        import string
        valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
        s = ''.join(c for c in s if c in valid_chars)
        return s

    def which_class(self):
        if self.url.find(ZHIHU) == -1 or self.url.find(ZHIHU_CAREERS) != -1 or self.url.find(ZHIHU_ZHSTATIC) != -1:
            self.url_class = UNSUIT
            return self.url_class
        if self.url.find(ZHIHU_PEOPLE) != -1:
            if self.url.count('/') > 4:
                index = self.url.index('/',30)
                self.url = self.url[0:index]
            if self.url.count('#') >0 :
                index2 = self.url.index('#',30)
                self.url = self.url[0:index2]
            self.url_class = PEOPLE
            return self.url_class
        if self.url.find(ZHIHU_QUESTION) != -1:
            index = self.url.index('/',25) + 9
            self.url = self.url[0:index]
            self.url_class = QUESTION
            return self.url_class
        if self.url.find(ZHIHU_ROUNDTABLE) != -1:
            if self.url.count('/') > 4:
                index = self.url.index('/',34)
                self.url = self.url[0:index]
            self.url_class = ROUNDTABLE
            return self.url_class
        if self.url.find(ZHIHU_ZHUANLAN) != -1:
            if self.url.count('/') > 4:
                index = self.url.index('/',27) + 9
                self.url = self.url[0:index]
            self.url_class = ZHUANLAN
            return self.url_class
        self.url_class = NORMALHTML
        return self.url_class

    def wether_polite(self):
        try:
            rp = robotparser.RobotFileParser()
            rp.set_url(urlparse.urljoin('https://www.zhihu.com/', 'robots.txt'))
            rp.read()
            return rp.can_fetch("*", self.url)
        except: return False

    def init_content(self):
        if self.url_class == PEOPLE or self.url_class == ZHUANLAN:
            try:
                self.driver.get(self.url)
                self.content = self.driver.page_source
                #self.driver.quit()
            except urllib2.URLError, msg:
                print('Failed to open page ' + self.url + ': ' + str(msg))
                self.content = ''
        else:
            try:
                req = urllib2.Request(self.url)
                req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; rv:14.0) Gecko/20100101 Firefox/14.0.1')
                data = {'Accept-encoding': 'gzip'}
                request = urllib2.Request(self.url, urllib.urlencode(data))
                try:
                    opener = urllib2.build_opener()
                    response = opener.open(request)
                    if response.code == 200:
                        predata = response.read()
                        pdata = StringIO(predata)
                        gzipper = GzipFile(fileobj=pdata)
                        try:
                            cnt = gzipper.read()
                        except:
                            cnt = predata
                        self.content = cnt
                        return
                except Exception, e:
                    pass
                response = urllib2.urlopen(req, data=None, timeout=3)
                # 判断一个url是否为网址链接（网址链接的content为html格式）
                HttpMessage = response.info()
                ContentType = HttpMessage.gettype()
                if "text/html" != ContentType:
                    self.url_class = 'ileagal_class'
                    return
                self.content = response.read()
            except:
                self.content = ''

    def get_hash_list(self):
        hash_list = []
        for seed in HASH_SEED_ARRAY:
            hash_val = self.The_BKDRHash(self.url, seed) % HASH_LIST_SIZE
            hash_list.append(hash_val)
        return hash_list

    def get_link_list(self):
        link_list = []
        soup = BeautifulSoup(self.content, "html.parser")
        for i in soup.findAll('a', {'href': re.compile('^http|^/')}):
            link = i.get('href', '')
            if link[0] == '/':
                link = urlparse.urljoin(self.url, link)
            link_list.append(link)
        return link_list

    def get_content(self):
        self.init_content()
        return self.content

    def add_to_folder(self):
        Crawer_message.page_name += 1
        index_filename = self.url_class + '.txt'
        folder = self.url_class
        filename = self.valid_filename(str(Crawer_message.page_name) + '.html')
        index = open(index_filename, 'a')
        index.write(self.url.encode('ascii', 'ignore') + '\t\t' + str(Crawer_message.page_name) + '\n')
        index.close()
        if not os.path.exists(folder):
            os.mkdir(folder)
        f = open(os.path.join(folder, filename), 'w')
        f.write(self.content)
        f.close()

class ThreadClass:
    url_seed = ''
    max_page = 0
    crawled = Bitarray(HASH_LIST_SIZE)
    lock = threading.Lock()
    tocrawl = Queue.Queue()
    count = 0
    end_sit = 0

    def __init__(self, seed, max, num):
        ThreadClass.url_seed = seed
        ThreadClass.max_page = max
        #ThreadClass.tocrawl.put(seed)

        for i in range(num):
            t = threading.Thread(target=self.working)
            t.setDaemon(True)
            t.start()

    def union_dfs(self, a, b):
        if a.qsize() < 100000:
            for e in b:
                a.put(e)

    def working(self):
        crawer_obj = Crawer_message()
        while True:
            try:
                if ThreadClass.count >= ThreadClass.max_page:
                    ThreadClass.end_sit = 1
                    break
                page = ThreadClass.tocrawl.get()
                crawer_obj.url = page
                if crawer_obj.which_class() == UNSUIT: continue
                if not crawer_obj.wether_polite(): continue
                hash_val_list = crawer_obj.get_hash_list()
                flag = False
                if ThreadClass.lock.acquire():
                    try:
                        for hash_val in hash_val_list:
                            if ThreadClass.crawled.get(hash_val) == 0:
                                flag = True
                        if flag == True:
                            for val in hash_val_list:
                                ThreadClass.crawled.set(val)
                    finally:
                        ThreadClass.lock.release()
                if flag == False: continue
                if crawer_obj.get_content() == '': continue
                if ThreadClass.lock.acquire():
                    time.sleep(1)
                    try:
                        if ThreadClass.count <= ThreadClass.max_page: print page, ThreadClass.count
                        crawer_obj.add_to_folder()
                        outlinks = crawer_obj.get_link_list()
                        self.union_dfs(ThreadClass.tocrawl, outlinks)  # 深度优先
                        ThreadClass.count += 1
                    finally:
                        ThreadClass.lock.release()
                ThreadClass.tocrawl.task_done()
            except: pass

def crawl(seed_url, max_page, trd_num):
    try:
        t = ThreadClass(seed_url, max_page, trd_num)
        while not ThreadClass.end_sit:
            time.sleep(10)
    finally: return

def log():
    print 'log ....'
    fpn = open('PageName.txt', 'w')
    fpn.write(str(Crawer_message.page_name))
    print 'page name finshed!'
    ftc = open('ToCrawl.txt', 'w')
    while not ThreadClass.tocrawl.empty():
        ftc.write(ThreadClass.tocrawl.get()+'\n')
    print 'tocrawl page finshed!'
    fcd = open('Crawled.txt', 'w')
    for i in range(HASH_LIST_SIZE):
        if ThreadClass.crawled.get(i) == True: fcd.write('1 ')
        else: fcd.write('0 ')
    print 'crawled finshed!'
    fpn.close()
    ftc.close()
    fcd.close()
    print 'log finshed!'

def init():
    print 'initlizing ....'
    fpn = open('PageName.txt', 'r')
    Crawer_message.page_name = int(fpn.read())
    print 'page name finshed!'
    ftc = open('ToCrawl.txt', 'r')
    for line in ftc:
        line = line.strip()
        ThreadClass.tocrawl.put(line)
    print 'tocrawl page finshed!'
    fcd = open('Crawled.txt', 'r')
    inf_str = fcd.read()
    inf_str_list = inf_str.split(' ')
    for i in range(len(inf_str_list)):
        if inf_str_list[i] == '1': ThreadClass.crawled.set(i)
    print 'crawled page finshed!'
    fpn.close()
    ftc.close()
    fcd.close()
    print 'initlize finshed!'


max_page = input('请输入最大爬取网页最大数目：')
thrd_num = input('请输入线程数目：')
start = time.clock()
init()
crawl('https://www.zhihu.com/', max_page, thrd_num)
log()
end = time.clock()
print 'The total time cost is ', end - start
