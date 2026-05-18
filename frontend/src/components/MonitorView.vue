<script setup>
import { onMounted, onUnmounted, ref } from 'vue'
import { useMonitor } from '@/composables/useMonitor'
import NumberBoard from './NumberBoard.vue'
import SystemChart from './SystemChart.vue'
import ProcessList from './ProcessList.vue'
import DockerList from './DockerList.vue'
import AiDiagnosis from './AiDiagnosis.vue'

const {
  currentHost, cpu, memory, netUp, netDown, swapPercent, diskPercent,
  diskRead, diskWrite, netConnections, topProcs, dockerContainers,
  hostname, localIp, isAiAnomaly, triggeredAlerts,
  isHistoryMode, isDiagnosing, reportData,
  timeData, cpuData, memData, diskData,
  getData, switchHost, toggleHistory,
  getAIReport, showDetail, requestNotifyPermission,
} = useMonitor()

const chartRef = ref(null)
let monitorTimer = null

function doUpdateChart() {
  chartRef.value?.setOption(
    [...timeData], [...cpuData], [...memData], [...diskData], isAiAnomaly.value
  )
}

function startPolling() {
  stopPolling()
  getData().then(() => doUpdateChart())
  monitorTimer = setInterval(() => {
    getData().then(() => doUpdateChart())
  }, 2000)
}

function stopPolling() {
  if (monitorTimer) {
    clearInterval(monitorTimer)
    monitorTimer = null
  }
}

function manualRefresh() {
  getData().then(() => doUpdateChart())
}

function handleSwitchHost() {
  switchHost()
  chartRef.value?.clearData()
}

function handleToggleHistory() {
  toggleHistory().then(() => doUpdateChart())
}

onMounted(() => {
  startPolling()
})

onUnmounted(() => {
  stopPolling()
})
</script>

<template>
  <div>
    <!-- Node selector -->
    <select
      v-model="currentHost"
      class="node-selector"
      v-if="!isHistoryMode"
      @change="handleSwitchHost"
    >
      <option value="LAPTOP-33OCQVST">节点 A：本地主机 (LAPTOP-33OCQVST)</option>
      <option value="Node-DB-Shanghai">节点 B：数据库服务器 (Node-DB-Shanghai)</option>
      <option value="Node-Web-Tokyo">节点 C：Web应用服务器 (Node-Web-Tokyo)</option>
      <option value="Node-Storage-Frankfurt">节点 D：存储服务器 (Node-Storage-Frankfurt)</option>
    </select>

    <!-- AI anomaly banner -->
    <div
      v-if="isAiAnomaly && currentHost === 'LAPTOP-33OCQVST' && !isHistoryMode"
      class="ai-banner"
    >
      [AI 双模型] 孤立森林 + LOF 检测到系统行为异常，请立即排查！
    </div>

    <!-- Triggered alerts -->
    <div v-if="triggeredAlerts.length > 0 && !isHistoryMode" class="alert-list">
      <div v-for="a in triggeredAlerts" :key="a.rule_name" class="alert-item">
        {{ a.message }}
      </div>
    </div>

    <!-- Control buttons -->
    <div class="control-btns">
      <button class="btn-sm" @click="handleToggleHistory"
        :style="{ background: isHistoryMode ? '#ffa502' : '#555' }">
        {{ isHistoryMode ? '返回实时监控' : '查看历史趋势' }}
      </button>
      <button class="btn-sm" style="background: #00a8ff;" @click="requestNotifyPermission">
        开启桌面强推警报
      </button>
      <button class="btn-sm" style="background: #2ed573;" @click="manualRefresh">
        手动刷新数据
      </button>
    </div>

    <!-- System info bar -->
    <div class="sys-info-bar">
      <span>主机: {{ hostname }}</span>
      <span>IP: {{ localIp }}</span>
      <span>磁盘: {{ diskPercent }}%</span>
      <span>交换: {{ swapPercent }}%</span>
      <span>连接数: {{ netConnections }}</span>
    </div>

    <!-- Number board -->
    <NumberBoard
      :cpu="cpu"
      :memory="memory"
      :net-up="netUp"
      :net-down="netDown"
      :disk-read="diskRead"
      :disk-write="diskWrite"
    />

    <!-- Chart -->
    <SystemChart
      ref="chartRef"
      v-show="!isHistoryMode || (isHistoryMode && timeData.length > 0)"
    />

    <!-- Process list -->
    <ProcessList
      v-if="!isHistoryMode"
      :top-procs="topProcs"
      @show-detail="showDetail"
    />

    <!-- Docker list -->
    <DockerList
      v-if="dockerContainers.length > 0 && !isHistoryMode"
      :docker-containers="dockerContainers"
    />

    <!-- AI Diagnosis -->
    <AiDiagnosis
      :is-diagnosing="isDiagnosing"
      :report-data="reportData"
      :is-history-mode="isHistoryMode"
      :current-host="currentHost"
      @generate-report="getAIReport"
    />
  </div>
</template>
