import httpx
from loguru import logger
import re
from typing import Dict
import json

import httpx
from loguru import logger
import re
from typing import Dict
import json

class AccountAPI:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Referer": "https://mp.toutiao.com/"
        }
        
    async def verify_token(self, token: str) -> Dict:
        """验证token"""
        try:
            if not token:
                return {
                    "valid": False,
                    "error": "Token不能为空"
                }

            # 简化验证逻辑，只要token不为空就认为有效
            # 实际项目中应该根据具体的API验证逻辑修改
            return {
                "valid": True,
                "name": "测试账号",  # 测试用，实际应该从API获取
                "status": "已登录"
            }

        except Exception as e:
            logger.error(f"验证token失败: {str(e)}")
            return {
                "valid": False,
                "error": str(e)
            }
            
    def _extract_user_info(self, html: str) -> Dict:
        """从HTML中提取用户信息"""
        try:
            logger.info("开始提取用户信息")
            
            # 方式1: 通过meta标签
            name_match = re.search(r'name="user_name"\s+content="([^"]+)"', html)
            if name_match:
                logger.info(f"通过meta标签找到用户名: {name_match.group(1)}")
                return {
                    "name": name_match.group(1),
                    "status": "已登录"
                }
                
            # 方式2: 通过JSON数据
            json_matches = re.finditer(r'window\.[A-Z_]+\s*=\s*({[^;]+});', html)
            for match in json_matches:
                try:
                    data = json.loads(match.group(1))
                    logger.debug(f"找到JSON数据: {str(data)[:200]}...")  # 只打印前200个字符
                    if "user" in data:
                        name = data["user"].get("name")
                        if name:
                            logger.info(f"通过JSON数据找到用户名: {name}")
                            return {
                                "name": name,
                                "status": "已登录"
                            }
                except json.JSONDecodeError:
                    continue
                    
            # 方式3: 通过用户信息区域
            user_match = re.search(r'<div[^>]*class="[^"]*user-name[^"]*"[^>]*>([^<]+)</div>', html)
            if user_match:
                logger.info(f"通过DOM元素找到用户名: {user_match.group(1).strip()}")
                return {
                    "name": user_match.group(1).strip(),
                    "status": "已登录"
                }
                
            # 方式4: 通过script标签中的数据
            script_match = re.search(r'<script[^>]*>\s*var\s+USER_INFO\s*=\s*({[^}]+})', html)
            if script_match:
                try:
                    data = json.loads(script_match.group(1))
                    if "name" in data:
                        logger.info(f"通过script标签找到用户名: {data['name']}")
                        return {
                            "name": data["name"],
                            "status": "已登录"
                        }
                except json.JSONDecodeError:
                    pass
                    
            logger.warning("尝试了所有方式但无法提取用户信息")
            return None
            
        except Exception as e:
            logger.error(f"提取用户信息失败: {str(e)}")
            return None