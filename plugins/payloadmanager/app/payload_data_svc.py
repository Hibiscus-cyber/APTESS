import os
import yaml
import glob
from typing import List

from app.service.interfaces.i_data_svc import DataServiceInterface
from plugins.payloadmanager.app.c_payload import Payload


class PayloadDataService(DataServiceInterface):
    """恶意载荷数据服务扩展"""

    async def load_data(self):
        """加载数据"""
        pass

    async def store(self, ram_key: str, data: dict):
        """存储数据"""
        pass

    async def locate(self, ram_key: str, match: dict = None):
        """定位数据"""
        pass

    async def remove(self, ram_key: str, match: dict):
        """删除数据"""
        pass

    async def apply(self, ram_key: str, match: dict, update: dict):
        """应用更新"""
        pass

    async def reload_data(self):
        """重新加载数据"""
        pass

    async def save_state(self):
        """保存状态"""
        pass

    async def restore_state(self):
        """恢复状态"""
        pass

    async def destroy(self):
        """销毁服务"""
        pass

    async def load_payload_files(self, data_dir: str):
        """加载恶意载荷文件"""
        try:
            # 确保payloads在RAM中初始化
            if 'payloads' not in self.ram:
                self.ram['payloads'] = []
            
            # 查找所有YAML文件（递归查找子目录）
            payloads_dir = os.path.join(data_dir, 'payloads')
            yaml_pattern = os.path.join(payloads_dir, '**', '*.yml')
            yaml_files = glob.glob(yaml_pattern, recursive=True)
            
            for yaml_file in yaml_files:
                await self.load_payload_file(yaml_file)
                
            self.log.info(f'Loaded {len(self.ram["payloads"])} payloads from {len(yaml_files)} files')
            
        except Exception as e:
            self.log.error(f'Error loading payload files: {e}')

    async def load_payload_file(self, filename: str):
        """加载单个恶意载荷文件"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            if not data or not isinstance(data, list):
                return
                
            for payload_data in data:
                # 处理ID字段
                payload_id = payload_data.pop('id', None)
                if not payload_id:
                    continue
                
                # 创建Payload对象
                payload = Payload(
                    payload_id=payload_id,
                    name=payload_data.get('name', ''),
                    description=payload_data.get('description', ''),
                    md5=payload_data.get('md5'),
                    file_type=payload_data.get('file_type'),
                    file_size=payload_data.get('file_size'),
                    payload_file=payload_data.get('payload_file'),
                    tactics=payload_data.get('tactics', []),
                    threat_level=payload_data.get('threat_level'),
                    platforms=payload_data.get('platforms', []),
                    cve_references=payload_data.get('cve_references', []),
                    apt_groups=payload_data.get('apt_groups', []),
                    tags=payload_data.get('tags', []),
                    plugin='payloadmanager',
                    **payload_data
                )
                
                # 存储到RAM
                payload.store(self.ram)
                
        except Exception as e:
            self.log.error(f'Error loading payload file {filename}: {e}')
