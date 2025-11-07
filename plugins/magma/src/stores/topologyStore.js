import * as d3 from 'd3'
import yaml from 'js-yaml'
import { ref, onMounted, onBeforeUnmount, defineAsyncComponent } from 'vue'
import platformIcon from '@/assets/img/graph/platform.svg'
import hotIcon from '@/assets/img/graph/breached.svg'
import normalIcon from '@/assets/img/graph/idle.svg'
import switchIcon from '@/assets/img/graph/switch.svg'
import { getAgentStatus } from "@/utils/agentUtil.js";
const containerEl = ref(null)

let flag=0;
let svg, g, linkG, nodeG, labelG, zoom, simulation
let disposeZoom = null
let containerElRef = null
let data;
let svdata
let allNodes = []
let latestData = null
let fileName=null
// 声明拖拽模式
const modes = {
  0: {
    // 自由模式：拖拽节点时，其他节点可继续动
    lockOthersWhileDrag: false,
    freezeSimulationDuringDrag: false,
    dragStartAlphaTarget: 0.2,
    dragEndAlphaTarget: 0,
    baseAlpha: 0.1,
    baseAlphaTarget: 0.1,
  },
  1: {
    // 控制模式：拖拽一个节点时，其他节点锁住不动
    lockOthersWhileDrag: true,
    freezeSimulationDuringDrag: true,
    dragStartAlphaTarget: 0.15,
    dragEndAlphaTarget: 0,
    baseAlpha: 0,
    baseAlphaTarget: 0,
  }
}
// 控制拖拽模式
function setFlag(newFlag) {
  flag = newFlag
  // 如果图已经初始化了，可以立即把模式对应的 alpha 应用到当前 simulation
  if (simulation) {
    const cfg = modes[flag]
    simulation.alpha(cfg.baseAlpha)//.restart()
    simulation.alphaTarget(cfg.baseAlphaTarget).restart()
  }
}


// group与颜色和形状的映射
const shapeByGroup = {
  Switch: 'square',
  Engaging: 'circle',
  Breached: 'circle',
  Blocked: 'circle',
  Idle: 'circle',
  Platform: "star",
  default: 'circle'
}
const colorByGroup = {
  Platform: '#ff7f0e',
  Engaging: '#9467bd',
  Breached: '#d62728',
  Blocked: '#999999',
  Idle: '#2ca02c',
  Switch: '#999999',
  default: '#2ca02c'
}
// 映射到 d3 的 symbol 类型
const symbolType = shape => ({
  triangle: d3.symbolTriangle,
  diamond: d3.symbolDiamond,
  pentagon: d3.symbolWye,   
  circle: d3.symbolCircle,
  star: d3.symbolStar,
}[shape] || d3.symbolCircle)

// 返回该节点要画的形状
const getShape = d => shapeByGroup[d.group] || 'circle'
// 将节点和边映射到d3的颜色中，采用color(d.group)就可以设置颜色
function setColor(d) {
  // 1. 找到 source 对应的节点对象
  let srcNode
  // d.source 可能是字符串（还没交给simulation之前）
  // 也可能是对象（simulation运行后，d3会把它替换成节点对象）
  if (typeof d.source === 'object') {
    srcNode = d.source
  } else {
    // d.source 是 id 字符串，去 allNodes 里找
    srcNode = allNodes.find(n => n.id === d.source)
  }

  // 容错：如果没找到节点，就给个默认
  if (!srcNode) {
    return '#999999' // 灰色兜底，防止报错
  }

  // 2. 按你的逻辑染色
  if (srcNode.group !== 'Platform') {
    // 使用节点颜色规则
    return getNodeColor(srcNode)
  } else {
    // Platform 走固定颜色
    return '#d62728'
  }
}

 
let hotSet = new Set()
// 根据后端返回的命中 label 集合，设置节点颜色
function getNodeColor(node) {
  // node.label 在后端列表里 => 红色
  if (node.group == 'Platform'){
    return "#9467bd"
  }
  if (node.group =='Switch'){
    return "#999999"
  }
  // TODO： 未来改成按照ip长度循环，如果有就返回红，否则遍历完后返回绿色
  const isHot = node.ip && node.ip.some(ipStr => hotSet.has(ipStr))


  if (isHot) {
    return '#ff0000' // 红
  } else {
    return '#00ff00' // 绿
  }
}

