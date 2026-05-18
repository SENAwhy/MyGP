<script setup>
defineProps({
  isDiagnosing: Boolean,
  reportData: String,
  isHistoryMode: Boolean,
  currentHost: String,
})
const emit = defineEmits(['generateReport'])
</script>

<template>
  <button
    class="btn-primary main-btn"
    :disabled="isDiagnosing || isHistoryMode || currentHost !== 'LAPTOP-33OCQVST'"
    @click="emit('generateReport')"
  >
    {{ isDiagnosing ? 'DeepSeek 正在深度分析中...' : '一键生成 AI 报告 (仅限本地)' }}
  </button>
  <div v-if="reportData" class="report-box">
    <h4 style="color: #00ffcc; margin-bottom: 8px;">AI 智能诊断：</h4>
    <p>{{ reportData }}</p>
  </div>
</template>
