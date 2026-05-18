import { ref, computed } from 'vue'
import { apiFetch } from '@/api'

const alertItems = ref([])
const alertTotal = ref(0)
const alertPage = ref(0)
const ALERT_PAGE_SIZE = 15

export function useAlerts() {
  const alertTotalPages = computed(() =>
    Math.max(1, Math.ceil(alertTotal.value / ALERT_PAGE_SIZE))
  )

  async function loadAlertHistory() {
    try {
      const offset = alertPage.value * ALERT_PAGE_SIZE
      const result = await apiFetch(`/api/alerts?limit=${ALERT_PAGE_SIZE}&offset=${offset}`)
      alertItems.value = result.items || []
      alertTotal.value = result.total || 0
    } catch (_) { /* silent */ }
  }

  function alertPrevPage() {
    if (alertPage.value > 0) {
      alertPage.value--
      loadAlertHistory()
    }
  }

  function alertNextPage() {
    if ((alertPage.value + 1) * ALERT_PAGE_SIZE < alertTotal.value) {
      alertPage.value++
      loadAlertHistory()
    }
  }

  return {
    alertItems, alertTotal, alertPage, alertTotalPages,
    loadAlertHistory, alertPrevPage, alertNextPage,
  }
}
