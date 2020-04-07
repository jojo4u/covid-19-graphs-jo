# covid-19-graphs-jo
COVID-19 graphs - especially cases per capita and growth.

![COVID-19 confirmed per capita by country"](https://github.com/jojo4u/covid-19-graphs-jo/raw/master/cumulative_capita-confirmed-latest.png)

![COVID-19 deaths per capita by country"](https://github.com/jojo4u/covid-19-graphs-jo/raw/master/cumulative_capita-deaths-latest.png)

![COVID-19 daily confirmed per capita by country"](https://github.com/jojo4u/covid-19-graphs-jo/raw/master/daily_capita-confirmed-latest.png)

![COVID-19 daily deaths per capita by country"](https://github.com/jojo4u/covid-19-graphs-jo/raw/master/daily_capita-deaths-latest.png)

![COVID-19 confirmed percent change by country"](https://github.com/jojo4u/covid-19-graphs-jo/raw/master/pct_change-confirmed-latest.png)

![COVID-19 deaths percent change by country"](https://github.com/jojo4u/covid-19-graphs-jo/raw/master/pct_change-deaths-latest.png)


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
$ git pull
```
or directly from CSSE

```
$ cd covid-19-data/scripts
$ python ./process.py
```

See requirements.txt for modules.
