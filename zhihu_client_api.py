import urllib, urllib2, cookielib, time, os, subprocess, json, bs4
from zhihu_settings import *

REQUEST_HEADERS = {
	'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36',
	'Referer': 'https://www.zhihu.com',
	'X-Requested-With': 'XMLHttpRequest',
	'Host': 'www.zhihu.com'
}

class zhihu_session:
	class redirect_handler(urllib2.HTTPRedirectHandler):
		def http_error_301(self, req, fp, code, msg, headers):
			pass
		def http_error_302(self, req, fp, code, msg, headers):
			pass

	def __init__(self):
		self.cookies = cookielib.CookieJar()
		self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cookies), zhihu_session.redirect_handler)

	# ~100 ways to login
	def _login(self, url, field, fieldval, password, tmpfile):
		with open(tmpfile, 'wb') as captchawriter:
			openedurl = self.opener.open(urllib2.Request(
				url = 'https://www.zhihu.com/captcha.gif?r={0}&type=login'.format(int(time.time() * 1000)),
				headers = REQUEST_HEADERS
			))
			captchawriter.write(openedurl.read())
		try:
			proc = subprocess.Popen(('eog', tmpfile), stdout = open('/dev/null', 'w'), stderr = open('/dev/null', 'w'))
			captcha = raw_input('Captcha: ')
			proc.kill()
		except:
			print 'Captcha has been saved to file', tmpfile
			captcha = raw_input('Captcha: ')
		login_result = json.loads(self.opener.open(urllib2.Request(
			url = url,
			headers = REQUEST_HEADERS,
			data = urllib.urlencode({
				'captcha': captcha,
				'password': password,
				field: fieldval
			})
		)).read())
		if login_result['r'] != 0:
			raise Exception(login_result['msg'].encode('utf8'))
		self._xsrf = bs4.BeautifulSoup(self.opener.open(urllib2.Request(
			url = 'https://www.zhihu.com',
			headers = REQUEST_HEADERS
		)).read(), HTML_PARSER).select("input[name='_xsrf']")[0]['value']
		self._header_with_xsrf = dict(REQUEST_HEADERS)
		self._header_with_xsrf['X-Xsrftoken'] = self._xsrf

	def login_phonenum(self, phonenum, password, tmpfile = 'tmp.gif'):
		self._login('https://www.zhihu.com/login/phone_num', 'phone_num', phonenum, password, tmpfile)
	def login_email(self, email, password, tmpfile = 'tmp.gif'):
		self._login('https://www.zhihu.com/login/email', 'email', email, password, tmpfile)


	def get_question_answer_list_raw(self, questionid, start, pagesize):
		return json.loads(self.opener.open(urllib2.Request(
			url = 'https://www.zhihu.com/node/QuestionAnswerListV2',
			headers = self._header_with_xsrf,
			data = urllib.urlencode({
				'method': 'next',
				'params': json.dumps({
					'url_token': questionid,
					'pagesize': pagesize,
					'offset': start
				})
			})
		)).read())


	def _get_userdata_api(self, section, user, start, pagesize):
		return json.loads(self.opener.open(urllib2.Request(
			url = 'https://www.zhihu.com/api/v4/members/{0}/{1}?limit={2}&offset={3}'.format(user, section, pagesize, start)
		)).read())

	def get_followees_raw(self, user, start, pagesize):
		return self._get_userdata_api('followees', user, start, pagesize)
	def get_followers_raw(self, user, start, pagesize):
		return self._get_userdata_api('followers', user, start, pagesize)
	def get_asked_questions_raw(self, user, start, pagesize):
		return self._get_userdata_api('questions', user, start, pagesize)
	def get_answered_questions_raw(self, user, start, pagesize):
		return self._get_userdata_api('answers', user, start, pagesize)
	def get_favourite_list_raw(self, user, start, pagesize):
		return self._get_userdata_api('favlists', user, start, pagesize)
	def get_articles_raw(self, user, start, pagesize):
		return self._get_userdata_api('articles', user, start, pagesize)
	def get_watched_topics_raw(self, user, start, pagesize):
		return self._get_userdata_api('following-topic-contributions', user, start, pagesize)

	def get_article_content_raw(self, article):
		return json.loads(self.opener.open(urllib2.Request(
			url = 'https://zhuanlan.zhihu.com/api/posts/{0}'.format(article)
		)).read())

	def get_question_watchers_raw(self, questionid, start):
		return json.loads(self.opener.open(urllib2.Request(
			url = 'https://www.zhihu.com/question/{0}/followers'.format(questionid),
			headers = self._header_with_xsrf,
			data = urllib.urlencode({
				'start': 0,
				'offset': start
			})
		)).read())


	def get_question_comments_raw(self, questionid):
		return self.opener.open(urllib2.Request(
			url = 'https://www.zhihu.com/node/QuestionCommentListV2?params={{"question_id":{0}}}'.format(questionid)
		)).read()

	def get_answer_comments_raw(self, answerid, page): # page starts from 1
		return json.loads(self.opener.open(urllib2.Request(
			url = 'https://www.zhihu.com/r/answers/{0}/comments?page={1}'.format(answerid, page)
		)).read())

	def get_article_comments_raw(self, articleid, start, pagesize):
		return json.loads(self.opener.open(urllib2.Request(
			url = 'https://zhuanlan.zhihu.com/api/posts/{0}/comments?limit={1}&offset={2}'.format(articleid, pagesize, start)
		)).read())


	def get_children_topics(self, topicid, idafter = ''):
		return json.loads(self.opener.open(urllib2.Request(
			url = 'https://www.zhihu.com/topic/{0}/organize/entire?child={1}&parent={0}'.format(topicid, idafter),
			headers = REQUEST_HEADERS,
			data = urllib.urlencode({
				'_xsrf': self._xsrf
			})
		)).read())

