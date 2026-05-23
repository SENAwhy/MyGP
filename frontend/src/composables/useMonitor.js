import { ref, computed } from 'vue'
import { apiFetch } from '@/api'

// ---- Shared state (module-level = singleton across components) ----
const currentHost = ref('')
const nodeList = ref([])
const localHostname = ref('')
const isLocalNode = computed(() => currentHost.value === localHostname.value && localHostname.value !== '')
const cpu = ref(0)
const memory = ref(0)
const netUp = ref(0)
const netDown = ref(0)
const swapPercent = ref(0)
const diskPercent = ref(0)
const diskRead = ref(0)
const diskWrite = ref(0)
const netConnections = ref(0)
const topProcs = ref([])
const dockerContainers = ref([])
const hostname = ref('获取中...')
const localIp = ref('0.0.0.0')
const isAiAnomaly = ref(false)
const anomalyDetail = ref({})
const triggeredAlerts = ref([])
const isHistoryMode = ref(false)

// Chart data arrays (plain, non-reactive — updated imperatively)
const timeData = []
const cpuData = []
const memData = []
const diskData = []

// Polling timer
let monitorTimer = null

// ---- Node list ----
async function fetchNodes() {
  try {
    const result = await apiFetch('/api/nodes')
    if (result.status === 'success') {
      nodeList.value = result.nodes || []
      localHostname.value = result.local || ''
      // Auto-select local node on first load
      if (!currentHost.value) {
        currentHost.value = result.local || (result.nodes?.[0] || '')
      }
    }
  } catch (_) {
    // Fallback: keep empty, user sees no nodes until API works
  }
}

export function useMonitor() {
  const isAlert = computed(() => cpu.value > 80 || memory.value > 90)

  async function getData() {
    if (!isHistoryMode.value) {
      try {
        const result = await apiFetch(
          `/api/system_status?host=${encodeURIComponent(currentHost.value)}`
        )
        if (result.status === 'success') {
          cpu.value = result.cpu_usage
          memory.value = result.memory_usage
          netUp.value = result.net_upload
          netDown.value = result.net_download
          diskPercent.value = result.disk_percent
          swapPercent.value = result.swap_percent
          diskRead.value = result.disk_read_mbps || 0
          diskWrite.value = result.disk_write_mbps || 0
          netConnections.value = result.net_connections || 0
          topProcs.value = result.top_processes || []
          dockerContainers.value = result.docker_containers || []
          hostname.value = result.hostname
          localIp.value = result.local_ip
          isAiAnomaly.value = result.is_anomaly
          anomalyDetail.value = result.anomaly_detail || {}
          triggeredAlerts.value = result.triggered_alerts || []

          // Push to chart arrays (imperative, not reactive)
          if (!isHistoryMode.value) {
            pushChartData(result.cpu_usage, result.memory_usage, result.disk_percent, result.time)
          }
        }
      } catch (_) {
        // silent
      }
    }
  }

  function pushChartData(cpuVal, memVal, diskVal, timeVal) {
    if (timeData.length > 20) {
      timeData.shift()
      cpuData.shift()
      memData.shift()
      diskData.shift()
    }
    timeData.push(timeVal)
    cpuData.push(cpuVal)
    memData.push(memVal)
    diskData.push(diskVal)
  }

  function chartSetOption() {
    // Called imperatively by MonitorView via SystemChart's defineExpose
    return { timeData, cpuData, memData, diskData, isAiAnomaly }
  }

  function startPolling() {
    stopPolling()
    getData()
    monitorTimer = setInterval(getData, 2000)
  }

  function stopPolling() {
    if (monitorTimer) {
      clearInterval(monitorTimer)
      monitorTimer = null
    }
  }

  function switchHost() {
    timeData.length = 0
    cpuData.length = 0
    memData.length = 0
    diskData.length = 0
    isAiAnomaly.value = false
    triggeredAlerts.value = []
  }

  async function toggleHistory() {
    isHistoryMode.value = !isHistoryMode.value
    timeData.length = 0
    cpuData.length = 0
    memData.length = 0
    diskData.length = 0

    if (isHistoryMode.value) {
      try {
        const result = await apiFetch('/api/history?limit=200')
        if (result.status === 'success') {
          for (const item of result.items) {
            timeData.push(item.time)
            cpuData.push(item.cpu)
            memData.push(item.mem)
            diskData.push(item.disk || 0)
          }
        }
      } catch (_) { /* silent */ }
    }
  }

  // AI diagnosis
  const isDiagnosing = ref(false)
  const reportData = ref('')

  async function getAIReport() {
    if (isDiagnosing.value) return
    isDiagnosing.value = true
    reportData.value = '正在深度扫描系统进程，请稍候...'
    try {
      const result = await apiFetch('/api/diagnose')
      if (result.status === 'success') {
        reportData.value = result.report
      } else {
        reportData.value = result.report || '诊断失败'
      }
    } catch (_) {
      reportData.value = '诊断失败，请稍后重试'
    } finally {
      isDiagnosing.value = false
    }
  }

  function showDetail(p) {
    alert(
      `进程名称: ${p.name}\nPID: ${p.pid}\n内存: ${p.mem_mb} MB\n路径: ${p.path || '无'}`
    )
  }

  function requestNotifyPermission() {
    if ('Notification' in window) {
      Notification.requestPermission().then((perm) => {
        if (perm === 'granted') {
          alert('已开启桌面通知权限！当系统高负载时会弹出警告。')
        }
      })
    } else {
      alert('当前浏览器不支持桌面通知。')
    }
  }

  return {
    // State
    currentHost, nodeList, localHostname, isLocalNode,
    cpu, memory, netUp, netDown, swapPercent, diskPercent,
    diskRead, diskWrite, netConnections, topProcs, dockerContainers,
    hostname, localIp, isAiAnomaly, anomalyDetail, triggeredAlerts,
    isHistoryMode, isDiagnosing, reportData,
    timeData, cpuData, memData, diskData,
    // Computed
    isAlert,
    // Methods
    fetchNodes, getData, startPolling, stopPolling, switchHost, toggleHistory,
    pushChartData, chartSetOption,
    getAIReport, showDetail, requestNotifyPermission,
  }
}
