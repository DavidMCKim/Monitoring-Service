from common.logs import CloudLogging, GetErrorMessage
from common.secret_manager import Secret_Manager
from time import sleep
from datetime import datetime, timedelta
import os
import sys
import database.social_api as social_api
import configparser
import socket
import json

config = configparser.ConfigParser()
# config.read('./config.ini', encoding='utf8')
config.read('D:\\Project\\5_TousFlux_2.0\\tousflux_v2_social_crawler\\config.ini', encoding='utf8')
        
container_name = socket.gethostname()

#  서버에 할당된 정보 조회
server_info = social_api.GetServerInfo(container_name)
channel_code = server_info[0]
server_os = server_info[1]

crawlCycle = True

def StartCrawlSchedule(crawlCycle):
    """ 스케줄 조회 """
    try:
        while crawlCycle:
            try:
                global channel_code
                # vm인지 로컬 환경인지 구분
                if channel_code == '-2':
                    raise Exception(f"{container_name}가 DB 서버 정보 조회에 실패하였습니다")
                elif channel_code == '-1':
                    tmp_cloud_logger = CloudLogging('vm')
                    tmp_cloud_logger.Error(file_path=os.path.abspath(__file__), function_name=sys._getframe().f_code.co_name, message=f"컨테이너 : {container_name} >> grpc 서버의 오류", status="Cotainer Failed Get Server Info", channelname='main')
                elif server_os == 'local':
                    server = 'local'
                else:
                    server = 'vm'

                # 로그 정보 세팅
                cloud_logger = CloudLogging(server)
                # 스케줄 조회   
                if container_name in config['indicator'][server_os]: 
                    channel_codes = channel_code.split(',')
                    current_date = datetime.now() # 현재 날짜와 시간 가져오기
                    three_days_ago = current_date - timedelta(days=3) # 3일 전의 날짜 계산

                    # 날짜를 특정한 형식으로 포맷팅
                    current_date = current_date.strftime("%Y%m%d")
                    three_days_ago = three_days_ago.strftime("%Y%m%d")
                    
                    for channel_code in channel_codes:            
                        if container_name in [config['indicator_server']['1'], config['indicator_server']['2'], config['indicator_server']['dcinside']]:
                            if channel_code == '1002':
                                cafe_range = 6
                                odd_cafes = [config.get("cafe_name", str(i)) for i in range(1, cafe_range + 1) if i % 2 != 0]
                                even_cafes = [config.get("cafe_name", str(i)) for i in range(1, cafe_range + 1) if i % 2 == 0]
                                 
                                if container_name == config['indicator_server']['1']: scrap_name_str = odd_cafes
                                else: scrap_name_str = even_cafes
                                
                                for cafe_str in range(0,int(len(scrap_name_str))):
                                    cafe_cnt = int(cafe_str) + 1
                                    three_days_ago, urls_data_3 = social_api.SocialRecrawl_3Day(channel_code, three_days_ago, scrap_name_str[cafe_str])
                                    if (three_days_ago != None) and (urls_data_3 != None) and (len(urls_data_3) > 0):
                                        IndicatorsChannel(3, server, channel_code, three_days_ago, urls_data_3, cloud_logger, social_api, container_name, scrap_name_str[cafe_str], cafe_cnt)
                            else:
                                three_days_ago, urls_data_3 = social_api.SocialRecrawl_3Day(channel_code, three_days_ago)
                                if (three_days_ago != None) and (urls_data_3 != None) and (len(urls_data_3) > 0):
                                    IndicatorsChannel(3, server, channel_code, three_days_ago, urls_data_3, cloud_logger, social_api, container_name)            
                    
                                    
                        # 과거 돌리기용
                        if container_name == config['indicator_server']['test']:
                            for past_days_ago in range(20231217,20231223):
                                past_days_ago = str(past_days_ago)
                                past_days_ago, urls_data_3 = social_api.Social_Recrawl_3Day_Past(channel_code, past_days_ago)
                                if (past_days_ago != None) and (urls_data_3 != None) and (len(urls_data_3) > 0):
                                    IndicatorsChannel(3, server, channel_code, past_days_ago, urls_data_3, cloud_logger, social_api, container_name)
                                
                    crawlCycle = False
                else:
                    schedule = social_api.GetSchedule(channel_code)
                    if schedule['channel_code'] != -1:
                        scrap_result, success_count, error_count = ProcessChannel(server, schedule['channel_code'], schedule['channel_name'], schedule['channel_type'], schedule['channel_category'],
                            schedule['scrap_category'], schedule['scrap_name'], schedule['channel_url'], schedule['crawl_start_date'], schedule['crawl_end_date'], cloud_logger, schedule['job_status'], social_api, container_name)
                        
                        update_result = social_api.UpdateSchedule(schedule['idx'], scrap_result, success_count, error_count)
                        cloud_logger.Info(file_path=os.path.abspath(__file__), function_name=sys._getframe().f_code.co_name, message=f"수집 완료 [{schedule['channel_code']}] - [{schedule['channel_name']}] - [{schedule['scrap_category']} / {schedule['scrap_name']}]", status=f"[ SUC : {success_count} / ERR : {error_count} ]", channelname=schedule['channel_name'])
                    else:
                        sleep(60)
            except Exception as e:
                e = str(e)
                if 'DB 서버 정보 조회' in e:
                    cloud_logger.Alert(file_path=os.path.abspath(__file__), function_name=sys._getframe().f_code.co_name, message=f"컨테이너 : {container_name}이 오류로 인하여 종료되었습니다", status="Container ShutDown", channelname='main')
                    crawlCycle = False
                else:
                    cloud_logger.Error(file_path=os.path.abspath(__file__), function_name=sys._getframe().f_code.co_name, message=f"Main Code Error", status=e, channelname=schedule.channel_name)
                    # 실행 중 오류가 발생한 건은 'v'로 update
                    social_api.UpdateSchedule(schedule['idx'], 'V', 0, 0)
    except Exception as e:
        pass


