import lucene, urllib2, bs4, collections, os, sys, time, traceback
from java.io import File
from org.apache.lucene.analysis.core import WhitespaceAnalyzer
from org.apache.lucene.index import DirectoryReader
from org.apache.lucene.queryparser.classic import QueryParser
from org.apache.lucene.store import SimpleFSDirectory
from org.apache.lucene.search import IndexSearcher, BooleanQuery, BooleanClause, Sort, SortField, MatchAllDocsQuery
from org.apache.lucene.index import FieldInfo, IndexWriter, IndexWriterConfig
from org.apache.lucene.document import Field
from org.apache.lucene.util import Version
import zhihu_page_analyzer as zh_pganlz
from zhihu_settings import *

class doc_object_data:
	def __init__(self):
		pass
class doc_object:
	def __init__(self):
		self.index = None
		self.data = doc_object_data()

def main():
	_vm = lucene.initVM(vmargs = ['-Djava.awt.headless=true'])

	searcher = IndexSearcher(DirectoryReader.open(SimpleFSDirectory(File(INDEXED_FOLDER))))
	analyzer = WhitespaceAnalyzer()
	query = MatchAllDocsQuery()
	with open('res.txt', 'w') as fout:
		res = searcher.search(query, 100)
		while len(res.scoreDocs) > 0:
			for x in res.scoreDocs:
				doc = searcher.doc(x.doc)
				for fd in list(doc.fields.toArray()):
					rfd = Field.cast_(fd)
					fout.write('{0} = "{1}"\n'.format(rfd.name(), rfd.stringValue().encode('utf8')))
				fout.write('\n')
			res = searcher.searchAfter(res.scoreDocs[-1], query, 100)

if __name__ == '__main__':
	main()
