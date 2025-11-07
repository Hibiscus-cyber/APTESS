<script>
import { b64DecodeUnicode } from "@/utils/utils";
    export default {
      inject: ["$api"],
      data() {
        return {
          // Core variables
          agents: [],
          links: [],
          obfuscators: [
                {
                    "description": "Obfuscates commands in base64",
                    "name": "base64"
                },
                {
                    "description": "Obfuscates commands in base64, then adds characters to evade base64 detection. Disclaimer: this may cause duplicate links to run.",
                    "name": "base64jumble"
                },
                {
                    "description": "Obfuscates commands in base64, then removes padding",
                    "name": "base64noPadding"
                },
                {
                    "description": "Obfuscates commands through a caesar cipher algorithm, which uses a randomly selected shift value.",
                    "name": "caesar cipher"
                },
                {
                    "description": "Does no obfuscation to any command, instead running it in plain text",
                    "name": "plain-text"
                },
                {
                    "description": "Obfuscates commands through image-based steganography",
                    "name": "steganography"
                }
            ],
          selectedObfuscator: 'base64',
          selectedAgent: {},
          selectedAgentPaw: '',
          abilities: [],
          filteredAbilities: [],
          selectedAbility: {},
          selectedAbilityId: '',
          tactics: [],
          selectedTactic: '',
          techniques: [],
          selectedTechnique: '',
          searchQuery: '',
          searchResults: [],
          // Modals
          showOutputModal: false,
          outputCommand: '',
          outputResult: '',
          showRunModal: false,
          facts: []
        };
      },
      created() {
        this.initPage();
      },
      methods: {
        async initPage() {
          try {
            const agentsRes = await this.$api.get('/api/v2/agents');
            this.agents = agentsRes.data;
            const abilityRes = await this.$api.get('/api/v2/abilities');
            this.abilities = abilityRes.data;
            const obfuscatorsRes = await this.$api.get('/api/v2/obfuscators');
            this.obfuscators = obfuscatorsRes.data;
            while (this.$refs.headerAccess) {
              await this.sleep(3000);
              this.refreshAgents();
            }
          } catch (error) {
            this.toast('There was an error initializing the page', false);
            console.error(error);
          }
        },

        selectAgent() {
          this.selectedAgent = this.agents.find((agent) => agent.paw === this.selectedAgentPaw);
          this.links = this.selectedAgent.links;
          this.filterAbilitiesByPlatform();
        },

        filterAbilitiesByPlatform() {
          let platform = this.selectedAgent.platform;
          this.filteredAbilities = [];
          this.abilities.forEach((ability) => {
            let execPlatforms = ability.executors.map((exec) => exec.platform);
            if (execPlatforms.includes(platform)) {
              this.filteredAbilities.push(ability);
            }
          });
        },

        async refreshAgents() {
          try {
            const res = await this.$api.get('/api/v2/agents');
            this.agents = res.data;
            if (this.selectedAgentPaw) {
              this.selectAgent();
            }
          } catch (error) {
            this.toast('There was an error refreshing the page', false);
            console.error(error);
          }
        },

        getLinkStatus(link) {
          if (link.status === 0) {
            return 'success';
          } else if (link.status > 0) {
            return 'failed';
          } else {
            return 'in progress';
          }
        },

        showOutput(link) {
          this.$api.post('/api/rest', {'index': 'result', 'link_id': link.unique}).then((data) => {
            this.outputCommand = b64DecodeUnicode(link.command);
            try {
              this.outputResult = JSON.parse(b64DecodeUnicode(data.data.output));
            } catch (SyntaxError) {
              this.outputResult = ""
            }
            this.showOutputModal = true;
          });
        },

        searchForAbility() {
          this.searchResults = [];
          if (!this.searchQuery) return;
          this.filteredAbilities.forEach((ability) => {
            if (ability.name.toLowerCase().indexOf(this.searchQuery.toLowerCase()) > -1) {
              this.searchResults.push({
                ability_id: ability.ability_id,
                name: ability.name
              });
            }
          });
        },

        selectAbility(id) {
          this.searchQuery = [];
          this.searchResults = [];
          this.selectedAbility = this.abilities.find((ability) => ability.ability_id === id);
          this.selectedTactic = this.selectedAbility.tactic;
          this.selectedTechnique = this.selectedAbility.technique_id;
          this.selectedAbilityId = id;
          this.findFacts();
        },

        findFacts() {
          let rxp = /#{([^}]+)}/g;
          let match;
          let matches = [];
          let commands = this.selectedAbility.executors.map((exec) => exec.command);
          commands.forEach((command) => {
            while (match = rxp.exec(command)) {
              matches.push(match[1]);
            }
          });
          this.facts = [...new Set(matches)].map((fact) => { 
            return { trait: fact, value: '' };
          });
        },

        async execute() {
          if (this.facts.length && this.facts.filter((fact) => !fact.value).length) {
            this.toast('Fact values cannot be empty!', false);
            return;
          }

          let requestBody = {
            paw: this.selectedAgentPaw,
            ability_id: this.selectedAbilityId,
            facts: this.facts,
            obfuscator: this.selectedObfuscator
          };

          try {
            await this.$api.post('/plugin/access/exploit', requestBody);
            this.showRunModal = false;
            this.refreshAgents();
            this.toast('Executed ability', true);
          } catch (error) {
            console.error(error);
          }
        },

        sleep(ms) {
          return new Promise(resolve => setTimeout(resolve, ms));
        },

        toast(message, type) {
          // Your toast implementation here
        }
      }
    };
