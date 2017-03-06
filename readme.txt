QQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQ
QQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQ
QQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQ
QQQQQQQQQQQ7"^"\QQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQ
QQQQQQQQQQ7`  QQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQ
QQQQQQQQQ7'  ^"""""""""""\QQ*"""""""""""""""QQQQQQ
QQQQQQQQQ"               "\Q'               QQQQQQ
QQQQQQQQ"'  {QQ}   {QQQQQQQQ'  {QQQQQQQQ}   QQQQQQ
QQQQQQQ7'  {QQQ7   *QQQQQQQQ'  "QQQQQQQQ*   QQQQQQ
QQQQQQ\\_{QQQQQ7   [QQQQQQQQ'  "QQQQQQQQ*   QQQQQQ
QQQQQQQQQQQQQQQ7   QQQQQQQQQ'  "QQQQQQQQ*   QQQQQQ
QQQQQQQQ\77777\*   *77777\QQ'  "QQQQQQQQ*   QQQQQQ
QQQQQQ\"                  "Q'  "QQQQQQQQ*   QQQQQQ
QQQQQQQQjjjjj\\,   \jjjjjjQQ'  "QQQQQQQQ*   QQQQQQ
QQQQQQQQQQQQQQ7'  "QQQQQQQQQ'  "QQQQQQQQ*   QQQQQQ
QQQQQQQQQQQQQQ"   "*\QQQQQQQ'  "QQQQQQQQ*   QQQQQQ
QQQQQQQQQQQQQ7'     ^"QQQQQQ'  "QQQQQQQQ*   QQQQQQ
QQQQQQQQQQQQ7'   {{   ^"QQQQ'  "QQQQQQQQ7   QQQQQQ
QQQQQQQQQQQ7'   {QQQ,   "QQQ'   ^*7"'       QQQQQQ
QQQQQQQQQ\*'   {QQQQQ\, "QQQ__,      ,_,,,,(QQQQQQ
QQQQQQQQ*'   ,[QQQQQQQQ{{QQQQQQ,  ,{QQQQQQQQQQQQQQ
QQQQQQ*'   ,{QQQQQQQQQQQQQQQQQQQ{QQQQQQQQQQQQQQQQQ
QQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQ
QQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQ
QQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQ

+------------------------------------------------+
|            ZHIHU STATISTICS SERVER             |
+------------------------------------------------+
| * Introduction                                 |
|   - Zhihu Statistics Crawler                   |
|   - Zhihu Statistics Viewer                    |
| * System Requirements & Dependencies           |
| * Launching                                    |
|   - The Crawler                                |
|   - The Image Crawler                          |
|   - The Server                                 |
| * Using the Search Engine                      |
| * Troubleshooting                              |
+------------------------------------------------+

* Introduction

  - Zhihu Statistics Crawler

    The Zhihu Statistics Crawler (the crawler) is
    a set of programs that acquires data from the
    Zhihu website (https://www.zhihu.com, the
    website) and stores the data retrieved in
    multiple local databases. The crawler consists
    of the Zhihu Crawler (the data crawler) and
    the Zhihu Image Crawler (the image crawler).
    The data crawler retrieves data related with
    users, questions, answers, articles, topics
    and comments on the website, while the image
    crawler retrieves all relating images.


  - Zhihu Statistics Viewer

    The Zhihu Statistics Viewer (the server)
    includes the Zhihu Statistics Server (the
    backend) that allows the user to query data on
    the website and the corresponding frontend
    webpage (the frontend). Queries made by the
    user through the frontend will be sent to the
    backend and processed, and the results will be
    sent back and presented by the frontend.



* System Requirements & Dependencies

  Zhihu Statistics Crawler (the crawler) and Zhihu
  Statistics Viewer (the server) runs on any system
  with an installation of Python 2.7 with following
  libraries:

  - BeautifulSoup 4.5.1 (or compatible, same with
    all the following)
  - OpenCV 2.4.13
  - numpy 1.11.2
  - PyLucene 4.10.1

  Moreover, some parts of the programs also
  requires two executables - `eog` and
  `gnome-shell` - to be in the PATH of the system.
  These executables being missing may lead to the
  programs' crasing.



* Launching

  Many of the programs will require you to log in
  with a zhihu account to proceed. Either enter
  your account information and the captcha every
  time a prompt shows up, or you can create a file
  named login_info under the base directory to
  avoid entering your account information. The file
  needs to contain your email (or phone number, has
  proper changes been made to the code) and your
  password, each on a new line.

  - The Crawler

  	In the shell, enter the directory containing
  	the zhihu_crawler.py . You'll have to
  	initialize the database (i.e., provide the seed
  	and proper database entries) for the first run
  	(i.e., when either the folder .index/ or the
  	folder .crawler_tasks/ is missing), just run

  	  python zhihu_crawler.py init <user-name>

  	where <user-name> is the index of the zhihu
  	user used as the seed. Had the crawler been
  	properly initialized, run

  	  python zhihu_crawler.py

  	to start crawling. Type `stop` into the main
  	console to stop crawling.


  - The Image Crawler

  	You first need to make sure that some tasks
  	have been completed by the crawler. If not,
  	just run the crawler to make it so. If this is
  	the first time that you've ran the image
  	crawler, you can directly enter

  	  pyton zhihu_image_crawler.py

  	into the shell. Type `stop` into the main
  	console to stop crawling. Part of the output
  	will look like this:

  	  ft:<10-digit-index> <optional>

  	where <10-digit-index> is the index that you'll
  	need to start from where you last stopped. For
  	example, if the last line of output that starts
  	with `ft:` has an index of 1234567890, type

  	  python zhihu_image_crawler.py 1234567890

  	into the shell to start crawling from where you
  	stopped.


  - The Server

    Type

      python zhihu_stats_server.py

    into the shell to start the server.


img_seach.py：对输入的图片或id进行处理，找到相对应的精确图片或相似图片
/zhihu_stats/crawler_for_html/crawer_for_html.py 网页爬虫
/zhihu_stats/crawler_for_html/phantomjs.exe 无界面浏览器内核
/zhihu_stats/crawler_for_html/support.py 网页爬虫的依赖常量
/zhihu_stats/templates/home.html 我们的主页面和结果页面
/zhihu_stats/statics/css/material.indigo-purple.min.css 应用的MDL库的css文件
/zhihu_stats/statics/css/style.css 自定义界面的css文件
/zhihu_stats/statics/img/* 界面引用的一些背景图片
/zhihu_stats/statics/js/jQuery.js 使用的javascript引擎
/zhihu_stats/statics/js/material.min.js 应用的MDL库的js文件
/zhihu_stats/statics/js/script.js 自定义页面交互的css文件


* Using the Search Engine

  - Type into the textbox on top, then press Enter
    to create a query.

  - Click on the `upload` button on the right of
    the search box, then click the button on the
    left to select an image to be sent to the
    server to search for similar images.

  - If you want to use raw Lucene query strings,
    turn on the switch on the right. More info
    about Lucene query strings can be found on
    http://lucene.apache.org/core/4_10_0/
    queryparser/org/apache/lucene/queryparser/
    classic/package-summary.html .

  - Select the items that you want to query for by
    checking / unchecking the checkboxes below.

  - Determine how the entries are sorted by
    checking the radio buttons on the right.

  - Determine which entries will be shown by
    opening on the tabs on the bottom of the search
    region.

  - If you want to see statistics of a certain
    user / question, put your mouse on the result
    item for a few moment and corresponding data
    will be shown on the right.

  - Scroll to the bottom of the page to load more
    result entries.


* Troubleshooting

  - How do I stop the server?

    - Simply press Ctrl+C or Ctrl+Z to stop the
      program. We recommend pressing Ctrl+C because
      `socket already in use` errors will be more
      unlikely to occur in the future.


  - I've typed `stop` into the crawler / the image
    crawler, why isn't it stopping?

    - Check your typing. The four letters are
      lower-cased.

    - Sometimes (for example, when the crawler is
      jammed) the crawler won't respond to your
      `stop` command. In this case, you'll have to
      use Ctrl+C, Ctrl+Z or kill the process
      manually.


  - The crawler is always reporting errors. Why is
    that?

    - Most of the errors doesn't affect the running
      of the crawlers. Errors are most likely
      caused by unstable network connections or
      irregular responses.

  - The frontend is not responding.
  - The queries made through the frontend yields
    incorrect / broken results.

    - The frontend may be unstable for now, so when
      problems occur, try refreshing the page.

    - Don't forget that you can always extract the
      data you want directly from the database.
