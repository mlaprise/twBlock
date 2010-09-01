import twython.core as twython
import time
import PyRSS2Gen
import datetime
import re
from operator import itemgetter
import simplegeo

'''

Twitter Filtering Building Block - fltr.in
Author:	Martin Laprise (martin.laprise.1@ulaval.ca)
fltr.in Backend

'''


def lstIntersect(a, b):
	'''
	Return the intersection of two lists
	'''
	return list(set(a) & set(b))


def lstUnion(a, b):
	''''
	Return the union of two lists
	'''
	return list(set(a) | set(b))


def lstDiff(a, b):
	'''
	Return whats in list b which isn't in list a
	'''
	return list(set(b).difference(set(a)))


def tlDiff(tlA, tlB):
	'''
	Return  whats in timeline b which isn't in timeline a
	'''
	tlAId = map(lambda tweet: tweet['id'], tlA)
	tlBId = map(lambda tweet: tweet['id'], tlB)
	tlDiffId = lstDiff(tlAId, tlBId)
	tlDiff = filter(lambda tweet: tlDiffId.count(tweet['id']) == 1, tlB)
	return tlDiff


def extractTime(tl):
	'''
	Extract the creation time and return a dict list ['id',[]]
	'''


class twBlock:
	'''
	twBlock Base class
	'''
	def __add__(self,Other):
		Other.setInput(self.output)
		return Other


	def terminal(self, refreshDelay = 60):
		'''
		Display the timeline feed on the terminal
		'''
		tlOld = []
		while 1:
			tlNow = self.output()
			tlNew = tlDiff(tlOld, tlNow)

			for tweet in tlNew:
				print '\x1b[32m'+tweet['user']['name']+str(': ')+'\x1b[0m'+tweet["text"]

			tlOld = tlNow
			time.sleep(refreshDelay)


	def pretty(self):
		'''
		Pretty print the tweet timeline
		'''
		tlNew = self.output()
		for tweet in tlNew:
			create_at_time = re.findall(r'([0-9]\d:[0-9]\d:[0-9]\d)', tweet['created_at'])[0]
			print '\x1b[31m'+create_at_time+' - '+'\x1b[32m'+tweet['user']['screen_name']+str(': ')+'\x1b[0m'+tweet["text"]


	def textOccur(self, word):
		count = 0
		tl = self.output()
		for tweet in tl:
			count += tweet['text'].count(word)
		return count


	def ajaxClient(self, refreshDelay = 60):
		'''
		Display the timeline feed on a AJAX client
		'''
		return 0


	def rssClient(self, refreshDelay = 3600):
		'''
		Create a RSS Feed with the timeline
		'''
		tlOld = []
		tlRSSItems = []
	
		while 1:
			tlNow = self.output()
			tlNew = tlDiff(tlOld, tlNow)

			for tweet in tlNew:
				tlRSSItems.append(PyRSS2Gen.RSSItem(
					title = tweet['user']['name'],
					link = "",
					description = tweet["text"],
					pubDate = datetime.datetime.now()))

			rss = PyRSS2Gen.RSS2(
				title = "mlaprise's fltr.in feed",
				link = "www.fltr.in/mlaprise",
				description = "My twitter stream filtered by fltr.in",
				lastBuildDate = datetime.datetime.now(), items = tlRSSItems)

			rss.write_xml(open("rss.xml", "w"))

			tlOld = tlNow
			time.sleep(refreshDelay)


	def rtClient(self, user, pw, refreshDelay = 600):
		'''
		reTweet client
		'''
		twitter = twython.setup(username=user, password=pw)
		tlNew = self.output()
		for tweet in tlNew:
			twitter.reTweet(tweet["id"])


	def favClient(self, twConnect):
		tlNew = self.output()
		if len(tlNew) >= 1:
			for tweet in tlNew:
				try:
					twConnect.createFavorite(tweet["id"])
					print "Favoris Ajoute"
				except TwythonError:
					print "Deja la !"
		return len(tlNew)