</script>

<template lang="pug">
div(ref="headerAccess")
.content 
    h2 访问控制

    p 在此，您可以在不依赖任何行动的情况下，从数据库中为任意代理分配任意能力任务。这在进行初始访问攻击时尤为有用。  
      | 您可以在本地部署一个代理，并为其分配 pre-ATT&CK 或初始访问阶段的策略，指向任意目标。  
      | 您甚至可以远程部署一个代理，并将其作为代理节点来执行初始访问攻击。  
      | 右侧将显示每个被直接分配任务的代理。
    hr
// 代理选择

div.mb-6
    form
        #select-agent.field.has-addons
            label.label.mr-5 选择代理
            .control.is-expanded
                .select.is-small.is-fullwidth
                    select(v-on:change="selectAgent()" v-model="selectedAgentPaw")
                        option(value="" disabled selected) 请选择代理
                        template(v-for="agent of agents" :key="agent.paw")
                            option(v-bind:value="agent.paw" v-text="`${agent.host} - ${agent.paw}`")

div.has-text-centered.content(v-show="!selectedAgentPaw")
    p 请选择一个代理以开始操作

div.mb-3(v-show="selectedAgentPaw")
    .is-flex(v-show="selectedAgentPaw")
        button.button.is-primary.is-small.mr-6(@click="showRunModal = true")
            span.icon
                i.fas.fa-running
            span 运行能力
        span.mr-6
            strong.mr-4 代理平台
            span(v-text="selectedAgent.platform")
        span
            strong.mr-4 可用能力数量
            span(v-text="filteredAbilities.length")
    p.has-text-centered.content(v-show="!links.length") 暂无可显示的链接

div(v-show="selectedAgentPaw && links.length")
    table.table.is-striped.is-fullwidth
        thead
            tr
                th 序号
                th 名称
                th 策略
                th 状态
                th
        tbody
            tr.pointer(v-for="(link, index) in links", :key="link.unique")
                td(v-text="index + 1")
                td(v-text="link.ability.name")
                td(v-text="link.ability.tactic")
                td(v-text="getLinkStatus(link)" v-bind:class="{ 'has-text-danger': getLinkStatus(link) === 'failed', 'has-text-success': getLinkStatus(link) === 'success' }")
                td
                    button.button.is-small.is-primary(@click="showOutput(link)") 查看输出

// 输出结果弹窗

div.modal(v-bind:class="{ 'is-active': showOutputModal }")
    .modal-background(@click="showOutputModal = false")
    .modal-card.wide
        header.modal-card-head
            p.modal-card-title 链接输出
        section.modal-card-body
            label.label 命令
            pre(v-text="outputCommand")
            label.label 标准输出
            pre(v-text="outputResult.stdout || '[ 无输出内容 ]'")
        footer.modal-card-foot
            nav.level
                .level-left
                .level-right
                    .level-item
                        button.button.is-small(@click="showOutputModal = false") 关闭