// 获取后端数据，并执行染色函数
async function refreshHotSet() {
  try {
    const resp = await fetch('/api/v2/agents'); // 后端接口
    const agents = await resp.json();

    // 只取存活或待终止代理的 IP
    const hotIps = agents
      .filter(a => getAgentStatus(a) === 'alive' || getAgentStatus(a) === 'pending kill')
      .flatMap(a => a.host_ip_addrs || [])
      .filter(ip => typeof ip === 'string' && ip.trim() !== '');

    hotSet = new Set(hotIps);

    recolorNodes(); // 每次更新后重新染色
  } catch (err) {
    console.warn('获取 hot-nodes 失败:', err);
  }
}

// async function refreshHotSet() {
//   try {
//     const resp = await fetch('/api/v2/profiles') // 后端接口
//     const json = await resp.json()
//     hotSet = new Set(json.map(item => item.description).filter(Boolean)) // 从后端拉取数据，并将非空的数据保存为一个Set
//     recolorNodes() // 每次更新后重新染色
//   } catch (err) {
//     console.warn('获取 hot-nodes 失败:', err)
//   }
// }

// 节点是否命中后端
function isHotNode(node) {
  return node.ip && node.ip.some(ipStr => hotSet.has(ipStr))
}

function getIconForNode(node) {
  if (node.group === 'Breached' || node.group === 'Idle') {
    return isHotNode(node) ? hotIcon : normalIcon
  }
  if (node.group === 'Platform') return platformIcon
  if (node.group === 'Switch') return switchIcon
}

// 遍历所有的节点，根据该节点的label是否存在于hotSet中为其填充颜色。
function recolorNodes() {
  //  nodeG 是装所有节点 <g> 的 group
  // 并且每个节点里有一个 .shape (circle/rect/path...)
  // 更新图标：注意用 href，不要再用 fill
  nodeG.selectAll('g.node').select('image.shape')
    .attr('href', d => getIconForNode(d))
  linkG.selectAll('line').attr('stroke', setColor)
}

let pollTimer = null
 // 每 5 秒重新获取后端数据并染色
function startPolling() {
  pollTimer = setInterval(() => {
    refreshHotSet()
  }, 1000)
}

function stopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

// 你现在的 d.size 是半径概念，转成面积更接近视觉等效
const symbolArea = d => {
  const base = Math.PI * d.size * d.size
  // 如果节点形状是五角星，则放大 1.5 倍面积
  return getShape(d) === 'star' ? base * 2.5 : base
}

// 初始化画布和力导向布局和缩放
function initSvg (containerEl) {
containerElRef = containerEl
  // 设置DOM元素
  const container = d3.select(containerElRef)
  svg = container.append('svg')
  const defs = svg.append('defs')
  defs.append('marker')
    .attr('id','arrow')
    .attr('viewBox','0 0 10 10')
    .attr('refX', 18)
    .attr('refY', 0)
    .attr('markerWidth', 6)
    .attr('markerHeight', 6)
    .attr('orient','auto')
    .append('path')
    .attr('d','M0,-5L10,0L0,5')
    .attr('fill','#999')

  g = svg.append('g')
  linkG = g.append('g').attr('stroke-width', 1.5)
  nodeG = g.append('g')
  labelG = g.append('g')

  // 配置缩放。缩放范围是0.2～4
  zoom = d3.zoom().scaleExtent([0.2, 4]).on('zoom', e => g.attr('transform', e.transform)).on('end', e => {saveGraphState()})
  svg.call(zoom)
  disposeZoom = () => svg.on('.zoom', null)

  // 配置力导向布局
  simulation = d3.forceSimulation()
  // strength设置边斥力大小，斥力越大拖动时边上两点反应越剧烈；d设置节点间连线距离
    .force('link', d3.forceLink().id(d => d.id).distance(d => 100 + (d.value ? d.value * 5 : 0)).strength(0.5))
  // strength设置节点间斥力大小，斥力越大节点间距离越大
    .force('charge', d3.forceManyBody().strength(-500))
  // radius配置节点间的碰撞半径
    .force('collide', d3.forceCollide().radius(d => (d.size || 10) + 6))
  // 图像会向设置的坐标位置偏移
    .force('center', d3.forceCenter(0, 0))
}

