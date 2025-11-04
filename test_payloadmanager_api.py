#!/usr/bin/env python3
"""
PayloadManager API测试脚本
测试API端点是否正常工作
"""

import asyncio
import aiohttp
import sys
import os

# 添加Caldera路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_api_endpoints():
    """测试API端点"""
    
    print("=" * 60)
    print("🧪 PayloadManager API测试")
    print("=" * 60)
    
    base_url = "http://localhost:8888"
    endpoints = [
        "/api/v2/malware-payloads",
        "/api/v2/health"
    ]
    
    async with aiohttp.ClientSession() as session:
        for endpoint in endpoints:
            print(f"\n测试端点: {endpoint}")
            try:
                async with session.get(f"{base_url}{endpoint}") as response:
                    print(f"   状态码: {response.status}")
                    
                    if response.status == 200:
                        data = await response.json()
                        if endpoint == "/api/v2/malware-payloads":
                            print(f"   ✅ 载荷数量: {len(data)}")
                        elif endpoint == "/api/v2/health":
                            plugins = data.get('plugins', [])
                            payloadmanager_plugin = next((p for p in plugins if 'payloadmanager' in p.get('name', '')), None)
                            if payloadmanager_plugin:
                                print(f"   ✅ payloadmanager插件已加载")
                            else:
                                print(f"   ❌ payloadmanager插件未找到")
                    elif response.status == 401:
                        print(f"   ⚠️ 需要认证（这是正常的）")
                    else:
                        text = await response.text()
                        print(f"   ❌ 错误: {text[:100]}...")
                        
            except aiohttp.ClientConnectorError:
                print(f"   ❌ 无法连接到服务器")
                print(f"   请确保Caldera服务器正在运行: python server.py")
            except Exception as e:
                print(f"   ❌ 测试失败: {e}")
    
    print("\n" + "=" * 60)
    print("📋 测试完成")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_api_endpoints())
