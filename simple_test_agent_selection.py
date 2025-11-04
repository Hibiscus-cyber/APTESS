#!/usr/bin/env python3
"""
简化的代理选择功能测试脚本
"""

import asyncio
import aiohttp
import json

# Caldera服务器配置
CALDERA_URL = "http://localhost:8888"
API_BASE = f"{CALDERA_URL}/api/v2"

async def test_with_curl_commands():
    """使用curl命令进行测试"""
    print("🧪 使用curl命令测试代理选择功能")
    print("=" * 50)
    
    print("📋 测试步骤:")
    print("1. 首先在浏览器中登录Caldera: http://localhost:8888")
    print("2. 使用默认用户名密码: admin/admin")
    print("3. 登录后，在Operations页面创建新操作")
    print("4. 测试以下场景:")
    print("")
    
    print("🔍 场景1: 创建基于组的操作")
    print("   - 选择 'red' 组")
    print("   - 创建操作")
    print("   - 检查是否所有红色组代理都能看到任务")
    print("")
    
    print("🔍 场景2: 创建基于自定义代理的操作")
    print("   - 选择 'Custom Selection'")
    print("   - 只选择一个特定代理")
    print("   - 创建操作")
    print("   - 检查是否只有选中的代理能看到任务")
    print("")
    
    print("📊 验证方法:")
    print("1. 在Operations页面查看操作详情")
    print("2. 检查 'host_group' 字段中的代理列表")
    print("3. 确认只有预期的代理被包含在操作中")
    print("")
    
    print("🔧 如果测试失败，检查以下内容:")
    print("1. 确保Caldera服务器正在运行")
    print("2. 确保有可用的代理")
    print("3. 检查浏览器控制台是否有JavaScript错误")
    print("4. 检查Caldera服务器日志")

async def test_api_directly():
    """直接测试API（需要认证）"""
    print("\n🔧 直接API测试（需要认证）")
    print("=" * 50)
    
    # 认证信息
    username = "admin"
    password = "admin"
    
    try:
        async with aiohttp.ClientSession() as session:
            # 步骤1: 登录获取token
            print("1. 尝试登录...")
            login_data = {
                "username": username,
                "password": password
            }
            
            async with session.post(
                f"{CALDERA_URL}/login",
                json=login_data,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    token = result.get('access_token')
                    if token:
                        print("✅ 登录成功")
                        headers = {
                            "Content-Type": "application/json",
                            "Authorization": f"Bearer {token}"
                        }
                    else:
                        print("❌ 登录响应中没有token")
                        return
                else:
                    print(f"❌ 登录失败: {response.status}")
                    error_text = await response.text()
                    print(f"   错误: {error_text}")
                    return
            
            # 步骤2: 获取现有代理
            print("\n2. 获取现有代理...")
            async with session.get(f"{API_BASE}/agents", headers=headers) as response:
                if response.status == 200:
                    agents = await response.json()
                    print(f"✅ 找到 {len(agents)} 个代理:")
                    for agent in agents:
                        print(f"   - {agent.get('paw', 'N/A')} ({agent.get('platform', 'N/A')}) - 组: {agent.get('group', 'N/A')}")
                else:
                    print(f"❌ 获取代理失败: {response.status}")
                    return
            
            # 步骤3: 创建测试操作
            if len(agents) >= 2:
                print("\n3. 创建测试操作...")
                
                # 选择前两个代理进行测试
                test_agent_ids = [agents[0]['paw'], agents[1]['paw']]
                
                operation_data = {
                    "name": "Test Custom Agent Selection",
                    "group": "custom",
                    "agent_ids": test_agent_ids,
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
                    headers=headers
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        print("✅ 操作创建成功")
                        print(f"   操作ID: {result.get('id')}")
                        print(f"   代理数量: {len(result.get('host_group', []))}")
                        print("   选中的代理:")
                        for agent in result.get('host_group', []):
                            print(f"     - {agent.get('paw')} ({agent.get('platform')})")
                        
                        # 验证代理选择是否正确
                        expected_paws = set(test_agent_ids)
                        actual_paws = set(agent.get('paw') for agent in result.get('host_group', []))
                        
                        if expected_paws == actual_paws:
                            print("✅ 代理选择正确！")
                        else:
                            print("❌ 代理选择不正确")
                            print(f"   期望: {expected_paws}")
                            print(f"   实际: {actual_paws}")
                    else:
                        print(f"❌ 创建操作失败: {response.status}")
                        error_text = await response.text()
                        print(f"   错误: {error_text}")
            else:
                print("❌ 需要至少2个代理才能进行测试")
                
    except Exception as e:
        print(f"❌ 测试异常: {e}")

async def main():
    """主函数"""
    print("🚀 代理选择功能测试")
    print("=" * 50)
    
    # 检查Caldera服务器
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(CALDERA_URL) as response:
                if response.status == 200:
                    print("✅ Caldera服务器正在运行")
                else:
                    print("❌ Caldera服务器响应异常")
                    return
    except Exception as e:
        print(f"❌ 无法连接到Caldera服务器: {e}")
        print("   请确保Caldera服务器正在运行: python3 server.py")
        return
    
    # 运行测试
    await test_with_curl_commands()
    await test_api_directly()
    
    print("\n🎉 测试完成!")
    print("\n📋 下一步:")
    print("1. 如果API测试成功，说明后端功能正常")
    print("2. 如果前端测试失败，检查前端代码")
    print("3. 查看Caldera服务器日志获取更多信息")

if __name__ == "__main__":
    asyncio.run(main())