// 绘制图像并重制图像位置
// 3) resetView：按优先级选择数据源重绘
function resetView () {
  try {
    if (latestData) {  
      console.log('draw from LatestData')         
      console.log(latestData)         // 1) 内存 data 优先
      draw(latestData)
      svg.transition().duration(800).call(zoom.transform, d3.zoomIdentity.translate(400, 180).scale(1))
      return
    }
    const savedRaw = localStorage.getItem('DataState')
    if (savedRaw) {
      const saved = JSON.parse(savedRaw)
      if (saved?.svdata && Array.isArray(saved.svdata.nodes) && Array.isArray(saved.svdata.links)) {
        // 2) 本地 data 次之（无视图信息，用默认视角）
        svdata = saved.svdata
        latestData = saved.svdata
        draw(saved.svdata)
        console.log('draw from localData')         
        console.log(svdata)
        svg.transition().duration(800).call(zoom.transform, d3.zoomIdentity.translate(400, 180).scale(1))
        return
      }
    }
    // 4) 都没有，兜底报错
    throw new Error('no data source')
  } catch (err) {
    alert('no data\n' + err.message)
  }
}


// // 读取文件内容到data，并绘制图像
async function onFileChange (e) {
  const file = e.target.files?.[0]

  if (!file) return
  const text = await file.text()
  
  try {
    data = yaml.load(text)
  } catch (err) {
    alert('YAML 解析失败: ' + err.message)
    return
  }
  if (!data || !Array.isArray(data.nodes) || !Array.isArray(data.links)) {
    alert('YAML 需包含 nodes[] 与 links[]')
    return
  } 
  latestData = data  
  svdata=data                    // 👈 记住内存态数据
  console.warn("set Latest Data")
  console.log(data)
  resetView()                            // 用 data 重绘并复位视角
  saveGraphState()                       // 👈 立刻持久化（含 data）
  fileName=file.name
  if(fileName!=null){
    saveDataState()
  }

  return file.name
}

