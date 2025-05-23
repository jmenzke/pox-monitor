#!/bin/bash
systemctl stop pox_serial_logger
DATE1=`date "+%Y-%m-%d"`
DATE2=`date "+%d.%m.%Y"`
DATE3=`date "+%Y%m%d_pulseox"`
DATE4=`date "+%Y%m%d_temperature"`
gzip /mnt/RAMDisk/buffer.out
#gzip /mnt/RAMDisk/temperature.csv
mv --backup=numbered /mnt/RAMDisk/buffer.out.gz /mnt/usb/data/$DATE3.txt.gz
#mv --backup=numbered /mnt/RAMDisk/temperature.csv.gz /mnt/usb/data/$DATE4.csv.gz
echo "" >  /mnt/RAMDisk/buffer.out
echo "" >  /mnt/RAMDisk/pox.json
systemctl start pox_serial_logger

