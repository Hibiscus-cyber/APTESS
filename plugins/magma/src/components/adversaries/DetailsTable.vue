<script setup>
import { storeToRefs } from "pinia";
import { ref, reactive, watch, inject } from "vue";

import { useAdversaryStore } from "@/stores/adversaryStore";
import { useObjectiveStore } from "@/stores/objectiveStore";
import { useCoreDisplayStore } from "@/stores/coreDisplayStore";
import CreateEditAbility from "@/components/abilities/CreateEditAbility.vue";
import FactBreakdownModal from "@/components/adversaries/FactBreakdownModal.vue";
import AddAbilitiesFromAdversaryModal from "@/components/adversaries/AddAbilitiesFromAdversaryModal.vue";
import AbilitySelection from "@/components/abilities/AbilitySelection.vue";
import DeleteAdversaryConfirmationModal from "./DeleteAdversaryConfirmationModal.vue";

const $api = inject("$api");

const adversaryStore = useAdversaryStore();
const { selectedAdversary, selectedAdversaryAbilities } = storeToRefs(adversaryStore);
const objectiveStore = useObjectiveStore();
const { objectives } = storeToRefs(objectiveStore);
const coreDisplayStore = useCoreDisplayStore();
const { modals } = storeToRefs(coreDisplayStore);

let isEditingName = ref(false);
let validation = reactive({
    name: ""
});

// Ability dependencies
let undefinedAbilities = ref([]);
let abilityDependencies = ref({});
let factBreakdown = ref([]);
let needsParser = ref([]);
let isTacticBreakdownActive = ref(false);
let onHoverLocks = ref([]);
let onHoverUnlocks = ref([]);

// Table row drag and drop
let tableDragTarget = ref(null);
let tableDragEndIndex = ref(null);
let tableDragTargetIndex = ref(null);
let tableDragHoverId = ref(null);

// Abilities
let selectedAbility = ref({});

// Modals
let showAbilitySelection = ref(false);
let showCreateEditAbilityModal = ref(false);
let showAddFromAdversary = ref(false);

findAbilityDependencies();

watch(selectedAdversaryAbilities, () => {
    findAbilityDependencies();
});

function findAbilityDependencies() {
    const types = {};
    let factsCollected = [];
    let factsRequired = [];
    undefinedAbilities.value = [];

    selectedAdversaryAbilities.value.forEach((ability) => {	
        let requireTypes = [];
        let enableTypes = [];

        // Skip building out enable types and require types if ability is unknown
        if (ability.ability_id !== undefined) {    
            // Get all parser types from executors
            ability.executors.forEach((executor) => {
                executor.parsers.forEach((parser) => {
                    enableTypes = enableTypes.concat(parser.parserconfigs.map((rel) => rel.source));
                });
            });
            // Get all requirement types
            ability.requirements.forEach((requirement) => {
                requireTypes = requireTypes.concat(requirement.relationship_match.map((match) => match.source));
            });
        } else {
            undefinedAbilities.value.push(ability.ability_id);
        }

        types[ability.ability_id] = {
            enableTypes: [...new Set(enableTypes)],
            requireTypes: [...new Set(requireTypes)]
        };
    });

    selectedAdversaryAbilities.value.forEach((ability, index) => {
        const enablesAbilityIds = [];
        const requiresAbilityIds = [];
        const requireTypesMet = [];

        // For each parser, look at and forward for any ability it unlocks
        types[ability.ability_id].enableTypes.forEach((key) => {
            if(selectedAdversaryAbilities.value) {
                for (let i = index; i < selectedAdversaryAbilities.value.length; i++) {
                    if (types[selectedAdversaryAbilities.value[i].ability_id].requireTypes.indexOf(key) > -1) {
                        enablesAbilityIds.push(selectedAdversaryAbilities.value[i].ability_id);
                    }
                }
            }
        });

        // For each requirement, look at and before for any ability to unlock it
        types[ability.ability_id].requireTypes.forEach((requirement) => {
            let requirementMet = false;
            for (let i = index; i >= 0; i--) {
                if (types[selectedAdversaryAbilities.value[i].ability_id].enableTypes.indexOf(requirement) > -1) {
                    requiresAbilityIds.push(selectedAdversaryAbilities.value[i].ability_id);
                    requirementMet = true;
                }
            }
            requireTypesMet.push(requirementMet);
        });

        abilityDependencies.value[ability.ability_id] = {
            // The ability IDs that this ability will enable
            enablesAbilityIds: [...new Set(enablesAbilityIds)],
            // The ability IDs that this ability is dependent on
            requiresAbilityIds: [...new Set(requiresAbilityIds)],
            // The names of the parser requirements this ability enables
            enableTypes: types[ability.ability_id].enableTypes,
            // The names of the requirements this ability needs from a parser
            requireTypes: types[ability.ability_id].requireTypes,
            // Same dimension as requireTypes, but true/false if requirement has been met
            requireTypesMet: requireTypesMet,
        };

        // Update fact totals for fact breakdown
        factsCollected = factsCollected.concat(types[ability.ability_id].enableTypes);
        factsRequired = factsRequired.concat(types[ability.ability_id].requireTypes);
    });

    factBreakdown.value = [];
    factsCollected = [...new Set(factsCollected)];
    factsRequired = [...new Set(factsRequired)];
    factsRequired.forEach((fact) => {
        factBreakdown.value.push({ fact: fact, type: factsCollected.includes(fact) ? 'met' : 'unmet' });
    });
    factsCollected.filter(x => !factsRequired.includes(x)).forEach((fact) => {
        factBreakdown.value.push({ fact: fact, type: 'extra' });
    });

    hasMetAbilityDependencies();
}

