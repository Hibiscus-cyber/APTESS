from app.utility.base_world import BaseWorld
from plugins.access2.app.access_api import AccessApi

name = 'Access2'
description = 'A toolkit containing initial access throwing modules'
address = '/plugin/access2/gui'
access = BaseWorld.Access.RED


async def enable(services):
    access_api = AccessApi(services=services)
    app = services.get('app_svc').application
    app.router.add_static('/access2', 'plugins/access2/static', append_version=True)
    app.router.add_route('GET', '/plugin/access2/gui', access_api.landing)
    app.router.add_route('POST', '/plugin/access2/exploit', access_api.exploit)
    app.router.add_route('POST', '/plugin/access2/abilities', access_api.abilities)
    app.router.add_route('POST', '/plugin/access2/executor', access_api.executor)
