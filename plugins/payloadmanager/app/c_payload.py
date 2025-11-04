import collections
import logging
import uuid
import os
import hashlib
from datetime import datetime

import marshmallow as ma

from app.objects.interfaces.i_object import FirstClassObjectInterface
from app.utility.base_object import BaseObject
from app.utility.base_world import AccessSchema


class PayloadSchema(ma.Schema):
    """恶意载荷数据模式"""
    
    class Meta:
        unknown = ma.EXCLUDE

    payload_id = ma.fields.String()
    name = ma.fields.String(load_default=None)
    description = ma.fields.String(load_default=None)
    md5 = ma.fields.String(load_default=None)
    file_type = ma.fields.String(load_default=None)
    file_size = ma.fields.Integer(load_default=None)
    payload_file = ma.fields.String(load_default=None)
    tactics = ma.fields.List(ma.fields.String(), load_default=None)
    threat_level = ma.fields.String(load_default=None)
    platforms = ma.fields.List(ma.fields.String(), load_default=None)
    cve_references = ma.fields.List(ma.fields.String(), load_default=None)
    apt_groups = ma.fields.List(ma.fields.String(), load_default=None)
    tags = ma.fields.List(ma.fields.String(), load_default=None)
    access = ma.fields.Nested(AccessSchema, load_default=None)
    plugin = ma.fields.String(load_default=None)
    created_date = ma.fields.DateTime(load_default=None)
    modified_date = ma.fields.DateTime(load_default=None)

    @ma.pre_load
    def fix_id(self, data, **_):
        if 'id' in data:
            data['payload_id'] = data.pop('id')
        return data

    @ma.post_load
    def build_payload(self, data, **kwargs):
        return None if kwargs.get('partial') is True else Payload(**data)


class Payload(FirstClassObjectInterface, BaseObject):
    """恶意载荷对象"""

    schema = PayloadSchema()
    display_schema = PayloadSchema()

    HOOKS = dict()

    # 威胁等级常量
    THREAT_LEVELS = ['Low', 'Medium', 'High', 'Critical']
    
    # 支持的平台
    SUPPORTED_PLATFORMS = ['windows', 'linux', 'darwin']
    
    # 支持的文件类型
    SUPPORTED_FILE_TYPES = ['exe', 'dll', 'ps1', 'sh', 'py', 'bat', 'cmd', 'scr', 'zip', 'rar', 'bin']

    @property
    def unique(self):
        return self.payload_id

    def __init__(self, payload_id='', name=None, description=None, md5=None, file_type=None,
                 file_size=None, payload_file=None, tactics=None, threat_level=None,
                 platforms=None, cve_references=None, apt_groups=None, tags=None,
                 access=None, plugin='', created_date=None, modified_date=None, **kwargs):
        super().__init__()
        
        self.payload_id = payload_id if payload_id else str(uuid.uuid4())
        self.name = name
        self.description = description
        self.md5 = md5
        self.file_type = file_type
        self.file_size = file_size
        self.payload_file = payload_file
        self.tactics = tactics if tactics else []
        self.threat_level = threat_level
        self.platforms = platforms if platforms else []
        self.cve_references = cve_references if cve_references else []
        self.apt_groups = apt_groups if apt_groups else []
        self.tags = tags if tags else []
        self.plugin = plugin
        self.created_date = created_date
        self.modified_date = modified_date
        
        if access:
            self.access = self.Access(access)
        else:
            self.access = None

    def store(self, ram):
        """存储载荷到内存"""
        existing = self.retrieve(ram['payloads'], self.unique)
        if not existing:
            # 检查名称冲突
            name_match = [x for x in ram['payloads'] if x.name == self.name]
            if name_match:
                self.name = self.name + " (2)"
                logging.debug(f"Collision in payload name detected for {self.payload_id} and {name_match[0].payload_id} "
                              f"({name_match[0].name}). Modifying name of the second payload to {self.name}...")
            ram['payloads'].append(self)
            return self.retrieve(ram['payloads'], self.unique)
        
        # 更新现有载荷
        existing.update('name', self.name)
        existing.update('description', self.description)
        existing.update('md5', self.md5)
        existing.update('file_type', self.file_type)
        existing.update('file_size', self.file_size)
        existing.update('payload_file', self.payload_file)
        existing.update('tactics', self.tactics)
        existing.update('threat_level', self.threat_level)
        existing.update('platforms', self.platforms)
        existing.update('cve_references', self.cve_references)
        existing.update('apt_groups', self.apt_groups)
        existing.update('tags', self.tags)
        existing.update('plugin', self.plugin)
        existing.update('modified_date', self.modified_date)
        return existing

    async def which_plugin(self):
        return self.plugin

    def calculate_md5(self, file_path):
        """计算文件MD5值"""
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            logging.error(f"Error calculating MD5 for {file_path}: {e}")
            return None

    def get_file_size(self, file_path):
        """获取文件大小"""
        try:
            return os.path.getsize(file_path)
        except Exception as e:
            logging.error(f"Error getting file size for {file_path}: {e}")
            return None

    def validate_threat_level(self, level):
        """验证威胁等级"""
        return level in self.THREAT_LEVELS

    def validate_platform(self, platform):
        """验证平台"""
        return platform in self.SUPPORTED_PLATFORMS

    def validate_file_type(self, file_type):
        """验证文件类型"""
        return file_type in self.SUPPORTED_FILE_TYPES

    def get_tactic_display_name(self, tactic):
        """获取战术显示名称"""
        tactic_names = {
            'discovery': 'Discovery',
            'execution': 'Execution', 
            'persistence': 'Persistence',
            'privilege-escalation': 'Privilege Escalation',
            'defense-evasion': 'Defense Evasion',
            'credential-access': 'Credential Access',
            'collection': 'Collection',
            'command-and-control': 'Command and Control',
            'exfiltration': 'Exfiltration',
            'impact': 'Impact',
            'lateral-movement': 'Lateral Movement'
        }
        return tactic_names.get(tactic, tactic.title())

    def get_platform_display_name(self, platform):
        """获取平台显示名称"""
        platform_names = {
            'windows': 'Windows',
            'linux': 'Linux',
            'darwin': 'macOS'
        }
        return platform_names.get(platform, platform.title())

    def get_threat_level_color(self):
        """获取威胁等级对应的颜色"""
        colors = {
            'Low': 'is-info',
            'Medium': 'is-warning', 
            'High': 'is-danger',
            'Critical': 'is-dark'
        }
        return colors.get(self.threat_level, 'is-light')

    def get_file_size_display(self):
        """获取文件大小的显示格式"""
        if not self.file_size:
            return 'Unknown'
        
        size = self.file_size
        units = ['B', 'KB', 'MB', 'GB']
        unit_index = 0
        
        while size >= 1024 and unit_index < len(units) - 1:
            size /= 1024
            unit_index += 1
            
        return f"{size:.1f} {units[unit_index]}"
