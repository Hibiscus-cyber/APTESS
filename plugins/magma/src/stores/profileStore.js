import { defineStore } from "pinia";

export const useProfileStore = defineStore("profileStore", {
  state: () => ({
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
  },

});
