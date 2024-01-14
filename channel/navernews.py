from bs4 import BeautifulSoup
from common.utils import Utils 
from datetime import datetime, timedelta
import pandas as pd
import requests
from time import sleep
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning) 

class NaverNews():
    def __init__(self, tk, start_date, end_date, logger) -> None:
        self.origin_url       = f'https://search.naver.com/search.naver?sm=tab_hty.top&where=news&query={tk}&de={end_date}&ds={start_date}&office_category=0&office_section_code=0&office_type=0&pd=4&photo=0&service_area=0&sort=1&start=<%page_num%>'
        # self.crawl_date       = datetime.strptime(crawl_start_date, "%Y-%m-%d %H:%M:%S").date().strftime("%Y-%m-%d").replace("-", "")
        self.crawl_start_date = datetime.strptime(start_date,'%Y-%m-%d')
        self.crawl_end_date   = datetime.strptime(end_date,'%Y-%m-%d')
        self.start_date       = start_date
        self.end_date         = end_date
        self.insert_count     = 0
        self.success_count    = 0
        self.error_count      = 0
        self.logger           = logger
        
        # Utils 정의
        util = Utils(logger)
        self.util = util

    def NaverNews_Crawl(self):
        """ crawl start date, crawl end date 사이에 있는 뉴스 링크 수집 """
        try:
            now = datetime.now()
            now_hour = now.hour
            now_date = datetime.strftime(now,'%Y-%m-%d')                
            self.logger.info(f'{now_date}  >>  네이버기사 수집 시작')
            next_page_flag = True
            main_page_no = 1
            article_list = []
            result = pd.DataFrame()
            while next_page_flag:
                try:          
                    page_url = self.origin_url
                    # 1페이지 수집 시 referer url의 페이지번호 설정 안 함 
                    # 그 외 페이지의 경우 이전 페이지 번호로 설정  
                    if main_page_no == 1:
                        referer_url = self.origin_url.replace("<%page_num%>", str(main_page_no))
                    else:
                        referer_url = self.origin_url.replace("<%page_num%>", str(main_page_no))
                        main_page_no += 10
                        
                    page_url = self.origin_url.replace("<%page_num%>", str(main_page_no))
                    try:
                        # 헤더 설정
                        custom_headers = {
                            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36',
                            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
                            'Referer': referer_url,
                            # 'Host': 'news.naver.com'
                        }
                        request = requests.get(page_url, headers=custom_headers, verify=False, timeout=5)
                        sleep(1)

                        html = request.text
                        soup = BeautifulSoup(html, "html.parser")
                    except Exception as e:
                        raise Exception('본문 통신 중 에러')
                        
                    # 헤드라인 li 모음
                    div = soup.find("ul", {"class": "list_news"})
                    if div:
                        headlines = div.find_all("li", {'class':'bx'})

                        for headline in headlines:
                            try:
                                link = headline.find("div", {'class':'news_contents'}).find('a').get('href').strip()
                                if link != "":
                                    # 수집 시간에 해당하는지 확인
                                    if len(headline.find_all("span", {"class": "info"})) == 1: url_date = self.util.ReplaceTime(headline.find_all("span", {"class": "info"})[0].text.strip())
                                    elif len(headline.find_all("span", {"class": "info"})) == 2: url_date = self.util.ReplaceTime(headline.find_all("span", {"class": "info"})[1].text.strip())
                                    url_date = datetime.strptime(url_date ,'%Y-%m-%d %H:%M:%S')
                                    
                                    if self.crawl_start_date <= url_date < self.crawl_end_date:
                                        title  = headline.find("div", {'class':'news_contents'}).find('a', {'class':'news_tit'}).get('title').strip()
                                        writer = headline.find("div", {'class':'info_group'}).find('a').text.strip()
                                        date = datetime.strftime(url_date ,'%Y-%m-%d %H:%M:%S')
                                        article_list.append([date, title, writer, link])
                                    elif self.crawl_start_date > url_date:
                                        next_page_flag = False
                                        break
                            except Exception as e:
                                self.logger.error('기사 수집 중 에러')

                        # 하단 페이지 번호들 중 마지막 페이지의 태그가 strong일 경우 next_page_flag = False
                        if next_page_flag:
                            pages = soup.find("div",{"class":"api_sc_page_wrap"}).find('a', {'class':'btn_next'}).get('aria-disabled')
                            next_page_flag = False if pages == 'false' else True
                    elif '검색결과가 없습니다' in soup.text:
                        article_list.append('검색결과가 없습니다')
                        result = pd.DataFrame(data = article_list, columns=['기사내용'])
                        self.logger.info('검색결과 없습니다.')
                        next_page_flag = False
                        break

                except Exception as e:
                    raise Exception('페이지처리 중 에러')
            if '검색결과가 없습니다' not in soup.text:
                result = pd.DataFrame(data = article_list, columns=['날짜', '기사제목', '작성자', 'Url'])
                result.to_excel(f'data/{now_date}_{now_hour}.xlsx', index=False, columns=['날짜', '기사제목', '작성자', 'Url'])
            
            self.logger.info(f'{now_date}  >>  네이버기사 수집 종료')
   
        except Exception as e:
            self.logger.error('기사 수집 중 에러')

        return result