def ProcessChannel(server, channel_code, channel_name, channel_type, channel_category, scrap_category, scrap_name, channel_url, crawl_start_date, crawl_end_date, cloud_logger, job_status, social_api, container_name):
    """ 채널코드에 맞춰 Url Scrap 로직 실행 """
    scrap_count = 0
    success_count = 0
    error_count = 0
    channel_code = int(channel_code)
    try:
        # 수집 시작 로그
        cloud_logger.Info(file_path=os.path.abspath(__file__), function_name=sys._getframe().f_code.co_name, message=f"수집 시작 [{channel_code}] - [{channel_name}] - [{scrap_category} / {scrap_name}]", status=f"{channel_name} 수집 시작", channelname = channel_name)
        
        # navernews
        if channel_code == 1000:
            from channel.navernews import NaverNews
            navernews = NaverNews(cloud_logger, channel_code, channel_name, channel_type, channel_category, scrap_category, channel_url, crawl_start_date, crawl_end_date, job_status, social_api, container_name)
            navernews.NaverNews_Crawl()
            scrap_count = navernews.insert_count
            success_count = navernews.success_count
            error_count = navernews.error_count
        # naverblog
        elif channel_code == 1004:
            from channel.naverblog import NaverBlog
            naverblog = NaverBlog(cloud_logger, channel_code, channel_name, channel_type, channel_category, scrap_category, scrap_name, channel_url, crawl_start_date, crawl_end_date, job_status, social_api, container_name)
            naverblog.NaverBlog_Crawl()
            scrap_count = naverblog.insert_count
            success_count = naverblog.success_count
            error_count = naverblog.error_count
        # ppomppu
        elif channel_code == 2000:
            from channel.ppomppu import Ppomppu
            ppomppu = Ppomppu(cloud_logger, channel_code, channel_name, channel_type, channel_category, scrap_category, scrap_name, channel_url, crawl_start_date, crawl_end_date, job_status, social_api, container_name)
            ppomppu.Ppomppu_Crawl()
            scrap_count = ppomppu.insert_count
            success_count = ppomppu.success_count
            error_count = ppomppu.error_count
        # clien
        elif channel_code == 2001:
            from channel.clien import Clien
            clien = Clien(cloud_logger, channel_code, channel_name, channel_type, channel_category, scrap_category, scrap_name, channel_url, crawl_start_date, crawl_end_date, job_status, social_api, container_name)
            clien.Clien_Crawl()
            scrap_count = clien.insert_count
            success_count = clien.success_count
            error_count = clien.error_count
        # dcinside
        elif channel_code == 2003:
            from channel.dcinside import Dcinside
            dcinside = Dcinside(cloud_logger, channel_code, channel_name, channel_type, scrap_category, scrap_name, channel_url, crawl_start_date, crawl_end_date, job_status, social_api, container_name)
            dcinside.DcInside_Crawl()
            scrap_count = dcinside.insert_count
            success_count = dcinside.success_count
            error_count = dcinside.error_count
        # ruliweb
        elif channel_code == 2012:
            from channel.ruliweb import Ruliweb
            ruliweb = Ruliweb(cloud_logger, channel_code, channel_name, channel_type, channel_category, scrap_category, scrap_name, channel_url, crawl_start_date, crawl_end_date, job_status, social_api, container_name)
            ruliweb.Ruliweb_Crawl()
            scrap_count = ruliweb.insert_count
            success_count = ruliweb.success_count
            error_count = ruliweb.error_count
        # natepann
        elif channel_code == 2015:
            from channel.natepann import NatePann
            natepann = NatePann(cloud_logger, channel_code, channel_name, channel_type, channel_category, scrap_category, channel_url, crawl_start_date, crawl_end_date, job_status, social_api, container_name)
            natepann.NatePann_Crawl()
            scrap_count = natepann.insert_count
            success_count = natepann.success_count
            error_count = natepann.error_count
        # youtube
        elif channel_code == 4003:
            from channel.youtube import Youtube
            # SecretManager로 유튜브 developer key 가져와서 전달            
            youtube_secret_id = 'youtube'
            tmp_token = Secret_Manager(server, cloud_logger, youtube_secret_id)
            tmp_token.SecretManager()

            token = tmp_token.token
            
            if len(token) > 0:
                config = configparser.ConfigParser()
                config.read('./config.ini', encoding='utf-8')        
                category_list = config["YOUTUBECATEGORY"]
                youtube = Youtube(cloud_logger, channel_code, channel_name, channel_type, channel_category, scrap_category, scrap_name, channel_url, crawl_start_date, crawl_end_date, token, category_list, job_status, social_api, container_name)
                youtube.Youtube_Crawl()
                scrap_count = youtube.insert_count
                success_count = youtube.success_count
                error_count = youtube.error_count
            else:
                job_status = "E"
        # navercafe
        elif channel_code == 1002:
            from channel.navercafe import NaverCafe
            navercafe = NaverCafe(cloud_logger, channel_code, channel_name, channel_type, channel_category, scrap_category, scrap_name, channel_url, crawl_start_date, crawl_end_date, job_status, social_api, container_name)
            navercafe.NaverCafe_Crawl()
            scrap_count = navercafe.insert_count
            success_count = navercafe.success_count
            error_count = navercafe.error_count
        # instagram
        elif channel_code in [ 4000 ]:
            # instagram
            if channel_code == 4000:
                from channel.instagram import Instagram
                # from channel.instagram_api import InstagramAPI
                instagram = Instagram(cloud_logger, channel_code, channel_name, channel_type, channel_category, scrap_category, scrap_name, channel_url, crawl_start_date, crawl_end_date, job_status, social_api, container_name, container_name)
                instagram.Instagram_Crawl()
                scrap_count = instagram.insert_count
                success_count = instagram.success_count
                error_count = instagram.error_count

    except Exception as e:
        scrap_count = -1
        exc_type, exc_obj, tb = sys.exc_info()
        error_message = GetErrorMessage(exc_obj, tb)
        cloud_logger.Error(file_path=os.path.abspath(__file__), function_name=sys._getframe().f_code.co_name, message=error_message, status=e, channelname = channel_name)
    
    finally:
        if success_count > 0:
            job_status = "Y"
        elif success_count == 0 and scrap_count != -1:
            job_status = "D"
        elif scrap_count < 0:
            job_status = "E"

    return job_status, success_count, error_count


