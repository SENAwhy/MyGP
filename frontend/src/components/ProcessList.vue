<script setup>
defineProps({
  topProcs: Array,
})
const emit = defineEmits(['showDetail'])
</script>

<template>
  <div class="process-list">
    <h4>实时高耗能进程 (Top 5)：</h4>
    <p v-if="topProcs.length === 0" style="color: #666;">暂无远程服务器进程权限...</p>
    <div
      v-for="(p, index) in topProcs"
      :key="p.pid"
      class="process-item"
      @click="emit('showDetail', p)"
    >
      <span>NO.{{ index + 1 }} | {{ p.name }} (PID: {{ p.pid }}) | {{ p.mem_mb }} MB</span>
      <span style="font-weight: bold; color: #ff4757;">{{ p.cpu_percent }}%</span>
    </div>
  </div>
</template>