// 绘制图像
function draw ({ nodes, links }) {
  // nodes和links是JS的数组
  // 规范化links和nodes的结构
links = links.flatMap(l =>
  Array.isArray(l.source)
    ? l.source.map(s => ({ ...l, source: s }))
    : [l]
)
// TODO：将IP 改成一个array
  nodes = nodes.map(d => ({
    id: d.id,
    group: d.group ?? 'default',
    size: +d.size > 0 ? +d.size : 10,
    label: d.label ?? String(d.id),
    ip: Array.isArray(d.ip)
      ? d.ip
      : (d.ip ? [d.ip] : [])
  }))
  
  allNodes = nodes
  // links是数据、d时匹配的数据，两者对比来判断数据的增删
  const linkSel = linkG.selectAll('line').data(links, d => d.source + '->' + d.target)
  // 移除数据中已经不存在的节点和边。
  linkSel.exit().remove()
  // 新增数据中存在但是html中不存在的边
  const linkEnter = linkSel.enter().append('line')
    .attr('class','link')
    .attr('stroke-width', d => d.value ? Math.max(1, +d.value) : 1.5)
    .attr('stroke', setColor)

  // 合并新画的线和已有的线
  const linksAll = linkEnter.merge(linkSel)

  // 判断节点的增删
  const nodeSel = nodeG.selectAll('g.node').data(nodes, d => d.id)
  // 移除数据中已经不存在的节点。
  nodeSel.exit().remove()
  // 新增数据中存在但是html中不存在的节点
  const nodeEnter = nodeSel.enter()
  .append('g')
  .attr('class','node')
  .call(drag(simulation, () => simulation.nodes()));
 // 为了更新也生效，先清掉旧形状
nodeEnter.selectAll('.shape').remove()
nodeEnter.each(function (d) {
  const sel = d3.select(this)

  sel.append('image')
    .attr('class', 'shape')
    .attr('href', getIconForNode(d))  // 根据后端是否有数据选图标
    .attr('width', d.size * 2)
    .attr('height', d.size * 2)
    .attr('x', -d.size)   // 以节点坐标为中心
    .attr('y', -d.size)
})

  const nodesAll = nodeEnter.merge(nodeSel)
  nodesAll.select('.shape')
    .attr('fill', getNodeColor)

  // 管理label的增删
// ---- labels (2-line label per node) ----

// 1. 把 node 数据绑定到 <g class="nodelabel">
const labelSel = labelG.selectAll('g.nodelabel')
  .data(nodes, d => d.id)

// 2. 把多余的旧 label 删除
labelSel.exit().remove()

const labelDy = d =>{
  const s = getShape(d)
  if (s === 'triangle') return -(d.size+10)
  if (s === 'square') return -(d.size+6)
  return -(d.size + 6)
}

// 3. 对新增节点，创建一整个 <g.nodelabel>
const labelEnter = labelSel.enter()
  .append('g')
  .attr('class', 'nodelabel')
  .attr('text-anchor', 'middle')
  .style('pointer-events', 'none') // 不挡鼠标拖拽

// 第一行：展示 d.label
labelEnter.append('text')
  .attr('class', 'label-line1')
  .attr('fill', '#ffffffff')
  .attr('font-size', 12)
  .attr('dy', d=> labelDy(d)) // 往下偏一点，方便放两行
  .text(d => d.label)

// 第二行：展示 d.ip
labelEnter.append('text')
  .attr('class', 'label-line2')
  .attr('fill', '#a8a8a8ff')
  .attr('font-size', 10)
  .attr('dy', d => labelDy(d)+14) // 比第一行再往下一些
  .text(d => (d.ip && d.ip.length > 0) ? d.ip.join(' & ') : '')

// 4. merge：把“旧的”和“新加的”合在一起，后面 tick 统一更新 transform
const labelsAll = labelEnter.merge(labelSel)


// ---- tick 刷新 ----
// ⚠️ 每次 draw() 前先把旧 tick handler 清空，然后重新设
const getRadius = d => (d.size || 10) + 4  // 4 是额外留白，可调
simulation.on('tick', null)
simulation.on('tick', () => {
  // 边更新位置
  linksAll
    .attr('x1', d => {
      const sx = d.source.x
      const sy = d.source.y
      const tx = d.target.x
      const ty = d.target.y

      const dx = tx - sx
      const dy = ty - sy
      const len = Math.hypot(dx, dy) || 1   // 防止除 0

      const r = getRadius(d.source)         // 离源节点中心多远
      return sx + (dx / len) * r            // 从源中心沿方向走 r
    })
    .attr('y1', d => {
      const sx = d.source.y
      const sy = d.source.y
      const tx = d.target.x
      const ty = d.target.y

      const dx = tx - d.source.x
      const dy = ty - d.source.y
      const len = Math.hypot(dx, dy) || 1

      const r = getRadius(d.source)
      return d.source.y + (dy / len) * r
    })
    .attr('x2', d => {
      const sx = d.source.x
      const sy = d.source.y
      const tx = d.target.x
      const ty = d.target.y

      const dx = tx - sx
      const dy = ty - sy
      const len = Math.hypot(dx, dy) || 1

      const r = getRadius(d.target)         // 离目标节点中心多远
      return tx - (dx / len) * r            // 从目标中心往回退 r
    })
    .attr('y2', d => {
      const sx = d.source.x
      const sy = d.source.y
      const tx = d.target.x
      const ty = d.target.y

      const dx = tx - sx
      const dy = ty - sy
      const len = Math.hypot(dx, dy) || 1

      const r = getRadius(d.target)
      return ty - (dy / len) * r
    })


  // 节点本身放到自己的坐标
  nodesAll.attr('transform', d => `translate(${d.x},${d.y})`)

  // label 放在节点的上方一点
  labelsAll.attr('transform', d => {
    // 根据节点形状/大小，往上提不同距离
    const offsetY = (() => {
      const shape = getShape(d)
      if (shape === 'triangle') return -(d.size + 10)
      if (shape === 'square')   return -(d.size + 6)
      return -(d.size + 6)
    })()
    // 把整组 label（两行文字）挪到节点上方
    return `translate(${d.x},${d.y + offsetY})`
  })
})
// 让力导向仿真知道当前的节点和边
simulation.nodes(nodes)
simulation.force('link').links(links)

// 重启仿真来计算 x y 坐标
simulation.alpha(1).restart()

}

