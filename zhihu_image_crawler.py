import lucene, urllib2, bs4, collections, os, sys, time, traceback, threading
from java.io import File
from org.apache.lucene.analysis.core import WhitespaceAnalyzer
from org.apache.lucene.index import DirectoryReader
from org.apache.lucene.queryparser.classic import QueryParser
from org.apache.lucene.store import SimpleFSDirectory
from org.apache.lucene.search import IndexSearcher, BooleanQuery, TermRangeQuery, BooleanClause, Sort, SortField, MatchAllDocsQuery, TermQuery
from org.apache.lucene.index import FieldInfo, IndexWriter, IndexWriterConfig, Term
from org.apache.lucene.document import Field
from org.apache.lucene.util import Version
import zhihu_client_api as zh_clnapi
import zhihu_page_analyzer as zh_pganlz
import zhihu_index_and_task_dispatch as zh_iatd
from zhihu_settings import *
from zhihu_common import *

_stop = False
_stopped = False
_vm = None

ZH_IMGTYPE_USER_AVATAR = 0
ZH_IMGTYPE_USERINFO_COVER = 1
ZH_IMGTYPE_ARTICLE_COVER = 2
ZH_IMGTYPE_TOPIC_ICON = 3
ZH_IMGTYPE_IN_ANSWER = 4
ZH_IMGTYPE_IN_ARTICLE = 5
ZH_IMGTYPE_IN_QUESTION = 6

def on_img_got(webp, toi, tid):
	print webp, toi, tid

def index_images_until_stop(session, handler, lbound):
	global _stop, _stopped, _vm

	_vm.attachCurrentThread()
	searcher = IndexSearcher(DirectoryReader.open(SimpleFSDirectory(File(TASK_FOLDER))))
	query = BooleanQuery()
	query.add(TermQuery(Term('finish_time', '0')), BooleanClause.Occur.MUST_NOT)
	query.add(MatchAllDocsQuery(), BooleanClause.Occur.MUST)
	if not lbound is None:
		query.add(TermRangeQuery.newStringRange('finish_time', lbound, '9999999999', False, True), BooleanClause.Occur.MUST)
	sort = Sort(SortField('finish_time', SortField.Type.INT))
	tmpbk = None
	res = searcher.search(query, 100, sort)
	answer_content_searcher = zh_iatd.create_searcher()
	logger = external_console_logger('/tmp/zh_imgc_info')
	while not _stop:
		print 'got', len(res.scoreDocs), 'docs'
		for x in res.scoreDocs:
			try:
				imgsgot = 0
				realdoc = searcher.doc(x.doc)
				doctype = realdoc['func_name']
				objid = realdoc['id']
				logger.write(' ft:{0}'.format(realdoc['finish_time']))
				if doctype == 'user_data':
					soup = bs4.BeautifulSoup(session.opener.open(urllib2.Request(
						url = 'https://www.zhihu.com/people/{0}'.format(objid)
					)), HTML_PARSER)
					cover = soup.select('#ProfileHeader .ProfileHeader-userCover img')
					if len(cover) > 0:
						cover_img = cover[0]['src']
						imgsgot += 1
						handler(cover_img, ZH_IMGTYPE_USERINFO_COVER, objid)
					avatar_img = soup.select('#ProfileHeader .ProfileHeader-main .UserAvatar img')[0]['src']
					imgsgot += 1
					handler(avatar_img, ZH_IMGTYPE_USER_AVATAR, objid)
				elif doctype == 'article_data':
					jsondata = session.get_article_content_raw(objid)
					if 'titleImage' in jsondata.keys():
						cover_img = jsondata['titleImage']
						if len(cover_img) > 0:
							imgsgot += 1
							handler(cover_img, ZH_IMGTYPE_ARTICLE_COVER, objid)
					soup = bs4.BeautifulSoup(jsondata['content'], HTML_PARSER)
					for x in soup.select('img'):
						imgsgot += 1
						handler(x['src'], ZH_IMGTYPE_IN_ARTICLE, objid)
				elif doctype == 'topic_data':
					soup = bs4.BeautifulSoup(session.opener.open(urllib2.Request(
						url = 'https://www.zhihu.com/topic/{0}/hot'.format(objid)
					)), HTML_PARSER)
					topic_img = soup.select('.zu-main-content .topic-avatar .zm-entry-head-avatar-link img')[0]['src']
					imgsgot += 1
					handler(topic_img, ZH_IMGTYPE_TOPIC_ICON, objid)
				elif doctype == 'answer_comments' and realdoc['start'] == '0':
					obj, q = zh_iatd.query_object(answer_content_searcher, objid, zh_pganlz.answer)
					for x in obj.data.text.as_soup().select('img'):
						imgsgot += 1
						handler(x['src'], ZH_IMGTYPE_IN_ANSWER, objid)
				elif doctype == 'question_data':
					soup = bs4.BeautifulSoup(session.opener.open(urllib2.Request(
						url = 'https://www.zhihu.com/question/{0}'.format(objid)
					)), HTML_PARSER)
					for x in soup.select('#zh-question-detail img'):
						imgsgot += 1
						handler(x['src'], ZH_IMGTYPE_IN_QUESTION, objid)
				else:
					logger.write('\n')
					continue
				logger.write(' ({0}, +{1})\n'.format(doctype, imgsgot))
				if _stop:
					break
				time.sleep(3)
			except Exception as e:
				logger.write('\n## ERROR ################################\n')
				logger.write(traceback.format_exc())
		if len(res.scoreDocs) > 0:
			tmpbk = res.scoreDocs[-1]
		res = searcher.searchAfter(tmpbk, query, 100, sort)
	print 'stopped'
	_stopped = True

def main():
	global _stop, _stopped, _vm

	_vm = lucene.initVM(vmargs = ['-Djava.awt.headless=true'])

	if os.path.exists('login_info'):
		with open('login_info', 'r') as fin:
			email = fin.readline()
			password = fin.readline()
		print 'Email:', email
		print 'Password: ', '*' * len(password)
	else:
		email = raw_input('Email: ')
		password = raw_input('Password: ')
	session = zh_clnapi.zhihu_session()
	session.login_email(email, password)

	if len(sys.argv) > 1:
		lbound = sys.argv[1]
	else:
		lbound = None
	newt = threading.Thread(target = index_images_until_stop, args = (session, on_img_got, lbound))
	newt.daemon = True
	newt.start()

	while True:
		x = raw_input()
		if x == 'stop':
			print 'stopping...'
			_stop = True
			while not _stopped:
				pass
			break

if __name__ == '__main__':
	main()
