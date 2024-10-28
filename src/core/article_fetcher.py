import httpx
from loguru import logger
import time
from typing import Dict
import json

class ArticleFetcher:
    def __init__(self, account_data: Dict):
        self.base_url = "https://mp.toutiao.com"
        self.account_data = account_data
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Origin": "https://mp.toutiao.com",
            "Referer": "https://mp.toutiao.com/profile_v4/graphic/articles",
            "Content-Type": "application/json;charset=UTF-8"
        }
        
    async def fetch_articles(self, page: int = 1, page_size: int = 20) -> Dict:
        """获取文章列表"""
        try:
            # 构建请求参数
            params = {
                "status": "published",
                "start_time": 0,
                "end_time": int(time.time()),
                "page": page,
                "page_size": page_size,
                "_signature": ""
            }
            
            logger.debug(f"Fetching articles with params: {params}")
            
            # 添加cookie到headers
            cookies = self.account_data.get("cookies", {})
            cookie_str = "; ".join([f"{k}={v}" for k, v in cookies.items()])
            
            async with httpx.AsyncClient(headers={**self.headers, "Cookie": cookie_str}) as client:
                url = f"{self.base_url}/api/article/article_list"
                response = await client.get(url, params=params)
                
                logger.debug(f"Response status: {response.status_code}")
                logger.debug(f"Response text: {response.text}")
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get("message") == "success":
                        return {
                            "articles": result["data"]["articles"],
                            "total": result["data"]["total"],
                            "has_more": result["data"]["has_more"]
                        }
                    else:
                        raise Exception(f"API返回错误: {result.get('message')}")
                else:
                    raise Exception(f"请求失败: {response.status_code}")
                    
        except Exception as e:
            logger.error(f"获取文章列表失败: {str(e)}")
            raise