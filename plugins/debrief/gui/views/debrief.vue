<script setup>
import { inject, ref, onMounted, computed } from "vue";
import { storeToRefs } from "pinia";

const $api = inject("$api");

onMounted(async () => {
  let d3Script = document.createElement("script");
  d3Script.setAttribute(
    "src",
    "/debrief/js/d3.v4.min.js"
  );
  let d4Script = document.createElement("script");
  d4Script.setAttribute(
    "src",
    "/debrief/js/d3-zoom.v1.min.js"
  );
  let graphScript = document.createElement("script");
  graphScript.setAttribute(
    "src",
    "/debrief/js/graph.js"
  );
  document.head.appendChild(d3Script);
  document.head.appendChild(d4Script);
  document.head.appendChild(graphScript);
});
</script>

<style scoped>
caption {
    display: none;
}

svg {
    width: 100%;
    height: 100%;
}

#debrief-graph {
    position: relative;
    background-color: black;
    width: 80% !important;
    height: 400px;
    border-radius: 4px;
}

#fact-graph {
    position: relative;
    margin: auto;
    background-color: black;
    border-radius: 4px;
    width: 800px;
    height: 600px;
}

#fact-limit {
    width: 800px;
    margin: auto;
}

#select-operation {
    max-width: 800px;
    margin: 0 auto;
}

#tactic-section {
    width: 600px;
    margin: auto;
}

div.d3-tooltip {
    position: absolute;
    text-align: left;
    width: auto;
    height: auto;
    padding: 5px;
    font: 12px sans-serif;
    background: #750b20;
    border: 0px;
    border-radius: 4px;
    pointer-events: none;
}

.graph-controls {
    position: absolute;
}

#tactic-section > .card {
    background-color: #121212;
}
</style>

