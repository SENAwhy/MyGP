<script setup>
import { ref } from 'vue'
import { useAuth } from '@/composables/useAuth'
import { useMonitor } from '@/composables/useMonitor'
import { useAlerts } from '@/composables/useAlerts'
import { useSystemInfo } from '@/composables/useSystemInfo'
import LoginForm from '@/components/LoginForm.vue'
import AppHeader from '@/components/AppHeader.vue'
import TabNav from '@/components/TabNav.vue'
import MonitorView from '@/components/MonitorView.vue'
import AlertsView from '@/components/AlertsView.vue'
import InfoView from '@/components/InfoView.vue'

const { isLoggedIn, doLogout } = useAuth()
const { isAlert, isAiAnomaly } = useMonitor()
const { loadAlertHistory } = useAlerts()
const { loadSystemInfo, loadSummary, loadAlertRules } = useSystemInfo()

const activeTab = ref('monitor')

function switchTab(tab) {
  activeTab.value = tab
  if (tab === 'alerts') {
    loadAlertHistory()
  } else if (tab === 'info') {
    loadSystemInfo()
    loadSummary()
    loadAlertRules()
  }
}

function handleLogout() {
  doLogout()
}
</script>

<template>
  <LoginForm v-if="!isLoggedIn" />
  <div
    v-else
    class="card"
    :class="{
      'alert-mode': isAlert && !isAiAnomaly,
      'ai-alert-mode': isAiAnomaly && activeTab === 'monitor',
    }"
  >
    <AppHeader :active-tab="activeTab" @logout="handleLogout" />
    <TabNav :active-tab="activeTab" @update:active-tab="switchTab" />

    <MonitorView v-show="activeTab === 'monitor'" />
    <AlertsView v-show="activeTab === 'alerts'" />
    <InfoView v-show="activeTab === 'info'" />
  </div>
</template>
