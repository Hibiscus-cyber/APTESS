import re
from typing import List, Dict, Any


TACTIC_PATTERN = re.compile(r'^TA\d{4}$')
MD5_PATTERN = re.compile(r'^[a-f0-9]{32}$')
ALLOWED_OS = {'windows', 'linux', 'darwin'}
ALLOWED_SEVERITY = {'low', 'medium', 'high', 'critical'}


def validate_payload_item(item: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    required = ['id', 'name', 'description', 'md5', 'file_type', 'os', 'tactics', 'source', 'executor']
    for k in required:
        if not item.get(k):
            errors.append(f'missing required field: {k}')

    if item.get('md5') and not MD5_PATTERN.match(item['md5']):
        errors.append('md5 must be 32 lowercase hex characters')

    os_list = item.get('os') or []
    if isinstance(os_list, list):
        for os_name in os_list:
            if os_name not in ALLOWED_OS:
                errors.append(f'os must be one of {sorted(ALLOWED_OS)}')
    else:
        errors.append('os must be a list')

    tactics = item.get('tactics') or []
    if isinstance(tactics, list):
        for t in tactics:
            if not TACTIC_PATTERN.match(str(t)):
                errors.append('tactics must be ATT&CK tactic keys like TA0001')
    else:
        errors.append('tactics must be a list')

    severity = item.get('severity')
    if severity and severity not in ALLOWED_SEVERITY:
        errors.append(f'severity must be one of {sorted(ALLOWED_SEVERITY)}')

    source = item.get('source')
    if source == 'local' and not item.get('source_path'):
        errors.append('source_path required for local source')
    if source == 'url' and not item.get('download_url'):
        errors.append('download_url required for url source')

    # args validation (optional)
    for arg in item.get('args', []) or []:
        if 'key' not in arg or not arg['key']:
            errors.append('each arg must have key')
        if arg.get('type') and arg['type'] not in ['string', 'int', 'bool', 'enum', 'path']:
            errors.append(f"arg {arg.get('key','?')} type invalid")

    return errors


def validate_manifest(doc: Dict[str, Any]) -> Dict[str, Any]:
    errors: List[Dict[str, Any]] = []
    items = (doc or {}).get('items') or []
    if not isinstance(items, list):
        return dict(ok=False, items=0, errors=[dict(index=-1, reason='items must be a list')])
    ok_count = 0
    for idx, it in enumerate(items):
        errs = validate_payload_item(it)
        if errs:
            errors.append(dict(index=idx, reason='; '.join(errs)))
        else:
            ok_count += 1
    return dict(ok=len(errors) == 0, items=ok_count, errors=errors)


