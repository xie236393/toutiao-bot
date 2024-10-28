import aiohttp
from loguru import logger
from datetime import datetime
import json
import asyncio

class Publisher:
    def __init__(self):
        self.base_url = "https://mp.toutiao.com/mp/agw/article/publish"
        
    async def publish_toutiao(self, token: str, article_data: dict) -> dict:
        """发布文章到头条号"""
        try:
            session_cookies = {
                "MONITOR_WEB_ID": token,
                "toutiao_sso_user": token,
                "passport_csrf_token": token
            }
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Content-Type": "application/json",
                "Accept": "application/json, text/plain, */*",
                "Origin": "https://mp.toutiao.com",
                "Referer": "https://mp.toutiao.com/profile_v4/graphic/publish",
                "X-CSRFToken": token
            }
            
            # 构建发布数据
            data = {
                "title": article_data.get("title", ""),
                "content": article_data.get("content", ""),
                "category": article_data.get("category", ""),
                "tags": article_data.get("tags", []),
                "article_type": 0,  # 0表示普通图文
                "save_status": 1,  # 1表示发布
                "timer_status": 0,  # 0表示立即发布
            }
            
            logger.debug(f"Publishing article with data: {json.dumps(data, ensure_ascii=False)}")
            
            async with aiohttp.ClientSession(cookies=session_cookies) as session:
                async with session.post(
                    self.base_url,
                    headers=headers,
                    json=data,
                    timeout=30
                ) as response:
                    logger.debug(f"Response status: {response.status}")
                    response_text = await response.text()
                    logger.debug(f"Response text: {response_text}")
                    
                    if response.status == 200:
                        try:
                            result = json.loads(response_text)
                        except json.JSONDecodeError as e:
                            logger.error(f"JSON解析失败: {str(e)}, 原始响应: {response_text}")
                            raise Exception("服务器返回数据格式错误")
                        
                        if result.get("message") == "success":
                            logger.info("文章发布成功")
                            return {
                                "article_id": result.get("data", {}).get("article_id", ""),
                                "status": "success",
                                "message": "发布成功"
                            }
                        else:
                            error_msg = result.get("message", "未知错误")
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
            logger.error(f"发布文章失败: {str(e)}")
            raise Exception(f"发布文章失败: {str(e)}")
            
    async def update_article(self, token: str, article_id: str, article_data: dict) -> dict:
        """更新已发布的文章"""
        try:
            session_cookies = {
                "MONITOR_WEB_ID": token,
                "toutiao_sso_user": token,
                "passport_csrf_token": token
            }
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Content-Type": "application/json",
                "Accept": "application/json, text/plain, */*",
                "Origin": "https://mp.toutiao.com",
                "Referer": f"https://mp.toutiao.com/profile_v4/graphic/edit/{article_id}",
                "X-CSRFToken": token
            }
            
            # 构建更新数据
            data = {
                "article_id": article_id,
                "title": article_data.get("title", ""),
                "content": article_data.get("content", ""),
                "category": article_data.get("category", ""),
                "tags": article_data.get("tags", []),
                "save_status": 1  # 1表示更新并发布
            }
            
            url = f"https://mp.toutiao.com/mp/agw/article/update"
            logger.debug(f"Updating article with data: {json.dumps(data, ensure_ascii=False)}")
            
            async with aiohttp.ClientSession(cookies=session_cookies) as session:
                async with session.post(
                    url,
                    headers=headers,
                    json=data,
                    timeout=30
                ) as response:
                    logger.debug(f"Response status: {response.status}")
                    response_text = await response.text()
                    logger.debug(f"Response text: {response_text}")
                    
                    if response.status == 200:
                        try:
                            result = json.loads(response_text)
                        except json.JSONDecodeError as e:
                            logger.error(f"JSON解析失败: {str(e)}, 原始响应: {response_text}")
                            raise Exception("服务器返回数据格式错误")
                        
                        if result.get("message") == "success":
                            logger.info("文章更新成功")
                            return {
                                "article_id": article_id,
                                "status": "success",
                                "message": "更新成功"
                            }
                        else:
                            error_msg = result.get("message", "未知错误")
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
            logger.error(f"更新文章失败: {str(e)}")
            raise Exception(f"更新文章失败: {str(e)}")