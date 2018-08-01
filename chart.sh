USERNAME=$1
PASSWORD=$2

while true
do
    echo `date`
    DATE=`date +%Y%m%d`

    python weibo.py -u $USERNAME -p $PASSWORD -m chart
    FILENAME=${DATE}_post_data.csv
    iconv -f UTF-8 -t GB18030 ${FILENAME} > ${DATE}_微博具体信息.csv

    sleep 300
done