import os
import yaml
import zipfile
import tempfile
import shutil
import uuid
from datetime import datetime
from typing import List, Dict, Any

from app.service.interfaces.i_data_svc import DataServiceInterface
from app.utility.base_service import BaseService
from plugins.payloadmanager.app.c_payload import Payload, PayloadSchema


class PayloadManagerService(BaseService):
    """恶意载荷管理服务"""

    def __init__(self):
        self.log = self.add_service('恶意载荷库服务', self)
        self.data_dir = 'plugins/payloadmanager/data'
        self.payloads_dir = 'plugins/payloadmanager/data/payloads'
        
    async def initialize(self):
        """初始化服务"""
        await self._ensure_directories()
        await self._load_payloads()
        
    async def _ensure_directories(self):
        """确保必要的目录存在"""
        directories = [
            self.data_dir,
            self.payloads_dir,
            os.path.join(self.payloads_dir, 'windows'),
            os.path.join(self.payloads_dir, 'linux'),
            os.path.join(self.payloads_dir, 'darwin'),
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
            
        # 为每个平台创建战术子目录
        tactics = ['discovery', 'execution', 'persistence', 'privilege-escalation',
                  'defense-evasion', 'credential-access', 'collection', 
                  'command-and-control', 'exfiltration', 'impact', 'lateral-movement']
        
        for platform in ['windows', 'linux', 'darwin']:
            for tactic in tactics:
                tactic_dir = os.path.join(self.payloads_dir, platform, tactic)
                os.makedirs(tactic_dir, exist_ok=True)

    async def _load_payloads(self):
        """加载所有恶意载荷"""
        try:
            # 遍历所有平台的payloads目录
            for platform in ['windows', 'linux', 'darwin']:
                platform_dir = os.path.join(self.payloads_dir, platform)
                if not os.path.exists(platform_dir):
                    continue
                    
                # 遍历所有战术目录
                for tactic in os.listdir(platform_dir):
                    tactic_dir = os.path.join(platform_dir, tactic)
                    if not os.path.isdir(tactic_dir):
                        continue
                        
                    # 加载该目录下的所有YAML文件
                    for yaml_file in os.listdir(tactic_dir):
                        if yaml_file.endswith('.yml'):
                            yaml_path = os.path.join(tactic_dir, yaml_file)
                            await self._load_payload_from_yaml(yaml_path)
            
            self.log.info('恶意载荷库: 已加载载荷数据')
        except Exception as e:
            self.log.error(f'恶意载荷库: 加载载荷数据失败 - {e}')

    async def _load_payload_from_yaml(self, yaml_path):
        """从YAML文件加载单个payload"""
        try:
            with open(yaml_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            if not data or not isinstance(data, list) or len(data) == 0:
                return
                
            payload_data = data[0]
            
            # 确保有payload_id
            if 'id' in payload_data:
                payload_data['payload_id'] = payload_data.pop('id')
            elif 'payload_id' not in payload_data:
                payload_data['payload_id'] = str(uuid.uuid4())
            
            # 创建Payload对象
            payload = Payload(**payload_data)
            
            # 如果文件存在，计算MD5和文件大小
            if payload.payload_file and os.path.exists(payload.payload_file):
                if not payload.md5:
                    payload.md5 = payload.calculate_md5(payload.payload_file)
                if not payload.file_size:
                    payload.file_size = payload.get_file_size(payload.payload_file)
            
            # 存储到内存
            data_svc = self.get_service('data_svc')
            payload.store(data_svc.ram)
            
            self.log.debug(f'Loaded payload: {payload.name} from {yaml_path}')
            
        except Exception as e:
            self.log.error(f'Error loading payload from {yaml_path}: {e}')

    async def create_payload(self, payload_data: Dict[str, Any], file_data=None) -> Payload:
        """创建新的恶意载荷"""
        try:
            # 验证必需字段
            required_fields = ['name', 'description', 'tactics', 'platforms', 'threat_level']
            for field in required_fields:
                if not payload_data.get(field):
                    raise ValueError(f'缺少必需字段: {field}')

            # 创建Payload对象
            payload = Payload(**payload_data)
            
            # 如果有文件数据，保存文件并更新信息
            if file_data:
                file_path = await self._save_payload_file(payload, file_data)
                payload.payload_file = file_path
                payload.md5 = payload.calculate_md5(file_path)
                payload.file_size = payload.get_file_size(file_path)
                
                # 从文件扩展名推断文件类型
                if not payload.file_type:
                    payload.file_type = os.path.splitext(file_path)[1][1:].lower()

            # 设置时间戳
            now = datetime.now()
            payload.created_date = now
            payload.modified_date = now

            # 存储到内存
            data_svc = self.get_service('data_svc')
            stored_payload = payload.store(data_svc.ram)
            
            # 保存到文件
            await self._save_payload_to_file(stored_payload)
            
            self.log.info(f'已创建载荷: {payload.name} ({payload.payload_id})')
            return stored_payload
            
        except Exception as e:
            self.log.error(f'Error creating payload: {e}')
            raise

    async def update_payload(self, payload_id: str, payload_data: Dict[str, Any], file_data=None) -> Payload:
        """更新恶意载荷"""
        try:
            data_svc = self.get_service('data_svc')
            payloads = await data_svc.locate('payloads', match=dict(payload_id=payload_id))
            
            if not payloads:
                raise ValueError(f'未找到载荷: {payload_id}')
                
            payload = payloads[0]
            
            # 更新字段
            for key, value in payload_data.items():
                if hasattr(payload, key):
                    setattr(payload, key, value)
            
            # 如果有新文件，更新文件信息
            if file_data:
                file_path = await self._save_payload_file(payload, file_data)
                payload.payload_file = file_path
                payload.md5 = payload.calculate_md5(file_path)
                payload.file_size = payload.get_file_size(file_path)
                
                if not payload.file_type:
                    payload.file_type = os.path.splitext(file_path)[1][1:].lower()

            payload.modified_date = datetime.now()
            
            # 保存到文件
            await self._save_payload_to_file(payload)
            
            self.log.info(f'已更新载荷: {payload.name} ({payload.payload_id})')
            return payload
            
        except Exception as e:
            self.log.error(f'Error updating payload: {e}')
            raise

    async def delete_payload(self, payload_id: str) -> bool:
        """删除恶意载荷"""
        try:
            data_svc = self.get_service('data_svc')
            payloads = await data_svc.locate('payloads', match=dict(payload_id=payload_id))
            
            if not payloads:
                return False
                
            payload = payloads[0]
            
            # 删除文件
            if payload.payload_file and os.path.exists(payload.payload_file):
                os.remove(payload.payload_file)
            
            # 从内存中删除
            await data_svc.remove('payloads', dict(payload_id=payload_id))
            
            # 删除YAML文件
            yaml_file = await self._get_payload_yaml_path(payload)
            if os.path.exists(yaml_file):
                os.remove(yaml_file)
            
            self.log.info(f'已删除载荷: {payload.name} ({payload.payload_id})')
            return True
            
        except Exception as e:
            self.log.error(f'Error deleting payload: {e}')
            return False

    async def get_payloads(self, filters: Dict[str, Any] = None) -> List[Payload]:
        """获取恶意载荷列表"""
        try:
            data_svc = self.get_service('data_svc')
            payloads = await data_svc.locate('payloads')
            
            if filters:
                filtered_payloads = []
                for payload in payloads:
                    match = True
                    
                    # 平台筛选
                    if 'platforms' in filters and filters['platforms']:
                        if not any(platform in payload.platforms for platform in filters['platforms']):
                            match = False
                    
                    # 战术筛选
                    if 'tactics' in filters and filters['tactics']:
                        if not any(tactic in payload.tactics for tactic in filters['tactics']):
                            match = False
                    
                    # 威胁等级筛选
                    if 'threat_level' in filters and filters['threat_level']:
                        if payload.threat_level != filters['threat_level']:
                            match = False
                    
                    # 搜索关键词
                    if 'search' in filters and filters['search']:
                        search_term = filters['search'].lower()
                        if not (search_term in payload.name.lower() or 
                               search_term in payload.description.lower()):
                            match = False
                    
                    if match:
                        filtered_payloads.append(payload)
                
                return filtered_payloads
            
            return payloads
            
        except Exception as e:
            self.log.error(f'Error getting payloads: {e}')
            return []

    async def _save_payload_file(self, payload: Payload, file_data) -> str:
        """保存载荷文件"""
        # 确定文件保存路径
        platform = payload.platforms[0] if payload.platforms else 'windows'
        tactic = payload.tactics[0] if payload.tactics else 'execution'
        
        file_dir = os.path.join(self.payloads_dir, platform, tactic)
        
        # 使用描述性文件名而不是UUID
        file_name = f"{payload.name.lower().replace(' ', '-')}.{payload.file_type or 'bin'}"
        file_path = os.path.join(file_dir, file_name)
        
        # 确保目录存在
        os.makedirs(file_dir, exist_ok=True)
        
        # 保存文件
        with open(file_path, 'wb') as f:
            f.write(file_data)
        
        return file_path

    async def _save_payload_to_file(self, payload: Payload):
        """保存载荷元数据到YAML文件"""
        yaml_file = await self._get_payload_yaml_path(payload)
        
        # 准备数据
        payload_data = PayloadSchema().dump(payload)
        payload_data['id'] = payload_data.pop('payload_id')
        
        # 保存YAML文件
        with open(yaml_file, 'w', encoding='utf-8') as f:
            yaml.dump([payload_data], f, default_flow_style=False, allow_unicode=True)

    async def _get_payload_yaml_path(self, payload: Payload) -> str:
        """获取载荷YAML文件路径（基于平台和战术分类）"""
        # 确定平台和战术
        platform = payload.platforms[0] if payload.platforms else 'windows'
        tactic = payload.tactics[0] if payload.tactics else 'execution'
        
        # 创建文件名（使用描述性名称）
        file_name = f"{payload.name.lower().replace(' ', '-')}.yml"
        
        # 构建路径
        yaml_dir = os.path.join(self.payloads_dir, platform, tactic)
        yaml_file = os.path.join(yaml_dir, file_name)
        
        return yaml_file

    async def export_payloads(self, payload_ids: List[str] = None, include_files: bool = True) -> bytes:
        """导出载荷数据"""
        try:
            payloads = await self.get_payloads()
            if payload_ids:
                payloads = [p for p in payloads if p.payload_id in payload_ids]
            
            # 创建临时ZIP文件
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
            temp_file.close()
            
            with zipfile.ZipFile(temp_file.name, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for payload in payloads:
                    # 添加YAML元数据
                    yaml_data = PayloadSchema().dump(payload)
                    yaml_data['id'] = yaml_data.pop('payload_id')
                    yaml_content = yaml.dump([yaml_data], default_flow_style=False, allow_unicode=True)
                    
                    zipf.writestr(f"payloads/{payload.payload_id}.yml", yaml_content)
                    
                    # 添加实际文件
                    if include_files and payload.payload_file and os.path.exists(payload.payload_file):
                        zipf.write(payload.payload_file, f"files/{os.path.basename(payload.payload_file)}")
            
            # 读取ZIP文件内容
            with open(temp_file.name, 'rb') as f:
                zip_content = f.read()
            
            # 清理临时文件
            os.unlink(temp_file.name)
            
            return zip_content
            
        except Exception as e:
            self.log.error(f'Error exporting payloads: {e}')
            raise

    async def import_payloads(self, zip_data: bytes) -> int:
        """导入载荷数据"""
        try:
            imported_count = 0
            
            # 创建临时目录
            with tempfile.TemporaryDirectory() as temp_dir:
                zip_file = os.path.join(temp_dir, 'import.zip')
                
                # 写入ZIP文件
                with open(zip_file, 'wb') as f:
                    f.write(zip_data)
                
                # 解压ZIP文件
                with zipfile.ZipFile(zip_file, 'r') as zipf:
                    zipf.extractall(temp_dir)
                
                # 处理YAML文件
                yaml_dir = os.path.join(temp_dir, 'payloads')
                files_dir = os.path.join(temp_dir, 'files')
                
                if os.path.exists(yaml_dir):
                    for yaml_file in os.listdir(yaml_dir):
                        if yaml_file.endswith('.yml'):
                            yaml_path = os.path.join(yaml_dir, yaml_file)
                            
                            # 读取YAML数据
                            with open(yaml_path, 'r', encoding='utf-8') as f:
                                yaml_data = yaml.safe_load(f)[0]
                            
                            # 处理文件引用
                            if 'payload_file' in yaml_data and os.path.exists(files_dir):
                                original_file = os.path.basename(yaml_data['payload_file'])
                                source_file = os.path.join(files_dir, original_file)
                                
                                if os.path.exists(source_file):
                                    # 读取文件数据
                                    with open(source_file, 'rb') as f:
                                        file_data = f.read()
                                    
                                    # 创建载荷
                                    await self.create_payload(yaml_data, file_data)
                                    imported_count += 1
                                else:
                                    # 只导入元数据
                                    await self.create_payload(yaml_data)
                                    imported_count += 1
                            else:
                                # 只导入元数据
                                await self.create_payload(yaml_data)
                                imported_count += 1
            
            self.log.info(f'已导入 {imported_count} 个载荷')
            return imported_count
            
        except Exception as e:
            self.log.error(f'Error importing payloads: {e}')
            raise