function hasMetAbilityDependencies() {
    let isMet = true;
    needsParser.value = [];

    Object.keys(abilityDependencies.value).forEach((abilityId) => {
        if (!abilityDependencies.value[abilityId].requireTypesMet.every(((requirement) => requirement))) {
            isMet = false;
            try {
                needsParser.value.push(selectedAdversaryAbilities.value.find((ability) => ability.ability_id === abilityId).name);
            } catch {
                needsParser.value.push();
            }
        }
    });

    return isMet;
}

function getExecutorDetail(detail, ability) {
    const executorNameMap = new Map([
        ['psh', 'powershell'],
        ['pwsh', 'powershell core'],
        ['sh', 'shell'],
        ['cmd', 'commandline'],
    ]);
    const plats = [];
    let hasCleanup = false;
    let hasPayload = false;
    let hasParser = false;

    if(ability.executors) {
        ability.executors.forEach((executor) => {
            if (executor.cleanup.length > 0) hasCleanup = true;
            if (executor.parsers.length > 0) hasParser = true;
            if (executor.payloads.length > 0) hasPayload = true;
            plats.push(`${executor.platform} (${executorNameMap.get(executor.name) || executor.name})`);
        });
    }

    switch (detail) {
        case 'cleanup':
            return hasCleanup;
        case 'parser':
            return hasParser;
        case 'payload':
            return hasPayload;
        case 'requirements':
            if(ability.requirements){
                return ability.requirements.length > 0;
            }
        case 'platforms':
            return plats;
        default:
            return false;
    }
}

function getTacticBreakdown() {
    if (!selectedAdversaryAbilities.value) return;
    let counts = {};
    selectedAdversaryAbilities.value.forEach((ability) => {
        counts[ability.tactic] ? counts[ability.tactic] += 1 : counts[ability.tactic] = 1;
    });
    return Object.keys(counts).sort().map((tactic) => {
        let percent = Math.ceil(counts[tactic] / selectedAdversaryAbilities.value.length * 10000) / 100
        return [tactic, percent]
    })
}

function hashStringToColor(str) {
    let hash = 5381;
    if(str) {
        for (let i = 0; i < str.length; i++) {
            hash = ((hash << 5) + hash) + str.charCodeAt(i);
        }
    }

    let r = (hash & 0xFF0000) >> 16;
    let g = (hash & 0x00FF00) >> 8;
    let b = hash & 0x0000FF;
    return "#" + ("0" + r.toString(16)).substr(-2) + ("0" + g.toString(16)).substr(-2) + ("0" + b.toString(16)).substr(-2);
}

