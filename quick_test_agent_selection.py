#!/usr/bin/env python3
"""
快速测试代理选择功能 - 处理认证问题
"""

import asyncio
import aiohttp
import json

# Caldera服务器配置
CALDERA_URL = "http://localhost:8888"
API_BASE = f"{CALDERA_URL}/api/v2"

async def test_caldera_connection():
    """测试Caldera连接和认证"""
    print("🔍 测试Caldera连接和认证...")
    
    try:
        async with aiohttp.ClientSession() as session:
            # 测试基本连接
            async with session.get(CALDERA_URL) as response:
                if response.status == 200:
                    print("✅ Caldera服务器连接正常")
                else:
                    print(f"❌ Caldera服务器响应异常: {response.status}")
                    return False
            
            # 尝试不同的认证方式
            auth_methods = [
                # 方法1: 标准登录
                {
                    "url": f"{CALDERA_URL}/login",
                    "data": {"username": "admin", "password": "admin"},
                    "name": "标准登录"
                },
                # 方法2: API登录
                {
                    "url": f"{API_BASE}/auth/login",
                    "data": {"username": "admin", "password": "admin"},
                    "name": "API登录"
                },
                # 方法3: 尝试不同的端点
                {
                    "url": f"{CALDERA_URL}/api/login",
                    "data": {"username": "admin", "password": "admin"},
                    "name": "API登录(备用)"
                }
            ]
            
            for method in auth_methods:
                print(f"\n🔐 尝试 {method['name']}...")
                try:
                    async with session.post(
                        method["url"],
                        json=method["data"],
                        headers={"Content-Type": "application/json"}
                    ) as response:
                        print(f"   状态码: {response.status}")
                        
                        if response.status == 200:
                            result = await response.json()
                            print(f"   响应: {result}")
                            
                            # 查找token
                            token = None
                            if isinstance(result, dict):
                                token = result.get('access_token') or result.get('token') or result.get('auth_token')
                            
                            if token:
                                print(f"✅ {method['name']} 成功，获得token")
                                return token
                            else:
                                print(f"⚠️ {method['name']} 成功但没有token")
                        else:
                            error_text = await response.text()
                            print(f"   ❌ {method['name']} 失败: {error_text[:200]}")
                            
                except Exception as e:
                    print(f"   ❌ {method['name']} 异常: {e}")
            
            print("\n❌ 所有认证方法都失败了")
            return False
            
    except Exception as e:
        print(f"❌ 连接测试异常: {e}")
        return False

async def test_without_auth():
    """尝试无认证测试"""
    print("\n🔓 尝试无认证测试...")
    
    try:
        async with aiohttp.ClientSession() as session:
            # 尝试获取代理列表
            async with session.get(f"{API_BASE}/agents") as response:
                print(f"   获取代理列表状态码: {response.status}")
                if response.status == 200:
                    agents = await response.json()
                    print(f"   ✅ 找到 {len(agents)} 个代理")
                    return True
                else:
                    error_text = await response.text()
                    print(f"   ❌ 获取代理失败: {error_text[:200]}")
                    return False
                    
    except Exception as e:
        print(f"❌ 无认证测试异常: {e}")
        return False

async def create_simple_test():
    """创建简单的测试操作"""
    print("\n📋 创建简单测试操作...")
    
    try:
        async with aiohttp.ClientSession() as session:
            # 尝试创建操作（可能不需要认证）
            operation_data = {
                "name": "Simple Test Operation",
                "group": "red",
                "adversary": {"adversary_id": "ad-hoc"},
                "planner": {"id": "atomic"},
                "source": {"id": "basic"},
                "jitter": "2/8",
                "state": "paused",
                "autonomous": 1,
                "obfuscator": "plain-text",
                "auto_close": False,
                "visibility": 50,
                "use_learning_parsers": True
            }
            
            async with session.post(
                f"{API_BASE}/operations",
                json=operation_data,
                headers={"Content-Type": "application/json"}
            ) as response:
                print(f"   创建操作状态码: {response.status}")
                if response.status == 200:
                    result = await response.json()
                    print(f"   ✅ 操作创建成功: {result.get('id')}")
                    return True
                else:
                    error_text = await response.text()
                    print(f"   ❌ 创建操作失败: {error_text[:200]}")
                    return False
                    
    except Exception as e:
        print(f"❌ 创建测试异常: {e}")
        return False

async def main():
    """主函数"""
    print("🚀 快速测试代理选择功能")
    print("=" * 50)
    
    # 测试连接和认证
    token = await test_caldera_connection()
    
    if token:
        print(f"\n✅ 认证成功，token: {token[:20]}...")
        print("   现在可以运行完整的自动化测试脚本")
        print("   运行: python3 automated_agent_selection_test.py")
    else:
        print("\n⚠️ 认证失败，尝试其他方法...")
        
        # 尝试无认证测试
        if await test_without_auth():
            print("✅ 无认证访问成功")
        else:
            print("❌ 无认证访问也失败")
        
        # 尝试创建简单测试
        if await create_simple_test():
            print("✅ 简单测试创建成功")
        else:
            print("❌ 简单测试创建失败")
    
    print("\n📋 故障排除建议:")
    print("1. 检查Caldera服务器是否正在运行")
    print("2. 检查默认用户名密码是否正确")
    print("3. 查看Caldera服务器日志")
    print("4. 尝试在浏览器中手动登录")
    print("5. 检查Caldera配置文件中是否有认证设置")

if __name__ == "__main__":
    asyncio.run(main())
