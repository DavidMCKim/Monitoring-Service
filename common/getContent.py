from datetime import datetime

from common.converthtml import ConvertHTML

class GetContent:
    def __init__(self, logger) -> None:
        self.logger = logger
        self.converthtml = ConvertHTML()

    def get_Summary_Content(self, now, table):
        result = ''
        try:
            # =============================================================================================
            # DA            
            str_date = datetime.strftime(now,'%Y-%m-%d')
            result = result + self.converthtml.get_h2(f'▶ {str_date} 자산운용사 관련 네이버뉴스 이슈')

            result += self.converthtml.get_h3('- ')   
            result += self.converthtml.get_da_table(table)                            

            result += self.converthtml.get_newline() + self.converthtml.get_newline()

        except Exception as e:
            self.logger.error('html변환 중 에러')
        return result
    
    def get_Summary_Content_nodata(self, now, table):
        result = ''
        try:
            # =============================================================================================
            # DA            
            str_date = datetime.strftime(now,'%Y-%m-%d')
            result = result + self.converthtml.get_h2(f'▶ {str_date} ')

            result += self.converthtml.get_h3('- ')   
            result += self.converthtml.get_da_table(table)                            

            result += self.converthtml.get_newline() + self.converthtml.get_newline()

        except Exception as e:
            self.logger.error('html변환 중 에러')
        return result    