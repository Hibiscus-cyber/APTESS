// 导入Pinia的defineStore函数，用于创建状态管理仓库
import { defineStore } from "pinia";

// 创建并导出accessStore仓库
// 命名空间为"accessStore"，用于在组件中通过useAccessStore调用
export const useAccessStore = defineStore("accessStore", {
    // 状态定义：初始化空对象
    // 实际应用中会通过其他方式填充状态数据
    state: () => {
        return {};
    },
    // Getter定义：用于获取派生状态
    getters: {
        // 获取启用的插件列表
        // 从mainConfig中提取plugins数组，如果mainConfig不存在则返回空数组
        enabledPlugins: (state) => (state.mainConfig ? state.mainConfig.plugins : [])  
    },
    // Action定义：用于处理异步操作和业务逻辑
    actions: {
        // 处理REST API请求的通用方法
        // @param {string} requestType - 请求类型(GET, POST等)
        // @param {any} data - 请求数据
        // @param {function} callback - 请求成功后的回调函数
        // @param {string} endpoint - 请求端点，默认为'/api/rest'
        async restRequest(requestType, data, callback = (r) => {
            console.log('Fetch Success', r);
        }, endpoint = '/api/rest') {
            // 根据请求类型构建请求配置
            const requestData = requestType === 'GET' ?
                {method: requestType, headers: {'Content-Type': 'application/json'}} :
                {method: requestType, headers: {'Content-Type': 'application/json'}, body: JSON.stringify(data)}

            // 发送fetch请求
            fetch(endpoint, requestData)
                .then((response) => {
                    if (!response.ok) {
                        throw (response.statusText);
                    }
                    return response.text();
                })
                .then((text) => {
                    try {
                        // 尝试解析JSON响应
                        callback(JSON.parse(text));
                    } catch {
                        // 解析失败时直接返回文本
                        callback(text);
                    }
                })
                .catch((error) => console.error(error));
        },

        // 专为API v2设计的请求方法
        // @param {string} requestType - 请求类型(GET, POST等)
        // @param {string} endpoint - 请求端点
        // @param {any} body - 请求体数据
        // @param {boolean} jsonRequest - 是否为JSON请求
        // @returns {Promise} - 返回包含响应数据的Promise
        async apiV2(requestType, endpoint, body = null, jsonRequest = true) {
            let requestBody = { method: requestType };
            // 配置请求头和请求体
            if (jsonRequest) {
                requestBody.headers = { 'Content-Type': 'application/json' };
                if (body) {
                    requestBody.body = JSON.stringify(body);
                }
            } else {
                if (body) {
                    requestBody.body = body;
                }
            }

            // 返回Promise以便调用者处理
            return new Promise((resolve, reject) => {
                fetch(endpoint, requestBody)
                    .then((response) => {
                        if (!response.ok) {
                            reject(response.statusText);
                        }
                        return response.text();
                    })
                    .then((text) => {
                        try {
                            // 尝试解析JSON响应
                            resolve(JSON.parse(text));
                        } catch {
                            // 解析失败时直接返回文本
                            resolve(text);
                        }
                    });
            });
        }
    },
});