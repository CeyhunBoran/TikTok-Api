from __future__ import annotations
from ..helpers import extract_video_id_from_url
from typing import TYPE_CHECKING, ClassVar, Iterator, Optional
from datetime import datetime
import requests
from ..exceptions import InvalidResponseException
import json
#new imports
from stem import Signal
from stem.control import Controller
import  time,   random
from urllib.parse import urlencode
import cv2
import base64
import numpy as np
if TYPE_CHECKING:
    from ..tiktok import TikTokApi
    from .user import User
    from .sound import Sound
    from .hashtag import Hashtag
    from .comment import Comment

class PuzzleSolver:
    def __init__(self, base64puzzle, base64piece):
        self.puzzle = base64puzzle
        self.piece = base64piece

    def get_position(self):
        puzzle = self.__background_preprocessing()
        piece = self.__piece_preprocessing()
        matched = cv2.matchTemplate(
            puzzle, 
            piece, 
            cv2.TM_CCOEFF_NORMED
        )
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(matched)
        return max_loc[0]

    def __background_preprocessing(self):
        img = self.__img_to_grayscale(self.piece)
        background = self.__sobel_operator(img)
        return background

    def __piece_preprocessing(self):
        img = self.__img_to_grayscale(self.puzzle)
        template = self.__sobel_operator(img)
        return template

    def __sobel_operator(self, img):
        scale = 1
        delta = 0
        ddepth = cv2.CV_16S

        img = cv2.GaussianBlur(img, (3, 3), 0)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        grad_x = cv2.Sobel(
            gray,
            ddepth,
            1,
            0,
            ksize=3,
            scale=scale,
            delta=delta,
            borderType=cv2.BORDER_DEFAULT,
        )
        grad_y = cv2.Sobel(
            gray,
            ddepth,
            0,
            1,
            ksize=3,
            scale=scale,
            delta=delta,
            borderType=cv2.BORDER_DEFAULT,
        )
        abs_grad_x = cv2.convertScaleAbs(grad_x)
        abs_grad_y = cv2.convertScaleAbs(grad_y)
        grad = cv2.addWeighted(abs_grad_x, 0.5, abs_grad_y, 0.5, 0)

        return grad

    def __img_to_grayscale(self, img):
        return cv2.imdecode(
            self.__string_to_image(img),
            cv2.IMREAD_COLOR
        )

    def __string_to_image(self, base64_string):

        return np.frombuffer(
            base64.b64decode(base64_string),
            dtype='uint8'
        )

