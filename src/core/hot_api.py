import httpx
from loguru import logger
import asyncio
from typing import List, Dict
import json
from pathlib import Path
import time
import urllib.parse

class HotAPI:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9",
        }
        self.cache_dir = Path("data/cache/hot")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
    async def _request(self, url: str, headers: Dict = None, params: Dict = None) -> Dict:
        """统一的请求方法"""
        try:
            _headers = self.headers.copy()
            if headers:
                _headers.update(headers)
                
            async with httpx.AsyncClient(headers=_headers, timeout=30.0) as client:
                response = await client.get(url, params=params, follow_redirects=True)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"请求失败 {url}: {str(e)}")
            return None

    async def get_toutiao_hot(self, api_source: str = '自动切换') -> List[Dict]:
        """获取头条热榜"""
        try:
            url = "https://www.toutiao.com/hot-event/hot-board/"
            headers = {
                "Referer": "https://www.toutiao.com/",
                "Cookie": "tt_webid=123456789"  # 随机Cookie
            }
            params = {"origin": "toutiao_pc"}
            
            data = await self._request(url, headers=headers, params=params)
            if data and "data" in data:
                hot_list = []
                for item in data["data"]:
                    hot_list.append({
                        "title": item.get("Title", ""),
                        "url": item.get("Url", ""),
                        "hot": item.get("HotValue", ""),
                        "rank": len(hot_list) + 1,
                        "tag": item.get("Label", ""),
                        "time": time.strftime("%Y-%m-%d %H:%M:%S")
                    })
                
                if hot_list:
                    self.cache_hot_list("toutiao", hot_list)
                    return hot_list
                    
            logger.error("获取头条热榜数据为空")
            return self.get_cached_hot_list("toutiao")
                    
        except Exception as e:
            logger.error(f"获取头条热榜异常: {str(e)}")
            return self.get_cached_hot_list("toutiao")

    # 其他平台的方法保持不变...
    async def get_weibo_hot(self, api_source: str = '自动切换') -> List[Dict]:
        """获取微博热搜"""
        apis = {
            'vvhan': {
                "url": "https://api.vvhan.com/api/hotlist",
                "params": {"type": "wbhot"},
                "parser": self._parse_vvhan
            },
            'oioweb': {
                "url": "https://api.oioweb.cn/api/common/HotList",
                "params": {"type": "weibo"},
                "parser": self._parse_oioweb
            }
        }
        
        if api_source == '自动切换':
            sources = list(apis.values())
        else:
            sources = [apis.get(api_source.lower(), apis['vvhan'])]
            
        for api in sources:
            try:
                data = await self._request(api["url"], params=api["params"])
                if data:
                    hot_list = api["parser"](data)
                    if hot_list:
                        self.cache_hot_list("weibo", hot_list)
                        return hot_list
            except Exception as e:
                logger.error(f"微博热搜 API 失败: {str(e)}")
                continue
                
        return self.get_cached_hot_list("weibo")

    # ... 其他方法保持不变 ...

    async def get_hot_list(self, platform: str, api_source: str = '自动切换') -> List[Dict]:
        """获取指定平台的热榜"""
        platform = platform.lower()
        if platform == "头条":
            return await self.get_toutiao_hot(api_source)
        elif platform == "微博":
            return await self.get_weibo_hot(api_source)
        elif platform == "知乎":
            return await self.get_zhihu_hot(api_source)
        elif platform == "b站":
            return await self.get_bilibili_hot(api_source)
        else:
            logger.error(f"不支持的平台: {platform}")
            return []
            
    def cache_hot_list(self, platform: str, hot_list: List[Dict]):
        """缓存热榜数据"""
        try:
            cache_file = self.cache_dir / f"{platform}.json"
            cache_data = {
                "timestamp": int(time.time()),
                "data": hot_list
            }
            
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logger.error(f"缓存热榜数据失败: {str(e)}")
            
    def get_cached_hot_list(self, platform: str) -> List[Dict]:
        """获取缓存的热榜数据"""
        try:
            cache_file = self.cache_dir / f"{platform}.json"
            if not cache_file.exists():
                return []
                
            with open(cache_file, "r", encoding="utf-8") as f:
                cache_data = json.load(f)
                
            # 检查缓存是否过期（5分钟）
            if int(time.time()) - cache_data.get("timestamp", 0) > 300:
                return []
                
            return cache_data.get("data", [])
            
        except Exception as e:
            logger.error(f"获取缓存热榜数据失败: {str(e)}")
            return []