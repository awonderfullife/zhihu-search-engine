import urllib, urllib2, cookielib, time, os, subprocess, json, bs4

REQUEST_HEADERS = {
	'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36',
	'Referer': 'https://www.zhihu.com',
	'X-Requested-With': 'XMLHttpRequest',
	'Host': 'www.zhihu.com'
}

class zhihu_session:
	def __init__(self):
		self.cookies = cookielib.CookieJar()
		self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cookies))

	def _login(self, url, field, fieldval, password, tmpfile):
		with open(tmpfile, 'wb') as captchawriter:
			openedurl = self.opener.open(urllib2.Request(
				url = 'https://www.zhihu.com/captcha.gif?r={0}&type=login'.format(int(time.time() * 1000)),
				headers = REQUEST_HEADERS
			))
			captchawriter.write(openedurl.read())
		subprocess.Popen(('eog', tmpfile))
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
		)).read(), 'html.parser').select("input[name='_xsrf']")[0]['value']
		self._header_with_xsrf = dict(REQUEST_HEADERS)
		self._header_with_xsrf['X-Xsrftoken'] = self._xsrf

	def login_phonenum(self, phonenum, password, tmpfile = 'tmp.gif'):
		self._login('https://www.zhihu.com/login/phone_num', 'phone_num', phonenum, password, tmpfile)

	def login_email(self, email, password, tmpfile = 'tmp.gif'):
		self._login('https://www.zhihu.com/login/email', 'email', email, password, tmpfile)

	def get_question_answer_list_raw(self, questionid, pagesize, offset):
		return json.loads(self.opener.open(urllib2.Request(
			url = 'https://www.zhihu.com/node/QuestionAnswerListV2',
			headers = self._header_with_xsrf,
			data = urllib.urlencode({
				'method': 'next',
				'params': json.dumps({
					'url_token': questionid,
					'pagesize': pagesize,
					'offset': offset
				})
			})
		)).read())

	def _parse_people_list(lst):
		result = []
		for x in lst:
			result.append(lst['url_token'])
		return result

	def get_followees_raw(self, user, pagesize, offset):
		return json.loads(self.opener.open(urllib2.Request(
			url = 'https://www.zhihu.com/api/v4/members/{0}/followees?limit={1}&offset={2}'.format(user, pagesize, offset)
		)).read())

	def get_followers_raw(self, user, pagesize, offset):
		return json.loads(self.opener.open(urllib2.Request(
			url = 'https://www.zhihu.com/api/v4/members/{0}/followers?limit={1}&offset={2}'.format(user, pagesize, offset)
		)).read())

	def get_question_comments_raw(self, questionid):
		return self.opener.open(urllib2.Request(
			url = 'https://www.zhihu.com/node/QuestionCommentBoxV2?params={{"question_id":{0}}}'.format(questionid)
		)).read()

	def get_answer_comments_raw(self, answerid, page): # page starts from 1
		return json.loads(self.opener.open(urllib2.Request(
			url = 'https://www.zhihu.com/r/answers/{0}/comments?page={1}'.format(answerid, page)
		)).read())

def main():
	if os.path.exists('login_info'):
		with open('login_info', 'r') as fin:
			phonenum = fin.readline()
			password = fin.readline()
		print 'Phone Number:', phonenum
		print 'Password: ', '*' * len(password)
	else:
		phonenum = raw_input('Phone Number: ')
		password = raw_input('Password: ')

	session = zhihu_session()
	session.login_phonenum(phonenum, password)
	# with open('test.txt', 'w') as fout:
	# 	fout.write(session.get_question_answer_list_raw(53568452, 10, 0)['msg'][0].encode('utf8'))
	# print session.get_followers_raw('niu-yue-lao-li-xiao-chang', 10, 0)
	# print session.get_question_comments_raw(13647249)
	print session.get_answer_comments_raw(49741710, 1)

if __name__ == '__main__':
	main()
