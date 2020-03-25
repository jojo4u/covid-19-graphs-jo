#!/bin/sh

check_errs()
{
  # Parameter 1 is the return code
  # Parameter 2 is text to display on failure.
  if [ "${1}" -ne "0" ]; then
    # play sound
    paplay /usr/share/sounds/freedesktop/stereo/suspend-error.oga
    echo "ERROR # ${1} : ${2}. Press enter to exit" 1>&2
    read enter_val
    # as a bonus, make our script exit with the right error code.
    exit ${1}
  fi
}

echo $1

case "$1" in
        --data-update) do_Update=1; echo "do data update";;
        *) do_Upate=0;echo "no data update";;
esac

#today=$(date +%Y-%m-%d)

today=2020-03-24

echo "output graphs for $today..."

if [[ do_Update == 1 ]]; then
  cd covid-19-data/scripts || check_errs 2 "cd data failed"
  python ./process.py || check_errs 2 "process.py failed"
  cd ..
  cd ..
fi

python ./covid-19-graphs-jo.py per_capita Confirmed || check_errs 2 "per_capita Confirmed failed"
python ./covid-19-graphs-jo.py per_capita Deaths    || check_errs 2 "per_capita Deaths failed"
python ./covid-19-graphs-jo.py pct_change Confirmed || check_errs 2 "pct_change Confirmed failed"
python ./covid-19-graphs-jo.py pct_change Deaths    || check_errs 2 "pct_change Deaths failed"

pingo -s9 ./output/*-$today.png #pingo is optional

cp ./output/pct_change-confirmed-$today.png pct_change-confirmed-latest.png || check_errs 2 "cp pct_change-confirmed failed"
cp ./output/pct_change-deaths-$today.png pct_change-deaths-latest.png       || check_errs 2 "cp pct_change-deaths failed"
cp ./output/per_capita-confirmed-$today.png per_capita-confirmed-latest.png || check_errs 2 "cp per_capita-confirmed failed"
cp ./output/per_capita-deaths-$today.png per_capita-confirmed-latest.png    || check_errs 2 "cp pct_change-deaths failed"

git add *.png output/*.png || check_errs 2 "git add failed"

git commit -m "$today output update" || check_errs 2 "git commit failed"

#put complete sound since here git push often needs user input
paplay /usr/share/sounds/freedesktop/stereo/complete.oga

git push origin master || check_errs 2 "git push origin master failed"
