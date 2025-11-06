import uuid
from app.objects.interfaces.i_object import FirstClassObjectInterface
from app.utility.base_object import BaseObject
import marshmallow as ma
from marshmallow import fields, validate



class ProfileSchema(ma.Schema):
    class Meta:
        unknown = ma.EXCLUDE
    profile_id = ma.fields.String()
    name = ma.fields.String()
    file_name = ma.fields.String()
    file_type = ma.fields.String()
    description = ma.fields.String()

    # 固定枚举值约束
    tactic = fields.List(fields.String(
        validate=validate.OneOf(["Discovery", "Execution", "Persistence", "Privilege Escalation","Defense Evasion","Credential Access","Collection","Command and Control","Exfiltration","Impact","Lateral Movement"])
    ))
    risk = fields.String(
        validate=validate.OneOf(["Low", "Medium", "High"])
    )
    platform = fields.List(fields.String(
        validate=validate.OneOf(["Windows", "Linux", "macOS", "Other"])
    ))

    @ma.post_load
    def build_profile(self, data, **kwargs):
        return None if kwargs.get('partial') is True else Profile(**data)

class Profile(FirstClassObjectInterface,BaseObject):
    schema = ProfileSchema()    # 在BaseObject中使用了schema变量
    
    def __init__(self, profile_id=None, name='', file_name='',file_type='',tactic=None,risk=None,platform=None,description='', **extras):
        super().__init__()

        self.profile_id = profile_id or str(uuid.uuid4())
        self.name = name
        self.file_name=file_name
        self.platform= platform or []
        self.tactic=tactic or []
        self.risk=risk or "Low"
        self.description = description or ''
        self.file_type=file_type 
        self.access = self.Access.RED

        # 读取没有被定义的未知字段
        for k, v in extras.items():
            setattr(self, k, v)

    @property
    def unique(self):
        return self.hash('%s' % self.profile_id)

    def store(self, ram):
        existing = self.retrieve(ram['profiles'], self.unique)
        if not existing:
            ram['profiles'].append(self)
            return self.retrieve(ram['profiles'], self.unique)
        existing.update('name', self.name)
        existing.update('file_name', self.file_name)
        existing.update('platform', self.platform)
        existing.update('description', self.description)
        existing.update('tactic', self.tactic)
        existing.update('risk', self.risk)
        return existing

    def search_tags(self, value):
        """用于 DataService.search() 的标签匹配"""
        return any(value.lower() in str(t).lower() for t in (self.tags or []))
