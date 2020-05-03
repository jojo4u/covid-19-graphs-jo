# covid-19-graphs-jo
COVID-19 graphs - especially cases per capita and growth.

![COVID-19 confirmed per capita by country"](https://github.com/jojo4u/covid-19-graphs-jo/raw/master/cumulative_capita-confirmed-latest.png)

![COVID-19 deaths per capita by country"](https://github.com/jojo4u/covid-19-graphs-jo/raw/master/cumulative_capita-deaths-latest.png)

![COVID-19 weekly confirmed per capita by country"](https://github.com/jojo4u/covid-19-graphs-jo/raw/master/weekly_capita-confirmed-latest.png)

![COVID-19 weekly deaths per capita by country"](https://github.com/jojo4u/covid-19-graphs-jo/raw/master/weekly_capita-deaths-latest.png)

## Run
```
$ git clone https://github.com/jojo4u/covid-19-graphs-jo.git
$ cd covid-19-graphs-jo
$ git submodule init
$ git submodule update --depth=1 
$ python ./covid-19-graphs-jo.py
```
See requirements.txt for modules.

## For data update:
```
$ cd covid-19-data
$ git pull
```
This pulls around 200 MB each da. Alternatively directly from GitHub:

```
cd covid19-datasets/exports/combined/v1/
curl --location --remote-name "https://github.com/cipriancraciun/covid19-datasets/raw/master/exports/combined/v1/values.tsv.gz" || { popd; check_errs 2 "curl values.tsv.gz failed"; }
gunzip --force values.tsv.gz
```

See requirements.txt for modules.

## Acknowledgements
Based on original data from JHU CSSE (https://github.com/CSSEGISandData/COVID-19),
as processed and augmented at https://github.com/cipriancraciun/covid19-datasets