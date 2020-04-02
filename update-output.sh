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

case "$1" in
  --from-CSSE) echo "data update from CSSE";;
            *) echo "no data update";;
esac

date=$(date -d "yesterday 13:00" '+%Y-%m-%d')

echo "update for $date"

#date=2020-03-27




if [[ $1 == "--from-CSSE" ]]; then
  pushd .
  cd covid-19-data/scripts || check_errs 2 "cd data/scripts failed"
  python ./process.py || { popd; check_errs 2 "process.py failed"; }
  popd
else 
  echo "data update from datasets/covid-19 git"
  pushd .
  cd covid-19-data || check_errs 2 "cd covid-19-data failed"
  git stash || { popd; check_errs 2 "git stash failed"; }
  git pull --no-edit || { popd; check_errs 2 "git pull failed"; }
  popd
fi

echo "output graphs for $date..."
python ./covid-19-graphs-jo.py per_capita Confirmed || check_errs 2 "per_capita Confirmed failed"
python ./covid-19-graphs-jo.py per_capita Deaths    || check_errs 2 "per_capita Deaths failed"
python ./covid-19-graphs-jo.py pct_change Confirmed || check_errs 2 "pct_change Confirmed failed"
python ./covid-19-graphs-jo.py pct_change Deaths    || check_errs 2 "pct_change Deaths failed"

paplay /usr/share/sounds/freedesktop/stereo/complete.oga

echo "compress, commit and push?"
read enter_val
echo "compressing with pingo..."
pingo -s9 ./output/*-$date.png #pingo is optional

cp ./output/pct_change-confirmed-$date.png pct_change-confirmed-latest.png || check_errs 2 "cp pct_change-confirmed failed"
cp ./output/pct_change-deaths-$date.png    pct_change-deaths-latest.png    || check_errs 2 "cp pct_change-deaths failed"
cp ./output/per_capita-confirmed-$date.png per_capita-confirmed-latest.png || check_errs 2 "cp per_capita-confirmed failed"
cp ./output/per_capita-deaths-$date.png    per_capita-deaths-latest.png    || check_errs 2 "cp pct_change-deaths failed"


git add *.png output/*.png || check_errs 2 "git add failed"

git commit -m "$date output update" || check_errs 2 "git commit failed"

git push origin master || check_errs 2 "git push origin master failed"