<script>
import { toast } from "bulma-toast";
import { b64DecodeUnicode } from "@/utils/utils";
export default {
  inject: ["$api"],
  data() {
    return {
        operations: [],
        selectedOperationIds: [],
        activeTab: 'stats',

        stats: [],
        agents: [],
        steps: [],
        tacticsAndTechniques: [],

        showCommandModal: false,
        command: '',
        commandOutput: '',
        commandAbilityName: '',

        showGraphSettingsModal: false,
        graphOptionLabels: true,
        graphOptionIcons: true,
        graphOptionSteps: true,

        showReportModal: false,
        reportSections: [],
        activeReportSections: [],
        useCustomLogo: false,
        logoFilename: '',
        logos: [],

        selectedGraphType: 'attackpath',
        nodesOrderedByTime: {},
        showGraphLegend: true,
        isGraphPlaying: false,
        graphInterval: null,
    };
  },
  created() {
    this.initPage();
  },
  methods: {
    initPage() {
            this.$api.get('/plugin/debrief/sections').then((data) => {
                this.reportSections = data.data.report_sections;
            }).catch((error) => {
                console.error(error);
                toast({
                  message:
                  "Error getting report sections",
                  type: "is-danger",
                  dismissible: true,
                  pauseOnHover: true,
                  duration: 2000,
                  position: "bottom-right",
                });
            });
            this.$api.get('/api/v2/operations').then((operations) => {
                this.operations = operations.data;
                this.initReportSections();
                return this.$api.get('/plugin/debrief/logos');
            }).then(async (data) => {
                this.logos = data.data.logos;
                if (typeof moveLegend !== 'undefined') {
                  window.addEventListener('resize', moveLegend);
                }

                // While the debrief tab is open, keep checking for new/killed agents
                setInterval(async () => {
                  this.refreshOperations();
                }, "3000");
            }).catch((error) => {
                console.error(error);
                toast({
                  message:
                  "Error getting operations",
                  type: "is-danger",
                  dismissible: true,
                  pauseOnHover: true,
                  duration: 2000,
                  position: "bottom-right",
                });
            });
        },

        refreshOperations() {
          this.$api.get('/api/v2/operations').then((operations) => {
                this.operations = operations.data;
            }).catch((error) => {
                console.error(error);
          toast({
            message:
            "Error refreshing operations",
            type: "is-danger",
            dismissible: true,
            pauseOnHover: true,
            duration: 2000,
            position: "bottom-right",
          });
            });
        },

        initReportSections() {
            const BASE_ORDERING = [ 
                "main-summary",
                "statistics",
                "agents",
                "attackpath-graph",
                "steps-graph",
                "tactic-graph",
                "technique-graph",
                "fact-graph",
                "tactic-technique-table",
                "steps-table",
                "facts-table"
            ];
            this.reportSections.sort((a, b) => {
                let aIndex = BASE_ORDERING.indexOf(a.key);
                let bIndex = BASE_ORDERING.indexOf(b.key);
                return aIndex - bIndex;
            });
            this.activeReportSections = this.reportSections.map((section) => section.key);
        },

        loadOperation() {
            if (!this.selectedOperationIds.length) return;
            this.$api.post('/plugin/debrief/report', { operations: this.selectedOperationIds }).then((data) => {
                data = data.data;
                this.stats = data.operations;
                this.agents = data.operations.map((o) => o.host_group).flat();

                this.steps = [];
                this.stats.forEach((stat) => {
                    stat.chain.forEach((c) => {
                        this.steps.push({ ...c, operation_name: stat.name });
                    });
                });

                Object.keys(data.ttps).forEach((tactic) => {
                    data.ttps[tactic].steps = Object.keys(data.ttps[tactic].steps).map((op) => {
                        return {
                            operation: op,
                            abilities: data.ttps[tactic].steps[op]
                        }
                    })
                })
                this.tacticsAndTechniques = data.ttps;

                updateReportGraph(this.selectedOperationIds);
            }).catch((error) => {
                toast({
                  message:
                  "Error loading operation",
                  type: "is-danger",
                  dismissible: true,
                  pauseOnHover: true,
                  duration: 2000,
                  position: "bottom-right",
                });
                console.error(error);
            })
        },

        operationSelectMousedown(el) {
            // An override to the select field so users don't need to hold CMD or Ctrl while selecting multiple op's
            el.selected = !el.selected;
            this.selectedOperationIds = Array.from(el.parentNode.childNodes)
                .filter((node) => node.localName === 'option' && node.selected)
                .map((node) => node.value);
            this.loadOperation();
        },
        
        getStatusName(status) {
            if (status === 0) {
                return 'success';
            } else if (status === -2) {
                return 'discarded';
            } else if (status === 1) {
                return 'failure';
            } else if (status === 124) {
                return 'timeout';
            } else if (status === -3) {
                return 'collected';
            } else if (status === -4) {
                return 'untrusted';
            } else if (status === -5) {
                return 'visibility';
            }
            return 'queued';
        },

        showCommand(id, command, abilityName) {
            this.commandAbilityName = abilityName;
            let requestBody = {
                index: 'result',
                link_id: id
            };
            this.$api.post('/api/rest', requestBody).then((data) => {
                if (data.data) {
                    try {
                        this.command = data.data.link.command;
                        this.commandOutput = JSON.parse(b64DecodeUnicode(data.data.output));
                    } catch (error) { // occurs when data is not JSON
                        this.commandOutput = '';
                        console.error(error);
                        toast({
                          message:
                          "Error getting command and/or command results.",
                          type: "is-danger",
                          dismissible: true,
                          pauseOnHover: true,
                          duration: 2000,
                          position: "bottom-right",
                        });
                    }
                } else {
                    this.command = 'No command to display';
                    this.commandOutput = '';
                }
                this.showCommandModal = true;
            });
        },

        moveReportSectionOrder(index, toIndex) {
            if (toIndex < 0 || toIndex >= this.reportSections.length) return;

            let temp = this.reportSections[index];
            this.reportSections[index] = this.reportSections[toIndex];
            this.reportSections[toIndex] = temp;

            let sortedActiveSections = this.activeReportSections;
            this.activeReportSections = this.reportSections.map((section) => section.key).filter((section) => sortedActiveSections.includes(section));
        },

        toggleReportSection(section) {
            let index = this.activeReportSections.indexOf(section);
            index >= 0 ? this.activeReportSections.splice(index, 1) : this.activeReportSections.push(section);
        },

        toggleLegend() {
            this.showGraphLegend = !this.showGraphLegend;
            document.querySelectorAll('.legend').forEach((legend) => {
                legend.style.display = (this.showGraphLegend ? 'block' : 'none');
            });
        },
        
        uploadLogo(el) {
            if (el.files.length === 0) return;

            let formData = new FormData()
            formData.append('header-logo', el.files[0])
            this.$api.post('/plugin/debrief/logo', formData, false).then((data) => {
                data = data.data;
                this.logos.push(data.filename);
                this.logoFilename = data.filename;
            }).catch((error) => {
                console.error(error);
                toast({
                  message:
                  "Error uploading file",
                  type: "is-danger",
                  dismissible: true,
                  pauseOnHover: true,
                  duration: 2000,
                  position: "bottom-right",
                });
            });
        },

        downloadPDF() {
            let requestBody = {
                'operations': this.selectedOperationIds,
                'graphs': this.getGraphData(),
                'report-sections': this.activeReportSections,
                'header-logo': this.logoFilename
            };
            this.$api.post('/plugin/debrief/pdf', requestBody, true).then((data) => {
                data = data.data;
                let dataStr = URL.createObjectURL(new Blob([data["pdf_bytes"]], { type: "application/pdf" }));
                let downloadAnchorNode = document.createElement("a");
                downloadAnchorNode.setAttribute("href", dataStr);
                downloadAnchorNode.setAttribute("download", data.filename);
                document.body.appendChild(downloadAnchorNode);
                downloadAnchorNode.click();
                downloadAnchorNode.remove();
            }).catch((error) => {
                console.error(error);
                toast({
                  message:
                  "Error downloading PDF report",
                  type: "is-danger",
                  dismissible: true,
                  pauseOnHover: true,
                  duration: 2000,
                  position: "bottom-right",
                });
            });
        },

        downloadJSON() {
          this.$api.post('/plugin/debrief/json', { 'operations': this.selectedOperationIds }).then((data) => {
                data = data.data;
                this.downloadJson(data.filename, data);
            }).catch((error) => {
                console.error(error);
                toast({
                  message:
                  "Error downloading JSON report",
                  type: "is-danger",
                  dismissible: true,
                  pauseOnHover: true,
                  duration: 2000,
                  position: "bottom-right",
                });
            });
        },

         downloadJson(filename, data) {
            let dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(data, null, 2));
            let downloadAnchorNode = document.createElement('a');
            downloadAnchorNode.setAttribute("href", dataStr);
            downloadAnchorNode.setAttribute("download", filename + ".json");
            document.body.appendChild(downloadAnchorNode);
            downloadAnchorNode.click();
            downloadAnchorNode.remove();
        },

        getGraphData() {
            let encodedGraphs = {}

            document.querySelectorAll('.debrief-svg').forEach((svg) => {
                let newSvg = svg.cloneNode(true);
                newSvg.setAttribute('id', 'copy-svg');
                document.getElementById('copy').appendChild(newSvg)
                document.querySelectorAll('#copy-svg .container').forEach((container) => container.setAttribute('transform', 'scale(5)'))

                // resize svg viewBox to fit content
                var copy = document.getElementById('copy-svg');
                if (copy.style.display == "none") {
                    copy.style.display = "";
                }
                var bbox = copy.getBBox();
                var viewBox = [bbox.x - 10, bbox.y - 10, bbox.width + 20, bbox.height + 20].join(" ");
                copy.setAttribute("viewBox", viewBox);

                // re-enable any hidden nodes
                document.querySelectorAll('#copy-svg .link').forEach((el) => el.style.display = '');
                document.querySelectorAll('#copy-svg polyline').forEach((el) => el.style.display = '');
                document.querySelectorAll('#copy-svg .link .icons').forEach((el) => {
                    Array.from(el.children).forEach((child) => { 
                        if (child.getAttribute('class').includes('svg-icon')) {
                            child.style.display = '';
                        }
                    })
                })
                document.querySelectorAll('#copy-svg .link .icons').forEach((el) => {
                    Array.from(el.children).forEach((child) => { 
                        if (child.getAttribute('class').includes('hidden')) {
                            child.remove();
                        }
                    })
                })
                document.querySelectorAll('#copy-svg text').forEach((el) => el.style.display = '');
                document.querySelectorAll('#copy-svg text').forEach((el) => el.style.fill = '#333');

                let serializedSvg = new XMLSerializer().serializeToString(document.getElementById('copy-svg'));
                let encodedData = window.btoa(serializedSvg);
                let graphKey = svg.id.split("-")[1];
                encodedGraphs[graphKey] = encodedData;
                document.getElementById('copy').innerHTML = '';
            })

            return encodedGraphs
        },

        toggleLabels() {
            if (this.graphOptionLabels) {
                document.querySelectorAll('#debrief-graph .label').forEach((el) => el.style.display = '');
            } else {
                document.querySelectorAll('#debrief-graph .label').forEach((el) => el.style.display = 'none');
            }
        },

        toggleIcons() {
            if (this.graphOptionIcons) {
                document.querySelectorAll('#debrief-graph .svg-icon:not(.hidden)').forEach((el) => el.style.display = '');
            } else {
                document.querySelectorAll('#debrief-graph .svg-icon:not(.hidden)').forEach((el) => el.style.display = 'none');
            }
        },

        toggleSteps() {
            if (this.graphOptionSteps) {
                document.querySelectorAll('#debrief-graph .link').forEach((el) => el.style.display = '');
                document.querySelectorAll('#debrief-steps-svg .next_link').forEach((el) => el.style.display = '');
            } else {
                document.querySelectorAll('#debrief-graph .link').forEach((el) => el.style.display = 'none');
                document.querySelectorAll('#debrief-steps-svg .next_link').forEach((el) => el.style.display = 'none');
            }
        },

        toggleTactics() {
            let showing = [];
            document.querySelectorAll('#debrief-graph .link .icons').forEach((el) => {
                Array.from(el.children).forEach((child) => { 
                    if (child.classList.contains('svg-icon') && !child.classList.contains('hidden')) showing.push(child);
                });
            });
            let hidden = [];
            document.querySelectorAll('#debrief-graph .link .icons').forEach((el) => {
                Array.from(el.children).forEach((child) => { 
                    if (child.classList.contains('hidden')) hidden.push(child);
                });
            });

            showing.forEach((child) => {
                child.style.display = 'none';
                child.classList.add('hidden');
            });
            hidden.forEach((child) => {
                child.style.display = '';
                child.classList.remove('hidden');
            });
        },

        // Graph functions

        getNodesOrderedByTime() {
            function compareTimestamp(a, b) {
                if (Date.parse(a.dataset.timestamp) < Date.parse(b.dataset.timestamp)) {
                    return -1;
                }
                if (Date.parse(a.dataset.timestamp) > Date.parse(b.dataset.timestamp)) {
                    return 1;
                }
                return 0;
            }
            function getSortedNodes(id) {
                return Array.from(document.querySelectorAll(`#${id} .node`)).sort(compareTimestamp);
            }
            
            this.nodesOrderedByTime = {};
            this.nodesOrderedByTime["debrief-steps-svg"] = getSortedNodes("debrief-steps-svg");
            this.nodesOrderedByTime["debrief-attackpath-svg"] = getSortedNodes("debrief-attackpath-svg");
            this.nodesOrderedByTime["debrief-tactic-svg"] = getSortedNodes("debrief-tactic-svg");
            this.nodesOrderedByTime["debrief-technique-svg"] = getSortedNodes("debrief-technique-svg");
        },

        async visualizePlayPause() {
            this.getNodesOrderedByTime();
            this.isGraphPlaying = !this.isGraphPlaying;
            let id = `debrief-${this.selectedGraphType}-svg`;

            if (this.isGraphPlaying) {
                if (!this.nodesOrderedByTime[id].find(node => node.style.display == "none")) {
                    this.visualizeBeginning();
                }

                while (this.isGraphPlaying) {
                    await this.sleep(1000);
                    if (this.isGraphPlaying) {
                        this.visualizeStepForward();
                    }
                }
            }
        },

       sleep(ms) {
          return new Promise((resolve) => setTimeout(resolve, ms));
      },
        visualizeBeginning() {
            let id = `debrief-${this.selectedGraphType}-svg`;
            document.querySelectorAll(`#${id} .node:not(.c2)`).forEach((node) => node.style.display = 'none');
            document.querySelectorAll(`#${id} polyline`).forEach((node) => node.style.display = 'none');
        },

        visualizeEnd() {
            let id = `debrief-${this.selectedGraphType}-svg`;
            document.querySelectorAll(`#${id} .node`).forEach((node) => node.style.display = 'block');
            document.querySelectorAll(`#${id} polyline`).forEach((node) => node.style.display = 'block');
        },

        visualizeStepForward() {
            this.getNodesOrderedByTime();
            let id = `debrief-${this.selectedGraphType}-svg`;

            let nextNode = this.nodesOrderedByTime[id].find(node => node.style.display == "none");
            if (nextNode) {
                nextNode.style.display = 'block';

                let showingNodesIds = this.nodesOrderedByTime[id].filter(node => node.style.display !== "none").map(node => node.id);
                document.querySelectorAll(`#${id} polyline`).forEach((line) => {
                    if (showingNodesIds.includes(`node-${line.getAttribute('data-target')}`) && showingNodesIds.includes(`node-${line.getAttribute('data-source')}`)) {
                        line.style.display = "block";
                    }
                })
            }

            if (!this.nodesOrderedByTime[id].find(node => node.style.display == "none")) {
                this.isGraphPlaying = false;
            }
        },

        visualizeStepBack() {
            this.getNodesOrderedByTime();
            let id = `debrief-${this.selectedGraphType}-svg`;

            let prevNode = this.nodesOrderedByTime[id].slice().reverse().find(node => node.style.display != "none");

            if (prevNode.id !== "node-0") {
                prevNode.style.display = 'none';

                let showingNodesIds = this.nodesOrderedByTime[id].filter(node => node.style.display != "none").map(node => node.id);
                document.querySelectorAll(`#${id} polyline`).forEach((line) => {
                    if (!showingNodesIds.includes(`node-${line.getAttribute('data-target')}`) || !showingNodesIds.includes(`node-${line.getAttribute('data-source')}`)) {
                        line.style.display = 'none';
                    }
                });
            }
        },
        useCustomLogoChange () {
            if (!this.useCustomLogo) this.logoFilename = '';
        },
  },
};
</script>

