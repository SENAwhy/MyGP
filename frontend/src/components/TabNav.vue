<script setup>
defineProps({
  activeTab: String,
})
const emit = defineEmits(['update:activeTab'])
</script>

<template>
  <div class="tab-nav">
    <button
      class="tab-btn"
      :class="{ active: activeTab === 'monitor' }"
      @click="emit('update:activeTab', 'monitor')"
    >实时监控</button>
    <button
      class="tab-btn"
      :class="{ active: activeTab === 'alerts' }"
      @click="emit('update:activeTab', 'alerts')"
    >告警历史</button>
    <button
      class="tab-btn"
      :class="{ active: activeTab === 'info' }"
      @click="emit('update:activeTab', 'info')"
    >系统信息</button>
  </div>
</template>
