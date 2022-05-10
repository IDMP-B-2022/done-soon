curl -o 'challenge-2021.tar.gz' 'https://www.minizinc.org/challenge2021/mznc2021_probs.tar.gz'
curl -o 'challenge-2020.tar.gz' 'https://www.minizinc.org/challenge2020/mznc2020-probs.tar.gz'
curl -o 'challenge-2019.tar.gz' 'https://www.minizinc.org/challenge2019/mznc2019-probs.tar.gz'
curl -o 'challenge-2018.tar.gz' 'https://www.minizinc.org/challenge2018/mznc2018-probs.tar.gz'
curl -o 'challenge-2017.tar.gz' 'https://www.minizinc.org/challenge2017/mznc2017-probs.tar.gz'
curl -o 'challenge-2016.tar.gz' 'https://www.minizinc.org/challenge2016/mznc2016-probs.tar.gz'
curl -o 'challenge-2015.tar.gz' 'https://www.minizinc.org/challenge2015/mznc2015-probs.tar.gz'
curl -o 'challenge-2014.tar.gz' 'https://www.minizinc.org/challenge2014/mznc2014-probs.tar.gz'
curl -o 'challenge-2014.tar.gz' 'https://www.minizinc.org/challenge2013/mznc2013-probs.tar.gz'
for f in *.tar.gz; do tar xf "$f"; done
rm *.tar.gz
wget 'https://github.com/MiniZinc/minizinc-benchmarks/archive/refs/heads/master.zip'
unzip master.zip
rm master.zip
mv minizinc-benchmarks-master mzncbenchmarks

find . -mindepth 2 -maxdepth 2 -exec cp -r {} . \;
rm -r mznc*