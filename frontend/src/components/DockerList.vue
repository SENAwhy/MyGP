<script setup>
defineProps({
  dockerContainers: Array,
})
</script>

<template>
  <div class="docker-list" v-if="dockerContainers.length > 0">
    <h4>Docker 容器状态：</h4>
    <div
      v-for="(c, index) in dockerContainers"
      :key="index"
      class="docker-item"
    >
      <span class="docker-name">{{ c.name }}</span>
      <span>CPU: {{ c.cpu_percent }}% | 内存: {{ c.mem_percent }}% ({{ c.mem_usage }})</span>
    </div>
  </div>
</template>
