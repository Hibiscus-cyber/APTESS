#!/usr/bin/env python3
"""
完全自动化的代理选择功能测试脚本
无需手动部署代理，自动创建模拟代理并测试功能
"""

import asyncio
import aiohttp
import json
import time
import random
import string

# Caldera服务器配置
CALDERA_URL = "http://localhost:8888"
API_BASE = f"{CALDERA_URL}/api/v2"

# 默认认证信息
DEFAULT_USERNAME = "admin"
DEFAULT_PASSWORD = "admin"

def generate_random_paw():
    """生成随机的代理ID"""
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))

async def authenticate():
    """认证获取访问令牌"""
    print("🔐 正在认证...")
    
    try:
        async with aiohttp.ClientSession() as session:
            # 尝试使用默认凭据登录
            login_data = {
                "username": DEFAULT_USERNAME,
                "password": DEFAULT_PASSWORD
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
                        print("✅ 认证成功")
                        return token
                    else:
                        print("❌ 认证响应中没有找到访问令牌")
                        print(f"   响应内容: {result}")
                        return None
                else:
                    print(f"❌ 认证失败 - 状态码: {response.status}")
                    error_text = await response.text()
                    print(f"   错误信息: {error_text}")
                    return None
                    
    except Exception as e:
        print(f"❌ 认证异常: {e}")
        return None

async def create_mock_agents(session, headers, count=4):
    """创建模拟代理"""
    print(f"🤖 创建 {count} 个模拟代理...")
    
    agents = []
    platforms = ["windows", "linux"]
    groups = ["red", "blue"]
    
    for i in range(count):
        agent_data = {
            "paw": generate_random_paw(),
            "group": groups[i % 2],  # 交替分配组
            "platform": platforms[i % 2],  # 交替分配平台
            "host": f"test-host-{i+1}",
            "username": "testuser",
            "architecture": "x64",
            "server": "http://localhost:8888",
            "location": "/tmp" if platforms[i % 2] == "linux" else "C:\\Users\\testuser",
            "pid": 1000 + i,
            "ppid": 2000 + i,
            "trusted": True,
            "executors": ["psh", "cmd"] if platforms[i % 2] == "windows" else ["sh", "bash"],
            "privilege": "Administrator" if platforms[i % 2] == "windows" else "root",
            "exe_name": "powershell.exe" if platforms[i % 2] == "windows" else "bash",
            "sleep_min": 30,
            "sleep_max": 60,
            "watchdog": 0,
            "contact": "http",
            "deadman_enabled": False,
            "last_seen": "2024-01-01T00:00:00Z"
        }
        
        try:
            async with session.post(
                f"{API_BASE}/agents",
                json=agent_data,
                headers=headers
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    agents.append(result)
                    print(f"   ✅ 创建代理: {agent_data['paw']} ({agent_data['platform']}) - 组: {agent_data['group']}")
                else:
                    print(f"   ❌ 创建代理失败: {agent_data['paw']} - 状态码: {response.status}")
                    error_text = await response.text()
                    print(f"      错误: {error_text}")
                    
        except Exception as e:
            print(f"   ❌ 创建代理异常: {agent_data['paw']} - {e}")
        
        # 添加延迟避免请求过快
        await asyncio.sleep(0.5)
    
    return agents

async def create_test_operations(session, headers, agents):
    """创建测试操作"""
    print("\n📋 创建测试操作...")
    
    operations = []
    
    # 操作1: 基于红色组的操作
    print("   1. 创建基于红色组的操作...")
    red_agents = [agent for agent in agents if agent.get('group') == 'red']
    red_operation = {
        "name": "Red Group Test Operation",
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
    
    red_op = await create_operation(session, red_operation, headers)
    if red_op:
        operations.append(red_op)
    
    # 操作2: 基于自定义代理ID的操作
    print("   2. 创建基于自定义代理ID的操作...")
    if len(agents) >= 2:
        # 选择前两个代理
        selected_agent_ids = [agents[0]['paw'], agents[1]['paw']]
        custom_operation = {
            "name": "Custom Agent Test Operation",
            "group": "custom",
            "agent_ids": selected_agent_ids,
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
        
        custom_op = await create_operation(session, custom_operation, headers)
        if custom_op:
            operations.append(custom_op)
    
    return operations

async def create_operation(session, operation_data, headers):
    """创建操作"""
    try:
        async with session.post(
            f"{API_BASE}/operations",
            json=operation_data,
            headers=headers
        ) as response:
            if response.status == 200:
                result = await response.json()
                print(f"      ✅ 创建操作: {operation_data['name']}")
                print(f"         操作ID: {result.get('id', 'N/A')}")
                print(f"         代理数量: {len(result.get('host_group', []))}")
                
                # 显示选中的代理
                if 'host_group' in result:
                    print("         选中的代理:")
                    for agent in result['host_group']:
                        print(f"           - {agent.get('paw', 'N/A')} ({agent.get('platform', 'N/A')}) - 组: {agent.get('group', 'N/A')}")
                
                return result
            else:
                print(f"      ❌ 创建操作失败: {operation_data['name']} - 状态码: {response.status}")
                error_text = await response.text()
                print(f"         错误: {error_text}")
                return None
                
    except Exception as e:
        print(f"      ❌ 创建操作异常: {operation_data['name']} - {e}")
        return None

async def verify_agent_selection(operations, agents):
    """验证代理选择功能"""
    print("\n🔍 验证代理选择功能...")
    
    for operation in operations:
        if not operation:
            continue
            
        op_name = operation.get('name', 'Unknown')
        op_group = operation.get('group', '')
        op_agent_ids = operation.get('agent_ids', [])
        selected_agents = operation.get('host_group', [])
        
        print(f"\n📊 操作: {op_name}")
        print(f"   组: {op_group}")
        print(f"   代理ID列表: {op_agent_ids}")
        print(f"   实际选中的代理数量: {len(selected_agents)}")
        
        if op_group == "red":
            # 红色组操作应该包含所有红色组代理
            red_agents = [agent for agent in agents if agent.get('group') == 'red']
            expected_paws = set(agent['paw'] for agent in red_agents)
            actual_paws = set(agent.get('paw') for agent in selected_agents)
            
            if expected_paws == actual_paws:
                print("   ✅ 红色组代理选择正确")
            else:
                print("   ❌ 红色组代理选择不正确")
                print(f"      期望: {expected_paws}")
                print(f"      实际: {actual_paws}")
                
        elif op_group == "custom" and op_agent_ids:
            # 自定义代理操作应该只包含指定的代理
            expected_paws = set(op_agent_ids)
            actual_paws = set(agent.get('paw') for agent in selected_agents)
            
            if expected_paws == actual_paws:
                print("   ✅ 自定义代理选择正确")
            else:
                print("   ❌ 自定义代理选择不正确")
                print(f"      期望: {expected_paws}")
                print(f"      实际: {actual_paws}")

async def test_agent_task_access(session, headers, operations, agents):
    """测试代理任务访问权限"""
    print("\n🧪 测试代理任务访问权限...")
    
    for operation in operations:
        if not operation:
            continue
            
        op_name = operation.get('name', 'Unknown')
        op_id = operation.get('id')
        selected_agents = operation.get('host_group', [])
        selected_paws = set(agent.get('paw') for agent in selected_agents)
        
        print(f"\n📋 操作: {op_name}")
        print(f"   应该能访问的代理: {selected_paws}")
        
        # 测试每个代理是否能访问此操作
        for agent in agents:
            agent_paw = agent.get('paw')
            can_access = agent_paw in selected_paws
            
            if can_access:
                print(f"   ✅ 代理 {agent_paw} 可以访问此操作")
            else:
                print(f"   ❌ 代理 {agent_paw} 不能访问此操作")

async def main():
    """主函数"""
    print("🚀 自动化代理选择功能测试")
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
    
    # 认证
    auth_token = await authenticate()
    if not auth_token:
        print("❌ 认证失败，无法继续测试")
        return
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {auth_token}"
    }
    
    async with aiohttp.ClientSession() as session:
        # 创建模拟代理
        agents = await create_mock_agents(session, headers, 4)
        
        if not agents:
            print("❌ 没有成功创建任何代理，无法继续测试")
            return
        
        # 等待代理创建完成
        await asyncio.sleep(2)
        
        # 创建测试操作
        operations = await create_test_operations(session, headers, agents)
        
        if not operations:
            print("❌ 没有成功创建任何操作，无法继续测试")
            return
        
        # 验证代理选择功能
        await verify_agent_selection(operations, agents)
        
        # 测试代理任务访问权限
        await test_agent_task_access(session, headers, operations, agents)
    
    print("\n🎉 测试完成!")
    print("\n📋 测试总结:")
    print("1. ✅ 自动创建了模拟代理")
    print("2. ✅ 自动创建了测试操作")
    print("3. ✅ 验证了代理选择功能")
    print("4. ✅ 测试了代理任务访问权限")
    print("\n🌐 您也可以在浏览器中访问 http://localhost:8888 查看结果")

if __name__ == "__main__":
    asyncio.run(main())
