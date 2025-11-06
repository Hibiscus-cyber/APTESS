from pathlib import Path
import asyncio, uuid, re, yaml, shutil
import sys
import traceback
import pathlib
import json 
import aiohttp_apispec 
from json import JSONDecodeError 
from aiohttp import web 
from app.api.v2.handlers.base_object_api import BaseObjectApi 
from .profile_api_manager import ProfileApiManager 
from app.api.v2.schemas.base_schemas import BaseGetAllQuerySchema, BaseGetOneQuerySchema 
from app.objects.c_profile import ProfileSchema, Profile 

class ProfileApi(BaseObjectApi):
    def __init__(self, services):
        super().__init__(description='profile',obj_class=Profile, schema=ProfileSchema, ram_key='profiles', id_property='profile_id', auth_svc=services['auth_svc']) 
        self._api_manager = ProfileApiManager(data_svc=services['data_svc'], file_svc=services['file_svc'])
        self._data_svc = services['data_svc']
    async def options_ok(request): return web.Response() 

    def add_routes(self, app: web.Application):
        router = app.router
        profiles_by_id_path = '/api/v2/profiles/{profile_id}' 
        router.add_get('/api/v2/profiles', self.get_profiles) 
        router.add_get(profiles_by_id_path, self.get_profile_by_id) 
        router.add_post('/api/v2/profiles', self.create_profile) 
        router.add_patch('/api/v2/profiles', self.update_profile) 
        # router.add_put(profiles_by_id_path, self.create_or_update_profile) 
        router.add_delete('/api/v2/profiles/by-name/{file_name}', self.delete_on_disk_object_by_name) 

        # app.router.add_route('OPTIONS', '/api/v2/profiles', self.options_ok)
        # app.router.add_route('OPTIONS', '/api/v2/profiles/', self.options_ok)    
    @aiohttp_apispec.docs(tags=['profiles'], summary='Get all profiles.', description='Provides a list of all available profiles.') 
    @aiohttp_apispec.querystring_schema(BaseGetAllQuerySchema) 
    @aiohttp_apispec.response_schema(ProfileSchema(many=True, partial=True), description='Returns a list of all profiles.') 
    
    async def get_profiles(self, request: web.Request): 
        profiles = await self.get_all_objects(request) 
        return web.json_response(profiles) 

    async def get_profile_by_id(self, request: web.Request): 
        profile = await self.get_object(request) 
        return web.json_response(profile)


    async def create_profile(self, request: web.Request):
        profile = await self.create_on_disk_object(request)
        return web.json_response(profile.display)

    async def delete_profile(self, request: web.Request):
        await self.delete_on_disk_object(request)
        return web.HTTPNoContent()

    async def delete_on_disk_object_by_name(self, request: web.Request):
        
        file_name = request.match_info['file_name']

        # 1) 先找出所有同名对象（为了拿到它们的 id 做磁盘删除）
        items = await self._data_svc.locate(self.ram_key, {'file_name': file_name})
        if not items:
            return web.json_response(
                {'status': 'error', 'error': f'{self.ram_key} named "{file_name}" not found'},
                status=404
            )

        # 2) 先从 RAM 删除所有 file_name 命中的对象
        await self._data_svc.remove(self.ram_key, {'file_name': file_name})

        # 3) 再逐个按 id 从磁盘删除
        deleted_ids = []
        for obj in items:
            obj_id = getattr(obj, self.id_property, None) or getattr(obj, 'id', None)
            if obj_id:
                await self._api_manager.remove_object_from_disk_by_id(
                    identifier=obj_id,
                    ram_key=self.ram_key
                )
                deleted_ids.append(obj_id)

        return web.json_response({
            'status': 'success',
            'deleted_name': file_name,
            'count': len(items),
            'deleted_ids': deleted_ids
        })

    async def update_profile(self, request: web.Request):
        # 读原始 body，方便调试
        raw = await request.text()
        # 1. 解析 JSON
        try:
            data = json.loads(raw)
        except JSONDecodeError as e: 
            return web.json_response({'error': f'Invalid JSON: {e}'}, status=400)
    
        # 2. 拿 profile_id
        profile_id = data.get('profile_id')
        if not profile_id:
            return web.json_response({'error': 'Missing profile_id in body'}, status=400)

        try:
            # 3. 利用 BaseApiManager 封装好的更新方法
            #    它会：找到对象 → 合并 data → 写回 YAML → 重新加载到 RAM
            updated_obj = await self._api_manager.find_and_update_on_disk_object(
                data=data,
                search={'profile_id': profile_id},
                ram_key=self.ram_key,          # 在 BaseObjectApi 里定义的
                id_property=self.id_property,  # 这里就是 "profile_id"
                obj_class=self.obj_class       # 这里就是 Profile
            )

            if not updated_obj:
                return web.json_response(
                    {'error': f'Profile {profile_id} not found'},
                    status=404
                )
            # 4. 正常返回
            return web.json_response({
                'status': 'success',
                'updated_id': profile_id,
                'profile': updated_obj.display
            })
        except Exception as e:
            tb = traceback.format_exc()
            print("Unexpected error in update_profile:", tb, file=sys.stderr)
            return web.json_response({'error': 'server_error', 'trace': tb}, status=500)
