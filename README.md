Automated Zabbix Anomaly Detection script written in python.

Note: This script only works with time series data. Parsing process has been done automatically but there might be some changes according to your fetched data.

The goal of this project is eliminate surprises and detect potencial anomalies beforehand.

You need to specify your zabbix machine ip to use and thats it.

Of couse there might be some packages to download. you can check included libraries to compare which one is needed to you.

Script does all the work for you such as pulling data from zabbix api,parsing json to csv,predicting and plotting your time series data with arima.

 It is an ongoing project and predictions may be sloppy but you can just adjust ARIMA parameters(P,D,Q) to change outcome and fiddle around to find best result for you.

-----------> Current(master) Version Notes <------------

-> Argparser added and working correctly. It does not sanitize user input though so be careful.
-> Results are promising and i am still trying to improve prediction results but it is highly dependent to fetched data.
-> Plot graphs and fetched data are saved to working directory of the program.