class twSource(twBlock):
	'''
	Return the home timeline
	'''
	def __init__(self, user, pw, count = 20, nbrPage = 1, tlInput = []):
		self.twitter = twython.setup(username=user, password=pw)
		self.nbrInput = 0	
		self.nbrOutput = 1
		self.count = count
		self.nbrPage = nbrPage
		self.timeLine = tlInput

	def setInput(self,tlInput):
		self.timeLine = tlInput

	def __add__(self,Other):
		'''
		Overload the add operator. Mux two twSource if we have two twSource
		instance
		'''
		if isinstance(Other,twSource):
			return twMux([self,Other])
		else:
			Other.setInput(self.output)
			return Other
	
	def output(self):
		outputTl = self.timeLine
		for i in range(self.nbrPage):
			tl = self.twitter.getHomeTimeline(count=self.count, page=i)
			outputTl += tl

		return outputTl


class twSearch(twBlock):
	'''
	Return the home timeline
	'''
	def __init__(self, user, pw, searchQuery, count = 20, nbrPage = 1, tlInput = []):
		self.twitter = twython.setup(username=user, password=pw)
		self.nbrInput = 0	
		self.nbrOutput = 1
		self.count = count
		self.nbrPage = nbrPage
		self.timeLine = tlInput
		self.query = searchQuery

	def setInput(self,tlInput):
		self.timeLine = tlInput

	def __add__(self,Other):
		'''
		Overload the add operator. Mux two twSource if we have two twSource
		instance
		'''
		if isinstance(Other,twSource):
			return twMux([self,Other])
		else:
			Other.setInput(self.output)
			return Other
	
	def output(self):
		outputTl = self.timeLine
		for i in range(self.nbrPage):
			tl = self.twitter.searchTwitter(self.query, count=self.count, page=i)
			outputTl += tl

		return outputTl
		

class twDummy(twBlock):
	'''
	Dummy block
	'''
	def __init__(self, tlInput = []):
		self.nbrInput = 1
		self.nbrOutput = 1
		self.timeLine = tlInput
	
	def setInput(self,tlInput):
		self.timeLine = tlInput

	def pretty(self):
		'''
		Pretty print the tweet timeline
		'''
		tlNew = self.timeLine
		for tweet in tlNew:
			create_at_time = re.findall(r'([0-9]\d:[0-9]\d:[0-9]\d)', tweet['created_at'])[0]
			print '\x1b[31m'+create_at_time+' - '+'\x1b[32m'+tweet['user']['screen_name']+str(': ')+'\x1b[0m'+tweet["text"]

	def output(self):
		return self.timeLine


class twMux(twBlock):
	'''
	Mux n timelines
	'''
	def __init__(self, lstTwSource=[]):
		self.nbrInput = 2	
		self.nbrOutput = 1
		self.nbrTimeline = len(lstTwSource)
		self.inputSources = lstTwSource
		self.timeLine = []

	def setInput(self, lstTwSource):
		self.nbrTimeline = len(lstTwSource)
		self.inputSources = lstTwSource
	
	def output(self):
		self.timeLine = []
		self.timeLine += self.inputSources[0].output()
		
		# Remove the duplicates and conc the new stuff
		for i in range(self.nbrTimeline-1):
			self.timeLine += tlDiff(self.inputSources[i].output(), self.inputSources[i+1].output())

		# ReOrdering the final timeline with the 'id' tag
		self.timeLine.sort(key=itemgetter('id'),reverse=True)
		
		return self.timeLine


class twHasWords(twBlock):
	'''
	Return the tweets containing a specified list of word
	'''
	def __init__(self, lstWord = [], operator = 'OR', tlInput = []):
		self.operator = operator
		self.lstWord = lstWord
		self.nbrInput = 1
		self.nbrOutput = 1
		self.timeLine = []
	
	def setInput(self,tlInput):
		self.timeLine = tlInput

	def _HasWordsCheckOr(self, tweet):
		count = 0
		for word in self.lstWord:
			count += tweet['text'].count(word)
		return count

	def _HasWordsCheckAnd(self, tweet):
		count = 0
		for word in self.lstWord:
			if tweet['text'].count(word) >= 1:
				count += 1
		if count == len(self.lstWord):
			return 1
		else:
			return 0

	def textOccur(self):
		count = 0
		for word in self.lstWord:
			for tweet in self.timeLine:
				count += tweet['text'].count(word)

		return count

	def output(self):
		if self.operator == 'OR':
			tlFiltered = filter(self._HasWordsCheckOr, self.timeLine())
		else:
			tlFiltered = filter(self._HasWordsCheckAnd, self.timeLine())

		return tlFiltered


