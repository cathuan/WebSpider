USERNAME=$1
PASSWORD=$2

while true
do
    echo `date`
    DATE=`date +%Y%m%d`

    python weibo.py -u $USERNAME -p $PASSWORD -m followers
    FILENAME=${DATE}_follower_counts.csv
    iconv -f UTF-8 -t GB18030 ${FILENAME} > ${DATE}_关注数.csv

    sleep 300
done