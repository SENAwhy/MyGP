<script setup>
import { useAuth } from '@/composables/useAuth'
import { useMonitor } from '@/composables/useMonitor'

defineProps({
  activeTab: String,
})
const emit = defineEmits(['logout'])

const { doLogout } = useAuth()
const { isHistoryMode } = useMonitor()

function onLogout() {
  doLogout()
  emit('logout')
}
</script>

<template>
  <div class="header">
    <h2 v-if="activeTab === 'monitor'">
      {{ isHistoryMode ? '历史记录穿越中...' : 'AIOps 分布式监控集群' }}
    </h2>
    <h2 v-else-if="activeTab === 'alerts'">告警历史记录</h2>
    <h2 v-else>系统信息 & 规则管理</h2>
    <button class="logout-btn" @click="onLogout">登出</button>
  </div>
</template>