def IndicatorsChannel(day_ago, server, channel_code, days_ago, urls_data, cloud_logger, social_api, container_name, scrap_name_str=None, cafe_cnt=999):
    try:
        # GCS 버킷명 설정
        # if day_ago == 1:   bucket_nm = 'tousflux_v2_social_recrawl_1day'
        # elif day_ago == 2: bucket_nm = 'tousflux_v2_social_recrawl_2day'
        # elif day_ago == 3: bucket_nm = 'tousflux_v2_social_recrawl_3day'
        bucket_nm = 'tousflux_v2_social_recrawl_3day'
        
        # 채널명 변수 할당
        global config
        channel_name = config['channel_name'][str(channel_code)]
        channel_code = int(channel_code)
        
        # 지표 재수집
        if channel_code == 1002:
            cloud_logger.Info(file_path=os.path.abspath(__file__), function_name=sys._getframe().f_code.co_name, message=f"{container_name}-지수 재수집 시작 [{channel_code}] - [{channel_name}] - [카페 채널명 : {scrap_name_str}] - [{len(urls_data['Idx'])} 건] - [{bucket_nm}] - [{days_ago}]", status=f"{channel_name} 지수 재수집 시작", channelname = channel_name)
            if cafe_cnt == 999:
                cloud_logger.Info(file_path=os.path.abspath(__file__), function_name=sys._getframe().f_code.co_name, message=f"{container_name}-지수 재수집 시작 [{channel_code}] - [{channel_name}] - [{len(urls_data['Idx'])} 건] - [{bucket_nm}] - [{days_ago}]", status=f"{channel_name} 지수 재수집 시작", channelname = channel_name)
        else:    
            cloud_logger.Info(file_path=os.path.abspath(__file__), function_name=sys._getframe().f_code.co_name, message=f"{container_name}-지수 재수집 시작 [{channel_code}] - [{channel_name}] - [{len(urls_data['Idx'])} 건] - [{bucket_nm}] - [{days_ago}]", status=f"{channel_name} 지수 재수집 시작", channelname = channel_name)
        # cloud_logger.Info(file_path=os.path.abspath(__file__), function_name=sys._getframe().f_code.co_name, message=f"{container_name}-지수 재수집 시작 [{channel_code}] - [{channel_name}] - [{len(urls_data['Idx'])} 건] - [{bucket_nm}] - [{days_ago}]", status=f"{channel_name} 지수 재수집 시작", channelname = channel_name)

        # navernews
        if channel_code == 1000:
            from channel.navernews import NaverNews
            navernews = NaverNews(cloud_logger, channel_code, channel_name, None, None, None, None, '2022-01-01 00:00:00', '2022-01-01 23:59:59', None, social_api, container_name)
            for idx in range(len(urls_data['Idx'])):
                navernews.NaverNews_Get_Comments(None, None, None, 'Y', urls_data['Idx'][str(idx)], urls_data['Url'][str(idx)])
            navernews.Indicators_Json(days_ago, bucket_nm)
            scrap_count = navernews.success_count + navernews.error_count
            success_count = navernews.success_count
            error_count = navernews.error_count
            cloud_logger.Info(file_path=os.path.abspath(__file__), function_name=sys._getframe().f_code.co_name, message=f'{container_name}-지수 재수집 완료 [{channel_code}] - [{channel_name}] - [{bucket_nm}] - [{days_ago}] :: 총건수 : {scrap_count}  /  성공건수 : {success_count}  /  실패건수 : {error_count}', status='지수 업데이트', channelname = channel_name)
        # naverblog
        elif channel_code == 1004:
            from channel.naverblog import NaverBlog
            naverblog = NaverBlog(cloud_logger, channel_code, channel_name, None, None, None, None, '2022-01-01 00:00:00', '2022-01-01 23:59:59', None, None, social_api, container_name)
            for idx in range(len(urls_data['Idx'])):
                naverblog.Indicators(None, None, 'Y', urls_data['Idx'][str(idx)], urls_data['Url'][str(idx)])
            naverblog.Indicators_Json(days_ago, bucket_nm)
            scrap_count = naverblog.success_count + naverblog.error_count
            success_count = naverblog.success_count
            error_count = naverblog.error_count
            cloud_logger.Info(file_path=os.path.abspath(__file__), function_name=sys._getframe().f_code.co_name, message=f'{container_name}-지수 재수집 완료 [{channel_code}] - [{channel_name}] - [{bucket_nm}] - [{days_ago}] :: 총건수 : {scrap_count}  /  성공건수 : {success_count}  /  실패건수 : {error_count}', status='지수 업데이트', channelname = channel_name)
        # ppomppu
        elif channel_code == 2000:
            from channel.ppomppu import Ppomppu
            ppomppu = Ppomppu(cloud_logger, channel_code, channel_name, None, None, None, None, None, '2022-01-01 00:00:00', '2022-01-01 23:59:59', None, social_api, container_name)
            for idx in range(len(urls_data['Idx'])):
                ppomppu.Ppomppu_Get_Contents(None, None, None, None, 'Y', urls_data['Idx'][str(idx)], urls_data['Url'][str(idx)])
            ppomppu.Indicators_Json(days_ago, bucket_nm)
            scrap_count = ppomppu.success_count + ppomppu.error_count
            success_count = ppomppu.success_count
            error_count = ppomppu.error_count
            cloud_logger.Info(file_path=os.path.abspath(__file__), function_name=sys._getframe().f_code.co_name, message=f'{container_name}-지수 재수집 완료 [{channel_code}] - [{channel_name}] - [{bucket_nm}] - [{days_ago}] :: 총건수 : {scrap_count}  /  성공건수 : {success_count}  /  실패건수 : {error_count}', status='지수 업데이트', channelname = channel_name)
        # clien
        elif channel_code == 2001:
            from channel.clien import Clien
            clien = Clien(cloud_logger, channel_code, channel_name, None, None, None, None, None, '2022-01-01 00:00:00', '2022-01-01 23:59:59', None, social_api, container_name)
            for idx in range(len(urls_data['Idx'])):
                clien.Clien_Get_Contents(None, 'Y', urls_data['Idx'][str(idx)], urls_data['Url'][str(idx)])
            clien.Indicators_Json(days_ago, bucket_nm)
            scrap_count = clien.success_count + clien.error_count
            success_count = clien.success_count
            error_count = clien.error_count
            cloud_logger.Info(file_path=os.path.abspath(__file__), function_name=sys._getframe().f_code.co_name, message=f'{container_name}-지수 재수집 완료 [{channel_code}] - [{channel_name}] - [{bucket_nm}] - [{days_ago}] :: 총건수 : {scrap_count}  /  성공건수 : {success_count}  /  실패건수 : {error_count}', status='지수 업데이트', channelname = channel_name)
        # dcinside
        elif channel_code == 2003:
            from channel.dcinside import Dcinside
            dcinside = Dcinside(cloud_logger, channel_code, channel_name, None, None, None, None, '2022-01-01 00:00:00', '2022-01-01 23:59:59', None, social_api, container_name)
            for idx in range(len(urls_data['Idx'])):
                dcinside.DcInside_Get_Content(None, 'Y', urls_data['Idx'][str(idx)], urls_data['Url'][str(idx)])
            dcinside.Indicators_Json(days_ago, bucket_nm)
            scrap_count = dcinside.success_count + dcinside.error_count
            success_count = dcinside.success_count
            error_count = dcinside.error_count
            cloud_logger.Info(file_path=os.path.abspath(__file__), function_name=sys._getframe().f_code.co_name, message=f'{container_name}-지수 재수집 완료 [{channel_code}] - [{channel_name}] - [{bucket_nm}] - [{days_ago}] :: 총건수 : {scrap_count}  /  성공건수 : {success_count}  /  실패건수 : {error_count}', status='지수 업데이트', channelname = channel_name)
        # ruliweb
        elif channel_code == 2012:
            pass
        # natepann
        elif channel_code == 2015:
            from channel.natepann import NatePann
            natepann = NatePann(cloud_logger, channel_code, channel_name, None, None, None, None, '2022-01-01 00:00:00', '2022-01-01 23:59:59', None, social_api, container_name)
            for idx in range(len(urls_data['Idx'])):
                natepann.NatePann_Get_Content(None, 'Y', urls_data['Idx'][str(idx)], urls_data['Url'][str(idx)])
            natepann.Indicators_Json(days_ago, bucket_nm)
            scrap_count = natepann.success_count + natepann.error_count
            success_count = natepann.success_count
            error_count = natepann.error_count
            cloud_logger.Info(file_path=os.path.abspath(__file__), function_name=sys._getframe().f_code.co_name, message=f'{container_name}-지수 재수집 완료 [{channel_code}] - [{channel_name}] - [{bucket_nm}] - [{days_ago}] :: 총건수 : {scrap_count}  /  성공건수 : {success_count}  /  실패건수 : {error_count}', status='지수 업데이트', channelname = channel_name)
        # youtube
        elif channel_code == 4003:
            from channel.youtube import Youtube
            # SecretManager로 유튜브 developer key 가져와서 전달            
            youtube_secret_id = 'youtube'
            tmp_token = Secret_Manager(server, cloud_logger, youtube_secret_id)
            tmp_token.SecretManager()

            token = tmp_token.token
            
            if len(token) > 0:
                config = configparser.ConfigParser()
                config.read('./config.ini', encoding='utf-8')        
                category_list = config["YOUTUBECATEGORY"]
                youtube = Youtube(cloud_logger, channel_code, channel_name, None, None, None, None, None, '2022-01-01 00:00:00', '2022-01-01 23:59:59', token, None, None, social_api, container_name)
                for idx in range(len(urls_data['Idx'])):
                    youtube.Youtube_Crawl_Info(None, 'Y', urls_data['Idx'][str(idx)], urls_data['Url'][str(idx)])
                youtube.Indicators_Json(days_ago, bucket_nm)
                scrap_count = youtube.success_count + youtube.error_count
                success_count = youtube.success_count
                error_count = youtube.error_count
                cloud_logger.Info(file_path=os.path.abspath(__file__), function_name=sys._getframe().f_code.co_name, message=f'{container_name}-지수 재수집 완료 [{channel_code}] - [{channel_name}] - [{bucket_nm}] - [{days_ago}] :: 총건수 : {scrap_count}  /  성공건수 : {success_count}  /  실패건수 : {error_count}', status='지수 업데이트', channelname = channel_name)
        # navercafe
        elif channel_code == 1002:
            if container_name == config['indicator_server']['test']:
                _, result_data = social_api.GetAccountInfo(channel_code, config['indicator_server']['3'])
            else:
                _, result_data = social_api.GetAccountInfo(channel_code, container_name)
            result_data = json.loads(result_data)
            if len(result_data) > 0 and result_data != None:
                from channel.navercafe import NaverCafe
                navercafe = NaverCafe(cloud_logger, channel_code, channel_name, None, None, None, None, None, '2022-01-01 00:00:00', '2022-01-01 23:59:59', None, social_api, container_name)
                navercafe.NaverCafe_Indicators(urls_data, result_data)
                cafe_scrap_nm = f'{scrap_name_str}'
                if container_name == config['indicator_server']['test']:
                    # 과거수집
                    navercafe.Indicators_Json(days_ago, bucket_nm)
                else:
                    navercafe.Indicators_Json(days_ago, bucket_nm, cafe_scrap_nm)
                scrap_count = navercafe.success_count + navercafe.error_count
                success_count = navercafe.success_count
                error_count = navercafe.error_count
                if cafe_cnt == 999:
                    cloud_logger.Info(file_path=os.path.abspath(__file__), function_name=sys._getframe().f_code.co_name, message=f'{container_name}-지수 재수집 완료 [{channel_code}] - [{channel_name}] - [{bucket_nm}] - [{days_ago}] :: 총건수 : {scrap_count}  /  성공건수 : {success_count}  /  실패건수 : {error_count}', status='지수 업데이트', channelname = channel_name)
                else:
                    cloud_logger.Info(file_path=os.path.abspath(__file__), function_name=sys._getframe().f_code.co_name, message=f'{container_name}-지수 재수집 완료 [{channel_code}] - [{channel_name}] - [카페 채널명 {cafe_cnt} : {scrap_name_str}] - [{bucket_nm}] - [{days_ago}] :: 총건수 : {scrap_count}  /  성공건수 : {success_count}  /  실패건수 : {error_count}', status='지수 업데이트', channelname = channel_name)
        # instagram
        elif channel_code in [ 4000 ]:
            # instagram
            if channel_code == 4000:
                pass

    except Exception as e:
        scrap_count = -1
        exc_type, exc_obj, tb = sys.exc_info()
        error_message = GetErrorMessage(exc_obj, tb)
        cloud_logger.Error(file_path=os.path.abspath(__file__), function_name=sys._getframe().f_code.co_name, message=error_message, status=e, channelname = channel_name)
    



if __name__ == "__main__":
    StartCrawlSchedule(crawlCycle)