function setAbilityHover(abilityId) {
    if (!abilityDependencies.value[abilityId]) return;
    onHoverLocks.value = abilityDependencies.value[abilityId].requiresAbilityIds;
    onHoverUnlocks.value = abilityDependencies.value[abilityId].enablesAbilityIds;
    if (abilityDependencies.value[abilityId].requireTypes.length) onHoverUnlocks.value.push(abilityId);
    if (abilityDependencies.value[abilityId].enableTypes.length) onHoverLocks.value.push(abilityId);
}

function startAbilitySwap(event) {
    tableDragTarget.value = event.target.parentNode;
    tableDragTargetIndex.value = parseInt(tableDragTarget.value.children[1].children[0].children[0].innerHTML, 10);
}

function swapAbilitiesHover(event) {
    if (!event.target.parentNode.children[1]) return;
    tableDragEndIndex.value = parseInt(event.target.parentNode.children[1].children[0].children[0].innerHTML, 10);
}

function swapAbilities() {
    const fromIndex = tableDragTargetIndex.value - 1;
    const toIndex = tableDragEndIndex.value - 1;
    const temp = selectedAdversaryAbilities.value[fromIndex]; 
    selectedAdversaryAbilities.value.splice(fromIndex, 1); 
    selectedAdversaryAbilities.value.splice(toIndex, 0, temp); 
    tableDragHoverId.value = undefined;
    tableDragEndIndex.value = undefined;
}

function selectAbility(ability) {
    selectedAbility.value = ability;
    showCreateEditAbilityModal.value = true;
}

function validateAndSaveAdversary() {
    if (!selectedAdversary.value.name || !selectedAdversary.value.description) {
        isEditingName.value = true;
        validation.name = "Name and description can't be blank";
        return;
    }
    adversaryStore.saveSelectedAdversary($api);
    validation.name = "";
    isEditingName.value = false;
}

function exportAdversary() {
    let yaml = `id: ${selectedAdversary.value.adversary_id}\n`;
    yaml += `name: ${selectedAdversary.value.name}\n`;
    yaml += `description: ${selectedAdversary.value.description}\n`;
    yaml += `objective: ${selectedAdversary.value.objective}\n`;
    yaml += `atomic_ordering:\n`;
    selectedAdversaryAbilities.value.forEach((ability) => yaml += `- ${ability.ability_id}\n`);
    yaml += `abilities:\n`;
    selectedAdversaryAbilities.value.forEach((ability) => {
        yaml += ` ${ability.ability_id}:\n`;
        yaml += `  name:  ${ability.name}\n`;
        yaml += `  tactic:  ${ability.tactic}\n`;
        yaml += `  technique_name:  "${ability.technique_name}"\n`;
        yaml += `  technique_id:  ${ability.technique_id}\n`;
        yaml += `  executors: \n`;
        ability.executors.forEach((executor) => {
            yaml += `   - ${executor.name}:\n`;
            yaml += `     platform: ${executor.platform}\n`;
            yaml += `     command: |\n       ${executor.command.replaceAll("\n", "\n       ")}\n`;
        });
    });

    const blob = new Blob([yaml], { type: 'application/x-yaml' })
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.style.display = 'none';
    a.href = url;
    a.download = `${selectedAdversary.value.name}.yaml`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
}

function addAbilityToAdversary(ability) {
    selectedAdversaryAbilities.value.push(ability);
    showAbilitySelection.value = false;
}

function addAbilitiesFromAdversary(abilities) {
    abilities.forEach((ability) => addAbilityToAdversary(ability));
    showAddFromAdversary.value = false;
}
</script>

<template lang="pug">
//- Header
.content(v-if="!isEditingName" @click="isEditingName = true")
    h3.pointer {{ selectedAdversary.name }} {{ selectedAdversary.name === "New adversary" ? "(点击以编辑)" : "" }}
    p.pointer {{ selectedAdversary.description }}