// 运行能力弹窗

div.modal(v-bind:class="{ 'is-active': showRunModal }")
    .modal-background(@click="showRunModal = false")
    .modal-card
        header.modal-card-head
            p.modal-card-title 运行能力
        section.modal-card-body
            p.has-text-centered 选择一个能力
            form
                .field.is-horizontal
                    .field-label.is-small
                        label.label
                            span.icon.is-small
                                i.fas.fa-search
                    .field-body
                        .field
                            .control
                                input.input.is-small(v-model="searchQuery" placeholder="搜索能力…" v-on:keyup="searchForAbility()")
                                .search-results
                                    template(v-for="result in searchResults", :key="result.ability_id")
                                        p(@click="selectAbility(result.ability_id)" v-text="result.name")
            form
                .field.is-horizontal
                    .field-label.is-small
                        label.label 策略
                    .field-body
                        .field
                            .control
                                div.select.is-small.is-fullwidth
                                    select(v-model="selectedTactic" v-on:change="selectedAbilityId = ''")
                                        option(disabled selected value="") 选择策略 
                                        option(v-for="tactic of [...new Set(filteredAbilities.map((e) => e.tactic))]", :key="tactic" :value="tactic") {{ tactic }}
                .field.is-horizontal
                    .field-label.is-small
                        label.label 技术
                    .field-body
                        .field
                            .control
                                div.select.is-small.is-fullwidth
                                    select(v-model="selectedTechnique" v-bind:disabled="!selectedTactic" v-on:change="selectedAbilityId = ''")
                                        option(disabled selected value="") 选择技术 
                                        template(:key="exploit.technique_id" v-for="exploit of [...new Set(filteredAbilities.filter((e) => selectedTactic === e.tactic).map((e) => e.technique_id))].map((t) => filteredAbilities.find((e) => e.technique_id === t))")
                                            option(v-bind:value="exploit.technique_id" v-text="exploit.technique_id")
                .field.is-horizontal
                    .field-label.is-small
                        label.label 能力
                    .field-body
                        .field
                            .control
                                div.select.is-small.is-fullwidth
                                    select(v-model="selectedAbilityId", v-bind:disabled="!selectedTechnique" v-on:change="selectAbility(selectedAbilityId)")
                                        option(disabled selected value="") 选择能力 
                                        template(v-for="ability of filteredAbilities.filter((e) => selectedTechnique === e.technique_id)", :key="ability.ability_id")
                                            option(v-bind:value="ability.ability_id" v-text="ability.name")
            template(v-if="selectedAbilityId")
                .content
                    hr
                    h3 {{ selectedAbility.name }}
                    p {{ selectedAbility.description }}

                    form.mb-4
                        .field.is-horizontal
                            .field-label.is-small
                                label.label 混淆器
                            .field-body
                                .field.is-narrow
                                    .control.is-expanded
                                        .select.is-fullwidth.is-small
                                            select(v-model="selectedObfuscator")
                                                template(v-for="obf in obfuscators" :key="obf.name")
                                                    option(v-bind:value="obf.name" v-text="obf.name")

                        template(v-for="fact in facts" :key="fact.trait")
                            .field.is-horizontal
                                .field-label.is-small
                                    label.label {{ fact.trait }}
                                .field-body
                                    .field
                                        .control
                                            input.input.is-small.is-fullwidth(v-model="fact.value" placeholder="请输入值…")

                    button.button.is-small.is-primary.is-fullwidth(@click="execute()") 执行

        footer.modal-card-foot
            nav.level
                .level-left
                .level-right
                    .level-item
                        button.button.is-small(@click="showRunModal = false") 关闭
</template>


<style scoped>
#select-agent {
    max-width: 800px;
    margin: 0 auto;
}

.search-results {
    overflow-y: scroll;
    max-height: 200px;
    background-color: #010101;
    border-radius: 0 4px;
}
.search-results p {
    margin-bottom: 0 !important;
    padding: 5px;
    cursor: pointer;
}
.search-results p:hover {
    background-color: #484848;
}
</style>
