#-*- coding: euc-kr -*-
import requests, grequests, re, gensim
from lxml import html
from urlparse import urlparse
from urllib import unquote, quote
from libextract.api import extract
from konlpy.tag import Twitter; t = Twitter()
from collections import defaultdict

def noun_counter(posed_articles):
	ret = defaultdict(int)
	for posed_article in posed_articles:
		for posed_token in posed_article:
			if posed_token[1] == u'Noun' and len(posed_token[0]) >= 2:
				ret[posed_token[0]] += 1
	return sorted(ret.iteritems(), key=lambda (k, v): -1 * v)[:10]

def get_top10():
	c = requests.get('http://www.naver.com/').content
	b = html.fromstring(c)
	ts = [unquote(urlparse(x).query.split('=')[2][:-3]) for x in b.xpath('//ol[@id="realrank"]/li/a/@href')]
	return ts[:-1]

def get_news_urls(query):
	newsurls = ['http://news.naver.com/main/search/search.nhn?query=' + quote(query.decode('utf-8').encode('euc-kr')) + '&ie=MS949&x=0&y=0&page=' + str(i) for i in xrange(2)]
	rs = grequests.map((grequests.get(u) for u in newsurls))
	rc = [r.content.decode(r.encoding) for r in rs]
	bodys = [html.fromstring(c) for c in rc]
	urls_list = [b.xpath('//ul[@class="srch_lst"]/li/div[@class="ct"]/div[@class="info"]/a/@href') for b in bodys]
	urls = [url for urls in urls_list for url in urls]
	return urls[:100]

def get_articles(urls):
	rs = grequests.map((grequests.get(u) for u in urls))
	rc = [r.content.decode(r.encoding) for r in rs]
	bodys = [html.fromstring(c) for c in rc]
	articles_entertain = [b.xpath('//div[@id="articeBody"]//text()') for b in bodys]
	articles_entertain = [[re.sub('\s+', ' ', aa.strip()) for aa in a] for a in articles_entertain]
	articles_sports = [b.xpath('//div[@id="naver_news_20080201_div"]//text()') for b in bodys]
	articles_sports = [[re.sub('\s+', ' ', aa.strip()) for aa in a] for a in articles_sports]
	articles_news = [b.xpath('//div[@id="articleBodyContents"]//text()') for b in bodys]
	articles_news = [[re.sub('\s+', ' ', aa.strip()) for aa in a] for a in articles_news]
	articles = [' '.join(articles_news[i] + articles_sports[i] + articles_entertain[i]) for i in xrange(len(articles_news))]
	return articles

def get_posed_articles(articles):
	return [t.pos(article) for article in articles]


top10 = get_top10()

with open('hehe.txt', 'w') as fp:
	for top in top10:
		url = get_news_urls(top)
		articles = get_articles(url)
		posed_articles = get_posed_articles(articles)

		texts = [[pos[0] for pos in posed_article if pos[1]==u'Noun' and len(pos[0])>=2] for posed_article in posed_articles]
		dictionary = gensim.corpora.Dictionary(texts)
		corpus = [dictionary.doc2bow(text) for text in texts]
		lsi = gensim.models.lsimodel.LsiModel(corpus=corpus, id2word=dictionary, num_topics=400)
		a = lsi.print_topics(1)
		

		nc = noun_counter(posed_articles)
		fp.write(top + ' : ' + ', '.join([n.encode('utf-8') for n, c in nc]) + '\n')
		for i in a:
			fp.write(top + ' : ' + i.encode('utf-8') + '\n')