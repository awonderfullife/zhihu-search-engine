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
from zhihu_page_analyzer import *
import zhihu_page_analyzer as zh_pganlz
import zhihu_index_and_task_dispatch as zh_iatd
import zhihu_client_api as zh_clnapi

def main():
	_vm = lucene.initVM(vmargs = ['-Djava.awt.headless=true'])

	query = BooleanQuery()
	query.add(MatchAllDocsQuery(), BooleanClause.Occur.MUST)
	query.add(TermQuery(Term('type', 'user')), BooleanClause.Occur.MUST)
	i = 0
	with zh_iatd.create_searcher() as searcher:
		with open('pagerank_data.txt', 'w') as fout:
			reslst = searcher.searcher.search(query, 100)
			initval = 1.0 / reslst.totalHits
			while len(reslst.scoreDocs) > 0:
				for x in reslst.scoreDocs:
					realdoc = searcher.searcher.doc(x.doc)
					obj = document_to_obj(realdoc)
					if not obj.data.followed_users is None:
						print '{0:8}'.format(i), '  user', obj.index, len(obj.data.followed_users)
						fout.write('{0}\t{1}\t{2}\n'.format(obj.index, initval, ' '.join((x.encode('utf8') for x in obj.data.followed_users))))
					else:
						print '{0:8}'.format(i), 'I user', obj.index
					i += 1
				reslst = searcher.searcher.searchAfter(reslst.scoreDocs[-1], query, 100)

if __name__ == '__main__':
	main()
