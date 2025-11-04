<script setup>
import { ref, inject } from "vue";
import { storeToRefs } from "pinia";

import { useAdversaryStore } from "@/stores/adversaryStore.js";

const $api = inject("$api");

const adversaryStore = useAdversaryStore();
const { selectedObjective } = storeToRefs(adversaryStore);

const OPERATORS = [ "<", ">", "<=", ">=", "in", "*", "==" ];
let goalIndexToEdit = ref(-1);

async function addNewGoal() {
    selectedObjective.value.goals.push({
        target: "",
        operator: "==",
        value: "",
        count: 1,
        achieved: false
    });
    saveObjective();
}

async function saveObjective() {
    await adversaryStore.saveObjective($api);
    goalIndexToEdit.value = -1;
}

function removeGoal(goalIndex) {
    selectedObjective.value.goals.splice(goalIndex, 1);
    saveObjective();
}
</script>

<template lang="pug">
.buttons
    button.button(@click="addNewGoal()")
        span.icon
            font-awesome-icon(icon="fas fa-plus")
        span 添加目标
table.table.is-striped.is-fullwidth
    thead
        tr
            th 目标对象
            th 运算符
            th 比较值
            th 计数
            th 是否达成
            th 操作
    tbody
        tr(v-for="(goal, index) in selectedObjective.goals")
            td 
                input.input(v-if="goalIndexToEdit === index" v-model="goal.target" placeholder="输入目标对象")
                span(v-else) {{ goal.target }}
            td 
                .control(v-if="goalIndexToEdit === index")
                    .select
                        select(v-model="goal.operator")
                            option(v-for="op in OPERATORS" :value="op") {{ op }}
                span(v-else) {{ goal.operator }}
            td 
                input.input(v-if="goalIndexToEdit === index" v-model="goal.value" placeholder="输入比较值")
                span(v-else) {{ goal.value }}
            td 
                input.input(v-if="goalIndexToEdit === index" type="number" v-model="goal.count" placeholder="输入目标计数")
                span(v-else) {{ goal.count }}
            td {{ goal.achieved ? '✅ 是' : '❌ 否' }}
            td
                .buttons
                    button.button.is-primary(
                            v-if="goalIndexToEdit === index" @click="saveObjective()"
                            :disabled="false"
                            )
                        span.icon
                            font-awesome-icon(icon="fa-save")
                    button.button(v-else @click="goalIndexToEdit = index")
                        span.icon
                            font-awesome-icon(icon="fa-pencil-alt")
                    button.button.is-danger.is-outlined(@click="removeGoal(index)")
                        span.icon
                            font-awesome-icon(icon="fa-trash")
</template>

