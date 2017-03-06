import lucene, urllib2, bs4, collections, os, sys, time, traceback
from java.io import File
from org.apache.lucene.analysis.core import WhitespaceAnalyzer
from org.apache.lucene.index import DirectoryReader
from org.apache.lucene.queryparser.classic import QueryParser
from org.apache.lucene.store import SimpleFSDirectory
from org.apache.lucene.search import IndexSearcher, BooleanQuery, BooleanClause, TermQuery
from org.apache.lucene.index import FieldInfo, IndexWriter, IndexWriterConfig, Term
from org.apache.lucene.util import Version
import zhihu_client_api as zh_clnapi
import zhihu_page_analyzer as zh_pganlz
from zhihu_settings import *

class crawler_task:
	def __init__(self, func, p_id = 0, p_start = 0, p_pagesize = 0, p_extra = 0):
		self.func = func
		self.result_new = []
		self.result_query = None
		self.result_rep_obj = None
		self.result_tasks = []
		self.prm_id = p_id
		self.prm_start = p_start
		self.prm_pagesize = p_pagesize
		self.prm_extra = p_extra
		self.fail_count = 0
	def reinitialize(self):
		self.result_new = []
		self.result_query = None
		self.result_rep_obj = None
		self.result_tasks = []

def create_index_writer(directory = INDEXED_FOLDER):
	config = IndexWriterConfig(Version.LUCENE_CURRENT, WhitespaceAnalyzer())
	config.setOpenMode(IndexWriterConfig.OpenMode.CREATE_OR_APPEND)
	return IndexWriter(SimpleFSDirectory(File(directory)), config)

class searcher_wrapper:
	def __init__(self, reader):
		self.reader = reader
		self.searcher = IndexSearcher(self.reader)
	def close(self):
		self.reader.close()

	def __enter__(self):
		return self
	def __exit__(self, exc_type, exc_value, exc_tb):
		self.close()

def create_searcher(directory = INDEXED_FOLDER):
	return searcher_wrapper(DirectoryReader.open(SimpleFSDirectory(File(directory))))
def create_query(qdict):
	q = BooleanQuery()
	for k, v in qdict.items():
		q.add(TermQuery(Term(k, v)), BooleanClause.Occur.MUST)
	return q
def create_query_for_object(objid, objtype):
	if isinstance(objid, unicode):
		return create_query({'index': objid.encode('utf8'), 'type': objtype.__name__})
	return create_query({'index': str(objid), 'type': objtype.__name__})

def query_object(searcher, objid, objtype):
	query = create_query_for_object(objid, objtype)
	res = searcher.searcher.search(query, 1)
	if res.totalHits == 0:
		return None
	if res.totalHits > 1:
		raise Exception('database corrupted')
	return zh_pganlz.document_to_obj(searcher.searcher.doc(res.scoreDocs[0].doc)), query


def get_and_parse_question_data(session, tsk):
	with create_searcher() as searcher:
		tsk.result_rep_obj, tsk.result_query = query_object(searcher, tsk.prm_id, zh_pganlz.question)
		resourceid = tsk.result_rep_obj.parse_page(session.opener.open(urllib2.Request(
			url = 'https://www.zhihu.com/question/{0}'.format(tsk.prm_id)
		)).read())
		# generate subtasks
		for x in tsk.result_rep_obj.data.tag_indices:
			if query_object(searcher, x, zh_pganlz.topic) is None:
				tsk.result_new.append(zh_pganlz.topic(x))
				tsk.result_tasks.append(crawler_task(get_and_parse_topic_data, x))
		tsk.result_tasks.append(crawler_task(get_and_parse_answers, tsk.prm_id, 0, 10))
		tsk.result_tasks.append(crawler_task(get_and_parse_question_comments, tsk.prm_id, p_extra = resourceid))

