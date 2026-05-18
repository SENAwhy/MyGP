<script setup>
import { onMounted } from 'vue'
import { useSystemInfo } from '@/composables/useSystemInfo'

const {
  sysInfo, modelInfo, alertRules, summary,
  loadSystemInfo, loadSummary, loadAlertRules, toggleRule,
} = useSystemInfo()

onMounted(() => {
  loadAll()
})

function loadAll() {
  loadSystemInfo()
  loadSummary()
  loadAlertRules()
}
</script>

<template>
  <div>
    <!-- Summary grid -->
    <div class="summary-grid">
      <div class="info-card">
        <div class="data-label">平均 CPU</div>
        <div class="data-text">{{ summary.avg_cpu }}%</div>
        <div>峰值 {{ summary.max_cpu }}%</div>
      </div>
      <div class="info-card">
        <div class="data-label">平均内存</div>
        <div class="data-text">{{ summary.avg_mem }}%</div>
        <div>峰值 {{ summary.max_mem }}%</div>
      </div>
      <div class="info-card">
        <div class="data-label">24h 异常次数</div>
        <div
          class="data-text"
          :class="{ 'alert-text': summary.anomaly_count_24h > 0 }"
        >{{ summary.anomaly_count_24h }}</div>
        <div>共 {{ summary.total_records }} 条记录</div>
      </div>
    </div>

    <!-- System info -->
    <div class="info-card" v-if="sysInfo.os_name">
      <h3 style="color:#00ffcc; margin-bottom:12px;">系统信息</h3>
      <div class="info-grid">
        <div class="info-label">操作系统</div><div class="info-value">{{ sysInfo.os_name }}</div>
        <div class="info-label">CPU 型号</div><div class="info-value">{{ sysInfo.cpu_model }}</div>
        <div class="info-label">逻辑核心数</div><div class="info-value">{{ sysInfo.cpu_cores_logical }}</div>
        <div class="info-label">物理核心数</div><div class="info-value">{{ sysInfo.cpu_cores_physical }}</div>
        <div class="info-label">CPU 频率</div><div class="info-value">{{ sysInfo.cpu_freq_current }} / {{ sysInfo.cpu_freq_max }} MHz</div>
        <div class="info-label">总内存</div><div class="info-value">{{ sysInfo.total_ram_gb }} GB</div>
        <div class="info-label">总磁盘</div><div class="info-value">{{ sysInfo.total_disk_gb }} GB</div>
        <div class="info-label">Python 版本</div><div class="info-value">{{ sysInfo.python_version }}</div>
        <div class="info-label">系统启动</div><div class="info-value">{{ sysInfo.boot_time }}</div>
      </div>
    </div>

    <!-- AI Model info -->
    <div class="info-card" v-if="modelInfo.is_trained">
      <h3 style="color:#00ffcc; margin-bottom:12px;">AI 异常检测模型</h3>
      <div class="info-grid">
        <div class="info-label">模型状态</div>
        <div class="info-value">
          <span class="status-badge" style="background:#2ed573;">已训练</span>
        </div>
        <div class="info-label">训练样本量</div><div class="info-value">{{ modelInfo.training_samples }} 条</div>
        <div class="info-label">使用模型</div><div class="info-value">{{ (modelInfo.models || []).join(', ') }}</div>
        <div class="info-label">IF 污染率</div><div class="info-value">{{ modelInfo.if_contamination }}</div>
        <div class="info-label">IF 树数量</div><div class="info-value">{{ modelInfo.if_n_estimators }}</div>
        <div class="info-label">LOF 邻居数</div><div class="info-value">{{ modelInfo.lof_n_neighbors }}</div>
      </div>
    </div>
    <div class="info-card" v-else>
      <h3 style="color:#00ffcc; margin-bottom:12px;">AI 异常检测模型</h3>
      <p>模型尚未训练，需要至少 50 条历史数据。</p>
    </div>

    <!-- Alert rules -->
    <div class="info-card">
      <h3 style="color:#00ffcc; margin-bottom:12px;">告警规则管理</h3>
      <div v-if="alertRules.length > 0">
        <div v-for="rule in alertRules" :key="rule.id" class="rule-item">
          <div class="rule-info">
            <span style="color:#00ffcc;">{{ rule.name }}</span>
            <span>{{ rule.metric }} {{ rule.operator }} {{ rule.threshold }} -- {{ rule.description }}</span>
          </div>
          <label class="toggle-switch">
            <input
              type="checkbox"
              :checked="rule.enabled"
              @change="toggleRule(rule.id, rule.enabled)"
            />
            <span class="toggle-slider"></span>
          </label>
        </div>
      </div>
      <p v-else>加载规则中...</p>
    </div>
  </div>
</template>
