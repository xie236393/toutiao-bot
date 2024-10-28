import httpx
import asyncio
import time
from typing import Dict
from loguru import logger

async def test_api(url: str, params: Dict = None, headers: Dict = None) -> bool:
    """测试 API 是否可用"""
    try:
        default_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        if headers:
            default_headers.update(headers)
            
        start_time = time.time()
        async with httpx.AsyncClient(headers=default_headers, timeout=10.0) as client:
            response = await client.get(url, params=params, follow_redirects=True)
            response.raise_for_status()
            data = response.json()
            elapsed = time.time() - start_time
            print(f"\n=== {url} ===")
            print(f"响应时间: {elapsed:.2f}秒")
            print(f"状态码: {response.status_code}")
            print(f"数据示例: {str(data)[:500]}...")
            return True
    except Exception as e:
        print(f"\n=== {url} ===")
        print(f"错误: {str(e)}")
        return False

async def main():
    # 要测试的 API 列表
    apis = [
        # 头条
        {
            "url": "https://www.toutiao.com/hot-event/hot-board/",
            "params": {"origin": "toutiao_pc"},
            "headers": {"Referer": "https://www.toutiao.com/"}
        },
        
        # 微博
        {
            "url": "https://weibo.com/ajax/side/hotSearch"
        },
        
        # 知乎
        {
            "url": "https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total",
            "params": {"limit": 50},
            "headers": {"Referer": "https://www.zhihu.com/"}
        },
        
        # B站
        {
            "url": "https://api.bilibili.com/x/web-interface/search/square",
            "params": {"limit": 50},
            "headers": {"Referer": "https://www.bilibili.com/"}
        },
        
        # 备用API
        {
            "url": "https://api.iyk0.com/ttnews"
        },
        {
            "url": "https://api.iyk0.com/wbtop"
        },
        {
            "url": "https://api.iyk0.com/zhihu"
        },
        {
            "url": "https://api.iyk0.com/bili"
        }
    ]
    
    for api in apis:
        await test_api(
            api["url"], 
            api.get("params"), 
            api.get("headers")
        )
        await asyncio.sleep(1)  # 避免请求太快

if __name__ == "__main__":
    asyncio.run(main())