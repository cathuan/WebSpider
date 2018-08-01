USERNAME=$1
PASSWORD=$2

while true
do
    echo `date`
    DATE=`date +%Y%m%d`

    python weibo.py -u $USERNAME -p $PASSWORD -m post
    FILENAME=${DATE}_chart.csv
    iconv -f UTF-8 -t GB18030 ${FILENAME} > ${DATE}_喜爱值.csv

    sleep 300
done