def main():
	if os.path.exists('login_info'):
		with open('login_info', 'r') as fin:
			email = fin.readline().strip()
			password = fin.readline().strip()
		print 'Email:', email
		print 'Password: ', '*' * len(password)
	else:
		email = raw_input('Email: ')
		password = raw_input('Password: ')

	session = zhihu_session()
	session.login_email(email, password)
	with open('children_topics.txt', 'w') as fout:
		json.dump(session.get_children_topics(19632577), fout)
	# with open('test.txt', 'w') as fout:
	# 	fout.write(str(session.get_question_answer_list_raw(53568452, 1000, 10)))
	# with open('followees.txt', 'w') as fout:
	# 	json.dump(session.get_followees_raw('excited-vczh', 2, 10), fout)
	# with open('followers.txt', 'w') as fout:
	# 	json.dump(session.get_followers_raw('excited-vczh', 2, 10), fout)
	# with open('ask.txt', 'w') as fout:
	# 	json.dump(session.get_asked_questions_raw('excited-vczh', 2, 10), fout)
	# with open('answer.txt', 'w') as fout:
	# 	json.dump(session.get_answered_questions_raw('excited-vczh', 2, 10), fout)
	# with open('articles.txt', 'w') as fout:
	# 	json.dump(session.get_articles_raw('excited-vczh', 2, 10), fout)
	# print session.get_followers_raw('niu-yue-lao-li-xiao-chang', 0, 10)
	# with open('question_comments.txt', 'w') as fout:
	# 	fout.write(session.get_question_comments_raw(4087751))
	# with open('answer_comments.txt', 'w') as fout:
	# 	json.dump(session.get_answer_comments_raw(49741710, 1), fout)
	# with open('articles.txt', 'w') as fout:
	# 	json.dump(session.get_articles_raw('excited-vczh', 0, 10), fout)
	# with open('article_content.txt', 'w') as fout:
	# 	json.dump(session.get_article_content_raw(24543157), fout)
	# with open('question_watchers.txt', 'w') as fout:
	# 	fout.write(session.get_question_watchers_raw(49741710, 1)['msg'][1].encode('utf8'))
	# print session.get_question_watchers_raw(49741710, 1)

if __name__ == '__main__':
	main()