class Captcha:
    def __init__(self, params_dict: dict, detail: str):
        self.domain = 'rc-verification-i18n'
        self.params = params_dict
        self.detail = detail
        
        self.__client = requests.Session()
        
    def __params(self):
        params = {
            'lang': 'en',
            'app_name': 'musical_ly',
            'h5_sdk_version': '2.31.2',
            'h5_sdk_use_type': 'cdn',
            'sdk_version': '2.3.3.i18n',
            'iid': self.params['iid'],
            'did': self.params['device_id'],
            'device_id': self.params['device_id'],
            'ch': 'googleplay',
            'aid': '1233',
            'os_type': '0',
            'mode': '',
            'tmp': str(int(time.time())),
            'platform': 'app',
            'webdriver': 'false',
            'verify_host': 'https://rc-verification-i18n.tiktokv.com/',
            'locale': 'fr',
            'channel': 'googleplay',
            'app_key': '',
            'vc': '31.5.3',
            'app_version': '31.5.3',
            'session_id': '',
            'region': 'in',
            'use_native_report': '1',
            'use_jsb_request': '1',
            'orientation': '2',
            'resolution': self.params['resolution'],
            'os_version': self.params['os_version'],
            'device_brand': self.params['device_brand'],
            'device_model': self.params['device_type'],
            'os_name': 'Android',
            'version_code': '3153',
            'device_type': self.params['device_type'],
            'device_platform': 'Android',
            'type': 'verify',
            'detail': self.detail,
            'server_sdk_env': json.dumps({'idc':'useast2a','region':'I18N','server_type':'passport'}, separators=(',', ':')),
            'subtype': 'slide',
            'challenge_code': '3058',
            'triggered_region': 'in',
            'device_redirect_info': ''
        }
        
        return urlencode(params)
    
    def __headers(self):
        return {
            'accept-encoding': 'gzip',
            'x-tt-request-tag': 'n=1;t=0',
            'x-vc-bdturing-sdk-version': '2.3.3.i18n',
            'x-ss-req-ticket': str(int(time.time() * 1000)),
            'x-tt-bypass-dp': '1',
            'content-type': 'application/json; charset=utf-8',
            'x-tt-dm-status': 'login=0;ct=0;rt=7',
            'x-tt-store-region': 'dz',
            'x-tt-store-region-src': 'did',
            'user-agent': 'com.zhiliaoapp.musically/2023105030 (Linux; U; Android 12; fr_FR; SM-G988N; Build/NRD90M;tt-ok/3.12.13.4-tiktok)',
            'host': 'rc-verification-i18n.tiktokv.com',
            'connection': 'Keep-Alive'
        }
    
    def __get_challenge(self):
        params = self.__params()

        p = self.__client.get('https://%s.tiktokv.com/captcha/get?%s' % (self.domain, params),
            headers = self.__headers()).json()
        #print(p)
        return p
    
    def __solve_captcha(self, url_1: str, url_2: str):
        puzzle = base64.b64encode(self.__client.get(url_1).content)
        piece  = base64.b64encode(self.__client.get(url_2).content)
        solver = PuzzleSolver(puzzle, piece)

        time.sleep(1)
        return {
            'maxloc'    : solver.get_position(),
            'randlenght': round(random.random() * (100 - 50) + 5)
        }
        
    def __post_captcha(self, solve: dict) -> dict:
        body = {
            'modified_img_width': 552,
            'id'    : solve['id'],
            'mode'  : 'slide',
            'reply' : list({
                'relative_time': i * solve['randlenght'],
                'x': round(solve['maxloc'] / (solve['randlenght'] / (i + 1))),
                'y': solve['tip']} for i in range(solve['randlenght']))
        }

        return self.__client.post('https://%s.tiktokv.com/captcha/verify?%s' % (self.domain, self.__params()),
            headers = self.__headers(), json = body).json()
    
    def solve_captcha(self):
        __challenge  = self.__get_challenge()
        __captcha_id = __challenge['data']['id']
        __tip_y      = __challenge['data']['question']['tip_y']

        solve = self.__solve_captcha(
            __challenge['data']['question']['url1'],
            __challenge['data']['question']['url2'])
        
        solve.update({
            'id' : __captcha_id,
            'tip': __tip_y})
        
        return self.__post_captcha(solve)
    
