from app.utility.base_world import BaseWorld
from plugins.system_time.app.system_time_api import SystemTimeApi

name = 'system_time'
description = '显示当前系统时间的插件'
address = '/plugin/system_time/gui'
access = BaseWorld.Access.APP


async def enable(services):
    system_time_api = SystemTimeApi(services=services)
    app = services.get('app_svc').application
    app.router.add_static('/system_time', 'plugins/system_time/static', append_version=True)
    app.router.add_route('GET', '/plugin/system_time/gui', system_time_api.landing)
    app.router.add_route('GET', '/plugin/system_time/current_time', system_time_api.get_current_time)