import lucene, urllib, urllib2, web, json, jieba, bs4, os
from org.apache.lucene.analysis.core import WhitespaceAnalyzer
from org.apache.lucene.index import Term
from org.apache.lucene.queryparser.classic import QueryParser
from org.apache.lucene.search import BooleanQuery, TermQuery, BooleanClause, Sort, SortField
import img_search
import zhihu_client_api as zh_clnapi
import zhihu_index_and_task_dispatch as zh_iatd
import zhihu_page_analyzer as zh_pganlz
from zhihu_common import *
from zhihu_settings import *

_SERVER_PREFIX = 'SS'
_SERVER_ANY_PREFIX = 'SA'

renderer = web.template.render('./templates/')

_vm = None
_session = zh_clnapi.zhihu_session()

class SS_:
	def GET(self):
		return renderer.home()

def summarize(text, cut_search, window = 100):
	content = get_content(doc.get('path'))
	tokres = jieba.tokenize(content, mode='search')
	search_words = {}
	for i in range(len(cut_search)):
		search_words[cut_search[i]] = i
	kaps = []
	for x in tokres:
		if x[0] in search_words.keys():
			kaps.append((x[1], x[2], search_words[x[0]]))
	kaps.sort(key = (lambda x: x[0]))
	nextitem = 0
	maxv, s, e = 0, 0, 0
	for i in range(len(kaps)):
		end = kaps[i][0] + window
		while nextitem < len(kaps) and kaps[nextitem][1] <= end:
			nextitem += 1
		exc, rni = nextitem - i, nextitem
		while rni < len(kaps) and kaps[rni][0] < end:
			if kaps[rni][1] <= end:
				exc += 1
			rni += 1
		if exc > maxv:
			maxv, s, e = exc, i, rni
	lens = kaps[s][0]
	kaps = kaps[s:e]
	maxk = max((x[1] for x in kaps if x[1] <= lens + window))
	lens -= (lens + window - maxk) / 2
	if lens + window > len(content):
		lens = len(content) - window
	if lens < 0:
		lens = 0
	return maxv, lens, len(content), content[lens:lens + window], kaps

class SS_search:
	def POST(self):
		def build_text_query(k, v):
			return QueryParser(k, WhitespaceAnalyzer()).parse(' '.join(jieba.lcut(v)))
		def build_anyterm_query(field, strv):
			res = BooleanQuery()
			for i in strv.split():
				res.add(TermQuery(Term(field, i)), BooleanClause.Occur.SHOULD)
			return res

		def get_query_result(sarc, dct):
			PAGE_SIZE = 10
			PAGE_JUMP = 10

			query = BooleanQuery()
			query.add(TermQuery(Term(zh_pganlz.LTPF_TYPE, '1')), BooleanClause.Occur.MUST)
			page = 0
			sort_lists = []
			summ_set = set()
			exclus_set = None
			words = []
			for k, v in dct.items():
				if k in ('index', 'type', 'tag_indices', 'author_index'):
					query.add(build_anyterm_query(k, dct[k]), BooleanClause.Occur.MUST)
				elif k in ('text', 'contents', 'title', 'description', 'alias'):
					words += jieba.lcut(v)
					query.add(build_text_query(k + zh_pganlz.LTPF_FOR_QUERY, dct[k]), BooleanClause.Occur.MUST)

				elif k == 'raw':
					query.add(QueryParser('index', WhitespaceAnalyzer()).parse(dct[k]), BooleanClause.Occur.MUST)
				elif k == 'enhraw':
					x = 0
					reslst = []
					for entry in v:
						if x == 2:
							reslst += [lastdoc + x.encode('utf8') for x in jieba.cut(entry)]
							x = 0
						else:
							if x == 0:
								reslst.append(entry.encode('utf8'))
							else:
								lastdoc = entry.encode('utf8')
							x += 1
					query.add(QueryParser('index', WhitespaceAnalyzer()).parse(' '.join(reslst)), BooleanClause.Occur.MUST)

				elif k == 'page':
					page = int(dct[k])
				elif k == 'sort':
					for x in dct['sort']:
						sort_type = SortField.Type.STRING
						if 'type' in x.keys():
							if x['type'] == 'int':
								sort_type = SortField.Type.INT
							elif x['type'] == 'float':
								sort_type = SortField.Type.FLOAT
						reverse = False
						if 'reverse' in x.keys():
							reverse = x['reverse']
						sort_lists.append(SortField(x['key'], sort_type, reverse))

				elif k == 'summarize':
					summ_set = set(v)
				elif k == 'exclusive':
					exclus_set = set(v)

			ressrt = Sort(*sort_lists)
			resdocs = sarc.searcher.search(query, PAGE_SIZE, ressrt)
			if page > 0:
				if resdocs.totalHits > page * PAGE_SIZE:
					page -= 1
					while page > PAGE_JUMP:
						resdocs = sarc.searcher.searchAfter(resdocs.scoreDocs[-1], query, PAGE_SIZE * PAGE_JUMP, ressrt)
						page -= PAGE_JUMP
					if page > 0:
						resdocs = sarc.searcher.searchAfter(resdocs.scoreDocs[-1], query, PAGE_SIZE * page, ressrt)
					resdocs = sarc.searcher.searchAfter(resdocs.scoreDocs[-1], query, PAGE_SIZE, ressrt)
				else:
					resdocs.scoreDocs = []
			reslst = []
			for x in resdocs.scoreDocs:
				dictobj = zh_pganlz.obj_to_json(zh_pganlz.document_to_obj(sarc.searcher.doc(x.doc)))
				if 'additional' in dct.keys():
					adres = []
					for x in dct['additional']:
						if isinstance(dictobj[x['sourcefield']], list):
							qlist = dictobj[x['sourcefield']]
						else:
							qlist = [dictobj[x['sourcefield']]]
						cres = []
						for qword in qlist:
							if not isinstance(qword, (unicode, str)):
								qword = str(qword)
							searchres = sarc.searcher.search(zh_iatd.create_query({'type': x['type'], x['targetfield']: qword}), 1)
							if searchres.totalHits > 1:
								print x, 'FOUND', searchres
							elif searchres.totalHits == 0:
								cres.append(None)
							else:
								cres.append(zh_pganlz.obj_to_json(zh_pganlz.document_to_obj(sarc.searcher.doc(searchres.scoreDocs[0].doc))))
						adres.append(cres)
				for k, v in dictobj.items():
					if k in summ_set:
						dictobj[k + '_summary'] = summarize(hyper_text(v).text, list(set(words)))
				if not exclus_set is None:
					for k in dictobj.keys():
						if not k in exclus_set:
							del dictobj[k]
				if 'additional' in dct.keys():
					dictobj['additional'] = adres
				reslst.append(dictobj)
			return {'total': resdocs.totalHits, 'data': reslst}

		global _vm

		_vm.attachCurrentThread()
		user_data = web.input()
		print user_data
		user_data = json.loads(user_data['data'])
		print user_data
		searcher = zh_iatd.create_searcher()
		print 'querys' in user_data
		if 'querys' in user_data:
			reslst = []
			for x in user_data['querys']:
				reslst.append(get_query_result(searcher, x))
			print len(reslst)
			print json.dumps({'results': reslst})
			return json.dumps({'results': reslst})
		else:
			print get_query_result(searcher, user_data)
			return json.dumps(get_query_result(searcher, user_data))