class Video:
    """
    A TikTok Video class

    Example Usage
    ```py
    video = api.video(id='7041997751718137094')
    ```
    """

    parent: ClassVar[TikTokApi]

    id: Optional[str]
    """TikTok's ID of the Video"""
    url: Optional[str]
    """The URL of the Video"""
    create_time: Optional[datetime]
    """The creation time of the Video"""
    stats: Optional[dict]
    """TikTok's stats of the Video"""
    author: Optional[User]
    """The User who created the Video"""
    sound: Optional[Sound]
    """The Sound that is associated with the Video"""
    hashtags: Optional[list[Hashtag]]
    """A List of Hashtags on the Video"""
    as_dict: dict
    """The raw data associated with this Video."""

    def __init__(
        self,
        id: Optional[str] = None,
        url: Optional[str] = None,
        data: Optional[dict] = None,
        **kwargs,
    ):
        """
        You must provide the id or a valid url, else this will fail.
        """
        self.id = id
        self.url = url
        if data is not None:
            self.as_dict = data
            self.__extract_from_data()
        elif url is not None:
            i, session = self.parent._get_session(**kwargs)
            self.id = extract_video_id_from_url(
                url,
                headers=session.headers,
                proxy=kwargs.get("proxy")
                if kwargs.get("proxy") is not None
                else session.proxy,
            )

        if getattr(self, "id", None) is None:
            raise TypeError("You must provide id or url parameter.")

    async def info(self, **kwargs) -> dict:
        """
        Returns a dictionary of all data associated with a TikTok Video.

        Note: This is slow since it requires an HTTP request, avoid using this if possible.

        Returns:
            dict: A dictionary of all data associated with a TikTok Video.

        Raises:
            InvalidResponseException: If TikTok returns an invalid response, or one we don't understand.

        Example Usage:
            .. code-block:: python

                url = "https://www.tiktok.com/@davidteathercodes/video/7106686413101468970"
                video_info = await api.video(url=url).info()
        """
        i, session = self.parent._get_session(**kwargs)
        proxy = (
            kwargs.get("proxy") if kwargs.get("proxy") is not None else session.proxy
        )
        if self.url is None:
            raise TypeError("To call video.info() you need to set the video's url.")

        r = requests.get(self.url, headers=session.headers, proxies=proxy)
        
        if 'captcha-us' in r.text:
            print('CAPTCAHA,CAPTCHA,captcha')
            print(r.text)
            with open('fil.txt','a') as writer:
                writer.write(r.text)
        if r.status_code != 200:
            raise InvalidResponseException(
                r.text, "TikTok returned an invalid response.", error_code=r.status_code
            )

        # Try SIGI_STATE first
        # extract tag <script id="SIGI_STATE" type="application/json">{..}</script>
        # extract json in the middle

        start = r.text.find('<script id="SIGI_STATE" type="application/json">')
        if start != -1:
            start += len('<script id="SIGI_STATE" type="application/json">')
            end = r.text.find("</script>", start)

            if end == -1:
                raise InvalidResponseException(
                    r.text, "TikTok returned an invalid response.", error_code=r.status_code
                )

            data = json.loads(r.text[start:end])
            video_info = data["ItemModule"][self.id]
        else:
            # Try __UNIVERSAL_DATA_FOR_REHYDRATION__ next

            # extract tag <script id="__UNIVERSAL_DATA_FOR_REHYDRATION__" type="application/json">{..}</script>
            # extract json in the middle

            start = r.text.find('<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__" type="application/json">')
            if start == -1:
                raise InvalidResponseException(
                    r.text, "TikTok returned an invalid response.", error_code=r.status_code
                )

            start += len('<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__" type="application/json">')
            end = r.text.find("</script>", start)

            if end == -1:
                raise InvalidResponseException(
                    r.text, "TikTok returned an invalid response.", error_code=r.status_code
                )

            data = json.loads(r.text[start:end])
            default_scope = data.get("__DEFAULT_SCOPE__", {})
            video_detail = default_scope.get("webapp.video-detail", {})
            if video_detail.get("statusCode", 0) != 0: # assume 0 if not present
                raise InvalidResponseException(
                    r.text, "TikTok returned an invalid response structure.", error_code=r.status_code
                )
            video_info = video_detail.get("itemInfo", {}).get("itemStruct")
            if video_info is None:
                raise InvalidResponseException(
                    r.text, "TikTok returned an invalid response structure.", error_code=r.status_code
                )
            
        self.as_dict = video_info
        self.__extract_from_data()
        return video_info, r.text

    async def bytes(self, **kwargs) -> bytes:
        """
        Returns the bytes of a TikTok Video.

        TODO:
            Not implemented yet.

        Example Usage:
            .. code-block:: python

                video_bytes = api.video(id='7041997751718137094').bytes()

                # Saving The Video
                with open('saved_video.mp4', 'wb') as output:
                    output.write(video_bytes)
        """

        raise NotImplementedError
        i, session = self.parent._get_session(**kwargs)
        downloadAddr = self.as_dict["video"]["downloadAddr"]

        cookies = await self.parent.get_session_cookies(session)
        cookie_str = "; ".join([f"{k}={v}" for k, v in cookies.items()])

        h = session.headers
        h["cookie"] = cookie_str

        # Fetching the video bytes using a browser fetch within the page context
        file_bytes = await session.page.evaluate(
            """
        async (url, headers) => {
            const response = await fetch(url, { headers });
            if (response.ok) {
                const buffer = await response.arrayBuffer();
                return new Uint8Array(buffer);
            } else {
                return `Error: ${response.statusText}`;  // Return an error message if the fetch fails
            }
        }
        """,
            (downloadAddr, h),
        )

        byte_values = [
            value
            for key, value in sorted(file_bytes.items(), key=lambda item: int(item[0]))
        ]
        return bytes(byte_values)

    def __extract_from_data(self) -> None:
        data = self.as_dict
        self.id = data["id"]

        timestamp = data.get("createTime", None)
        if timestamp is not None:
            try:
                timestamp = int(timestamp)
            except ValueError:
                pass

        self.create_time = datetime.fromtimestamp(timestamp)
        self.stats = data["stats"]

        author = data["author"]
        if isinstance(author, str):
            self.author = self.parent.user(username=author)
        else:
            self.author = self.parent.user(data=author)
        self.sound = self.parent.sound(data=data)

        self.hashtags = [
            self.parent.hashtag(data=hashtag) for hashtag in data.get("challenges", [])
        ]

        if getattr(self, "id", None) is None:
            Video.parent.logger.error(
                f"Failed to create Video with data: {data}\nwhich has keys {data.keys()}"
            )
    ###new tor ip        
    async def new_tor_ip():
        with Controller.from_port(port = 9051) as controller:
            controller.authenticate()
            controller.signal(Signal.NEWNYM)
            controller.close()
    
    async def comments(self, count=20, cursor=0, **kwargs) -> Iterator[Comment]:
        """
        Returns the comments of a TikTok Video.

        Parameters:
            count (int): The amount of comments you want returned.
            cursor (int): The the offset of comments from 0 you want to get.

        Returns:
            async iterator/generator: Yields TikTokApi.comment objects.

        Example Usage
        .. code-block:: python

            async for comment in api.video(id='7041997751718137094').comments():
                # do something
        ```
        """
        error_count = 0
      
        found = 0
        while found < count:
          try:
            params = {
                "aweme_id": self.id,
                "count": 20,
                "cursor": cursor,
            }

            resp = await self.parent.make_request(
                url="https://www.tiktok.com/api/comment/list/",
                params=params,
                headers=kwargs.get("headers"),
                session_index=kwargs.get("session_index"),
            )

            if resp is None:
                raise InvalidResponseException(
                    resp, "TikTok returned an invalid response."
                )
            
            for video in resp.get("comments", []):
                yield self.parent.comment(data=video)
                found += 1
            
                
            if not resp.get("has_more", False):
                return
            
            cursor = resp.get("cursor")
          except Exception as e:
            if error_count < 3:
               device = {'Cookies': {'install_id': '7284359982429800197', 'store-country-code': 'pa', 'store-country-code-src': 'did', 'store-idc': 'maliva', 'ttreq': '1$cb3fec43d1e03b8a752f6f12ec90eafeb5c38e9e'}, 'Device_Info': {'ab_version': '31.5.1', 'ac': 'wifi', 'ac2': 'wifi', 'aid': '1233', 'app_language': 'en', 'app_name': 'musical_ly', 'app_type': 'normal', 'build_number': '31.5.1', 'carrier_region': 'PA', 'cdid': '710569ab-29a3-4e3b-9d4c-0725d1dffa24', 'channel': 'googleplay', 'device_brand': 'PANASONIC_WA0EC', 'device_id': '7284359569500014085', 'device_platform': 'android', 'device_type': 'panasonic', 'dpi': '240', 'host_abi': 'armeabi-v7a', 'iid': '7284359982429800197', 'language': 'en', 'locale': 'en', 'manifest_version_code': '2023105010', 'mcc_mnc': '7142', 'okhttp_version': '4.2.152.12-tiktok', 'op_region': 'PA', 'openudid': '25b89230286e26cc', 'os': 'android', 'os_api': '31', 'os_version': '12', 'passport-sdk-version': '19', 'region': 'PA', 'resolution': '720*1280', 'ssmix': 'a', 'support_webview': '1', 'sys_region': 'PA', 'timezone_name': 'America/Panama', 'timezone_offset': -18000, 'uoo': '0', 'update_version_code': '2023105010', 'use_store_region_cookie': '1', 'version_code': '310501', 'version_name': '31.5.1'}, 'Ri_Report': True, 'Seed_Algorithm': 6, 'Seed_Token': 'MDGnGJ7SrXMAIj91yWozx4nsnuZyTnF8AzR4ovcLT0iHKkvRF2Y8HFV5FRqxNQKm2egOIADEwBCTvw7OUKfxVVORwzDaVuMAf9hnmhRGuDRr+cgcFrqz9SpEMHmL7tbMA/E=', 'is_activated': 'success', 'secDeviceIdToken': 'ApwszCTXxL-5QyiIiw3qIMW_7'}
               captcha = Captcha(device['Device_Info'], 'dzLcZ0u2MHJowbiidnJ5cHQRP3YkMbobGtH1kA2*MBK1Fm*bIsNzbrwXvYN6hklSYvSA2-QAgk6JxxFbUa1G2bPWS-dQ9QOZIG-rkhlrE06Ox0cJ*6cUrZV8wnQfh5TYRMMN1SAMOPKdXPsSmN6GSZWBsLnq68*7Yo9jWx4-NEu6HlL2o-w8spMl*1oeQsnX7qcAPtYqK8FZFLThN0JIJ4uv5DxnBbm9vvQiL36dT1db-Wqw9-89BIopYUqhk29rWnYA5gqkFihs3hg1xctCchUIoc8x0VoZVFVpQeEJMzivuymsVlAYA4MXSIaRlU*0txaaG7fqVEOtpUnKK8byysJrExOuVe4hgok7vMLVSTNiQuKu4WOCLopO9HeYXQCr3-7vroicxSnFxDfRQF1LxNX7MfPCXFSaiomy87zKn24PveRgTYOVSZ7LDcFf')
               print(captcha.solve_captcha())
               error_count += 1
            else:
               raise e    
      
    async def related_videos(
        self, count: int = 30, cursor: int = 0, **kwargs
    ) -> Iterator[Video]:
        """
        Returns related videos of a TikTok Video.

        Parameters:
            count (int): The amount of comments you want returned.
            cursor (int): The the offset of comments from 0 you want to get.

        Returns:
            async iterator/generator: Yields TikTokApi.video objects.

        Example Usage
        .. code-block:: python

            async for related_videos in api.video(id='7041997751718137094').related_videos():
                # do something
        ```
        """
        found = 0
        while found < count:
            params = {
                "itemID": self.id,
                "count": 16,
            }

            resp = await self.parent.make_request(
                url="https://www.tiktok.com/api/related/item_list/",
                params=params,
                headers=kwargs.get("headers"),
                session_index=kwargs.get("session_index"),
            )

            if resp is None:
                raise InvalidResponseException(
                    resp, "TikTok returned an invalid response."
                )

            for video in resp.get("itemList", []):
                yield self.parent.video(data=video)
                found += 1

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return f"TikTokApi.video(id='{getattr(self, 'id', None)}')"
