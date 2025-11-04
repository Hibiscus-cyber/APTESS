from app.utility.base_world import BaseWorld
name = 'topology'
description = 'Example topology page'
address = '/plugin/topology/gui'   # 前端页面入口
access = BaseWorld.Access.RED

async def enable(services):
    pass

