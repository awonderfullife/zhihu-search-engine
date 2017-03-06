import lucene, sys, os, threading, time, traceback
from java.io import File
from org.apache.lucene.analysis.core import WhitespaceAnalyzer
from org.apache.lucene.document import Document, Field, FieldType, StringField, TextField
from org.apache.lucene.index import DirectoryReader, FieldInfo, IndexWriter, IndexWriterConfig, Term
from org.apache.lucene.queryparser.classic import QueryParser
from org.apache.lucene.store import SimpleFSDirectory
from org.apache.lucene.search import MatchAllDocsQuery, IndexSearcher, Sort, SortField, BooleanQuery, BooleanClause
from org.apache.lucene.util import Version
from zhihu_settings import *
from zhihu_common import *
from zhihu_page_analyzer import *
import zhihu_page_analyzer as zh_pganlz
import zhihu_index_and_task_dispatch as zh_iatd
import zhihu_client_api as zh_clnapi

def obj_to_document_old(obj):
	res = Document()
	res.add(StringField('index', str(obj.index), Field.Store.YES))
	res.add(StringField('type', obj.__class__.__name__, Field.Store.YES))
	for k, v in vars(obj.data).items():
		if v is None:
			res.add(Field(LT_NONE + k, '', Field.Store.YES, Field.Index.NO))
		elif isinstance(v, list):
			if len(v) > 0 and isinstance(v[0], int):
				res.add(TextField(LT_INTLIST + k, ' '.join((str(x) for x in set(v))), Field.Store.YES))
			else:
				res.add(TextField(LT_LIST + k, ' '.join(list(set(v))), Field.Store.YES))
		elif isinstance(v, str) or isinstance(v, unicode):
			res.add(Field(LT_STRING + k, v, Field.Store.YES, Field.Index.NO))
			res.add(TextField(LT_FOR_QUERY + k, ' '.join(jieba.lcut(v)), Field.Store.NO))
		elif isinstance(v, hyper_text):
			res.add(Field(LT_HYPERTEXT + k, v.raw, Field.Store.YES, Field.Index.NO))
			res.add(TextField(LT_FOR_QUERY + k, ' '.join(jieba.lcut(v.text)), Field.Store.NO))
		elif isinstance(v, bool):
			if v:
				vs = '1'
			else:
				vs = '0'
			res.add(StringField(LT_BOOL + k, vs, Field.Store.YES))
		elif isinstance(v, int) or isinstance(v, long):
			res.add(StringField(LT_INT + k, str(v), Field.Store.YES))
		else:
			raise Exception('unrecognized data type')
	return res
def document_to_obj_old(doc):
	obj = globals()[doc['type']]()
	for field in list(doc.fields.toArray()):
		rf = Field.cast_(field)
		k, v = rf.name(), rf.stringValue()
		if k == 'type':
			pass
		elif k == 'index':
			if isinstance(obj, user):
				obj.index = v
			else:
				obj.index = int(v)
		else:
			if k[0] == LT_FOR_QUERY:
				pass
			elif k[0] == LT_NONE:
				setattr(obj.data, k[1:], None)
			elif k[0] == LT_LIST:
				setattr(obj.data, k[1:], v.split())
			elif k[0] == LT_INTLIST:
				setattr(obj.data, k[1:], [int(x) for x in v.split()])
			elif k[0] == LT_STRING:
				setattr(obj.data, k[1:], v)
			elif k[0] == LT_HYPERTEXT:
				setattr(obj.data, k[1:], hyper_text(v))
			elif k[0] == LT_BOOL:
				if v == '1':
					setattr(obj.data, k[1:], True)
				elif v == '0':
					setattr(obj.data, k[1:], False)
				else:
					raise Exception('invalid bool value')
			elif k[0] == LT_INT:
				setattr(obj.data, k[1:], int(v))
			else:
				raise Exception('unrecognized property: ' + k)
	return obj

def main():
	_vm = lucene.initVM(vmargs = ['-Djava.awt.headless=true'])
	db_writer = zh_iatd.create_index_writer('.newdb')
	db_reader = zh_iatd.create_searcher(INDEXED_FOLDER)

	if len(sys.argv) < 2:
		res = db_reader.searcher.search(MatchAllDocsQuery(), 100)
		tot = 0
		while len(res.scoreDocs) > 0:
			for x in res.scoreDocs:
				realdoc = db_reader.searcher.doc(x.doc)
				obj = document_to_obj(realdoc)
				newdoc = obj_to_document(obj)
				db_writer.addDocument(newdoc)
				tot += 1
				sys.stdout.write('\r{0}'.format(tot))
				sys.stdout.flush()
			res = db_reader.searcher.searchAfter(res.scoreDocs[-1], MatchAllDocsQuery(), 100)
	elif sys.argv[1] == 'mergerank':
		ranks = {}
		with open('prrank.txt', 'r') as fin:
			for x in fin.readlines():
				v = x.split()
				ranks[v[0]] = float(v[1])

		res = db_reader.searcher.search(MatchAllDocsQuery(), 100)
		tot = 0
		while len(res.scoreDocs) > 0:
			for x in res.scoreDocs:
				realdoc = db_reader.searcher.doc(x.doc)
				obj = document_to_obj(realdoc)
				if isinstance(obj, zh_pganlz.user):
					if obj.index in ranks.keys():
						obj.data.rank = ranks[obj.index]
				newdoc = obj_to_document(obj)
				db_writer.addDocument(newdoc)
				tot += 1
				sys.stdout.write('\r{0}'.format(tot))
				sys.stdout.flush()
			res = db_reader.searcher.searchAfter(res.scoreDocs[-1], MatchAllDocsQuery(), 100)

	db_writer.commit()

if __name__ == '__main__':
	main()
