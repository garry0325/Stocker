import sys
import numpy as np
import matplotlib.pyplot as plt
import datetime
from dateutil.relativedelta import relativedelta
import stockInfo

# information from https://www.facebook.com/XQ.com.tw/posts/10153060513946343/

class countTable():
	def __init__(self, uplimitCount=0, downlimitCount=0, lastUplimitDate=None, lastDownlimitDate=None):
		self.uplimitCount = uplimitCount
		self.downlimitCount = downlimitCount
		self.lastUplimitDate = lastUplimitDate
		self.lastDownlimitDate = lastDownlimitDate


def evaluate(endDate, tracebackDates=180):

	table = {}
	date = endDate
	
	d = stockInfo.generateStockPricesDictionaryByDate(date, False)
	for item in d:
		table[item] = countTable()

	dateCount = 0
	while dateCount < tracebackDates:
		d = stockInfo.generateStockPricesDictionaryByDate(date, False)
		
		if(d == None):
			date = date - relativedelta(days=1)
			continue
		
		for item in d:
			high = d[item].high
			low = d[item].low
			try:
				yesterday = d[item].price - d[item].offset

				if(high >= yesterday * 1.094):
					table[item].uplimitCount = table[item].uplimitCount + 1
					if(table[item].lastUplimitDate == None):
						table[item].lastUplimitDate = date
				if(low <= yesterday * 0.906):
					table[item].downlimitCount = table[item].downlimitCount + 1
					if(table[item].lastDownlimitDate == None):
						table[item].lastDownlimitDate = date
			except Exception as e:
				continue

		dateCount = dateCount + 1
		date = date - relativedelta(days=1)


	stockDict = []
	date = endDate
	dateCount = 0
	while dateCount < 20:
		d = stockInfo.generateStockPricesDictionaryByDate(date, False)

		if(d == None):
			date = date - relativedelta(days=1)
			continue
		
		stockDict.append(d)

		dateCount = dateCount + 1
		date = date - relativedelta(days=1)

	nextDate = endDate
	today = None
	while today == None:
		nextDate = nextDate + relativedelta(days=1)
		today = stockInfo.generateStockPricesDictionaryByDate(nextDate, False)

	print("%d/%02d/%02d" % (today['2330'].date.year, today['2330'].date.month, today['2330'].date.day))
	print("chg\tmax\tmin\tprice")
	for item in table:
		if(table[item].lastUplimitDate == None):
			continue
		lastUplimitDays = (endDate - table[item].lastUplimitDate).days
		if(((table[item].uplimitCount - table[item].downlimitCount) >= (tracebackDates / 20)) and
		   (lastUplimitDays <= 20) and
		   lastUplimitDays < table[item].uplimitCount):
			
			try:
				volume = 0
				for i in range(20):
					volume = volume + stockDict[i][item].volume
				volume = volume / 20
			except:
				continue
			
			if(volume > 200):
				open = today[item].open
				chg = (today[item].price - open) * 100 / open
				max = (today[item].high - open) * 100 / open
				min = (today[item].low - open) * 100 / open
				
				print("%4.1f%%\t%4.1f%%\t%4.1f%%\t%4.2f\t%s\t%d\t%d\t%d\t%3.2f" % (chg, max, min, today[item].price, item, table[item].uplimitCount, table[item].downlimitCount, (endDate - table[item].lastUplimitDate).days, (lastUplimitDays - table[item].downlimitCount) / (table[item].uplimitCount - table[item].downlimitCount)))


evaluate(datetime.datetime(2019, 12, 17), 180)
