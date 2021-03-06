#               ---------TO DO --------------

#check pdq combination selector,global variables
#check imports,if modules are exist on machine(importlib)

# 				--------- TO DO ------------


from pyzabbix import ZabbixAPI
import pandas as pd
import json
import csv
import matplotlib.pyplot as plt
from statsmodels.graphics.tsaplots import plot_acf
from statsmodels.tsa.arima_model import ARIMA
from sklearn.metrics import mean_squared_error
from math import sqrt
import os, sys
import time as t
import argparse
import itertools
import warnings
import importlib
import datetime

# PART 0 

#Argument parsing
#argumentparser reads arguments as simple strings by default
parser = argparse.ArgumentParser(description='Automated Zabbix Anomaly Detector')

#url parse
parser.add_argument('-url', type = str, default = 'http://localhost/zabbix',
	help = 'http(s)://<your_zabbix_machine_url/zabbix>.', required = True)

#itemid parse
parser.add_argument('-itemid', type = int, default = '23303', 
	help = '<itemid> , ex = 20303(CPU Softrq Time)', required = True)

#limit parse
parser.add_argument('-limit', type = int, default = '500', 
	help = '<limit> , ex = 500, How many data points you want from past?', required = True)

#datatype parse
parser.add_argument('-dtype', type = int, default = 0, 
	help = '<dtype> , History data type. 0 -> numeric float \n 3 -> numeric unsigned. NOTE: 1(char),2(log) and 4(text) are not valid value types for this application.')

#Zabbix username
parser.add_argument('-u', type = str, default = 'Admin', 
	help = '<username>, username of zabbix user. default:"<Admin>" . Note: Make sure,selected user has auth to read data.')

#Zabbix password
parser.add_argument('-p', type = str, default = 'zabbix', 
	help = '<password>, password of zabbix user. default:"<zabbix>"')

#P,D,Q range
parser.add_argument('-r', type = int, default = 5,
	help = '<value> , Advised to use stock value(5) if you have no clue. ARIMA p,d,q variables range. This range will determine how many combinations will be.ex =[0,0,0] to [5,5,5]. This will effect performance of your computer.Higher value, will take longer time.')

#Plot graphs save name
parser.add_argument('-o', type = str, default = 'plots.pdf', 
	help = '<filename.extention> , Save generated plots to your current directory with a selected name. ex: "plots.pdf".')


#now we pars the args

args = parser.parse_args()

print("\n\nEntered arguments are(including defaults):\n")

print(args)

#wait for 2 seconds for user to read prompts.
t.sleep(1)

#check if needed modules exist on working machine



# ---------------------  END  ---------------
# PART 1
#zabbix server url
zapi = ZabbixAPI(args.url) 
#zabbix creds
zapi.login(args.u, args.p)

#connection verify
print("Connected to Zabbix API Version %s" % zapi.api_version())


#variables for arima parameters and aic function value
global param_temp
global time
global aic_temp
global mse_temp
global range_temp
range_temp = args.r


#filename concatenated with execution time to eliminate confusion
time = datetime.datetime.now()
#convert time to string
time_now = time.strftime('%Y-%M-%d_%H-%m-%S')
filename = "zabbixdata_%s_.json" % time_now
print(filename)


#plot images output address
plt_out_addr = "_%s"% time_now  + args.o  

print(plt_out_addr)

#ForecastCPU values(float) sorted by clock,json data. (select itemid,key_,name from items where key_="anything";)
#select itemid,name,key_ form items; to display full list of items.
for h in zapi.history.get(history=args.dtype, itemids=args.itemid, sortfield='clock', sortorder='DESC',limit = args.limit):
	#convert dict data to json 
	h = json.dumps(dict(h))
	#write json data to file
	f = open(filename,"a+")
	f.write(h + "\r\n")
    
#open json with pandas and convert to csv

with open(filename) as f_input:
	filename = filename + ".csv"
	print(filename)
	#read from json file and convert to csv
	df = pd.read_json(f_input, encoding = 'utf-8', lines = True)
	df.to_csv(filename, encoding = 'utf-8', index = False)

#wait for 2 seconds for user to read prompts.
t.sleep(1)
#-----------------------END-------------------------


# PART 2

# now we parse the csv data and  apply arima function to data.


#2.0
#read data from file and parse it
tseries = pd.read_csv(filename, index_col = 'clock')

# we only want clock and value colums to process
tseries_parsed = tseries[tseries.columns[2]]
print(tseries_parsed.head())