// 配置画布的大小、偏移、缩放
function fitView (ns) {
  const w = containerElRef?.clientWidth || 800
  const h = containerElRef?.clientHeight || 600
  svg.attr('viewBox', [0, 0, w, h])
  const k = Math.min(3, 0.9 / Math.sqrt(ns.length / 30 + 0.3))
  svg.call(zoom.transform, d3.zoomIdentity.translate(w / 2, h / 2).scale(k))
}


// 控制拖拽时的反应强烈程度
// 传入 sim，以及一个函数 getNodes()，返回当前 nodes 数组
function drag(sim, getNodes) {
  return d3.drag()
    .on('start', (event, d) => {
      const cfg = modes[flag]

      // 如果需要锁其它节点
      if (cfg.lockOthersWhileDrag) {
        const nodes = getNodes()
        nodes.forEach(n => {
          if (n !== d) {
            n.fx = n.x
            n.fy = n.y
          }
        })
      }

      // 当前这个节点先固定到当前位置
      d.fx = d.x
      d.fy = d.y

      // 启动一点活力，避免位置不刷
      if (!event.active) {
        sim.alphaTarget(cfg.dragStartAlphaTarget).restart()
      }

      // 如果需要冻结力导向（防止全图“呼吸”一下）
      if (cfg.freezeSimulationDuringDrag) {
        sim.alpha(0)
      }
    })

    .on('drag', (event, d) => {
      const cfg = modes[flag]

      // 被拖的节点跟随鼠标
      d.fx = event.x
      d.fy = event.y

      if (cfg.freezeSimulationDuringDrag) {
        sim.alpha(0)
      }
    })

    .on('end', (event, d) => {
      const cfg = modes[flag]

      // 解锁其他节点
      if (cfg.lockOthersWhileDrag) {
        const nodes = getNodes()
        nodes.forEach(n => {
          if (n !== d) {
            n.fx = null
            n.fy = null
          }
        })
      }

      // 当前节点是否继续固定？这里按你的旧逻辑，松开后恢复自由
      d.fx = null
      d.fy = null

      // 降低活力，逐渐停下来
      if (!event.active) {
        sim.alphaTarget(cfg.dragEndAlphaTarget)
      }

      if (cfg.freezeSimulationDuringDrag) {
        sim.alpha(0)
      }

      // 保存当前状态（坐标、视角）
      saveGraphState()
    })
}

