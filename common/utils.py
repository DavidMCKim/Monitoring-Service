from datetime import datetime, timedelta
import os
import re
import sys

class Utils():
    def __init__(self, logger) -> None:
        self.logger = logger
        
    def ReplaceTime(self, time_str):
        currentDate = datetime.now() # 현재 시간

        try:
            regex_time_1 = re.compile('[0-9]{2}:[0-9]{2}')
            regex_time_2 = re.compile('\d*.\d*.\d.')
            if '시간' in time_str:
                time = time_str.replace('시간 전', '').replace('시간전', '')
                diff_time = timedelta(hours=int(time))
                time_str = datetime.strftime(currentDate - diff_time, "%Y-%m-%d %H:%M:%S")
            elif '분' in time_str:
                time = time_str.replace('분 전', '').replace('분전', '')
                diff_time = timedelta(minutes=int(time))
                time_str = datetime.strftime(currentDate - diff_time, "%Y-%m-%d %H:%M:%S")
            elif '일' in time_str:
                time = time_str.replace('일 전', '').replace('일전', '')
                diff_time = timedelta(days=int(time))
                time_str = datetime.strftime(currentDate - diff_time, "%Y-%m-%d %H:%M:%S")
            elif '오늘' in time_str:
                time_str = datetime.strftime(currentDate, "%Y-%m-%d %H:%M:%S")
            elif '어제' in time_str:
                diff_time = timedelta(days=1)
                time_str = datetime.strftime(currentDate - diff_time, "%Y-%m-%d %H:%M:%S")
            elif '방금' in time_str:
                time_str = datetime.strftime(currentDate, "%Y-%m-%d %H:%M:%S")
            elif '주' in time_str:
                time = time_str.replace('주 전', '').replace('주전', '')
                diff_time = timedelta(weeks=int(time))
                time_str = datetime.strftime(currentDate - diff_time, "%Y-%m-%d %H:%M:%S")
            elif '개월' in time_str:
                time = time_str.replace('개월 전', '').replace('개월전', '')
                diff_time = timedelta(months=int(time))
                time_str = datetime.strftime(currentDate - diff_time, "%Y-%m-%d %H:%M:%S")
            elif '년' in time_str:
                time = time_str.replace('년 전', '').replace('년전', '')
                diff_time = timedelta(years=int(time))
                time_str = datetime.strftime(currentDate - diff_time, "%Y-%m-%d %H:%M:%S")
            elif regex_time_1.match(time_str):
                time_str = f"{datetime.now().strftime('%Y-%m-%d')} {time_str}:00"
            elif regex_time_2.match(time_str):
                if '오후' in time_str:
                    diff_time = timedelta(hours=12)
                    if len(time_str.split('오후 ')[1].split(':')[0]) == 2:
                        time_str = datetime.strftime(datetime.strptime(time_str.replace('. ',' ').replace('.', '-').replace('오후 ','')+':00','%Y-%m-%d %H:%M:%S')+diff_time,'%Y-%m-%d %H:%M:%S')
                    else:
                        time_str = datetime.strftime(datetime.strptime(time_str.replace('. ',' ').replace('.', '-').replace('오후 ','0')+':00','%Y-%m-%d %H:%M:%S')+diff_time,'%Y-%m-%d %H:%M:%S')
                elif '오전' in time_str:
                    if len(time_str.split('오전 ')[1].split(':')[0]) == 2:
                        time_str = datetime.strftime(datetime.strptime(time_str.replace('. ',' ').replace('.', '-').replace('오전 ','')+':00','%Y-%m-%d %H:%M:%S'),'%Y-%m-%d %H:%M:%S')
                    else:
                        time_str = datetime.strftime(datetime.strptime(time_str.replace('. ',' ').replace('.', '-').replace('오전 ','0')+':00','%Y-%m-%d %H:%M:%S'),'%Y-%m-%d %H:%M:%S')

                else:
                    time_str = time_str[:-1].replace('.','-') + ' 00:00:00'
            
        except Exception as e:
            self.logger.error('ReplaceTime Error')
            time_str = '-1'

        return time_str    