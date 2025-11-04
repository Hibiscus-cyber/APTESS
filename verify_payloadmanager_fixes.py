#!/usr/bin/env python3
"""
PayloadManager修复验证脚本
验证所有修改是否正确应用
"""

import os
import sys

def verify_fixes():
    """验证修复是否正确应用"""
    
    print("=" * 60)
    print("🔍 PayloadManager修复验证")
    print("=" * 60)
    
    fixes_applied = []
    
    # 1. 检查hook.py修改
    print("\n1. 检查hook.py修改...")
    hook_file = "plugins/payloadmanager/hook.py"
    if os.path.exists(hook_file):
        with open(hook_file, 'r', encoding='utf-8') as f:
            content = f.read()
            if "services['payload_manager_service']" in content:
                fixes_applied.append("✅ hook.py: 服务注册名称已修改为英文")
            else:
                fixes_applied.append("❌ hook.py: 服务注册名称未修改")
                
            if "Plugin enabled successfully" in content:
                fixes_applied.append("✅ hook.py: 日志消息已修改为英文")
            else:
                fixes_applied.append("❌ hook.py: 日志消息未修改")
    
    # 2. 检查payload_api.py修改
    print("\n2. 检查payload_api.py修改...")
    api_file = "plugins/payloadmanager/app/payload_api.py"
    if os.path.exists(api_file):
        with open(api_file, 'r', encoding='utf-8') as f:
            content = f.read()
            if "services['payload_manager_service']" in content:
                fixes_applied.append("✅ payload_api.py: 服务引用名称已修改为英文")
            else:
                fixes_applied.append("❌ payload_api.py: 服务引用名称未修改")
    
    # 3. 检查payloadmanager_svc.py修改
    print("\n3. 检查payloadmanager_svc.py修改...")
    svc_file = "plugins/payloadmanager/app/payloadmanager_svc.py"
    if os.path.exists(svc_file):
        with open(svc_file, 'r', encoding='utf-8') as f:
            content = f.read()
            if "self.add_service('payload_manager_service'" in content:
                fixes_applied.append("✅ payloadmanager_svc.py: 服务注册名称已修改为英文")
            else:
                fixes_applied.append("❌ payloadmanager_svc.py: 服务注册名称未修改")
    
    # 4. 检查payloadmanager.vue修改
    print("\n4. 检查payloadmanager.vue修改...")
    vue_file = "plugins/payloadmanager/gui/views/payloadmanager.vue"
    if os.path.exists(vue_file):
        with open(vue_file, 'r', encoding='utf-8') as f:
            content = f.read()
            if "credentials: 'include'" in content:
                fixes_applied.append("✅ payloadmanager.vue: API调用已添加认证信息")
            else:
                fixes_applied.append("❌ payloadmanager.vue: API调用未添加认证信息")
                
            if "需要登录，请先登录Caldera" in content:
                fixes_applied.append("✅ payloadmanager.vue: 错误处理已改进")
            else:
                fixes_applied.append("❌ payloadmanager.vue: 错误处理未改进")
    
    # 输出结果
    print("\n" + "=" * 60)
    print("📊 修复验证结果")
    print("=" * 60)
    
    for fix in fixes_applied:
        print(f"   {fix}")
    
    success_count = len([f for f in fixes_applied if f.startswith("✅")])
    total_count = len(fixes_applied)
    
    print(f"\n修复成功率: {success_count}/{total_count}")
    
    if success_count == total_count:
        print("\n🎉 所有修复已成功应用！")
        print("\n📋 下一步操作：")
        print("1. 重新构建Magma: cd plugins/magma && npm run build")
        print("2. 重启Caldera服务器: python server.py")
        print("3. 清除浏览器缓存 (Ctrl+F5)")
        print("4. 访问 http://localhost:8888")
        print("5. 点击左侧菜单中的 'payloadmanager'")
        print("6. 检查页面是否正常显示")
    else:
        print(f"\n⚠️ 还有 {total_count - success_count} 个修复未完成")
        print("请检查上述错误并手动修复")
    
    print("=" * 60)

if __name__ == "__main__":
    verify_fixes()
