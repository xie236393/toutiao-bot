import aiohttp
from loguru import logger
from datetime import datetime
import json
import asyncio

class ArticleFetcher:
    def __init__(self, token: str):
        self.token = token
        self.base_url = "https://mp.toutiao.com/mp/agw/article/list"
        self.session_cookies = {
            "MONITOR_WEB_ID": token,
            "toutiao_sso_user": token,
            "passport_csrf_token": token
        }
        
    async def fetch_articles(self, page: int = 1, page_size: int = 20) -> dict:
        """获取文章列表"""
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Content-Type": "application/json",
                "Accept": "application/json, text/plain, */*",
                "Origin": "https://mp.toutiao.com",
                "Referer": "https://mp.toutiao.com/profile_v4/graphic/articles",
                "X-CSRFToken": self.token
            }
            
            params = {
                "status": "published",
                "start_time": 0,
                "end_time": int(datetime.now().timestamp()),
                "page": page,
                "page_size": page_size,
                "_signature": ""  # 如果需要签名可以在这里添加
            }
            
            logger.debug(f"Fetching articles with params: {params}")
            
            async with aiohttp.ClientSession(cookies=self.session_cookies) as session:
                async with session.get(
                    self.base_url,
                    headers=headers,
                    params=params,
                    timeout=30
                ) as response:
                    logger.debug(f"Response status: {response.status}")
                    response_text = await response.text()
                    logger.debug(f"Response text: {response_text}")
                    
                    if response.status == 200:
                        try:
                            data = json.loads(response_text)
                        except json.JSONDecodeError as e:
                            logger.error(f"JSON解析失败: {str(e)}, 原始响应: {response_text}")
                            raise Exception("服务器返回数据格式错误")
                        
                        if data.get("message") == "success":
                            articles = data.get("data", {}).get("articles", [])
                            total = data.get("data", {}).get("total", 0)
                            
                            formatted_articles = []
                            for article in articles:
                                try:
                                    publish_time = datetime.fromtimestamp(
                                        int(article.get("publish_time", 0))
                                    ).strftime("%Y-%m-%d %H:%M:%S")
                                except (ValueError, TypeError):
                                    publish_time = "未知时间"
                                    
                                formatted_articles.append({
                                    "title": article.get("title", "无标题"),
                                    "article_id": article.get("article_id", ""),
                                    "publish_time": publish_time,
                                    "read_count": article.get("read_count", 0),
                                    "comment_count": article.get("comment_count", 0),
                                    "article_url": article.get("article_url", "")
                                })
                            
                            logger.info(f"成功获取 {len(formatted_articles)} 篇文章")
                            return {
                                "articles": formatted_articles,
                                "total": total,
                                "has_more": len(articles) >= page_size
                            }
                        else:
                            error_msg = data.get("message", "未知错误")
                            logger.error(f"API返回错误: {error_msg}")
                            raise Exception(f"API返回错误: {error_msg}")
                    else:
                        logger.error(f"HTTP错误: {response.status}, 响应: {response_text}")
                        raise Exception(f"HTTP错误: {response.status}")
                        
        except asyncio.TimeoutError:
            logger.error("请求超时")
            raise Exception("请求超时，请检查网络连接")
        except aiohttp.ClientError as e:
            logger.error(f"网络请求错误: {str(e)}")
            raise Exception(f"网络请求错误: {str(e)}")
        except Exception as e:
            logger.error(f"获取文章列表失败: {str(e)}")
            raise Exception(f"获取文章列表失败: {str(e)}")
            
    async def get_article_detail(self, article_id: str) -> dict:
        """获取文章详情"""
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Content-Type": "application/json",
                "Accept": "application/json, text/plain, */*",
                "Origin": "https://mp.toutiao.com",
                "Referer": f"https://mp.toutiao.com/profile_v4/graphic/detail/{article_id}",
                "X-CSRFToken": self.token
            }
            
            url = f"https://mp.toutiao.com/mp/agw/article/detail?article_id={article_id}"
            
            async with aiohttp.ClientSession(cookies=self.session_cookies) as session:
                async with session.get(
                    url, 
                    headers=headers,
                    timeout=30
                ) as response:
                    response_text = await response.text()
                    logger.debug(f"Article detail response: {response_text}")
                    
                    if response.status == 200:
                        try:
                            data = json.loads(response_text)
                        except json.JSONDecodeError as e:
                            logger.error(f"JSON解析失败: {str(e)}, 原始响应: {response_text}")
                            raise Exception("服务器返回数据格式错误")
                        
                        if data.get("message") == "success":
                            article = data.get("data", {})
                            try:
                                publish_time = datetime.fromtimestamp(
                                    int(article.get("publish_time", 0))
                                ).strftime("%Y-%m-%d %H:%M:%S")
                            except (ValueError, TypeError):
                                publish_time = "未知时间"
                                
                            return {
                                "title": article.get("title", "无标题"),
                                "content": article.get("content", ""),
                                "article_id": article_id,
                                "publish_time": publish_time,
                                "status": article.get("status", ""),
                                "article_url": article.get("article_url", "")
                            }
                        else:
                            error_msg = data.get("message", "未知错误")
                            logger.error(f"API返回错误: {error_msg}")
                            raise Exception(f"API返回错误: {error_msg}")
                    else:
                        logger.error(f"HTTP错误: {response.status}, 响应: {response_text}")
                        raise Exception(f"HTTP错误: {response.status}")
                        
        except asyncio.TimeoutError:
            logger.error("请求超时")
            raise Exception("请求超时，请检查网络连接")
        except aiohttp.ClientError as e:
            logger.error(f"网络请求错误: {str(e)}")
            raise Exception(f"网络请求错误: {str(e)}")
        except Exception as e:
            logger.error(f"获取文章详情失败: {str(e)}")
            raise Exception(f"获取文章详情失败: {str(e)}")