<template lang="pug">
div
.content
  h2 复盘
  p
    strong 战役分析。
    |  复盘会为所选的一组行动汇聚整体战役信息与分析，
    |  提供集中化的行动元数据视图、行动可视化图形、
    |  所使用的技术与策略，以及行动过程中发现的事实。

hr

div
  .buttons
    button.button.is-primary.is-small(:disabled="!selectedOperationIds.length", @click="showGraphSettingsModal = true")
      span.icon.is-small
        font-awesome-icon(icon="fas fa-cog")
      span 图表设置
    button.button.is-primary.is-small(:disabled="!selectedOperationIds.length", @click="showReportModal = true")
      span.icon.is-small
        font-awesome-icon(icon="fas fa-download")
      span 下载 PDF 报告
    button.button.is-primary.is-small(:disabled="!selectedOperationIds.length", @click="downloadJSON")
      span.icon.is-small
        font-awesome-icon(icon="fas fa-download")
      span 下载行动 JSON

  .columns.mb-6
    .column.is-3
      form
        .field
          label.label 选择一个或多个行动
          .control.is-expanded
            .select.is-small.is-fullwidth.is-multiple
              select(size="10", multiple, v-model="selectedOperationIds", @change="loadOperation")
                template(v-for="operation in operations", :key="operation.id")
                  option(:value="operation.id") {{ operation.name }}
    .column.is-9.is-flex.is-justify-content-center.m-0
      #images(style="display: none")
      #copy
      #debrief-graph.svg-container(v-show="selectedOperationIds.length")
        .d3-tooltip#op-tooltip(style="opacity: 0")
        .is-flex.graph-controls.m-2
          .select.is-small.mr-2
            select(v-model="selectedGraphType")
              option(value="attackpath") 攻击路径
              option(value="steps") 步骤
              option(value="tactic") 策略
              option(value="technique") 技术
          button.button.is-small(@click="toggleLegend") {{ showGraphLegend ? '隐藏' : '显示' }} 图例
        svg#debrief-steps-svg.op-svg.debrief-svg(v-show="selectedGraphType === 'steps'")
        svg#debrief-attackpath-svg.op-svg.debrief-svg(v-show="selectedGraphType === 'attackpath'")
        svg#debrief-tactic-svg.op-svg.debrief-svg(v-show="selectedGraphType === 'tactic'")
        svg#debrief-technique-svg.op-svg.debrief-svg(v-show="selectedGraphType === 'technique'")
        .buttons.is-justify-content-center.mt-2
          button.button.is-small(@click="visualizeBeginning")
            span.icon.is-small
              font-awesome-icon(icon="fas fa-fast-backward")
          button.button.is-small(@click="visualizeStepBack")
            span.icon.is-small
              font-awesome-icon(icon="fas fa-backward")
          button.button.is-small(v-show="isGraphPlaying", @click="visualizePlayPause")
            span.icon.is-small
              font-awesome-icon(icon="fas fa-pause")
          button.button.is-small(v-show="!isGraphPlaying", @click="visualizePlayPause")
            span.icon.is-small
              font-awesome-icon(icon="fas fa-play")
          button.button.is-small(@click="visualizeStepForward")
            span.icon.is-small
              font-awesome-icon(icon="fas fa-forward")
          button.button.is-small(@click="visualizeEnd")
            span.icon.is-small
              font-awesome-icon(icon="fas fa-fast-forward")

  .tabs.is-centered(v-show="selectedOperationIds.length")
    ul.ml-0
      li(:class="{ 'is-active': activeTab === 'stats' }", @click="activeTab = 'stats'")
        a 统计
      li(:class="{ 'is-active': activeTab === 'agents' }", @click="activeTab = 'agents'")
        a 代理
      li(:class="{ 'is-active': activeTab === 'steps' }", @click="activeTab = 'steps'")
        a 步骤
      li(:class="{ 'is-active': activeTab === 'tactics' }", @click="activeTab = 'tactics'")
        a 策略与技术
      li(:class="{ 'is-active': activeTab === 'facts' }", @click="activeTab = 'facts'")
        a 事实图谱

  div(v-show="selectedOperationIds.length")
    div(v-show="activeTab === 'stats'")
      table.table.is-striped
        caption 行动统计
        thead
          tr
            th 名称
            th 状态
            th 策划器
            th 目标
            th 时间
        tbody
          template(v-for="stat in stats")
            tr
              td {{ stat.name }}
              td {{ stat.state.toUpperCase() }}
              td {{ stat.planner.name }}
              td {{ stat.objective.name }}
              td {{ stat.start }}

    div(v-show="activeTab === 'agents'")
      table.table.is-striped
        caption 行动代理
        thead
          tr
            th Paw（代理ID）
            th 主机
            th 平台
            th 用户名
            th 权限
            th 可执行文件
        tbody
          template(v-for="agent in agents")
            tr
              td {{ agent.paw }}
              td {{ agent.host }}
              td {{ agent.platform }}
              td {{ agent.username }}
              td {{ agent.privilege }}
              td {{ agent.exe_name }}

    div(v-show="activeTab === 'steps'")
      table.table.is-striped
        caption 行动步骤
        thead
          tr
            th 状态
            th 时间
            th 名称
            th 代理
            th 行动
            th 命令
        tbody
          template(v-for="step in steps")
            tr
              td {{ getStatusName(step.status) }}
              td {{ step.finish }}
              td {{ step.ability.name }}
              td {{ step.paw }}
              td {{ step.operation_name }}
              td
                button.button.is-small(@click="showCommand(step.id, step.command, step.ability.name)") 查看命令

    div(v-show="activeTab === 'tactics'")
      template(v-for="tactic in tacticsAndTechniques")
        .card.mb-4
          header.card-header
            p.card-header-title.is-size-5 {{ tactic.name }}
          .card-content
            .content
              p.has-text-centered
                strong 技术
              ul
                template(v-for="technique in Object.keys(tactic.techniques)")
                  li {{ `${tactic.techniques[technique]} | ${technique}` }}
              p.has-text-centered
                strong 步骤
              template(v-for="step in tactic.steps")
                .block
                  p {{ step.operation }}
                  ul
                    template(v-for="ability in step.abilities")
                      li {{ ability }}

    div(v-show="activeTab === 'facts'")
      #fact-graph
        svg#debrief-fact-svg.debrief-svg
        .d3-tooltip#fact-tooltip(style="opacity: 0")
      article#fact-limit.message.is-info
        #fact-limit-msg.message-body

  .modal(v-bind:class="{ 'is-active': showGraphSettingsModal }")
    .modal-background(@click="showGraphSettingsModal = false")
    .modal-card
      header.modal-card-head
        p.modal-card-title 图表设置
      section.modal-card-body
        p
          strong 显示选项
        form
          .field
            .control
              label.checkbox
                input(type="checkbox", v-model="graphOptionLabels", @change="toggleLabels")
                |  显示标签
          .field
            .control
              label.checkbox
                input(type="checkbox", v-model="graphOptionIcons", @change="toggleIcons")
                |  显示图标
        p
          strong 数据选项
        form
          .field
            .control
              label.checkbox
                input(type="checkbox", v-model="graphOptionSteps", @change="toggleSteps")
                |  显示行动步骤
          .field
            .control
              label.checkbox
                input(type="checkbox", @change="toggleTactics")
                |  以策略展示步骤
      footer.modal-card-foot
        nav.level
          .level-left
          .level-right
            .level-item
              button.button.is-small(@click="showGraphSettingsModal = false") 关闭

  .modal(v-bind:class="{ 'is-active': showCommandModal }")
    .modal-background(@click="showCommandModal = false")
    .modal-card
      header.modal-card-head
        p.modal-card-title {{ `步骤：${commandAbilityName}` }}
      section.modal-card-body
        p 命令
        pre {{ command }}
        p {{ `标准输出${commandOutput.stdout ? '' : '：无可显示内容'}` }}
        template(v-if="commandOutput != '' && commandOutput.stdout !== ''")
          pre.has-text-left.white-space-pre-line {{ commandOutput.stdout }}
        p {{ `标准错误${commandOutput.stderr ? '' : '：无可显示内容'}` }}
        template(v-if="commandOutput != '' && commandOutput.stderr !== ''")
          pre.has-text-left.white-space-pre-line.has-text-danger {{ commandOutput.stderr }}
      footer.modal-card-foot
        nav.level
          .level-left
          .level-right
            .level-item
              button.button.is-small(@click="showCommandModal = false") 关闭

  .modal(v-bind:class="{ 'is-active': showReportModal }")
    .modal-background(@click="showReportModal = false")
    .modal-card
      header.modal-card-head
        p.modal-card-title 以 PDF 下载报告
      section.modal-card-body.content.mb-0
        h5 报告页眉徽标
        p.help 选择一个徽标，它将显示在每页右上角。
        form
          label.checkbox
            input(type="checkbox", v-model="useCustomLogo", @change="useCustomLogoChange")
            | 使用自定义徽标
        .mt-3
        .columns(v-show="useCustomLogo")
          .column.is-6.m-0
            form
              .field
                label.label 选择徽标
                .control
                  .select.is-small.is-fullwidth
                    select(v-model="logoFilename")
                      option(default, disabled, value="") 请选择徽标
                      template(v-for="logo in logos", :key="logo")
                        option(v-bind:value="logo") {{ logo }}
              .field
                .file.is-dark.is-small.is-fullwidth
                  label.file-label
                    input.file-input(type="file", name="userLogo", accept="image/*", v-on:change="uploadLogo($el)", ref="fileInput")
                    span.file-cta
                      span.file-icon
                        i.fas.fa-upload
                      span.file-label 上传新徽标…
          .column.is-6.m-0.is-flex.is-align-items-center.is-justify-content-center
            template(v-if="logoFilename")
              img(:alt="'用于报告页眉的徽标'", :src="`/logodebrief/header-logos/${logoFilename}`")
            p(v-else) 选择徽标以预览
        h5 报告章节
        p.help 勾选的章节将按下方列表顺序显示在报告中。
        table
          caption 报告中显示的章节
          thead
            tr
              th(scope="col")
              th(scope="col")
              th(scope="col")
          tbody
            template(v-for="(section, index) in reportSections", :key="section.key")
              tr
                td.is-flex.is-flex-direction-column.is-align-items-center.is-justify-content-center
                  span.icon.is-small(@click="moveReportSectionOrder(index, index - 1)")
                    i(v-show="index", class="fas fa-sort-up")
                  span.icon.is-small(@click="moveReportSectionOrder(index, index + 1)")
                    i(v-show="index < reportSections.length - 1", class="fas fa-sort-down")
                td
                  .is-flex.is-align-items-center
                    input(type="checkbox", v-bind:checked="activeReportSections.includes(section.key)", v-on:change="toggleReportSection(section.key)")
                td {{ section.name }}

      footer.modal-card-foot
        nav.level
          .level-left
            .level-item
              button.button.is-small(@click="showReportModal = false") 关闭
          .level-right
            .level-item
              button.button.is-small.is-primary(@click="downloadPDF") 下载

  .modal(v-bind:class="{ 'is-active': showCommandModal }")
    .modal-background(@click="showCommandModal = false")
    .modal-card
      header.modal-card-head
        p.modal-card-title {{ `步骤：${commandAbilityName}` }}
      section.modal-card-body
        p 命令
        pre {{ command }}
        p {{ `标准输出${commandOutput.stdout ? '' : '：无可显示内容'}` }}
        template(v-if="commandOutput && commandOutput.stdout")
          pre.has-text-left.white-space-pre-line {{ commandOutput.stdout }}
        p {{ `标准错误${commandOutput.stderr ? '' : '：无可显示内容'}` }}
        template(v-if="commandOutput && commandOutput.stderr")
          pre.has-text-left.white-space-pre-line.has-text-danger {{ commandOutput.stderr }}

      footer.modal-card-foot
        nav.level
          .level-left
          .level-right
            .level-item
              button.button.is-small(@click="showCommandModal = false") 关闭
</template>
