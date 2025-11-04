from app.utility.base_world import BaseWorld
from plugins.payloads.app.payloads_api import PayloadsAPI


name = 'Payloads'
description = 'Malicious payload library with filtering and dispatch capabilities'
address = '/plugin/payloads/gui'
access = BaseWorld.Access.APP


async def enable(services):
    app = services.get('app_svc').application
    api = PayloadsAPI(services)

    # REST endpoints (initial skeleton)
    app.router.add_route('GET', '/plugin/payloads', api.list_payloads)
    app.router.add_route('GET', '/plugin/payloads/facets', api.get_facets)
    app.router.add_route('GET', '/plugin/payloads/{pid}', api.get_payload_detail)
    app.router.add_route('POST', '/plugin/payloads/import', api.import_payloads)
    app.router.add_route('POST', '/plugin/payloads/upload-file', api.upload_file)
    app.router.add_route('GET', '/plugin/payloads/export', api.export_payloads)
    app.router.add_route('POST', '/plugin/payloads/batch', api.batch_actions)
    app.router.add_route('GET', '/plugin/payloads/agents', api.list_agents)
    app.router.add_route('GET', '/plugin/payloads/{pid}/download', api.download_payload)
    app.router.add_route('POST', '/plugin/payloads/dispatch', api.dispatch)
    app.router.add_route('GET', '/plugin/payloads/history', api.history)
    # Pure SFC mode: GUI is served via magma PluginView scanning plugins/payloads/gui/views


