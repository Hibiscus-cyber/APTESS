"""
PayloadManager Plugin Hook
恶意载荷库管理插件
"""

import os
from app.utility.base_world import BaseWorld
from plugins.payloadmanager.app.payloadmanager_svc import PayloadManagerService
from plugins.payloadmanager.app.payload_api import PayloadApi

# Caldera期望的模块级变量
name = 'payloadmanager'
description = '恶意载荷库管理插件'
address = '/plugin/payloadmanager/gui'
access = BaseWorld.Access.APP
data_dir = os.path.join('plugins', name.lower(), 'data')


async def enable(services):
    """启用插件"""
    app = services.get('app_svc').application
    
    # 确保数据目录存在
    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(os.path.join(data_dir, 'payloads'), exist_ok=True)
    
    # 初始化服务
    payload_service = PayloadManagerService()
    await payload_service.initialize()
    
    # 注册服务
    services['恶意载荷库服务'] = payload_service
    
    # 注册API
    payload_api = PayloadApi(services)
    services['payload_api'] = payload_api
    
    # 添加API路由
    payload_api.add_routes(app)
    
    print('恶意载荷库: 插件启用成功')
