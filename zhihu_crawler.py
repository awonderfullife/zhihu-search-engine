import lucene, sys, os, threading, time, traceback
from java.io import File
from org.apache.lucene.analysis.core import WhitespaceAnalyzer
from org.apache.lucene.document import Document, Field, FieldType, StringField, TextField
from org.apache.lucene.index import DirectoryReader, FieldInfo, IndexWriter, IndexWriterConfig, Term
from org.apache.lucene.queryparser.classic import QueryParser
from org.apache.lucene.store import SimpleFSDirectory
from org.apache.lucene.search import MatchAllDocsQuery, IndexSearcher, Sort, SortField, BooleanQuery, BooleanClause, TermQuery
from org.apache.lucene.util import Version
from zhihu_settings import *
from zhihu_common import *
import zhihu_index_and_task_dispatch as zh_iatd
import zhihu_client_api as zh_clnapi
import zhihu_page_analyzer as zh_pganlz

class task:
	def __init__(self):
		self.func_name = ''
		self.p_id = 0
		self.p_start = 0
		self.p_pagesize = 0
		self.p_extra = 0
		self.fails = 0
		self.finish_time = 0
		self.docid = 0

	def to_crawler_task(self):
		res = zh_iatd.crawler_task(
			vars(zh_iatd)['get_and_parse_' + self.func_name],
			self.p_id,
			self.p_start,
			self.p_pagesize,
			self.p_extra
		)
		res.fail_count = self.fails
		return res
	def from_crawler_task(self, ct):
		self.func_name = ct.func.func_name[14:]
		self.p_id = ct.prm_id
		self.p_start = ct.prm_start
		self.p_pagesize = ct.prm_pagesize
		self.p_extra = ct.prm_extra
		self.fails = ct.fail_count

	def to_document(self):
		def bool_to_int(bv):
			if bv:
				return 1
			return 0
		doc = Document()
		doc.add(StringField('func_name', self.func_name, Field.Store.YES))
		doc.add(StringField('id_isint', str(bool_to_int(isinstance(self.p_id, (int, long)))), Field.Store.YES))
		if isinstance(self.p_id, unicode):
			doc.add(StringField('id', self.p_id.encode('utf8'), Field.Store.YES))
		else:
			doc.add(StringField('id', str(self.p_id), Field.Store.YES))
		doc.add(StringField('start_isint', str(bool_to_int(isinstance(self.p_start, (int, long)))), Field.Store.YES))
		doc.add(StringField('start', str(self.p_start), Field.Store.YES))
		doc.add(StringField('pagesize', str(self.p_pagesize), Field.Store.YES))
		doc.add(StringField('pextra', str(self.p_extra), Field.Store.YES))
		doc.add(StringField('fails', str(self.fails), Field.Store.YES))
		doc.add(StringField('finish_time', str(self.finish_time), Field.Store.YES))
		doc.add(StringField('docid', str(self.docid), Field.Store.YES))
		return doc
	def from_document(self, doc):
		self.func_name = doc['func_name']
		if doc['id_isint'] == '1':
			self.p_id = int(doc['id'])
		else:
			self.p_id = doc['id']
		if doc['start_isint'] == '1':
			self.p_start = int(doc['start'])
		else:
			self.p_start = doc['start']
		self.p_pagesize = int(doc['pagesize'])
		self.p_extra = int(doc['pextra'])
		self.fails = int(doc['fails'])
		self.finish_time = int(doc['finish_time'])
		self.docid = long(doc['docid'])

ROOT_TOPIC = 19776749

def initialize(usr):
	task_writer = zh_iatd.create_index_writer(TASK_FOLDER)

	it = task()
	it.from_crawler_task(zh_iatd.crawler_task(zh_iatd.get_and_parse_user_data, usr))
	it.docid = 0
	task_writer.addDocument(it.to_document())

	it = task()
	it.from_crawler_task(zh_iatd.crawler_task(zh_iatd.get_and_parse_topic_data, ROOT_TOPIC))
	it.docid = 1
	task_writer.addDocument(it.to_document())

	task_writer.commit()
	task_writer.close()

	db_writer = zh_iatd.create_index_writer()
	db_writer.addDocument(zh_pganlz.obj_to_document(zh_pganlz.user(usr)))
	db_writer.addDocument(zh_pganlz.obj_to_document(zh_pganlz.topic(ROOT_TOPIC)))
	db_writer.commit()
	db_writer.close()

_vm = None
_stop = False
_stopped = False

