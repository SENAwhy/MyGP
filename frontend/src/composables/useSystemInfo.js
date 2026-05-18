import { ref } from 'vue'
import { apiFetch } from '@/api'

const sysInfo = ref({})
const modelInfo = ref({})
const alertRules = ref([])
const summary = ref({})

export function useSystemInfo() {
  async function loadSystemInfo() {
    try {
      const result = await apiFetch('/api/system_info')
      if (result.status === 'success') {
        sysInfo.value = result
        modelInfo.value = result.model_info || {}
      }
    } catch (_) { /* silent */ }
  }

  async function loadSummary() {
    try {
      const result = await apiFetch('/api/dashboard_summary')
      if (result.status === 'success') {
        summary.value = result
      }
    } catch (_) { /* silent */ }
  }

  async function loadAlertRules() {
    try {
      const result = await apiFetch('/api/alert_rules')
      alertRules.value = result.rules || []
    } catch (_) { /* silent */ }
  }

  async function toggleRule(ruleId, currentEnabled) {
    const newState = !currentEnabled
    try {
      await apiFetch(`/api/alert_rules/${ruleId}?enabled=${newState}`)
      await loadAlertRules()
    } catch (_) { /* silent */ }
  }

  return {
    sysInfo, modelInfo, alertRules, summary,
    loadSystemInfo, loadSummary, loadAlertRules, toggleRule,
  }
}
