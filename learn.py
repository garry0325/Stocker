import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import pathlib
import seaborn as sns
import sys
import random

def preprocessDataset(fileName):
	dataset = pd.read_csv(fileName, sep=',')

	dataset['獲利'] = [float(i.strip('%')) for i in dataset['獲利']]
	dataset['殖利'] = [float(i.strip('%')) for i in dataset['殖利']]
	dataset['營收'] = [float(i.strip('%')) for i in dataset['營收']]
	dataset['YoY'] = [float(i.strip('%')) for i in dataset['YoY']]
	dataset['MoM'] = [float(i.strip('%')) for i in dataset['MoM']]
	dataset['MA20Progress'] = [float(i.strip('%')) for i in dataset['MA20Progress']]

	
	dataset.pop('代號')
	dataset.pop('公司')
	dataset.pop('股價buy')
	dataset.pop('股價sell')
	dataset.pop('Month')

	return dataset

def sampleFromDataset(dataset, fraction=0.8, randomState=15):

	# pick train & test dataset at random
	trainDataset = dataset.sample(frac=fraction, random_state=randomState)
	testDataset = dataset.drop(trainDataset.index)

	return trainDataset, testDataset

def normalize(x, stat):
	return (x - stat['mean']) / stat['std']

def normalizeDataset(stat, trainDataset, testDataset):
	# getting normalize details
	stat = stat.describe()
	stat.pop('獲利')
	stat = stat.transpose()
	
	return normalize(trainDataset, stat), normalize(testDataset, stat)


def buildModel():
	model = keras.Sequential([layers.Dense(64, activation='relu', input_shape=[len(trainDataset.keys())]),
							  layers.Dense(64, activation='relu'),
							  layers.Dense(1)])
							  
	optimizer = tf.keras.optimizers.RMSprop(0.001)

	model.compile(loss='mse', optimizer=optimizer, metrics=['mae', 'mse'])
	return model



class PrintDot(keras.callbacks.Callback):
	def on_epoch_end(self, epoch, logs):
		if epoch % 100 == 0: print('')
		print('.', end='')


def plot_history(history):
	hist = pd.DataFrame(history.history)
	hist['epoch'] = history.epoch

	plt.figure()
	plt.xlabel('Epoch')
	plt.ylabel('Mean Abs Error [MPG]')
	plt.plot(hist['epoch'], hist['mean_absolute_error'], label='Train Error')
	plt.plot(hist['epoch'], hist['val_mean_absolute_error'], label = 'Val Error')
	plt.legend()
	
	plt.figure()
	plt.xlabel('Epoch')
	plt.ylabel('Mean Square Error [$MPG^2$]')
	plt.plot(hist['epoch'], hist['mean_squared_error'], label='Train Error')
	plt.plot(hist['epoch'], hist['val_mean_squared_error'], label = 'Val Error')
	plt.legend()
	plt.show()


if(sys.argv[1] == '0'):
	dataset = preprocessDataset('data.csv')
	trainDataset, testDataset = sampleFromDataset(dataset, fraction=0.8, randomState=15)

	trainDatasetCopy = trainDataset.copy()
	
	trainLabels = trainDataset.pop('獲利')
	testLabels = testDataset.pop('獲利')
	
	normedTrainDataset, normedTestDataset = normalizeDataset(trainDatasetCopy, trainDataset, testDataset)
	

	EPOCHS = 5000
	model = buildModel()
	history = model.fit(
						normedTrainDataset, trainLabels,
						epochs=EPOCHS, validation_split = 0.2, verbose=1,
						callbacks=[PrintDot()])

	model.save('learndModel.h5')

	hist = pd.DataFrame(history.history)
	print(hist.head())
	print(hist.tail())
	hist['epoch'] = history.epoch

	plot_history(history)

elif(sys.argv[1] == '1'):
	model = tf.keras.models.load_model('learndModel.h5')
	
	dataset = preprocessDataset('data.csv')
	trainDataset, testDataset = sampleFromDataset(dataset, fraction=0.8, randomState=15)
	
	trainDatasetCopy = trainDataset.copy()
	
	trainLabels = trainDataset.pop('獲利')
	testLabels = testDataset.pop('獲利')
	
	normedTrainDataset, normedTestDataset = normalizeDataset(trainDatasetCopy, trainDataset, testDataset)

	testPredictions = model.predict(normedTrainDataset).flatten()
	a = plt.axes(aspect='equal')
	plt.scatter(trainLabels, testPredictions)
	plt.xlabel('True value')
	plt.ylabel('Predictions')
	plt.show()


elif(sys.argv[1] == '2'):
	dataset = preprocessDataset('data.csv')
	
	splitWidth = 10
	splitCases = int(90 / splitWidth) + 2
	
	case = []
	caseCount = []
	for i in range(0, splitCases):
		case.append(np.zeros(10))
		caseCount.append(0)
	
	for i in dataset.iterrows():
		profit = i[1]['獲利']
		
		if(profit >= 60):
			case[0] = case[0] + i[1]
			caseCount[0] = caseCount[0] + 1
		elif(profit < -30):
			case[splitCases-1] = case[splitCases-1] + i[1]
			caseCount[splitCases-1] = caseCount[splitCases-1] + 1
		else:
			n = int((60 - profit) / splitWidth) + 1
			case[n] = case[n] + i[1]
			caseCount[n] = caseCount[n] + 1
				
	for i in range(0, splitCases):
		case[i] = case[i] / caseCount[i]

	categorized = pd.DataFrame(case, columns=['獲利', '殖利', '本益', '淨值', '營收', 'YoY', 'MoM', '成交量', 'MA20', 'MA20Progress'])


	print(categorized)
			
elif(sys.argv[1] == '3'):
	dataset = preprocessDataset('data.csv')

	while True:
		c = input()
		if(len(c)>0):
			break
		x = []
		y = []
		for i in range(0, 100):
			pick = random.randint(0, 4000)
			score = [0, 0, 0, 0, 0, 0]
			score[0] = abs(dataset.iloc[pick]['殖利'] - 2.467895) / 2.467895
			score[1] = abs(dataset.iloc[pick]['本益'] - 35.359474) / 35.359474
			score[2] = abs(dataset.iloc[pick]['營收'] - 23.368421) / 23.368421
			score[3] = abs(dataset.iloc[pick]['YoY'] - 43.947368) / 43.947368
			score[4] = abs(dataset.iloc[pick]['MoM'] - 7.789474) / 7.789474
			score[5] = abs(dataset.iloc[pick]['MA20Progress'] - 1.047421) / 4

			x.append(round(sum(score),2))
			y.append(dataset.iloc[pick]['獲利'])


		plt.scatter(x,y, s=10)
		plt.show()
