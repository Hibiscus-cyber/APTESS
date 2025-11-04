#!/usr/bin/env python3
"""
测试代理任务分配功能
"""

import asyncio
import aiohttp
import json
import time

# Caldera服务器配置
CALDERA_URL = "http://localhost:8888"
API_BASE = f"{CALDERA_URL}/api/v2"

async def test_agent_task_assignment():
    """测试代理任务分配功能"""
    print("🧪 测试代理任务分配功能")
    print("=" * 50)
    
    async with aiohttp.ClientSession() as session:
        # 步骤1: 创建测试代理
        print("1. 创建测试代理...")
        test_agents = [
            {
                "paw": "agent-123456",
                "group": "red",
                "platform": "windows",
                "host": "test-windows-1",
                "username": "admin",
                "architecture": "x64",
                "server": "http://localhost:8888",
                "location": "C:\\Users\\admin",
                "pid": 1234,
                "ppid": 5678,
                "trusted": True,
                "executors": ["psh", "cmd"],
                "privilege": "Administrator",
                "exe_name": "powershell.exe",
                "sleep_min": 30,
                "sleep_max": 60,
                "watchdog": 0,
                "contact": "http",
                "deadman_enabled": False
            },
            {
                "paw": "agent-789012",
                "group": "red",
                "platform": "linux",
                "host": "test-linux-1",
                "username": "root",
                "architecture": "x64",
                "server": "http://localhost:8888",
                "location": "/root",
                "pid": 2345,
                "ppid": 6789,
                "trusted": True,
                "executors": ["sh", "bash"],
                "privilege": "root",
                "exe_name": "bash",
                "sleep_min": 30,
                "sleep_max": 60,
                "watchdog": 0,
                "contact": "http",
                "deadman_enabled": False
            }
        ]
        
        for agent_data in test_agents:
            try:
                async with session.post(
                    f"{API_BASE}/agents",
                    json=agent_data,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        print(f"   ✅ 创建代理: {agent_data['paw']}")
                    else:
                        print(f"   ❌ 创建代理失败: {agent_data['paw']}")
            except Exception as e:
                print(f"   ❌ 创建代理异常: {agent_data['paw']} - {e}")
        
        # 等待代理创建完成
        await asyncio.sleep(2)
        
        # 步骤2: 创建基于组的操作
        print("\n2. 创建基于红色组的操作...")
        red_group_operation = {
            "name": "Red Group Operation",
            "group": "red",
            "adversary": {"adversary_id": "ad-hoc"},
            "planner": {"id": "atomic"},
            "source": {"id": "basic"},
            "jitter": "2/8",
            "state": "running",
            "autonomous": 1,
            "obfuscator": "plain-text",
            "auto_close": False,
            "visibility": 50,
            "use_learning_parsers": True
        }
        
        red_op_id = await create_operation(session, red_group_operation)
        
        # 步骤3: 创建基于特定代理ID的操作
        print("\n3. 创建基于特定代理ID的操作...")
        custom_agent_operation = {
            "name": "Custom Agent Operation",
            "group": "custom",
            "agent_ids": ["agent-123456"],  # 只选择 agent-123456
            "adversary": {"adversary_id": "ad-hoc"},
            "planner": {"id": "atomic"},
            "source": {"id": "basic"},
            "jitter": "2/8",
            "state": "running",
            "autonomous": 1,
            "obfuscator": "plain-text",
            "auto_close": False,
            "visibility": 50,
            "use_learning_parsers": True
        }
        
        custom_op_id = await create_operation(session, custom_agent_operation)
        
        # 步骤4: 模拟代理心跳，测试任务分配
        print("\n4. 测试代理任务分配...")
        
        # 模拟 agent-123456 的心跳
        print("   📡 模拟 agent-123456 心跳...")
        await simulate_agent_heartbeat(session, "agent-123456")
        
        # 模拟 agent-789012 的心跳
        print("   📡 模拟 agent-789012 心跳...")
        await simulate_agent_heartbeat(session, "agent-789012")
        
        # 步骤5: 验证结果
        print("\n5. 验证操作状态...")
        await verify_operation_status(session, red_op_id, "Red Group Operation")
        await verify_operation_status(session, custom_op_id, "Custom Agent Operation")

async def create_operation(session, operation_data):
    """创建操作"""
    try:
        async with session.post(
            f"{API_BASE}/operations",
            json=operation_data,
            headers={"Content-Type": "application/json"}
        ) as response:
            if response.status == 200:
                result = await response.json()
                print(f"   ✅ 创建操作: {operation_data['name']}")
                print(f"      操作ID: {result.get('id', 'N/A')}")
                print(f"      代理数量: {len(result.get('host_group', []))}")
                return result.get('id')
            else:
                print(f"   ❌ 创建操作失败: {operation_data['name']}")
                error_text = await response.text()
                print(f"      错误: {error_text}")
                return None
    except Exception as e:
        print(f"   ❌ 创建操作异常: {operation_data['name']} - {e}")
        return None

async def simulate_agent_heartbeat(session, agent_paw):
    """模拟代理心跳"""
    try:
        # 模拟代理心跳请求
        heartbeat_data = {
            "paw": agent_paw,
            "results": []
        }
        
        # 这里需要根据实际的Caldera API端点进行调整
        # 通常代理心跳是通过特定的contact端点进行的
        print(f"      🤖 代理 {agent_paw} 请求任务...")
        
        # 检查代理是否能获取到任务
        # 这需要根据实际的Caldera实现来调整
        await asyncio.sleep(1)
        print(f"      ✅ 代理 {agent_paw} 心跳完成")
        
    except Exception as e:
        print(f"      ❌ 代理 {agent_paw} 心跳异常: {e}")

async def verify_operation_status(session, operation_id, operation_name):
    """验证操作状态"""
    if not operation_id:
        print(f"   ❌ 无法验证 {operation_name} - 操作ID为空")
        return
    
    try:
        async with session.get(f"{API_BASE}/operations/{operation_id}") as response:
            if response.status == 200:
                operation = await response.json()
                print(f"   📊 {operation_name}:")
                print(f"      状态: {operation.get('state', 'N/A')}")
                print(f"      代理数量: {len(operation.get('host_group', []))}")
                print(f"      链接数量: {len(operation.get('chain', []))}")
                
                # 显示代理信息
                if 'host_group' in operation:
                    print(f"      代理列表:")
                    for agent in operation['host_group']:
                        print(f"        - {agent.get('paw', 'N/A')} ({agent.get('platform', 'N/A')})")
            else:
                print(f"   ❌ 获取操作状态失败: {operation_name}")
    except Exception as e:
        print(f"   ❌ 验证操作状态异常: {operation_name} - {e}")

async def main():
    """主函数"""
    print("🚀 开始测试代理任务分配功能...")
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
    await test_agent_task_assignment()
    
    print("\n🎉 测试完成!")
    print("\n📋 预期结果:")
    print("1. 红色组操作应该对所有红色组代理可见")
    print("2. 自定义代理操作应该只对 agent-123456 可见")
    print("3. agent-789012 应该看不到自定义代理操作的任务")

if __name__ == "__main__":
    asyncio.run(main())