def get_and_parse_user_data(session, tsk):
	with create_searcher() as searcher:
		tsk.result_rep_obj, tsk.result_query = query_object(searcher, tsk.prm_id, zh_pganlz.user)
	tsk.result_rep_obj.parse_personal_info_page(session.opener.open(urllib2.Request(
		url = 'https://www.zhihu.com/people/{0}'.format(tsk.prm_id.encode('utf8'))
	)).read())
	# generate subtasks
	tsk.result_tasks.append(crawler_task(get_and_parse_user_followed, tsk.result_rep_obj.index, 0, 10))
	tsk.result_tasks.append(crawler_task(get_and_parse_user_asked, tsk.result_rep_obj.index, 0, 10))
	tsk.result_tasks.append(crawler_task(get_and_parse_user_articles, tsk.result_rep_obj.index, 0, 10))
	tsk.result_tasks.append(crawler_task(get_and_parse_user_watched_topics, tsk.result_rep_obj.index, 0, 10))

def get_and_parse_topic_data(session, tsk):
	with create_searcher() as searcher:
		tsk.result_rep_obj, tsk.result_query = query_object(searcher, tsk.prm_id, zh_pganlz.topic)
	tsk.result_rep_obj.parse_info_page(bs4.BeautifulSoup(session.opener.open(urllib2.Request(
		url = 'https://www.zhihu.com/topic/{0}/hot'.format(tsk.prm_id)
	)).read(), HTML_PARSER))
	# generate subtasks
	tsk.result_tasks.append(crawler_task(get_and_parse_topic_children_indices, tsk.result_rep_obj.index, ''))

def get_and_parse_article_data(session, tsk):
	with create_searcher() as searcher:
		tsk.result_rep_obj, tsk.result_query = query_object(searcher, tsk.prm_id, zh_pganlz.article)
		artjson = session.get_article_content_raw(tsk.prm_id)
		tsk.result_rep_obj.data.tag_indices = []
		tsk.result_rep_obj.data.title = artjson['title']
		for x in artjson['topics']:
			tsk.result_rep_obj.data.tag_indices.append(x['id'])
		tsk.result_rep_obj.data.text = zh_pganlz.hyper_text(artjson['content'])
		tsk.result_rep_obj.data.likes = artjson['likesCount']
		tsk.result_rep_obj.data.date = zh_pganlz.date_to_int(zh_pganlz.parse_javascript_date(artjson['publishedTime']))
		# generate subtasks
		for x in tsk.result_rep_obj.data.tag_indices:
			if query_object(searcher, x, zh_pganlz.topic) is None:
				tsk.result_new.append(zh_pganlz.topic(x))
				tsk.result_tasks.append(crawler_task(get_and_parse_topic_data, x))
		tsk.result_tasks.append(crawler_task(get_and_parse_article_comments, tsk.prm_id, 0, 10))


def get_and_parse_answers(session, tsk):
	with create_searcher() as searcher:
		ansjson = session.get_question_answer_list_raw(tsk.prm_id, tsk.prm_start, tsk.prm_pagesize)
		if len(ansjson['msg']) == 0:
			return
		for x in ansjson['msg']:
			ansobj = zh_pganlz.answer()
			ansobj.parse(bs4.BeautifulSoup(x, HTML_PARSER).html.body.div)
			ansobj.data.question_index = tsk.prm_id
			if query_object(searcher, ansobj.index, zh_pganlz.answer) is None:
				tsk.result_new.append(ansobj)
		# generate subtasks
		tsk.result_tasks.append(crawler_task(get_and_parse_answers, tsk.prm_id, tsk.prm_start + tsk.prm_pagesize, tsk.prm_pagesize))
		newuser_list = []
		newuser_set = set()
		for x in tsk.result_new:
			if not x.data.author_index is None:
				if query_object(searcher, x.data.author_index, zh_pganlz.user) is None and x.data.author_index not in newuser_set:
					newuser_set.add(x.data.author_index)
					newuser_list.append(zh_pganlz.user(x.data.author_index))
					tsk.result_tasks.append(crawler_task(get_and_parse_user_data, x.data.author_index))
			tsk.result_tasks.append(crawler_task(get_and_parse_answer_comments, x.index, 1))
		tsk.result_new += newuser_list