function drawFromSnapshot ({ nodes, links,view }) {
  // 1. 先像你原来那样标准化 links（继承 group）
  links = links.flatMap(l =>
    Array.isArray(l.source)
      ? l.source.map(s => ({ ...l, source: s }))
      : [l]
  )

  // 2. nodes 已经包含 x,y,fx,fy，不要重置它们
  // 但我们还是要保证基本字段存在（id/group/size/label）
nodes = nodes.map(n => ({
  id: n.id,
  group: n.group ?? 'default',
  size: +n.size > 0 ? +n.size : 10,
  label: n.label ?? String(n.id),
  ip: Array.isArray(n.ip)
      ? n.ip
      : (n.ip ? [n.ip] : []),
  x: n.x,
  y: n.y,
  fx: n.fx,
  fy: n.fy
}))



  allNodes=nodes
  // --- 下面基本照抄你 draw() 里的 enter/update 逻辑 ---
  const linkSel = linkG.selectAll('line').data(links, d => d.source + '->' + d.target)
  linkSel.exit().remove()
  const linkEnter = linkSel.enter().append('line')
    .attr('class','link')
    .attr('stroke-width', d => d.value ? Math.max(1, +d.value) : 1.5)
    .attr('stroke', setColor)
  const linksAll = linkEnter.merge(linkSel)

  const nodeSel = nodeG.selectAll('g.node').data(nodes, d => d.id)
  nodeSel.exit().remove()
  const nodeEnter = nodeSel.enter()
    .append('g')
    .attr('class','node')
    .call(drag(simulation, () => simulation.nodes()))

  nodeEnter.selectAll('.shape').remove()
nodeEnter.each(function (d) {
  const sel = d3.select(this)

  sel.append('image')
    .attr('class', 'shape')
    .attr('href', getIconForNode(d))  // 根据后端是否有数据选图标
    .attr('width', d.size * 2)
    .attr('height', d.size * 2)
    .attr('x', -d.size)   // 以节点坐标为中心
    .attr('y', -d.size)
})
  const nodesAll = nodeEnter.merge(nodeSel)
  // ⬇ 这个是新的补充步骤
  nodesAll.select('.shape')
    .attr('fill', getNodeColor)


// 绑定到 <g.nodelabel>，而不是 text.label
// 先清理旧的 label group （可选，merge 其实会覆盖）
// ---- labels (2-line label per node) ----

// 1. 把 node 数据绑定到 <g class="nodelabel">
const labelSel = labelG.selectAll('g.nodelabel')
  .data(nodes, d => d.id)

// 2. 把多余的旧 label 删除
labelSel.exit().remove()

const labelDy = d =>{
  const s = getShape(d)
  if (s === 'triangle') return -(d.size+10)
  if (s === 'square') return -(d.size+6)
  return -(d.size + 6)
}

// 3. 对新增节点，创建一整个 <g.nodelabel>
const labelEnter = labelSel.enter()
  .append('g')
  .attr('class', 'nodelabel')
  .attr('text-anchor', 'middle')
  .style('pointer-events', 'none') // 不挡鼠标拖拽

// 第一行：展示 d.label
labelEnter.append('text')
  .attr('class', 'label-line1')
  .attr('fill', '#ffffffff')
  .attr('font-size', 12)
  .attr('dy', d=> labelDy(d)) // 往下偏一点，方便放两行
  .text(d => d.label)

// 第二行：展示 d.ip
labelEnter.append('text')
  .attr('class', 'label-line2')
  .attr('fill', '#a8a8a8ff')
  .attr('font-size', 10)
  .attr('dy', d => labelDy(d)+14) // 比第一行再往下一些
  .text(d => (d.ip && d.ip.length > 0) ? d.ip.join(' & ') : '')

// 4. merge：把“旧的”和“新加的”合在一起，后面 tick 统一更新 transform
const labelsAll = labelEnter.merge(labelSel)


// ---- tick 刷新 ----
// ⚠️ 每次 draw() 前先把旧 tick handler 清空，然后重新设
const getRadius = d => (d.size || 10) + 4  // 4 是额外留白，可调

simulation.on('tick', null)
simulation.on('tick', () => {
  // 边更新位置
  linksAll
    .attr('x1', d => {
      const sx = d.source.x
      const sy = d.source.y
      const tx = d.target.x
      const ty = d.target.y

      const dx = tx - sx
      const dy = ty - sy
      const len = Math.hypot(dx, dy) || 1   // 防止除 0

      const r = getRadius(d.source)         // 离源节点中心多远
      return sx + (dx / len) * r            // 从源中心沿方向走 r
    })
    .attr('y1', d => {
      const sx = d.source.y
      const sy = d.source.y
      const tx = d.target.x
      const ty = d.target.y

      const dx = tx - d.source.x
      const dy = ty - d.source.y
      const len = Math.hypot(dx, dy) || 1

      const r = getRadius(d.source)
      return d.source.y + (dy / len) * r
    })
    .attr('x2', d => {
      const sx = d.source.x
      const sy = d.source.y
      const tx = d.target.x
      const ty = d.target.y

      const dx = tx - sx
      const dy = ty - sy
      const len = Math.hypot(dx, dy) || 1

      const r = getRadius(d.target)         // 离目标节点中心多远
      return tx - (dx / len) * r            // 从目标中心往回退 r
    })
    .attr('y2', d => {
      const sx = d.source.x
      const sy = d.source.y
      const tx = d.target.x
      const ty = d.target.y

      const dx = tx - sx
      const dy = ty - sy
      const len = Math.hypot(dx, dy) || 1

      const r = getRadius(d.target)
      return ty - (dy / len) * r
    })

  // 节点本身放到自己的坐标
  nodesAll.attr('transform', d => `translate(${d.x},${d.y})`)

  // label 放在节点的上方一点
  labelsAll.attr('transform', d => {
    // 根据节点形状/大小，往上提不同距离
    const offsetY = (() => {
      const shape = getShape(d)
      if (shape === 'triangle') return -(d.size + 10)
      if (shape === 'square')   return -(d.size + 6)
      return -(d.size + 6)
    })()
    // 把整组 label（两行文字）挪到节点上方
    return `translate(${d.x},${d.y + offsetY})`
  })
})

// 恢复节点和边到 simulation
simulation.nodes(nodes)
simulation.force('link').links(links)

// 不用让它自动跑太久 你可以手动推进几步
simulation.alpha(0)      // 我们不想重新抖动布局


// 现在 d.x / d.y 一定存在


  // 主动触发一次 tick 回调，确保画面立即反映坐标
  simulation.tick()

  // ✅ 恢复你上次看的视角（平移+缩放）
  if (view && typeof view.x === 'number' && typeof view.y === 'number' && typeof view.k === 'number') {
    // 用 zoom.transform 主动把 zoom 状态设回去
    const w = containerEl.value?.clientWidth || 800
    const h = containerEl.value?.clientHeight || 600
    svg.attr('viewBox', [0, 0, w, h])
    svg.call(
      zoom.transform,
      d3.zoomIdentity.translate(view.x, view.y).scale(view.k)
    )

  } else {
    // 如果没有保存视角，就用默认全图居中
    fitView(nodes)
  }
}
function destroy() {

  if (disposeZoom) disposeZoom()
    saveGraphState()
    saveDataState()
}


