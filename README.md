# covid-19-graphs-jo
COVID-19 graphs - especially cases per capita and growth.

![COVID-19 confirmed per capita by country"](https://github.com/jojo4u/covid-19-graphs-jo/raw/master/per_capita-confirmed-latest.png)

![COVID-19 deaths per capita by country"](https://github.com/jojo4u/covid-19-graphs-jo/raw/master/per_capita-deaths-latest.png)

## Run
```
$ git clone https://github.com/jojo4u/covid-19-graphs-jo.git
$ cd covid-19-graphs-jo
$ git submodule init
$ git submodule update 
$ python ./covid-19-graphs-jo.py
```
See requirements.txt for modules.

## For data update:
```
$ cd covid-19-data
$ python process.py
```
See requirements.txt for modules.
