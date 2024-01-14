import configparser
from datetime import datetime, timedelta
from loguru import logger
import os
import pandas as pd
import urllib.parse

from channel.navernews import NaverNews
from common.getContent import GetContent
from common.sendEmail import EmailSender, EmailHTMLContent

# 현재 파일 위치
file_path = os.path.abspath(__file__)

# 키워드 불러오기 위한 config파일 불러오기
config = configparser.ConfigParser()
config.read('config.ini')
main_keyword = config['MAIN KEYWORD']['keyword']
sub_keyword = config['SUB KEYWORD']['keyword']

# 프로그램 시작 시 현재 날짜 조회하기
now = datetime.now()
now_date = datetime.strftime(now,'%Y-%m-%d')

# 프로그램 폴더 내 log폴더 안에 날짜와 라운드별 로그파일 설정하기
logger.add(f"./logs/{now_date}_{now.hour}.log", format="{time:YYYY-MM-DD at HH:mm:ss} | {level} | {message}") 

if __name__ == '__main__':
    total_keyword = f'{sub_keyword} +{main_keyword}'
    tk = urllib.parse.quote(string=total_keyword)
    now = datetime.now()
    start_date = datetime.strftime(now,'%Y-%m-%d')
    end_date = datetime.strftime(now+timedelta(1),'%Y-%m-%d')

    # 네이버 기사 수집 시작
    nn = NaverNews(tk, start_date, end_date, logger)
    table = nn.NaverNews_Crawl()

    # html 콘텐츠 만들기
    content = GetContent(logger)
    content.get_Summary_Content(now, table)

    str_host = 'smtp.gmail.com'
    num_port = 587 
    es  = EmailSender(str_host, num_port)

    # 메일 내용
    text = ''
    # -- TEST -- #
    text = content.get_Summary_Content(now, table)

    logger.info('[PROCESS][__main__] : Getting Content')

    pre_body = '<html><head></head><body>'
    post_body = '</body></html>'
    template = pre_body + text + post_body

    
    template_params = {'NAME': 'Anthonynoh'}
    

    str_subject = '자산운용' # 제목
    ehc = EmailHTMLContent(str_subject, template)


    logger.info('[PROCESS][__main__] : Getting Content Success!')
    logger.info('[PROCESS][__main__] : Setting Success!')

    
    logger.info('[PROCESS][__main__] : Send Mail')

    # 발신자 이메일 주소
    str_from_email_addr = config['EMAIL']['sender']

    # 수신자 이메일 주소
    str_to_email_addrs = config['EMAIL']['receiver'].split(' | ')
    es.send_message(ehc, str_from_email_addr, str_to_email_addrs)

    print('[PROCESS][__main__] : Send Mail Success!')
    print()


