import re
import json
import shlex
import base64
import secrets
import urllib3
import subprocess
from random import *
from datetime import datetime
import defusedxml.ElementTree as ET


class Radiko_Downloader():
    def __init__(self, args):
        self.version = args['version']
        self.station_id = args['station']
        self.areafree = args['areaFree']
        self.timefree = args['timeFree']
        self.startTime = args['startTime']
        self.endTime = args['endTime']
        self.save_path = args['save_path']
        
        self.auth_key = self.get_Full_Key()
        self.user_id = self.get_User_ID()
        self.app, self.device, self.connection = self.get_platform_info()
        
        self.http = urllib3.PoolManager()
    
    def load_json(self, file_path):
        try:
            with open(file_path, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"[Error] Loading JSON file {file_path}: {e}")
            return {}
    
    def get_User_ID(self):
        try:
            return secrets.token_hex(nbytes=16)
        except Exception as e:
            print(f"[Error] Generating user ID: {e}")
            return None
    
    def get_platform_info(self):
        return 'aSmartPhone7o', 'Python.Radiko', 'wifi'
    
    def get_Available_Stations(self) -> list:
        url = "https://radiko.jp/v3/station/region/full.xml"
        try:
            response = self.http.request(method="GET", url=url)
            if response.status == 200:
                return response.data
            else:
                print(f"Failed to load station data. HTTP Status: {response.status}")
                return []
        except Exception as e:
            print(f"[Error] Fetching station data: {e}")
            return []
    
    def get_station_info(self, get_mode='areaID') -> dict:
        try:
            available_stations = self.get_Available_Stations()
            if not available_stations:
                return None
            
            root = ET.fromstring(available_stations)
            
            stations = []
            for station in root.findall(".//station"):
                station_id = station.find("id").text
                name = station.find("name").text

                if get_mode == "areaID":
                    if station_id == self.station_id:
                        area_id = station.find("area_id").text
                        return area_id
                elif get_mode == "stationID":
                    stations.append({"id": station_id, "name": name})

            if get_mode == "stationID":
                return stations

            return None

        except Exception as e:
            print(f"[Error] Getting station info: {e}")
            return None
    
    def get_GPS(self, area_id) -> str:
        try:
            file_path = f'./data/json/area.json'
            COORDINATES_LIST = self.load_json(file_path)
            latitude = COORDINATES_LIST.get(area_id, {}).get('latitude', 0)
            longitude = COORDINATES_LIST.get(area_id, {}).get('longitude', 0)
            
            latitude += random() / 40.0 * (1 if random() > 0.5 else -1)
            longitude += random() / 40.0 * (1 if random() > 0.5 else -1)
            
            return f'{round(latitude, 6)},{round(longitude, 6)},gps'
        except Exception as e:
            print(f"[Error] Getting GPS data for area_id {area_id}: {e}")
        return ''
    
    def get_Full_Key(self) -> str:
        file_path = f'./data/auth/auth_key.bin'
        try:
            with open(file_path, 'rb') as f:
                return base64.b64encode(f.read())
        except Exception as e:
            print(f"[Error] Loading authentication key: {e}")
        return ''
    
    def access_Auth1(self, area_id):
        try:
            if not re.match(r'JP|^[1-47]$', area_id):
                raise TypeError('Invalid Area ID')
            
            url = 'https://radiko.jp/v2/api/auth1'
            headers = {
                'X-Radiko-App': self.app,
                'X-Radiko-App-Version': self.version,
                'X-Radiko-Device': self.device,
                'X-Radiko-User': self.user_id
            }
            
            response = self.http.request(method='GET', url=url, headers=headers)
            return response
        except Exception as e:
            print(f"[Error] During Auth1 request: {e}")
        return None
    
    def access_Partial_Key(self, auth1):
        try:
            auth_key = base64.b64decode(self.auth_key)
            auth_token = auth1.getheader('x-radiko-authtoken')
            key_offset = int(auth1.getheader('x-radiko-keyoffset'))
            key_length = int(auth1.getheader('x-radiko-keylength'))
            
            partial_key = auth_key[key_offset : key_offset + key_length]
            return auth_token, base64.b64encode(partial_key)
        except Exception as e:
            print(f"[Error] Processing partial key: {e}")
        return None, None
    
    def access_Auth2(self, auth_token, coordinate, partial_key):
        try:
            url = 'https://radiko.jp/v2/api/auth2'
            headers = {
                'X-Radiko-App': self.app,
                'X-Radiko-App-Version': self.version,
                'X-Radiko-AuthToken': auth_token,
                'X-Radiko-Connection': self.connection,
                'X-Radiko-Device': self.device,
                'X-Radiko-Location': coordinate,
                'X-Radiko-PartialKey': partial_key,
                'X-Radiko-User': self.user_id
            }
            
            response = self.http.request(method='GET', url=url, headers=headers)
            return response.data.decode('utf-8')
        except Exception as e:
            print(f"[Error] During Auth2 request: {e}")
        return ''
    
    def access_Authentication(self) -> str:
        try:
            area_id = self.get_station_info(get_mode='areaID')
            auth1 = self.access_Auth1(area_id)
            auth_token, partial_key = self.access_Partial_Key(auth1)
            coordinate = self.get_GPS(area_id)
            auth2 = self.access_Auth2(auth_token, coordinate, partial_key)
            
            return auth_token
        except Exception as e:
            print(f"[Error] During authentication process: {e}")
        return ''
    
    def convert_datetime(self, date, mode='strptime'):
        if date:
            try:
                if mode == 'strptime':
                    return datetime.strptime(date, '%Y%m%d%H%M%S')
                elif mode == 'strftime':
                    return date.strftime('%Y%m%d%H%M%S')
            except ValueError:
                print(f"[Warning] Invalid datetime format: {date}")
        return None
    
    def get_program_url(self, selected_station, selected_date):
        if not selected_station:
            print("No station selected.")
            return None

        url = f"https://radiko.jp/v3/program/station/date/{selected_date}/{selected_station}.xml"
            
        return url
    
    def get_program_data(self, selected_station, selected_date, parse_function):
        url = self.get_program_url(selected_station=selected_station, selected_date=selected_date)
        
        try:
            response = self.http.request(method="GET", url=url)
            if response.status == 200:
                parse_function(response.data)
            else:
                print(f"Failed to load data. HTTP Status: {response.status}")
        except Exception as e:
            print(f"Error fetching data: {e}")
        
    
    def get_program_title(self, xml_data):
        root = ET.fromstring(xml_data)
        
        titles = []
        for program in root.findall(".//prog"):
            title = program.find("title").text or "No Title"
            titles.append(title)
        return titles
    
    def get_program_time(self, xml_data, selected_title):
        root = ET.fromstring(xml_data)
        for program in root.findall(".//prog"):
            title = program.find("title").text or "No Title"
            if title == selected_title:
                self.startTime = program.get("ft")
                self.endTime = program.get("to")
                performer = program.find("pfm").text or "No Performer"
                img_url = program.find("img").text
                
                self.startTime = self.convert_datetime(date=self.startTime, mode='strptime')
                self.endTime = self.convert_datetime(date=self.endTime, mode='strptime')
                
                return self.startTime, self.endTime, performer, img_url
            
    def get_program_image(self, img_url):
        img = self.http.request(method="GET", url=img_url).data
        
        return img
    
    def get_Stream_Info(self):
        try:
            auth_token = self.access_Authentication()
            m3u8_url = 'https://radiko.jp/v2/api/ts/playlist.m3u8'
            stream_info = {
                'token': auth_token,
                'url': f'{m3u8_url}?station_id={self.station_id}&l=15'
            }
            
            if self.startTime and self.endTime:
                startTime = self.convert_datetime(date=self.startTime, mode='strftime')
                endTime = self.convert_datetime(date=self.endTime, mode='strftime')
                
                stream_info['url'] += f'&ft={startTime}&to={endTime}'
                
            return stream_info
        except Exception as e:
            print(f"[Error] Getting stream info: {e}")
        return {}
    
    def get_Program_Path(self, cmd_name) -> str:
        try:
            if subprocess.getstatusoutput(f'type {cmd_name}')[0] == 0:
                return subprocess.check_output(f'which {cmd_name}', shell=True).strip().decode('utf8')
            else:
                print(f'{cmd_name} not found , install {cmd_name} ')
                exit()
        except Exception as e:
            print(f"[Error] Getting program path for {cmd_name}: {e}")
        return ''
    
    def get_FFmpeg_Command(self, FFmpeg_program, out_filename) -> str:
        try:
            stream_info = self.get_Stream_Info()
            input_url = stream_info['url']
            auth_token = stream_info['token']
            print(f"URL: '{input_url}'")
            
            if FFmpeg_program == 'ffmpeg':
                program_path = self.get_Program_Path('ffmpeg')
                return f'"{program_path}" -n -headers "X-Radiko-AuthToken: {auth_token}" -i "{input_url}" -threads 8 "{out_filename}"'
            elif FFmpeg_program == 'ffplay':
                program_path = self.get_Program_Path('ffplay')
                return f'{program_path} "{input_url}"'
        except Exception as e:
            print(f"[Error] Generating FFmpeg command: {e}")
        return ''
    
    def save_mp3_file(self):
        try:
            print(f"save_path: '{self.save_path}'")
            
            save_cmd = self.get_FFmpeg_Command(FFmpeg_program='ffmpeg', out_filename=self.save_path)
            save_cmd_split = shlex.split(save_cmd)
            process = subprocess.Popen(save_cmd_split)
            process.communicate()
            
        except Exception as e:
            print(f"[Error] Saving program: {e}")
    
