import aiohttp_apispec
from aiohttp import web
from aiohttp.web_request import Request
from aiohttp.web_response import Response
import json

from app.api.v2.handlers.base_object_api import BaseObjectApi
from app.api.v2.managers.base_api_manager import BaseApiManager
from app.api.v2.schemas.base_schemas import BaseGetAllQuerySchema, BaseGetOneQuerySchema
from plugins.payloadmanager.app.c_payload import Payload, PayloadSchema


class PayloadApi(BaseObjectApi):
    """恶意载荷API处理器"""

    def __init__(self, services):
        super().__init__(description='payload', obj_class=Payload, schema=PayloadSchema, 
                         ram_key='payloads', id_property='payload_id', auth_svc=services['auth_svc'])
        self._api_manager = BaseApiManager(data_svc=services['data_svc'], file_svc=services['file_svc'])
        self._payload_service = services['恶意载荷库服务']

    def add_routes(self, app: web.Application):
        """添加API路由"""
        router = app.router
        router.add_get('/payloads', self.get_payloads)
        router.add_get('/payloads/{payload_id}', self.get_payload_by_id)
        router.add_post('/payloads', self.create_payload)
        router.add_put('/payloads/{payload_id}', self.create_or_update_payload)
        router.add_patch('/payloads/{payload_id}', self.update_payload)
        router.add_delete('/payloads/{payload_id}', self.delete_payload)
        router.add_post('/payloads/import', self.import_payloads)
        router.add_get('/payloads/export', self.export_payloads)
        router.add_get('/payloads/filters', self.get_filter_options)

    @aiohttp_apispec.docs(tags=['payloads'], summary='Get all payloads.',
                          description='Provides a list of all available payloads with optional filtering.')
    @aiohttp_apispec.querystring_schema(BaseGetAllQuerySchema)
    @aiohttp_apispec.response_schema(PayloadSchema(many=True, partial=True),
                                     description='Returns a list of all payloads.')
    async def get_payloads(self, request: Request) -> Response:
        """获取所有恶意载荷"""
        try:
            # 解析查询参数
            query_params = dict(request.query)
            filters = {}
            
            # 处理筛选参数
            if 'platforms' in query_params:
                filters['platforms'] = query_params['platforms'].split(',')
            if 'tactics' in query_params:
                filters['tactics'] = query_params['tactics'].split(',')
            if 'threat_level' in query_params:
                filters['threat_level'] = query_params['threat_level']
            if 'search' in query_params:
                filters['search'] = query_params['search']
            
            # 获取载荷列表
            payloads = await self._payload_service.get_payloads(filters)
            
            # 转换为显示格式
            payload_data = [payload.display for payload in payloads]
            
            return web.json_response(payload_data)
            
        except Exception as e:
            self.log.error(f'Error getting payloads: {e}')
            return web.json_response({'error': f'获取载荷列表失败: {str(e)}'}, status=500)

    @aiohttp_apispec.docs(tags=['payloads'], summary='Get a payload.',
                          description='Provides one payload based on its payload id.',
                          parameters=[{
                              'in': 'path',
                              'name': 'payload_id',
                              'schema': {'type': 'string'},
                              'required': 'true',
                              'description': 'UUID of the Payload to be retrieved'
                          }])
    @aiohttp_apispec.querystring_schema(BaseGetOneQuerySchema)
    @aiohttp_apispec.response_schema(PayloadSchema(partial=True),
                                     description='JSON dictionary representation of the existing Payload.')
    async def get_payload_by_id(self, request: Request) -> Response:
        """根据ID获取单个恶意载荷"""
        try:
            payload_id = request.match_info['payload_id']
            data_svc = self.get_service('data_svc')
            payloads = await data_svc.locate('payloads', match=dict(payload_id=payload_id))
            
            if not payloads:
                return web.json_response({'error': '未找到指定的载荷'}, status=404)
            
            return web.json_response(payloads[0].display)
            
        except Exception as e:
            self.log.error(f'Error getting payload by ID: {e}')
            return web.json_response({'error': f'获取载荷详情失败: {str(e)}'}, status=500)

    @aiohttp_apispec.docs(tags=['payloads'], summary='Create a new payload.',
                          description='Creates a new payload based on the PayloadSchema.')
    @aiohttp_apispec.request_schema(PayloadSchema)
    @aiohttp_apispec.response_schema(PayloadSchema,
                                     description='JSON dictionary representation of the created Payload.')
    async def create_payload(self, request: Request) -> Response:
        """创建新的恶意载荷"""
        try:
            # 解析请求数据
            data = await request.json()
            
            # 处理文件上传
            file_data = None
            if hasattr(request, 'form') and 'file' in request.form:
                file_data = request.form['file'].file.read()
            
            # 创建载荷
            payload = await self._payload_service.create_payload(data, file_data)
            
            return web.json_response(payload.display)
            
        except Exception as e:
            self.log.error(f'Error creating payload: {e}')
            return web.json_response({'error': f'创建载荷失败: {str(e)}'}, status=400)
            
    @aiohttp_apispec.docs(tags=['payloads'], summary='Create or update a payload.',
                          description='Creates a new payload or updates an existing one based on the PayloadSchema.')
    @aiohttp_apispec.request_schema(PayloadSchema)
    @aiohttp_apispec.response_schema(PayloadSchema,
                                     description='JSON dictionary representation of the created or updated Payload.')
    async def create_or_update_payload(self, request: Request) -> Response:
        """创建或更新恶意载荷"""
        try:
            payload_id = request.match_info['payload_id']
            data = await request.json()
            
            # 检查载荷是否存在
            data_svc = self.get_service('data_svc')
            existing_payloads = await data_svc.locate('payloads', match=dict(payload_id=payload_id))
            
            if existing_payloads:
                # 更新现有载荷
                return await self.update_payload(request)
            else:
                # 创建新载荷
                return await self.create_payload(request)
                
        except Exception as e:
            self.log.error(f'Error creating or updating payload: {e}')
            return web.json_response({'error': f'创建或更新载荷失败: {str(e)}'}, status=400)

    @aiohttp_apispec.docs(tags=['payloads'], summary='Update an existing payload.',
                          description='Updates a payload based on the PayloadSchema values provided.')
    @aiohttp_apispec.request_schema(PayloadSchema(partial=True))
    @aiohttp_apispec.response_schema(PayloadSchema,
                                     description='JSON dictionary representation of the updated Payload.')
    async def update_payload(self, request: Request) -> Response:
        """更新恶意载荷"""
        try:
            payload_id = request.match_info['payload_id']
            data = await request.json()
            
            # 处理文件上传
            file_data = None
            if hasattr(request, 'form') and 'file' in request.form:
                file_data = request.form['file'].file.read()
            
            # 更新载荷
            payload = await self._payload_service.update_payload(payload_id, data, file_data)
            
            return web.json_response(payload.display)
            
        except Exception as e:
            self.log.error(f'Error updating payload: {e}')
            return web.json_response({'error': f'更新载荷失败: {str(e)}'}, status=400)

    @aiohttp_apispec.docs(tags=['payloads'], summary='Delete a payload.',
                          description='Deletes an existing payload.')
    async def delete_payload(self, request: Request) -> Response:
        """删除恶意载荷"""
        try:
            payload_id = request.match_info['payload_id']
            success = await self._payload_service.delete_payload(payload_id)
            
            if success:
                return web.HTTPNoContent()
            else:
                return web.json_response({'error': '未找到指定的载荷'}, status=404)
                
        except Exception as e:
            self.log.error(f'Error deleting payload: {e}')
            return web.json_response({'error': f'删除载荷失败: {str(e)}'}, status=500)

    @aiohttp_apispec.docs(tags=['payloads'], summary='Import payloads.',
                          description='Import payloads from a ZIP file.')
    async def import_payloads(self, request: Request) -> Response:
        """导入恶意载荷"""
        try:
            # 获取上传的文件
            data = await request.read()
            
            # 导入载荷
            imported_count = await self._payload_service.import_payloads(data)
            
            return web.json_response({
                'message': f'成功导入 {imported_count} 个载荷',
                'imported_count': imported_count
            })
            
        except Exception as e:
            self.log.error(f'Error importing payloads: {e}')
            return web.json_response({'error': f'导入载荷失败: {str(e)}'}, status=400)

    @aiohttp_apispec.docs(tags=['payloads'], summary='Export payloads.',
                          description='Export payloads to a ZIP file.')
    async def export_payloads(self, request: Request) -> Response:
        """导出恶意载荷"""
        try:
            # 解析查询参数
            query_params = dict(request.query)
            payload_ids = None
            include_files = True
            
            if 'payload_ids' in query_params:
                payload_ids = query_params['payload_ids'].split(',')
            if 'include_files' in query_params:
                include_files = query_params['include_files'].lower() == 'true'
            
            # 导出载荷
            zip_data = await self._payload_service.export_payloads(payload_ids, include_files)
            
            # 返回ZIP文件
            response = web.Response(body=zip_data)
            response.headers['Content-Type'] = 'application/zip'
            response.headers['Content-Disposition'] = 'attachment; filename="载荷导出.zip"'
            
            return response
            
        except Exception as e:
            self.log.error(f'Error exporting payloads: {e}')
            return web.json_response({'error': f'导出载荷失败: {str(e)}'}, status=500)

    @aiohttp_apispec.docs(tags=['payloads'], summary='Get filter options.',
                          description='Get available filter options for payloads.')
    async def get_filter_options(self, request: Request) -> Response:
        """获取筛选选项"""
        try:
            data_svc = self.get_service('data_svc')
            payloads = await data_svc.locate('payloads')
            
            # 收集所有可能的选项
            platforms = set()
            tactics = set()
            threat_levels = set()
            file_types = set()
            
            for payload in payloads:
                platforms.update(payload.platforms)
                tactics.update(payload.tactics)
                threat_levels.add(payload.threat_level)
                if payload.file_type:
                    file_types.add(payload.file_type)
            
            filter_options = {
                'platforms': sorted(list(platforms)),
                'tactics': sorted(list(tactics)),
                'threat_levels': sorted(list(threat_levels)),
                'file_types': sorted(list(file_types))
            }
            
            return web.json_response(filter_options)
            
        except Exception as e:
            self.log.error(f'Error getting filter options: {e}')
            return web.json_response({'error': f'获取筛选选项失败: {str(e)}'}, status=500)
