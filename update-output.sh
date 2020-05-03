#!/bin/zsh

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
  --git-pull) ;;
           *) ;;
esac

date=$(date -d "yesterday 13:00" '+%Y-%m-%d')
#date=2020-03-27

echo "update for $date"

pushd .

if [[ $1 == "--git-pull" ]]; then
    echo "data update from GitHub cipriancraciun/covid19-datasets.git"
    cd covid19-datasets || check_errs 2 "cd covid19-datasets failed"
    git stash || { popd; check_errs 2 "git stash failed"; }
    git pull --no-edit || { popd; check_errs 2 "git pull failed"; }
    rm exports/combined/v1/values.tsv || { popd; check_errs 2 "rm values.tsv failed"; }
    gunzip --force exports/combined/v1/values.tsv.gz || { popd; check_errs 2 "gunzip values.tsv failed"; }
else
    echo "data update by curl download from GitHub cipriancraciun/covid19-datasets"
    cd covid19-datasets/exports/combined/v1/ || { popd; check_errs 2 "cd covid19-datasets/exports/combined/v1/ failed"; }
    curl --location --remote-name "https://github.com/cipriancraciun/covid19-datasets/raw/master/exports/combined/v1/values.tsv.gz" || { popd; check_errs 2 "curl values.tsv.gz failed"; }
    gunzip --force values.tsv.gz || { popd; check_errs 2 "gunzip values.tsv failed"; }
fi

popd

echo "output graphs for $date..."
python ./covid-19-graphs-jo.py weekly_capita confirmed      || check_errs 2 "weekly_capita confirmed failed"
python ./covid-19-graphs-jo.py weekly_capita deaths         || check_errs 2 "weekly_capita deaths failed"
python ./covid-19-graphs-jo.py cumulative_capita confirmed || check_errs 2 "cumulative_capita confirmed failed"
python ./covid-19-graphs-jo.py cumulative_capita deaths    || check_errs 2 "cumulative_capita deaths failed"
#python ./covid-19-graphs-jo.py pct_change confirmed        || check_errs 2 "pct_change confirmed failed"
#python ./covid-19-graphs-jo.py pct_change deaths           || check_errs 2 "pct_change deaths failed"

paplay /usr/share/sounds/freedesktop/stereo/complete.oga

echo "compress, commit and push? (any key/Ctrl-C)"
read enter_val
echo "storing git password..."
git push --dry-run origin master
echo "compressing with pingo..."
pingo -s9 ./output/*-$date.png #pingo is optional,, no check_errs

cp ./output/weekly_capita-confirmed-$date.png      weekly_capita-confirmed-latest.png      || check_errs 2 "cp weekly_capita-confirmed failed"
cp ./output/weekly_capita-deaths-$date.png         weekly_capita-deaths-latest.png         || check_errs 2 "cp weekly_capita-deaths failed"
cp ./output/cumulative_capita-confirmed-$date.png  cumulative_capita-confirmed-latest.png || check_errs 2 "cp cumulative_capita-confirmed failed"
cp ./output/cumulative_capita-deaths-$date.png     cumulative_capita-deaths-latest.png    || check_errs 2 "cp cumulative_change-deaths failed"
#cp ./output/pct_change-confirmed-$date.png        pct_change-confirmed-latest.png        || check_errs 2 "cp pct_change-confirmed failed"
#cp ./output/pct_change-deaths-$date.png           pct_change-deaths-latest.png           || check_errs 2 "cp pct_change-deaths failed"


git add *.png output/*.png || check_errs 2 "git add failed"

git commit -m "$date output update" || check_errs 2 "git commit failed"

git push origin master || check_errs 2 "git push origin master failed"

paplay /usr/share/sounds/freedesktop/stereo/complete.oga