class crawl_strategy:
	def __init__(self):
		self.types = (
			# 'question_data',
			# 'user_data',
			# 'topic_data',
			# 'article_data',
			# 'answers',
			'user_followed',
			# 'user_asked',
			# 'question_comments',
			# 'answer_comments',
			# 'user_articles',
			# 'article_comments',
			'topic_children_indices',
			'user_watched_topics'
		)
		self.curtype = 0

	def process_query(self, q):
		q.add(TermQuery(Term('func_name', self.types[self.curtype])), BooleanClause.Occur.MUST)
		self.curtype += 1
		if self.curtype == len(self.types):
			self.curtype = 0

def crawl_until_stop(session):
	global _vm, _stop, _stopped

	_vm.attachCurrentThread()

	db_writer = zh_iatd.create_index_writer()

	info_logger = external_console_logger('/tmp/zh_c_info')
	error_logger = external_console_logger('/tmp/zh_c_err')
	strategy = crawl_strategy()

	errcount = 0

	while not _stop:
		info_logger.write('  acquiring new tasks... ')
		task_reader = zh_iatd.create_searcher(TASK_FOLDER)
		default_query = BooleanQuery()
		default_query.add(TermQuery(Term('finish_time', '0')), BooleanClause.Occur.MUST)
		strategy.process_query(default_query)
		idstart = task_reader.reader.numDocs()
		searchres = task_reader.searcher.search(default_query, 100)
		resdocs = [task_reader.searcher.doc(x.doc) for x in searchres.scoreDocs]
		info_logger.write('got:{0} total:{1}\n'.format(searchres.totalHits, idstart))
		task_reader.close()

		task_writer = zh_iatd.create_index_writer(TASK_FOLDER)

		for doct in resdocs:
			curt = task()
			curt.from_document(doct)
			crlt = curt.to_crawler_task()
			try:
				crlt.func(session, crlt)
			except Exception as e:
				info_logger.write('FAIL')
				error_logger.write('## ERROR ################################\n')
				zh_pganlz.print_object(crlt, out = error_logger)
				error_logger.write('-- stacktrace ---------------------------\n')
				error_logger.write(traceback.format_exc())
				errcount += 1
				error_logger.write('[Error count: {0}]\n'.format(errcount))

				task_writer.deleteDocuments(Term('docid', str(doct['docid'])))
				curt.fails += 1
				task_writer.addDocument(curt.to_document())
			else:
				if not crlt.result_rep_obj is None:
					db_writer.deleteDocuments(crlt.result_query)
					db_writer.addDocument(zh_pganlz.obj_to_document(crlt.result_rep_obj))
				for x in crlt.result_new:
					db_writer.addDocument(zh_pganlz.obj_to_document(x))
				db_writer.commit()

				task_writer.deleteDocuments(Term('docid', str(doct['docid'])))
				curt.finish_time = int(time.time())
				task_writer.addDocument(curt.to_document())
				for x in crlt.result_tasks:
					newt = task()
					newt.from_crawler_task(x)
					newt.docid = idstart
					idstart += 1
					task_writer.addDocument(newt.to_document())
			if isinstance(crlt.prm_id, unicode):
				prids = crlt.prm_id.encode('utf8')
			else:
				prids = str(crlt.prm_id)
			info_logger.write(' ~{0}(+{1}) -{2} {3}({4}, {5}, {6}, {7})\n'.format(
				task_writer.numDocs(),
				len(crlt.result_tasks),
				curt.fails,
				crlt.func.func_name[14:],
				prids,
				crlt.prm_start,
				crlt.prm_pagesize,
				crlt.prm_extra
			))
			if _stop:
				break
			time.sleep(1)
		task_writer.close()
	info_logger.write('stopped\n')
	_stopped = True

def main():
	global _vm, _stop, _stopped

	_vm = lucene.initVM(vmargs = ['-Djava.awt.headless=true'])
	if len(sys.argv) > 2 and sys.argv[1] == 'init':
		initialize(sys.argv[2])
	else:
		if os.path.exists('login_info'):
			with open('login_info', 'r') as fin:
				email = fin.readline().strip()
				password = fin.readline().strip()
			print 'Email:', email
			print 'Password:', '*' * len(password)
		else:
			email = raw_input('Email: ')
			password = raw_input('Password: ')
		session = zh_clnapi.zhihu_session()
		session.login_email(email, password)

		crawlt = threading.Thread(target = crawl_until_stop, args = (session,))
		crawlt.daemon = True
		crawlt.start()

		while True:
			x = raw_input()
			if x == 'stop':
				print 'stopping...'
				_stop = True
				while not _stopped:
					pass
				break
		print 'stopped'

if __name__ == '__main__':
	main()
