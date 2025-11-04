import hashlib
import itertools
import json
import os
from collections import defaultdict
from typing import Dict, List, Any, Set

import yaml
from datetime import datetime, timezone

from .schemas import validate_manifest


class PayloadsService:
    def __init__(self, services):
        self._services = services
        self._payloads: Dict[str, Dict[str, Any]] = {}
        self._index: Dict[str, Dict[str, Set[str]]] = defaultdict(lambda: defaultdict(set))
        self._by_words: Dict[str, Set[str]] = defaultdict(set)

    async def load_from_disk(self, manifest_dir: str):
        if not os.path.isdir(manifest_dir):
            return
        for root, _, files in os.walk(manifest_dir):
            for fn in files:
                if fn.lower().endswith(('.yml', '.yaml')):
                    path = os.path.join(root, fn)
                    with open(path, 'r', encoding='utf-8') as f:
                        doc = yaml.safe_load(f.read()) or {}
                    if not isinstance(doc, dict):
                        continue
                    val = validate_manifest(doc)
                    if not val.get('ok'):
                        continue
                    for item in doc.get('items') or []:
                        self._upsert_item(item)

    def _upsert_item(self, item: Dict[str, Any]):
        pid = item.get('id') or ''
        # defaults
        if not item.get('name'):
            item['name'] = pid
        if not item.get('severity'):
            item['severity'] = 'medium'
        if not item.get('status'):
            item['status'] = 'active'
        if not item.get('updated_at'):
            item['updated_at'] = datetime.now(timezone.utc).isoformat()
        
        self._payloads[pid] = item
        # index
        for os_name in item.get('os', []) or []:
            self._index['os'][os_name].add(pid)
        for tac in item.get('tactics', []) or []:
            self._index['tactics'][str(tac)].add(pid)
        ft = item.get('file_type')
        if ft:
            self._index['file_type'][ft].add(pid)
        for tag in item.get('tags', []) or []:
            self._index['tags'][tag].add(pid)
        status = item.get('status', 'active')
        self._index['status'][status].add(pid)
        sev = item.get('severity') or 'medium'
        self._index['severity'][sev].add(pid)
        # word index
        text = ' '.join([item.get('name',''), item.get('description','')] + (item.get('tags') or []))
        for w in self._tokenize(text):
            self._by_words[w].add(pid)

    def _tokenize(self, text: str) -> List[str]:
        return [t for t in (text or '').lower().split() if t]

    def _match_filters(self, q: Dict[str, Any]) -> List[str]:
        sets: List[Set[str]] = []
        # keyword
        search = (q.get('search') or '').strip().lower()
        if search:
            kws = [w for w in search.split() if w]
            if kws:
                s = None
                for k in kws:
                    s2 = self._by_words.get(k, set())
                    s = s2 if s is None else s.intersection(s2)
                sets.append(s or set())
        # facets
        for key in ['tactics', 'os', 'file_types', 'tags', 'status', 'severity']:
            vals = q.get(key)
            if not vals:
                continue
            if key == 'file_types':
                idx = self._index['file_type']
            else:
                idx = self._index[key]
            s = None
            for v in vals:
                s2 = idx.get(v, set())
                s = s2 if s is None else s.intersection(s2)
            sets.append(s or set())

        if not sets:
            return list(self._payloads.keys())
        result = sets[0].copy()
        for s in sets[1:]:
            result.intersection_update(s)
        return list(result)

    def list_payloads(self, q: Dict[str, Any]) -> Dict[str, Any]:
        ids = self._match_filters(q)
        sort = q.get('sort') or 'updated_at:desc'
        reverse = sort.endswith(':desc')
        key = sort.split(':')[0]
        severity_order = {'low': 0, 'medium': 1, 'high': 2, 'critical': 3}
        def _key(pid):
            v = self._payloads[pid].get(key)
            if v is None:
                return ''
            if key == 'severity':
                return severity_order.get(str(v).lower(), 1)
            return v
        ids.sort(key=_key, reverse=reverse)
        page = int(q.get('page') or 1)
        size = int(q.get('page_size') or 20)
        start = (page-1)*size
        end = start + size
        items = [self._payloads[i] for i in ids[start:end]]
        return dict(items=items, total=len(ids), page=page, page_size=size)

    def facets(self, q: Dict[str, Any]) -> Dict[str, Any]:
        ids = set(self._match_filters({k: v for k, v in q.items() if k not in ['tactics','os','file_types','tags','status','severity']}))
        res = {}
        for dim, idx in [('tactics','tactics'), ('os','os'), ('file_types','file_type'), ('tags','tags'), ('status','status'), ('severity','severity')]:
            counts = []
            m = self._index[idx]
            for k, s in m.items():
                counts.append(dict(key=k, count=len(ids.intersection(s))))
            res[dim] = sorted(counts, key=lambda x: x['key'])
        return res

    async def handle_yaml_import(self, data: bytes) -> Dict[str, Any]:
        doc = yaml.safe_load(data.decode('utf-8', errors='ignore')) or {}
        result = validate_manifest(doc)
        imported = 0
        errors = list(result.get('errors') or [])
        if result.get('ok'):
            for idx, item in enumerate(doc.get('items') or []):
                self._upsert_item(item)
                imported += 1
        return dict(imported=imported, failed=len(errors), errors=errors)

    async def save_uploaded_file(self, field) -> Dict[str, Any]:
        file_svc = self._services.get('file_svc')
        filename = field.filename
        data = await field.read(decode=False)
        md5 = hashlib.md5(data).hexdigest()
        rel_path = os.path.join('plugins', 'payloads', 'data', 'files', filename)
        os.makedirs(os.path.dirname(rel_path), exist_ok=True)
        await file_svc.save_file(rel_path, data, '', encrypt=False)
        size = len(data)
        return dict(source_path=rel_path, md5=md5, size=size)