def get_and_parse_user_followed(session, tsk):
	with create_searcher() as searcher:
		tsk.result_rep_obj, tsk.result_query = query_object(searcher, tsk.prm_id, zh_pganlz.user)
		foljson = session.get_followees_raw(tsk.prm_id, tsk.prm_start, tsk.prm_pagesize)
		newlst = []
		for userdata in foljson['data']:
			newlst.append(userdata['url_token'])
		if tsk.result_rep_obj.data.followed_users is None:
			tsk.result_rep_obj.data.followed_users = newlst
		else:
			tsk.result_rep_obj.data.followed_users += newlst
		# generate subtasks
		found_users = set()
		for x in newlst:
			if query_object(searcher, x, zh_pganlz.user) is None and x not in found_users:
				found_users.add(x)
				tsk.result_new.append(zh_pganlz.user(x))
				tsk.result_tasks.append(crawler_task(get_and_parse_user_data, x))
	if foljson['paging']['is_end']:
		return
	tsk.result_tasks.append(crawler_task(get_and_parse_user_followed, tsk.prm_id, tsk.prm_start + tsk.prm_pagesize, tsk.prm_pagesize))

def get_and_parse_user_asked(session, tsk):
	with create_searcher() as searcher:
		tsk.result_rep_obj, tsk.result_query = query_object(searcher, tsk.prm_id, zh_pganlz.user)
		askjson = session.get_asked_questions_raw(tsk.prm_id, tsk.prm_start, tsk.prm_pagesize)
		newlst = []
		for qdata in askjson['data']:
			newlst.append(qdata['id'])
		if tsk.result_rep_obj.data.asked_questions is None:
			tsk.result_rep_obj.data.asked_questions = newlst
		else:
			tsk.result_rep_obj.data.asked_questions += newlst
		# generate subtasks
		for x in newlst:
			if query_object(searcher, x, zh_pganlz.question) is None:
				tsk.result_new.append(zh_pganlz.question(x))
				tsk.result_tasks.append(crawler_task(get_and_parse_question_data, x))
	if askjson['paging']['is_end']:
		return
	tsk.result_tasks.append(crawler_task(get_and_parse_user_asked, tsk.prm_id, tsk.prm_start + tsk.prm_pagesize, tsk.prm_pagesize))

def get_and_parse_question_comments(session, tsk):
	with create_searcher() as searcher:
		soup = bs4.BeautifulSoup(session.get_question_comments_raw(tsk.prm_extra), HTML_PARSER)
		for x in soup.select('.zm-item-comment'):
			comm = zh_pganlz.comment()
			comm.parse_question_comment(x)
			comm.data.target = tsk.prm_id
			comm.data.target_type = zh_pganlz.ZH_CT_QUESTION
			if query_object(searcher, comm.index, zh_pganlz.comment) is None:
				tsk.result_new.append(comm)
		# generate subtasks
		newuser_list = []
		newuser_set = set()
		for x in tsk.result_new:
			if not x.data.author_index is None:
				if query_object(searcher, x.data.author_index, zh_pganlz.user) is None and x.data.author_index not in newuser_set:
					newuser_set.add(x.data.author_index)
					newuser_list.append(zh_pganlz.user(x.data.author_index))
					tsk.result_tasks.append(crawler_task(get_and_parse_user_data, x.data.author_index))
		tsk.result_new += newuser_list

