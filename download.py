import pandas as pd
import requests
from io import StringIO
import os
import time
import datetime
from dateutil.relativedelta import relativedelta
import pickle


def downloadMonthlyReport(year, month):

	rocyear = year
	if rocyear > 1990:
		rocyear = rocyear - 1911
	
	# switch tse/otc stocks
	tseotc = ['sii', 'otc']
	for cat in tseotc:
		url = 'https://mops.twse.com.tw/nas/t21/' + cat + '/t21sc03_' + str(rocyear) + '_' + str(month) + '.csv'

		headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}

		req = requests.get(url, headers=headers)
		req.encoding = 'utf-8'

		if(len(req.text) <= 500):
			print("error with " + str(year) + "-" + "%02d" % (month))
			return

		file = open("monthlyReport/" + cat + "report" + str(year) + "%02d" % (month) + ".csv", "w")
		file.write(req.text)
		file.close()

		print(cat + "report" + str(year) + "%02d" % (month) + ".csv written" + "(%d)" %(len(req.text)))

def downloadMonthlyReportUntil(year=2015):
	thistime = datetime.datetime.now()
	while thistime.year >= year:
		thistime = thistime - relativedelta(months=1)
		
		if(os.path.exists("monthlyReport/otcreport%d%02d.csv" % (thistime.year, thistime.month))):
		   continue
		downloadMonthlyReport(thistime.year, thistime.month)
		time.sleep(1.5)



if __name__ == "__main__":

	downloadMonthlyReportUntil(2015)
