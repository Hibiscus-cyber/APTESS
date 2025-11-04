<script setup>
import { ref, inject } from "vue";
import { useAuthStore } from "../stores/authStore.js";
let username = ref("");
let password = ref("");
let loginError = ref("");
const $api = inject("$api");

async function handleLogin(e) {
    e.preventDefault();
    const authStore = useAuthStore();
    try {
        await authStore.login(username, password, $api);
    } catch (error) {
        loginError.value = error;
    }
}
</script>

<template lang="pug">
#login.container.content.fullwh.is-flex.is-flex-direction-column.is-align-items-center.is-justify-content-center()
    img(src="/src/assets/img/caldera-logo.png" alt="Caldera 标志")
    .p-6
        form
            .field
                label.label 用户名
                .control.has-icons-left
                    input.input(v-focus v-model="username" type="text" placeholder="请输入用户名")
                    span.icon.is-small.is-left
                        font-awesome-icon(icon="fas fa-user")
            .field
                label.label 密码
                .control.has-icons-left
                    input.input(v-model="password" type="password" placeholder="请输入密码")
                    span.icon.is-small.is-left
                        font-awesome-icon(icon="fas fa-lock")
            button.button.fancy-button.is-fullwidth(type="submit" @click="handleLogin") 登 录
        .has-text-danger
            p {{ loginError }}
</template>


<style scoped>
#login {
    height: 100vh;
}

#login img {
    width: 250px;
    margin: 16px;
}

.fancy-button:hover {
    background-image: linear-gradient(to right, #8b0000, #191970) !important;
    border-width: 2px;
}
</style>