form.mb-4(v-else)
    .field
        .control
            input.input.is-large(v-model="selectedAdversary.name" placeholder="对手名称")
    .field
        .control
            input.input(v-model="selectedAdversary.description" placeholder="对手描述")
    p.help.has-text-danger.mb-3(v-if="validation.name") {{ validation.name }}
    button.button.is-primary(@click="isEditingName = false") 完成

//- Button row
.is-flex.is-align-items-center
    button.button.mr-2(@click="showAbilitySelection = true")
        span.icon 
            font-awesome-icon(icon="fas fa-plus") 
        span 添加能力 
    button.button.mr-2(@click="showAddFromAdversary = true")
        span.icon 
            font-awesome-icon(icon="fas fa-plus") 
        span 从其他对手添加 
    button.button.mr-2(@click="modals.adversaries.showFactBreakdown = true")
        span.icon 
            font-awesome-icon(icon="fas fa-unlock-alt") 
        span 知识要素分解
    .vr
    span.mr-2 目标：
    .field.mb-0.mr-2
        .control
            .select
                select(v-model="selectedAdversary.objective")
                    option(v-for="objective in objectives" :value="objective.id") {{ objective.name }}
    .vr 
    button.button.mr-2(@click="exportAdversary()")
        span.icon 
            font-awesome-icon(icon="fas fa-file-export") 
        span 导出 
    button.button.is-success.mr-2(@click="validateAndSaveAdversary()") 
        span.icon
            font-awesome-icon(icon="fas fa-save")
        span 保存 
    button.button.is-danger.is-outlined.mr-2(@click="modals.adversaries.showDeleteConfirm = true") 
        span.icon
            font-awesome-icon(icon="fas fa-trash")
        span 删除

//- Tactic breakdown
.tactic-breakdown.pt-4.pb-4(title="点击以展开或折叠" @click="isTacticBreakdownActive = !isTacticBreakdownActive")
    span.tactic-item(v-for="tactic in getTacticBreakdown()" :class="{ 'active': isTacticBreakdownActive }" :style="`width: ${tactic[1]}%; background-color: ${hashStringToColor(tactic[0])};`" v-tooltip="tactic[0]") {{ `${tactic[0]}  ${tactic[1]}%` }}

