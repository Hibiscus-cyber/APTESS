from app.utility.base_world import BaseWorld
from plugins.profile.app.profile_api import ProfileApi

name = 'profile'
description = 'Example plugin page'
address = '/plugin/profile/gui'   # 前端页面入口
access = BaseWorld.Access.RED

async def enable(services):
    profile_api = ProfileApi(services=services)
    app = services.get('app_svc').application

    profile_api.add_routes(app)