def get_and_parse_answer_comments(session, tsk):
	commjson = session.get_answer_comments_raw(tsk.prm_id, tsk.prm_start)
	if len(commjson['data']) == 0:
		return
	with create_searcher() as searcher:
		for x in commjson['data']:
			comm = zh_pganlz.comment()
			comm.index = x['id']
			comm.data.target = tsk.prm_id
			comm.data.target_type = zh_pganlz.ZH_CT_ANSWER
			comm.data.likes = x['likesCount']
			if not ('anonymous' in x['author'].keys() and x['author']['anonymous']):
				comm.data.author_index = x['author']['slug']
			comm.data.response_to_index = x['inReplyToCommentId']
			comm.data.is_response = comm.data.response_to_index != 0
			if not comm.data.is_response:
				comm.data.response_to_index = None
			comm.data.text = x['content']
			comm.data.date = zh_pganlz.date_to_int(zh_pganlz.parse_javascript_date(x['createdTime']))
			if query_object(searcher, comm.index, zh_pganlz.comment) is None:
				tsk.result_new.append(comm)
		# generate subtasks
		newuser_list = []
		newuser_set = set()
		for x in tsk.result_new:
			if not x.data.author_index is None:
				if query_object(searcher, x.data.author_index, zh_pganlz.user) is None and x.data.author_index not in newuser_set:
					newuser_set.add(x.data.author_index)
					newuser_list.append(zh_pganlz.user(x.data.author_index))
					tsk.result_tasks.append(crawler_task(get_and_parse_user_data, x.data.author_index))
		tsk.result_new += newuser_list
		tsk.result_tasks.append(crawler_task(get_and_parse_answer_comments, tsk.prm_id, tsk.prm_start + 1))

def get_and_parse_user_articles(session, tsk):
	with create_searcher() as searcher:
		tsk.result_rep_obj, tsk.result_query = query_object(searcher, tsk.prm_id, zh_pganlz.user)
		askjson = session.get_articles_raw(tsk.prm_id, tsk.prm_start, tsk.prm_pagesize)
		newlst = []
		for qdata in askjson['data']:
			if query_object(searcher, qdata['id'], zh_pganlz.article) is None:
				newlst.append(qdata['id'])
		if tsk.result_rep_obj.data.asked_questions is None:
			tsk.result_rep_obj.data.asked_questions = newlst
		else:
			tsk.result_rep_obj.data.asked_questions += newlst
		# generate subtasks
		for x in newlst:
			if query_object(searcher, x, zh_pganlz.article) is None:
				tsk.result_new.append(zh_pganlz.article(x))
				tsk.result_tasks.append(crawler_task(get_and_parse_article_data, x))
	if askjson['paging']['is_end']:
		return
	tsk.result_tasks.append(crawler_task(get_and_parse_user_articles, tsk.prm_id, tsk.prm_start + tsk.prm_pagesize, tsk.prm_pagesize))

def get_and_parse_article_comments(session, tsk):
	commjson = session.get_article_comments_raw(tsk.prm_id, tsk.prm_start, tsk.prm_pagesize)
	if len(commjson) == 0:
		return
	with create_searcher() as searcher:
		for x in commjson:
			comm = zh_pganlz.comment()
			comm.index = x['id']
			comm.data.target = tsk.prm_id
			comm.data.target_type = zh_pganlz.ZH_CT_ARTICLE
			comm.data.text = x['content']
			comm.data.author_index = x['author']['slug']
			comm.data.is_response = x['inReplyToCommentId'] > 0
			if comm.data.is_response:
				comm.data.response_to_index = x['inReplyToCommentId']
			comm.data.likes = x['likesCount']
			comm.data.date = zh_pganlz.date_to_int(zh_pganlz.parse_javascript_date(x['createdTime']))
			if query_object(searcher, comm.index, zh_pganlz.comment) is None:
				tsk.result_new.append(comm)
		# generate subtasks
		newuser_lst = []
		newuser_set = set()
		for x in tsk.result_new:
			if query_object(searcher, x.data.author_index, zh_pganlz.user) is None and x.data.author_index not in newuser_set:
				newuser_set.add(x.data.author_index)
				newuser_lst.append(zh_pganlz.user(x.data.author_index))
				tsk.result_tasks.append(crawler_task(get_and_parse_user_data, x.data.author_index))
		tsk.result_new += newuser_lst
		tsk.result_tasks.append(crawler_task(get_and_parse_article_comments, tsk.prm_id, tsk.prm_start + tsk.prm_pagesize, tsk.prm_pagesize))