class twHasHash(twBlock):
	'''
	Return the tweets containing a specified hash code
	'''
	def __init__(self, hashCode='#', tlInput = []):
		self.hashCode = hashCode
		self.nbrInput = 1
		self.nbrOutput = 1
		self.timeLine = []
	
	def setInput(self,tlInput):
		self.timeLine = tlInput

	def output(self):
		tlFiltered = filter(lambda tweet: tweet['text'].count(self.hashCode) >= 1, self.timeLine())
		return tlFiltered


class twHasStock(twBlock):
	'''
	Return the tweets containing a Stock symbols
	'''
	def __init__(self, hashCode='$', tlInput = []):
		self.hashCode = hashCode
		self.nbrInput = 1
		self.nbrOutput = 1
		self.timeLine = []
	
	def setInput(self,tlInput):
		self.timeLine = tlInput

	def output(self):
		tlFiltered = filter(lambda tweet: tweet['text'].count(self.hashCode) >= 1, self.timeLine())
		return tlFiltered


class twHasNoHash(twBlock):
	'''
	Return the tweets containing a specified hash code
	'''
	def __init__(self, hashCode='#', tlInput = []):
		self.hashCode = hashCode
		self.nbrInput = 1
		self.nbrOutput = 1
		self.timeLine = []
	
	def setInput(self,tlInput):
		self.timeLine = tlInput

	def output(self):
		tlFiltered = filter(lambda tweet: tweet['text'].count(self.hashCode) == 0, self.timeLine())
		return tlFiltered


class twHasMention(twBlock):
	'''
	Return the tweets containing a specified hash code
	'''
	def __init__(self, mention='@', tlInput = []):
		self.mention = mention
		self.nbrInput = 1
		self.nbrOutput = 1
		self.timeLine = []
	
	def setInput(self,tlInput):
		self.timeLine = tlInput

	def output(self):
		tlFiltered = filter(lambda tweet: tweet['text'].count(self.mention) >= 1, self.timeLine())
		return tlFiltered


class twHasNoMention(twBlock):
	'''
	Return the tweets containing a specified hash code
	'''
	def __init__(self, mention='@', tlInput = []):
		self.mention = mention
		self.nbrInput = 1
		self.nbrOutput = 1
		self.timeLine = []
	
	def setInput(self,tlInput):
		self.timeLine = tlInput

	def output(self):
		tlFiltered = filter(lambda tweet: tweet['text'].count(self.mention) == 0, self.timeLine())
		return tlFiltered


class twHasLink(twBlock):
	'''
	Return the tweets containing a link
	'''
	def __init__(self, link='http://', tlInput = []):
		self.link = link
		self.nbrInput = 1
		self.nbrOutput = 1
		self.timeLine = []
	
	def setInput(self,tlInput):
		self.timeLine = tlInput

	def output(self):
		tlFiltered = filter(lambda tweet: tweet['text'].count(self.link) >= 1, self.timeLine())
		return tlFiltered


class twSimpleGeo(twBlock):
	'''
	Return the tweets containing a GeoTag and send it to SimpleGeo
	'''
	def __init__(self, tlInput = []):

		self.nbrInput = 1
		self.nbrOutput = 1
		self.timeLine = []
	
	def setInput(self,tlInput):
		self.timeLine = tlInput

	def output(self):
		smpGeoClient = simplegeo.Client('c3ZCgWtrbPTBV4WeDe2pYq4gHyp7zzZq','CsDuTvA6VXDw7FWZjLy2SsqdY4f9hWwD')
		layerName = 'premiertest1'
		smpGeoRecs = []
		tlFiltered = filter(lambda tweet: tweet['geo'] != None, self.timeLine())
		for tweet in tlFiltered:
			geoCoords = tweet['geo']['coordinates']
			smpGeoRecs.append(simplegeo.Record(layerName, tweet['user']['screen_name'], geoCoords[0], geoCoords[1]))
		
		smpGeoClient.add_records(layerName, smpGeoRecs)
		return tlFiltered