//- Ability table
table.table.is-striped.is-fullwidth.is-narrow
    thead
        tr
            th
            th 顺序 
            th 名称 
            th 策略
            th 技术
            th 执行器
            th 依赖 
            th 解锁 
            th 载荷 
            th 清理 
            th
    tbody
        tr.pointer(
            v-for="(ability, index) in selectedAdversaryAbilities"
            :class="{ 'row-hover-above': ability.ability_id === tableDragHoverId && tableDragHoverId != undefined && tableDragEndIndex < tableDragTargetIndex, 'row-hover-below': ability.ability_id === tableDragHoverId && tableDragHoverId != undefined && tableDragEndIndex > tableDragTargetIndex, 'orange-row': needsParser.indexOf(ability.name) > -1, 'row-hover': ability.ability_id === tableDragHoverId && tableDragHoverId != undefined, 'red-row-unclickable': undefinedAbilities.indexOf(ability.ability_id) > -1}" 
            @click="selectAbility(ability)"
            @mouseenter="setAbilityHover(ability.ability_id)"
            @mouseleave="onHoverLocks = []; onHoverUnlocks = [];"
            )
            td.drag.is-flex.is-align-items-center.is-justify-content-center(@click.stop draggable="true" @dragenter="tableDragHoverId = ability.ability_id" @dragstart="startAbilitySwap" @dragover.prevent="swapAbilitiesHover" @dragend="swapAbilities")
                span &#9776;
            td 
                .icon-text 
                    span {{ index + 1 }}
                    span.icon.has-text-danger(v-if="!ability.ability_id")
                        font-awesome-icon(icon="fas fa-ban")
                    span.icon.has-text-warning(v-if="needsParser.indexOf(ability.name) > -1")
                        font-awesome-icon(icon="fas fa-exclamation-triangle") 
            td {{ ability.ability_id ? ability.name : "未定义能力" }}
            td 
                span(:style="`border-bottom: 2px ridge ${hashStringToColor(ability.tactic)}`") {{ ability.tactic }}
            td {{ ability.technique_name }}
            td 
                span(v-for="platform in getExecutorDetail('platforms', ability)" v-tooltip="platform")
                    span.icon.is-small.mr-2
                        font-awesome-icon(v-if="platform.includes('windows')" icon="fab fa-windows")
                        font-awesome-icon(v-if="platform.includes('darwin')" icon="fab fa-apple")
                        font-awesome-icon(v-if="platform.includes('linux')" icon="fab fa-linux")
            td.has-text-centered(:class="{ 'unlock': onHoverUnlocks.indexOf(ability.ability_id) > -1 }")
                span(v-if="abilityDependencies[ability.ability_id] && getExecutorDetail('requirements', ability)" v-tooltip="`该能力有依赖项：(${abilityDependencies[ability.ability_id].requireTypes})`")
                    span.icon.is-small
                        font-awesome-icon(icon="fas fa-lock") 
            td.has-text-centered(:class="{ 'lock': onHoverLocks.indexOf(ability.ability_id) > -1 }")
                span(v-if="abilityDependencies[ability.ability_id] && getExecutorDetail('parser', ability)" v-tooltip="`该能力可解锁其他能力：(${abilityDependencies[ability.ability_id].enableTypes})`")
                    span.icon.is-small
                        font-awesome-icon(icon="fas fa-key")
            td.has-text-centered 
                span(v-if="getExecutorDetail('payload', ability)" v-tooltip="'该能力使用载荷'")
                    span.icon.is-small
                        font-awesome-icon(icon="fas fa-weight-hanging")
            td.has-text-centered
                span(v-if="getExecutorDetail('cleanup', ability)" v-tooltip="'该能力可自行清理'")
                    span.icon.is-small
                        font-awesome-icon(icon="fas fa-trash")
            td.has-text-centered
                button.delete(@click.stop="selectedAdversaryAbilities.splice(index, 1)")

.container.has-text-centered(v-if="!selectedAdversaryAbilities.length")
    p 此配置文件暂无能力
.icon-text(v-if="needsParser.length")
    span.icon.has-text-warning
        font-awesome-icon(icon="fas fa-exclamation-triangle")
    span 一个或多个能力存在未满足的依赖条件，若按顺序执行可能导致行动失败。
.icon-text.mt-2(v-if="undefinedAbilities.length")
    span.icon.has-text-danger 
        font-awesome-icon(icon="fas fa-ban") 
    span 一个或多个引用的能力未被定义

//- Modals
AbilitySelection(:active="showAbilitySelection" @select="addAbilityToAdversary" @close="showAbilitySelection = false" :canCreate="true")

CreateEditAbility(:ability="selectedAbility" :active="showCreateEditAbilityModal" :creating="false" @close="showCreateEditAbilityModal = false")

FactBreakdownModal(:breakdown="factBreakdown")

AddAbilitiesFromAdversaryModal(:active="showAddFromAdversary" @select="addAbilitiesFromAdversary" @close="showAddFromAdversary = false")

DeleteAdversaryConfirmationModal
</template>


<style scoped>
.drag {
    cursor: grab;
}

.red-row-unclickable {
    pointer-events: none;
    font-weight: bold;
    border: 3px solid #8B0000;
}

.lock {
    background-color: blueviolet !important;
}
.unlock {
    background-color: coral !important;
}

.orange-row {
    border: 2px solid orange;
}

.row-hover {
    background-color: #484848 !important;
}

.row-hover-above {
  border-top: 3px solid green;
}

.row-hover-below {
  border-bottom: 3px solid green;
}

.tactic-breakdown {
    display: table;
    width: 100%;
    overflow: hidden;
    white-space: nowrap;
    cursor: pointer;
    user-select: none;
    transform-style: preserve-3d;
}

.tactic-item {
    display: table-cell;
    line-height: 8px;
    text-indent: -9999px;
    border-bottom: none !important;
}
.tactic-item.active {
    line-height: 30px;
    text-indent: 6px;
    font-size: .7em;
}
</style>
