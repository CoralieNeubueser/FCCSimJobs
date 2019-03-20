python python/send.py --local inits/reco.py --physics --process Wqq --etaMax 0.5 --pt 500 -n 25 -N 3000  --condor --local inits/newTileCal.py
python python/send.py --local inits/reco.py --physics --process Wqq --etaMax 0.5 --pt 500 -n 25 -N 3000  --condor --local inits/newTileCal.py --resegmentHCal --recPositions
python python/send.py --local inits/reco.py --physics --process Wqq --etaMax 0.5 --pt 500 -n 25 -N 3000  --condor --local inits/newTileCal.py --resegmentHCal --recTopoClusters --noise