class twHasNoLink(twBlock):
	'''
	Return the tweets containing a link
	'''
	def __init__(self, link='http://', tlInput = []):
		self.link = link
		self.nbrInput = 1
		self.nbrOutput = 1
		self.timeLine = []
	
	def setInput(self,tlInput):
		self.timeLine = tlInput

	def output(self):
		tlFiltered = filter(lambda tweet: tweet['text'].count(self.link) == 0, self.timeLine())
		return tlFiltered


class twHasOldRT(twBlock):
	'''
	Return the tweets containing a old fashion ReTweet
	'''
	def __init__(self, reTweet='RT', tlInput = []):
		self.reTweet = reTweet
		self.nbrInput = 1
		self.nbrOutput = 1
		self.timeLine = []
	
	def setInput(self,tlInput):
		self.timeLine = tlInput

	def output(self):
		tlFiltered = filter(lambda tweet: tweet['text'].count(self.reTweet) >= 1, self.timeLine())
		return tlFiltered


class twHasNoOldRT(twBlock):
	'''
	Return the tweets containing a old fashion ReTweet
	'''
	def __init__(self, reTweet='RT', tlInput = []):
		self.reTweet = reTweet
		self.nbrInput = 1
		self.nbrOutput = 1
		self.timeLine = []
	
	def setInput(self,tlInput):
		self.timeLine = tlInput

	def output(self):
		tlFiltered = filter(lambda tweet: tweet['text'].count(self.reTweet) == 0, self.timeLine())
		return tlFiltered


class twFromUser(twBlock):
	'''
	Return the tweets from a specified user
	'''
	def __init__(self, twUser='', tlInput = []):
		self.twUser = twUser
		self.nbrInput = 1
		self.nbrOutput = 1
		self.timeLine = []
	
	def setInput(self,tlInput):
		self.timeLine = tlInput

	def output(self):
		tlFiltered = filter(lambda tweet: tweet['user']['screen_name'] == self.twUser, self.timeLine())
		return tlFiltered


class twNotFromUser(twBlock):
	'''
	Return the tweets except one from a specific user
	'''
	def __init__(self, twUser='', tlInput = []):
		self.twUser = twUser
		self.nbrInput = 1
		self.nbrOutput = 1
		self.timeLine = []
	
	def setInput(self,tlInput):
		self.timeLine = tlInput

	def output(self):
		tlFiltered = filter(lambda tweet: tweet['user']['screen_name'] != self.twUser, self.timeLine())
		return tlFiltered


class twHasGeoTag(twBlock):
	'''
	Return the tweets containing a Geo tag
	'''
	def __init__(self, tlInput = []):
		self.nbrInput = 1
		self.nbrOutput = 1
		self.timeLine = []
	
	def setInput(self,tlInput):
		self.timeLine = tlInput

	def output(self):
		tlFiltered = filter(lambda tweet: tweet['geo'] != None, self.timeLine())
		return tlFiltered


class twAddGeoTag(twBlock):
	'''
	Add a GeoTag to a tweet
	'''
	def __init__(self, tlInput = []):
		self.nbrInput = 1
		self.nbrOutput = 1
		self.timeLine = []
	
	def setInput(self,tlInput):
		self.timeLine = tlInput

	def output(self):
		return tlFiltered


class twExpandURL(twBlock):
	'''
	Return the tweets with the URL expanded
	 -- Broke the compatibility with twitter --
	'''
	def __init__(self, tlInput = []):
		self.nbrInput = 1
		self.nbrOutput = 1
		self.timeLine = []
	
	def setInput(self,tlInput):
		self.timeLine = tlInput

	def output(self):
		HasBitlyLink = filter(lambda tweet: tweet['text'].count('http://bit.ly/') >= 1, self.timeLine())
		return HasBitlyLink