class SS_idb:
	def POST(self):
		global _vm

		_vm.attachCurrentThread()
		user_data = web.input()
		reslst = []
		for x in json.loads(user_data['data'])['data']:
			ctk = crawler_task(vars(zh_iatd)['get_and_parse_' + x['func']], x['id'])
			ctk.func(_session, ctk)
			reslst.append(zh_pganlz.obj_to_json(ctk.result_rep_obj))
		return json.dumps({'results': reslst})

class SS_img:
	def GET(self):
		global _vm, _session

		_vm.attachCurrentThread()
		user_data = web.input()
		return _session.opener.open(user_data['url']).read()

class SS_stat:
	def POST(self):
		global _vm, _session

		_vm.attachCurrentThread()
		user_data = json.loads(web.input()['data'])
		print user_data
		tgtype = user_data['type']
		if tgtype == 'user':
			tfield = 'author_index'
		elif tgtype == 'question':
			tfield = 'question_index'
		else:
			return ''
		with zh_iatd.create_searcher() as searcher:
			res1 = searcher.searcher.search(
				zh_iatd.create_query({'type': 'answer', tfield: user_data['index']}),
				200,
				Sort(SortField('likes', SortField.Type.INT, True))
			);
			res2 = searcher.searcher.search(
				zh_iatd.create_query({'type': 'answer', tfield: user_data['index']}),
				200,
				Sort(SortField('date', SortField.Type.INT, True))
			)
			res1 = [zh_pganlz.document_to_obj(searcher.searcher.doc(x.doc)).data.likes for x in res1.scoreDocs]
			res2 = [zh_pganlz.document_to_obj(searcher.searcher.doc(x.doc)) for x in res2.scoreDocs]
			res2 = [{'x': x.data.date, 'y': x.data.likes} for x in res2]
		return json.dumps({'histogram': res1, 'graph': res2})

class SS_imgrangesearch:
	def POST(self):
		user_data = web.input()
		print type(user_data)
		with open('res.jpg', 'wb') as fout:
			fout.write(user_data.keyword)
		result = img_search.use_seacher_range('res.jpg')
		return json.dumps(result)

class SS_imagequicksearch:
	def POST(self):
		user_data = web.input()
		print type(user_data)
		with open('res.jpg', 'wb') as fout:
			fout.write(user_data.keyword)
		result = img_search.use_seacher_quick('res.jpg')
		return json.dumps(result)

def generate_url_list():
	res = []
	for k in globals().keys():
		if k.startswith(_SERVER_PREFIX):
			res.append(k[len(_SERVER_PREFIX):].replace('_', '/').lower())
			res.append(k)
		elif k.startswith(_SERVER_ANY_PREFIX):
			res.append(k[len(_SERVER_ANY_PREFIX):].replace('_', '/').lower() + '(.*)')
			res.append(k)
	return res

def main():
	global _vm, _session

	_vm = lucene.initVM(vmargs = ['-Djava.awt.headless=true'])
	jieba.initialize()

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

	web.application(generate_url_list(), globals()).run()

if __name__ == '__main__':
	main()
