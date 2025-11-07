import { defineStore } from "pinia";

export const useProfileStore = defineStore("profileStore", {
  state: () => ({
    //  在内存中维护现有的profiles
    profiles: [],
  }),
  getters: {
    // 按你的后端字段增补，这里给出通用示例
    desription: (state) => ([...new Set(state.profiles.map(p => p.plugin))].sort()),
    names:   (state) => ([...new Set(state.profiles.map(p => p.name))].sort()),
  },
  actions: {
    async getProfiles($api, params = {}) {
      try {
        const { data } = await $api.get("/api/v2/profiles", { params });
        this.profiles = Array.isArray(data) ? data : (data?.items ?? []);
      } catch (error) {
        console.error("Error fetching profiles", error);
      }
    },

    async saveProfiles($api, profiles) {
      const response = await $api.post(`/api/v2/profiles`, profiles);
      this.profiles.push(response.data);
  },

    async deleteProfile($api, profileName, addPath=false) {
        
      await $api.delete(`/api/v2/profiles/by-name/${encodeURIComponent(profileName)}`);
      
    },

    // src/stores/profileStore.js
    async editProfile($api, profile) {
      try {
        if (!profile || !profile.profile_id) {
          console.error("editProfile 缺少 profile_id");
          return;
        }
        // 这里直接把整个 profile 发给后端即可，后端会用 data 里的字段更新
        const response = await $api.patch("/api/v2/profiles", profile);

        // 同步更新本地 state
        const idx = this.profiles.findIndex(p => p.profile_id === profile.profile_id);
        if (idx !== -1) {
          // 后端返回的结构如果是 {status, profile: {...}} 就用 response.data.profile
          this.profiles[idx] = response.data.profile || response.data;
        }

        return response.data;
      } catch (error) {
        console.error("Error updating profile:", error.response?.data || error);
        throw error;
      }
    },
  },

});
