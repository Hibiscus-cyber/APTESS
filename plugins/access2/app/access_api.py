from aiohttp import web
from aiohttp_jinja2 import template

from app.objects.secondclass.c_fact import Fact
from app.service.auth_svc import for_all_public_methods, check_authorization
import copy


# 权限装饰器：确保该类的所有公共方法都需要进行授权检查
@for_all_public_methods(check_authorization)
class AccessApi:
    """
    Access 插件的 API 类
    提供初始访问攻击的核心功能，包括能力执行、代理管理和任务分配
    """

    def __init__(self, services):
        """
        初始化 Access API
        
        Args:
            services: Caldera 服务容器，包含所有核心服务
        """
        # 获取数据服务：用于查询和管理 Caldera 中的各种数据对象
        self.data_svc = services.get('data_svc')
        # 获取 REST 服务：用于与代理进行通信和任务分配
        self.rest_svc = services.get('rest_svc')
        # 获取认证服务：用于权限验证和用户管理
        self.auth_svc = services.get('auth_svc')

    @template('access2.html')
    async def landing(self, request):
        """
        主界面数据准备方法
        为 Access 插件的 Web 界面提供所需的所有数据
        
        Args:
            request: HTTP 请求对象
            
        Returns:
            dict: 包含代理、能力、战术、混淆器等数据的字典
        """
        # 获取当前用户的权限列表，用于过滤可访问的资源
        search = dict(access=tuple(await self.auth_svc.get_permissions(request)))
        
        # 根据用户权限获取可访问的能力列表
        abilities = await self.data_svc.locate('abilities', match=search)
        
        # 从所有能力中提取战术类型，去重并排序
        # 例如：['execution', 'persistence', 'discovery', ...]
        tactics = sorted(list(set(a.tactic.lower() for a in abilities)))
        
        # 获取所有可用的混淆器，用于命令混淆
        obfuscators = [o.display for o in await self.data_svc.locate('obfuscators')]
        
        # 返回完整的数据字典，供前端模板使用
        return dict(
            # 用户有权限访问的代理列表
            agents=[a.display for a in await self.data_svc.locate('agents', match=search)],
            # 用户有权限使用的能力列表
            abilities=[a.display for a in abilities],
            # 所有可用的战术类型
            tactics=tactics,
            # 所有可用的混淆器
            obfuscators=obfuscators
        )

    async def exploit(self, request):
        """
        执行攻击方法
        向指定代理分配并执行攻击能力
        
        Args:
            request: HTTP 请求对象，包含攻击参数
            
        Returns:
            web.json_response: 执行完成的响应
        """
        # 解析请求中的 JSON 数据
        data = await request.json()
        
        # 将前端发送的事实数据转换为 Fact 对象
        # 事实数据用于动态替换能力命令中的变量
        # 例如：将 #{target.ip} 替换为实际的目标 IP
        converted_facts = [Fact(trait=f['trait'], value=f['value']) for f in data.get('facts', [])]
        
        # 调用 REST 服务向指定代理分配能力任务
        # 参数说明：
        # - data['paw']: 代理的唯一标识符
        # - data['ability_id']: 要执行的能力ID
        # - data['obfuscator']: 使用的混淆器名称
        # - converted_facts: 动态事实数据
        await self.rest_svc.task_agent_with_ability(
            data['paw'], 
            data['ability_id'], 
            data['obfuscator'], 
            converted_facts
        )
        
        # 返回执行完成的响应
        return web.json_response('complete')

    async def abilities(self, request):
        """
        获取代理可用能力方法
        根据选择的代理返回其能够执行的能力列表
        
        Args:
            request: HTTP 请求对象，包含代理 PAW
            
        Returns:
            web.json_response: 代理可执行的能力列表
        """
        # 解析请求中的 JSON 数据
        data = await request.json()
        
        # 构建代理搜索条件：权限 + PAW
        agent_search = dict(
            access=tuple(await self.auth_svc.get_permissions(request)), 
            paw=data['paw']
        )
        
        # 根据搜索条件查找指定代理
        agent = (await self.data_svc.locate('agents', match=agent_search))[0]
        
        # 构建能力搜索条件：仅基于用户权限
        ability_search = dict(access=tuple(await self.auth_svc.get_permissions(request)))
        
        # 获取用户有权限的所有能力
        abilities = await self.data_svc.locate('abilities', match=ability_search)
        
        # 检查代理能够执行哪些能力
        # 这包括平台兼容性、执行器可用性等检查
        capable_abilities = await agent.capabilities(list(abilities))
        
        # 返回代理可执行的能力列表
        return web.json_response([a.display for a in capable_abilities])

    async def executor(self, request):
        """
        获取执行器信息方法
        为指定的代理和能力找到最佳的执行器
        
        Args:
            request: HTTP 请求对象，包含代理 PAW 和能力 ID
            
        Returns:
            web.json_response: 优化后的能力信息或错误信息
        """
        # 解析请求中的 JSON 数据
        data = await request.json()
        
        # 构建代理搜索条件：权限 + PAW
        agent_search = dict(
            access=tuple(await self.auth_svc.get_permissions(request)), 
            paw=data['paw']
        )
        
        # 查找指定代理
        agent = (await self.data_svc.locate('agents', match=agent_search))[0]
        
        # 构建能力搜索条件：权限 + 能力 ID
        ability_search = dict(
            access=tuple(await self.auth_svc.get_permissions(request)), 
            ability_id=data['ability_id']
        )
        
        # 查找指定能力
        ability = (await self.data_svc.locate('abilities', match=ability_search))[0]
        
        # 获取代理对该能力的最佳执行器
        # 执行器选择基于平台兼容性、可用性等因素
        executor = await agent.get_preferred_executor(ability)
        
        # 如果没有找到合适的执行器，返回错误信息
        if not executor:
            return web.json_response(dict(error='Executor not found for ability'))
        
        # 创建能力的深拷贝，避免修改原始对象
        trimmed_ability = copy.deepcopy(ability)
        
        # 移除能力中的所有执行器
        trimmed_ability.remove_all_executors()
        
        # 只添加最佳执行器，优化能力对象
        trimmed_ability.add_executor(executor)
        
        # 返回优化后的能力信息
        return web.json_response(trimmed_ability.display)