function setDataFromSnapshot(snapshot) {
  data = snapshot
}
function saveGraphState() {
  if (!data || !simulation || !svg || !g) return

  // 1. 保存节点的当前状态（含坐标和固定情况）
const simNodes = simulation.nodes().map(n => ({
  id: n.id,
  group: n.group,
  size: n.size,
  label: n.label,
  ip: Array.isArray(n.ip)
    ? n.ip
    : (n.ip ? [n.ip] : []),

  x: n.x,
  y: n.y,
  fx: n.fx,
  fy: n.fy
}))



  // 2. 保存边（用 id 而不是对象引用，方便恢复）
  const simLinks = simulation.force('link').links().map(l => ({
    source: (typeof l.source === 'object' ? l.source.id : l.source),
    target: (typeof l.target === 'object' ? l.target.id : l.target),
    value: l.value,
    group: l.group
  }))

  // 3. 保存当前视图的缩放和平移
  // 取当前 zoom transform：用 d3.zoomTransform(svg.node()) 或直接从 <g> 的 transform 解析
  const t = d3.zoomTransform(svg.node())
  const view = {
    x: t.x,
    y: t.y,
    k: t.k
  }

  // ⚠️ 一并保存 data，优先 latestData，其次 data，全无则存 null
  const payload = {
    nodes: simNodes,
    links: simLinks,
    view,
    svdata: latestData ||svdata|| null,

  }
  localStorage.setItem('graphState', JSON.stringify(payload))
}
function saveDataState() {
  if (!svdata) return


  // ⚠️ 一并保存 data，优先 latestData，其次 data，全无则存 null
  const payload = {
    svdata: latestData ||svdata|| null,
    filename: fileName || null,
  }
  localStorage.setItem('DataState', JSON.stringify(payload))
}

  function get_fileName(){
    const savedRaw = localStorage.getItem('DataState')
    if (savedRaw) {
      const saved = JSON.parse(savedRaw)
      console.log(saved.filename)
      return saved.filename
    }
    return null
  }
export {
  initSvg,
  drawFromSnapshot,
  destroy,
  resetView,
  setDataFromSnapshot,
  onFileChange,
  setFlag,
  refreshHotSet,  
  startPolling,
  stopPolling,
  get_fileName

}