tseries_parsed.plot(color = 'green', label = 'parsed data')
plt.xlabel("clock")
plt.ylabel("values")
plt.legend(loc = 'upper left')

#2.1
#regression part, we examine how data will behave after 5 time differenciation

tseries_parsed_diff = tseries_parsed.diff(periods = 5)

#we extract NaN values out
tseries_parsed_diff = tseries_parsed_diff[5:]
tseries_parsed_diff.plot(color = 'purple', label= 'diff_by5')
plt.xlabel("clock")
plt.ylabel("values")
plt.legend(loc = 'upper left')


#2.2
#autocorrelation plots before and after diff,so we can observe data
plot_acf(tseries_parsed, color = 'gray', label = 'before_diff')
plt.xlabel("clock")
plt.ylabel("values")
plt.legend(loc = 'upper left')
plot_acf(tseries_parsed_diff, color= 'brown', label = 'after_diff')
plt.xlabel("clock")
plt.ylabel("values")
plt.legend(loc = 'upper left')




#2.3
#train and prediction values will be set

#check how many values are there,which will be 499(because we exctracted 1 by selecting clock as an index).
X = tseries_parsed.values

#train and prediction data variables
global X_TNEW
global X_PNEW

#check if X size is even number
if X.size % 2 == 0:
	#X_TNEW = Train data %90
	X_TNEW = X[0:int(len(X)*0.9)]
	#X_PNEW = Predic data %10
	X_PNEW = X[int(len(X)*0.9):]
#check if X size is odd number	
if X.size % 2 == 1:
	X_TNEW = X[0:int(len(X)*0.9)]
	X_PNEW = X[int(len(X)*0.9):]

print("loaded data count: %d \n"% (X.size))

#train data is set to train variable
train = X_TNEW 
print("train data count : %d \n" % (train.size))

#test data is set to test variable
test = X_PNEW
print("test data count : %d \n" % (test.size))

#predictions variable
predictions = []


#----------------------- END ------------------------

#PART 3
#--------------------------------OPTIONAL-----------------------------------------
#now we are trying to find best combination of parameters for arima

warnings.filterwarnings('ignore')

#we can appends this range to find best combination if we havent yet.
p=d=q= range(0,range_temp)

pdq = list(itertools.product(p,d,q))
print(pdq)

#now we make for loop to iterate over

for param in pdq:
	
	try:
		model_arima = ARIMA(train, order= param)
		model_arima_fit = model_arima.fit()
		print(mean_squared_error, param, model_arima_fit.aic)
		
		aic_temp = model_arima_fit.aic
		param_temp = param
		mse_temp = mean_squared_error

		if aic_temp < model_arima_fit.aic & model_arima_fit.aic > 0:
			
			mse_temp = mean_squared_error
			param_temp = param
			aic_temp = model_arima_fit.aic
		elif aic_temp > model_arima_fit.aic & model_arima_fit.aic < 0:
			mse_temp = mean_squared_error
			param_temp = param
			aic_temp = model_arima_fit.aic
	except:
		continue
print("\n\nResults:\n")
print(mse_temp,param_temp,aic_temp)

#wait 3 seconds for user to read prompt
t.sleep(3)

#----------------------END----------------------

#after determination of best parameter combination,we plot the graph



#PART 4
#ARIMA Model First Part(Auto Regression(AR))

#p,d,q parameters correspond to AR,I,MA parameters.
#periods, order of diff, lag

#4.1

#we pass param_temp value which was fetched from aic trials
model_arima = ARIMA(train, order = param_temp)

#substract each value from the one that follows it. thus allows graph to be smoother.
model_arima_fit = model_arima.fit()

#4.2

#we apply forecast(in arima,we use forecast func instead of predict) and store it in predictions
predictions = model_arima_fit.forecast(steps = X_PNEW.size)[0]


#test as red,predictions as yellow color
plt.plot(test,color = 'red', label = 'test_data')
plt.plot(predictions, color ='blue', label = 'predictions_data')
plt.xlabel('Clock')
plt.ylabel('Values')
plt.legend(loc = 'upper left')

#4.3

#mean square error
mse = mean_squared_error(test,predictions)
#sqrt mse is to evaluate performance of model
rmse = sqrt(mse)

print("Test result: {} ".format(mse))
print("RMSE : %3.f \n" % rmse)
plt.savefig(plt_out_addr, format = 'pdf', dpi= 100)

plt.show()

print("\n\nPlots of the data, saved to your current working directory!")

#-----------------END-------------------
