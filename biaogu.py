import numpy as np
import datetime
from dateutil.relativedelta import relativedelta
import stockInfo

def calculateBBands(date=datetime.datetime.now(), defaultTracebackDates=90):
	stockList = {}
	latestDate = stockInfo.generateStockPricesDictionaryByDate(date)['2330'].date

	day = 1
	date = datetime.datetime.now()
	while day <= defaultTracebackDates:
		stockPrices = stockInfo.generateStockPricesDictionaryByDate(date, autoCorrectDate=False)
		if(stockPrices != None):
			for stockItem in stockPrices:
				if(stockItem in stockList):
					stockList[stockItem] = np.append(stockList[stockItem], stockPrices[stockItem].price)
				else:
					stockList[stockItem] = np.array(stockPrices[stockItem].price)
			day = day + 1
		date = date - relativedelta(days=1)

	print("Latest date %d/%02d/%02d" % (latestDate.year, latestDate.month, latestDate.day))



