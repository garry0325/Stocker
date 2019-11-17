import numpy as np
import matplotlib.pyplot as plt
import datetime
from dateutil.relativedelta import relativedelta
import stockInfo

class bband():
	def __init__(self, price, MA, upper, lower):
		self.price = price
		self.MA = MA
		self.upper = upper
		self.lower = lower

def calculateBBands(date=datetime.datetime.now(),
					trackbackDates=90,
					N=20,	# days to make MA
					K=2):	# amplitude of band in stdev
	stockList = {}
	latestDate = stockInfo.generateStockPricesDictionaryByDate(date)['2330'].date
	datesNeeded = trackbackDates + N - 1
	day = 1
	
	date = datetime.datetime.now()
	while day <= datesNeeded:
		stockPrices = stockInfo.generateStockPricesDictionaryByDate(date, autoCorrectDate=False)
		if(stockPrices != None):
			for stockItem in stockPrices:
				if(stockItem in stockList):
					stockList[stockItem] = np.append(stockList[stockItem], stockPrices[stockItem].price)
				else:
					stockList[stockItem] = np.array(stockPrices[stockItem].price)
			day = day + 1
		date = date - relativedelta(days=1)


	bbandList = {}
	stockListCopy = stockList.copy()
	for stockItem in stockListCopy:
		if(len(stockList[stockItem]) != datesNeeded):
			del stockList[stockItem]
			continue


		bbandList[stockItem] = []

		for i in range(0, trackbackDates):
			n = stockList[stockItem][i:i+N]
			mean = n.mean()
			s = n.std()
			
			bbandList[stockItem].append(bband(stockList[stockItem][i], mean, mean + K * s, mean - K * s))

	print("Latest date %d/%02d/%02d" % (latestDate.year, latestDate.month, latestDate.day))

	return bbandList

def plotBand(bbandList, stockId):
	ma = []
	upper = []
	lower = []
	price = []

	for i in bbandList[stockId]:
		price.insert(0, i.price)
		ma.insert(0, i.MA)
		upper.insert(0, i.upper)
		lower.insert(0, i.lower)

	l = range(0, len(ma))
	plt.plot(l, price, c='red', linewidth=2.0)
	plt.plot(l, ma, linewidth=1.5, alpha=0.5)
	plt.plot(l, upper, linewidth=1.5, alpha=0.5)
	plt.plot(l, lower, linewidth=1.5, alpha=0.5)

	plt.xlabel(stockId)
	plt.ylabel('Price')

	plt.show()

def filterPriceHigherThanUpper(bbandList):
	bbandListCopy = bbandList.copy()
	for stockItem in bbandListCopy:
		if(bbandList[stockItem][0].price <= bbandList[stockItem][0].upper):
			del bbandList[stockItem]

	print("%d stocks found after filtering out price lower than upper" % (len(bbandList)))

	return bbandList

def filterHighestPriceForDays(bbandList, days=20):
	bbandListCopy = bbandList.copy()
	for stockItem in bbandListCopy:
		highest = True
		for i in range(1, days):
			if(bbandList[stockItem][i].price >= bbandList[stockItem][0].price):
				highest = False
				break

		if(not highest):
			del bbandList[stockItem]

	print("%d stocks found after highest price filter" % (len(bbandList)))

date = datetime.datetime(2019, 11, 16)
bband = calculateBBands(date, trackbackDates=90)
bband = filterPriceHigherThanUpper(bband)
bband = filterHighestPriceForDays(bband)
