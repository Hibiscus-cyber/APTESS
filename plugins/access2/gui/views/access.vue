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
        this.agentRefreshInterval = setInterval(() => {
          this.refreshAgents();
        }, 3000);
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
      }).catch(error => {
        console.error('Error fetching output:', error);
        this.toast('Failed to load output', false);
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
        await this.$api.post('/plugin/access2/exploit', requestBody);
        this.showRunModal = false;
        this.refreshAgents();
        this.toast('Executed ability', true);
      } catch (error) {
        console.error(error);
        this.toast('Failed to execute ability', false);
      }
    },

    sleep(ms) {
      return new Promise(resolve => setTimeout(resolve, ms));
    },

    toast(message, type) {
      // Your toast implementation here
    }
  },
  beforeDestroy() {
    if (this.agentRefreshInterval) {
      clearInterval(this.agentRefreshInterval);
    }
  }
};
</script>

<template lang="pug">
div(ref="headerAccess")
    h2 Access2
    p Here you can task any agent with any ability from the database - outside the scope of an operation. This is especially useful for conducting initial access attacks. To do this, deploy an agent locally and task it with either pre-ATT&CK or initial access tactics, pointed at any target. You can even deploy an agent remotely and use it as a proxy to conduct your initial access attacks. To the right, you'll see every ability directly tasked to an agent.
    hr
// AGENT SELECTION

div.mb-6
    form
        #select-agent.field.has-addons
            label.label.mr-5 Select an agent
            .control.is-expanded
                .select.is-small.is-fullwidth
                    select(v-on:change="selectAgent()" v-model="selectedAgentPaw")
                        option(value="" disabled selected) Select an agent
                        template(v-for="agent of agents" :key="agent.paw")
                            option(v-bind:value="agent.paw" v-text="`${agent.host} - ${agent.paw}`")

div.has-text-centered.content(v-show="!selectedAgentPaw")
    p Select an agent to get started

div.mb-3(v-show="selectedAgentPaw")
    .is-flex(v-show="selectedAgentPaw")
        button.button.is-primary.is-small.mr-6(@click="showRunModal = true")
            span.icon
                i.fas.fa-running
            span Run an Ability
        span.mr-6
            strong.mr-4 Agent Platform
            span(v-text="selectedAgent.platform")
        span
            strong.mr-4 Compatible Abilities
            span(v-text="filteredAbilities.length")
    p.has-text-centered.content(v-show="!links.length") No links to show

div(v-show="selectedAgentPaw && links.length")
    table.table.is-striped.is-fullwidth
        thead
            tr
                th order
                th name
                th tactic
                th status
                th
        tbody
            tr.pointer(v-for="(link, index) in links" :key="link.unique")
                td(v-text="index + 1")
                td(v-text="link.ability.name")
                td(v-text="link.ability.tactic")
                td(v-text="getLinkStatus(link)" v-bind:class="{ 'has-text-danger': getLinkStatus(link) === 'failed', 'has-text-success': getLinkStatus(link) === 'success' }")
                td
                    button.button.is-small.is-primary(@click="showOutput(link)") Output

// MODALS

div.modal(v-bind:class="{ 'is-active': showOutputModal }")
    .modal-background(@click="showOutputModal = false")
    .modal-card.wide
        header.modal-card-head
            p.modal-card-title Link Output
        section.modal-card-body
            label.label Command
            pre(v-text="outputCommand")
            label.label Standard Output
            pre(v-text="outputResult.stdout || '[ no output to show ]'")
        footer.modal-card-foot
            nav.level
                .level-left
                .level-right
                    .level-item
                        button.button.is-small(@click="showOutputModal = false") Close

div.modal(v-bind:class="{ 'is-active': showRunModal }")
    .modal-background(@click="showRunModal = false")
    .modal-card
        header.modal-card-head
            p.modal-card-title Run an Ability
        section.modal-card-body
            p.has-text-centered Select an Ability
            form
                .field.is-horizontal
                    .field-label.is-small
                        label.label
                            span.icon.is-small
                                i.fas.fa-search
                    .field-body
                        .field
                            .control
                                input.input.is-small(v-model="searchQuery" placeholder="Search for an ability..." v-on:keyup="searchForAbility()")
                                .search-results
                                    template(v-for="result in searchResults" :key="result.ability_id")
                                        p(@click="selectAbility(result.ability_id)" v-text="result.name")
            form
                .field.is-horizontal
                    .field-label.is-small
                        label.label Tactic
                    .field-body
                        .field
                            .control
                                .select.is-small
                                    select(v-model="selectedTactic" @change="tacticFilter")
                                        option(value="") All Tactics
                                        option(v-for="tactic in tactics" :key="tactic" v-bind:value="tactic" v-text="tactic")
                .scrollable-abilities
                    template(v-for="ability in filteredAbilities" :key="ability.ability_id")
                        .ability-selector-item(v-if="abilityMatchesSearch(ability) && abilityMatchesTactic(ability)" @click="selectAbility(ability.ability_id)")
                            span.ability-name(v-text="ability.name")
                            span.ability-tactic(v-text="ability.tactic")
                .mt-4(v-if="selectedAbilityId")
                    h3.title.is-5(v-text="selectedAbility.name")
                    .field.is-horizontal
                        .field-label.is-small
                            label.label Description
                        .field-body
                            .field
                                p(v-text="selectedAbility.description")
                    .field.is-horizontal
                        .field-label.is-small
                            label.label Technique
                        .field-body
                            .field
                                p(v-text="selectedAbility.technique_id")
                    .field.is-horizontal
                        .field-label.is-small
                            label.label Executor
                        .field-body
                            .field
                                .select.is-small
                                    select(v-model="selectedObfuscator")
                                        option(v-for="obfuscator in obfuscators" :key="obfuscator.name" v-bind:value="obfuscator.name" v-text="`${obfuscator.name} (${obfuscator.description})`")
                .mt-4(v-if="facts.length > 0")
                    h3.title.is-5 Facts
                    p Fill in the values for these facts
                    div(v-for="fact in facts" :key="fact.trait")
                        .field.is-horizontal
                            .field-label.is-small
                                label.label(v-text="fact.trait")
                            .field-body
                                .field
                                    input.input.is-small(v-model="fact.value" v-bind:placeholder="'Enter value for ' + fact.trait")
        footer.modal-card-foot
            nav.level
                .level-left
                .level-right
                    .level-item
                        button.button.is-small.is-primary(v-if="selectedAbilityId" @click="execute()") Execute
                    .level-item
                        button.button.is-small(@click="showRunModal = false") Close
</template>

<style scoped>
#select-agent {
  margin-bottom: 20px;
}

.scrollable-abilities {
  max-height: 200px;
  overflow-y: auto;
  border: 1px solid #dbdbdb;
  border-radius: 4px;
  padding: 10px;
}

.ability-selector-item {
  padding: 8px;
  border-bottom: 1px solid #eee;
  cursor: pointer;
}

.ability-selector-item:hover {
  background-color: #f5f5f5;
}

.ability-name {
  font-weight: bold;
  display: block;
}

.ability-tactic {
  font-size: 0.8em;
  color: #666;
}

.search-results {
  position: absolute;
  background-color: white;
  border: 1px solid #dbdbdb;
  border-radius: 4px;
  max-height: 200px;
  overflow-y: auto;
  z-index: 100;
  width: calc(100% - 20px);
  margin-top: 5px;
}

.search-results p {
  padding: 8px;
  margin: 0;
  cursor: pointer;
}

.search-results p:hover {
  background-color: #f5f5f5;
}
</style>