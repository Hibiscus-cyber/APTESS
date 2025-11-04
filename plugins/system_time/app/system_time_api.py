import datetime
from aiohttp import web
from aiohttp_jinja2 import template
from app.service.auth_svc import for_all_public_methods, check_authorization


@for_all_public_methods(check_authorization)
class SystemTimeApi:
    """
    系统时间插件的API类
    提供显示当前系统时间的功能
    """

    def __init__(self, services):
        """
        初始化SystemTimeApi实例
        
        Args:
            services: Caldera服务容器，包含所有可用的核心服务
        """
        self.data_svc = services.get('data_svc')
        self.auth_svc = services.get('auth_svc')

    @template('plugins/system_time/gui/system_time.html')
    async def landing(self, request):
        """
        提供系统时间页面的主入口
        
        Args:
            request: HTTP请求对象
        
        Returns:
            dict: 包含初始数据的字典
        """
        current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        return {
            'current_time': current_time
        }

    async def get_current_time(self, request):
        """
        API端点：获取当前系统时间
        
        Args:
            request: HTTP请求对象
        
        Returns:
            web.json_response: 包含当前时间的JSON响应
        """
        current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        return web.json_response({
            'current_time': current_time,
            'timestamp': int(datetime.datetime.now().timestamp())
        })