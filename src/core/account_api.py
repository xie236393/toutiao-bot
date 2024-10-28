import httpx
from loguru import logger
import json
from pathlib import Path
from typing import Dict, Optional

class AccountAPI:
    def __init__(self):
        self.base_url = "https://mp.toutiao.com"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Origin": "https://mp.toutiao.com",
            "Referer": "https://mp.toutiao.com/",
            "Content-Type": "application/json;charset=UTF-8"
        }
        
    async def login(self, username: str, password: str) -> Dict:
        """登录头条号"""
        try:
            # 第一步：获取登录所需的参数
            async with httpx.AsyncClient(headers=self.headers) as client:
                # 访问登录页面获取必要的cookie
                await client.get(f"{self.base_url}/profile_v4/index")
                
                # 登录请求
                login_url = f"{self.base_url}/api/login/v2"
                login_data = {
                    "username": username,
                    "password": password,
                    "captcha": "",
                    "remember": True
                }
                
                response = await client.post(
                    login_url, 
                    json=login_data,
                    headers={
                        **self.headers,
                        "Cookie": "; ".join([f"{k}={v}" for k, v in client.cookies.items()])
                    }
                )
                
                logger.debug(f"Login response: {response.text}")
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get("message") == "success":
                        # 保存登录信息
                        account_data = {
                            "token": response.cookies.get("tt_token", ""),  # 从cookie中获取token
                            "name": result["data"].get("name", username),
                            "status": "已登录",
                            "valid": True,
                            "cookies": dict(response.cookies)  # 保存所有cookie
                        }
                        self._save_account(account_data)
                        return account_data
                    else:
                        raise Exception(result.get("message", "登录失败"))
                else:
                    raise Exception(f"登录请求失败: {response.status_code}")
                    
        except Exception as e:
            logger.error(f"登录失败: {str(e)}")
            raise

    def _save_account(self, account_data: Dict):
        """保存账号信息"""
        try:
            data_dir = Path("data")
            data_dir.mkdir(exist_ok=True)
            
            with open(data_dir / "last_account.json", "w", encoding="utf-8") as f:
                json.dump(account_data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logger.error(f"保存账号信息失败: {str(e)}")
            
    def load_last_account(self) -> Optional[Dict]:
        """加载上次登录的账号"""
        try:
            account_file = Path("data/last_account.json")
            if account_file.exists():
                with open(account_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            return None
            
        except Exception as e:
            logger.error(f"加载账号信息失败: {str(e)}")
            return None