def get_and_parse_topic_children_indices(session, tsk):
	with create_searcher() as searcher:
		ansjson = session.get_children_topics(tsk.prm_id, tsk.prm_start)
		tsk.result_rep_obj, tsk.result_query = query_object(searcher, tsk.prm_id, zh_pganlz.topic)
		nextpg = None
		ctpc = []
		for x in ansjson['msg'][1]:
			curt = x[0]
			if curt[0] == 'load':
				nextpg = int(curt[2])
			elif curt[0] == 'topic':
				ctpc.append(int(curt[2]))
		if tsk.result_rep_obj.data.child_tag_indices is None:
			tsk.result_rep_obj.data.child_tag_indices = ctpc
		else:
			tsk.result_rep_obj.data.child_tag_indices += ctpc
		# generate subtasks
		for x in ctpc:
			if query_object(searcher, x, zh_pganlz.topic) is None:
				tsk.result_new.append(zh_pganlz.topic(x))
				tsk.result_tasks.append(crawler_task(get_and_parse_topic_data, x))
		if not nextpg is None:
			tsk.result_tasks.append(crawler_task(get_and_parse_topic_children_indices, tsk.prm_id, nextpg))

def get_and_parse_user_watched_topics(session, tsk):
	with create_searcher() as searcher:
		tsk.result_rep_obj, tsk.result_query = query_object(searcher, tsk.prm_id, zh_pganlz.user)
		askjson = session.get_watched_topics_raw(tsk.prm_id, tsk.prm_start, tsk.prm_pagesize)
		newlst = []
		for qdata in askjson['data']:
			if query_object(searcher, qdata['topic']['id'], zh_pganlz.topic) is None:
				newlst.append(int(qdata['topic']['id']))
		if tsk.result_rep_obj.data.followed_topics is None:
			tsk.result_rep_obj.data.followed_topics = newlst
		else:
			tsk.result_rep_obj.data.followed_topics += newlst
		# generate subtasks
		for x in newlst:
			if query_object(searcher, x, zh_pganlz.topic) is None:
				tsk.result_new.append(zh_pganlz.topic(x))
				tsk.result_tasks.append(crawler_task(get_and_parse_topic_data, x))
	if askjson['paging']['is_end']:
		return
	tsk.result_tasks.append(crawler_task(get_and_parse_user_watched_topics, tsk.prm_id, tsk.prm_start + tsk.prm_pagesize, tsk.prm_pagesize))


def main():
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

	q = collections.deque()
	q.append(crawler_task(get_and_parse_user_data, 'excited-vczh'))
	# q.append(crawler_task(get_and_parse_user_data, 'bao-xue-you-xi-yun-ying-tuan-dui'))
	# q.append(crawler_task(get_and_parse_answer_comments, 46554899, 1))
	# q.append(crawler_task(get_and_parse_question_data, 51420695))
	iwriter = create_index_writer()
	iwriter.commit() # create the folder and files for following search operations
	while len(q) > 0:
		ct = q.popleft()

		try:
			ct.func(session, ct)
		except Exception as e:
			print '! TASKFAIL'
			zh_pganlz.print_object(ct)
			traceback.print_exc()
			ct.reinitialize()
			ct.fail_count += 1
			q.append(ct)
		else:
			if not ct.result_rep_obj is None:
				iwriter.deleteDocuments(ct.result_query)
				iwriter.addDocument(zh_pganlz.obj_to_document(ct.result_rep_obj))
			for x in ct.result_new:
				iwriter.addDocument(zh_pganlz.obj_to_document(x))
			iwriter.commit()
			for x in ct.result_tasks:
				q.append(x)
			if ct.fail_count > 0:
				fstr = 'fails:{0} '.format(ct.fail_count)
			else:
				fstr = ''
			print 'TASKDONE', ct.func.func_name, ct.prm_id, fstr + 'tasks:{0}(+{1})'.format(len(q), len(ct.result_tasks))
		time.sleep(1)

if __name__ == '__main__':
	main()
