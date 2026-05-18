<script setup>
import { onMounted } from 'vue'
import { useAlerts } from '@/composables/useAlerts'

const { alertItems, alertTotal, alertPage, alertTotalPages,
  loadAlertHistory, alertPrevPage, alertNextPage } = useAlerts()

onMounted(() => {
  loadAlertHistory()
})
</script>

<template>
  <div>
    <div class="alert-table-wrap" v-if="alertItems.length > 0">
      <table class="alert-table">
        <thead>
          <tr>
            <th>#</th>
            <th>节点</th>
            <th>规则名称</th>
            <th>指标</th>
            <th>当前值</th>
            <th>阈值</th>
            <th>AI异常</th>
            <th>时间</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="a in alertItems"
            :key="a.id"
            :class="{ 'alert-row-ai': a.is_ai_anomaly }"
          >
            <td>{{ a.id }}</td>
            <td>{{ a.hostname }}</td>
            <td>{{ a.rule_name }}</td>
            <td>{{ a.metric }}</td>
            <td :class="{ 'alert-text': a.current_value > a.threshold }">{{ a.current_value }}</td>
            <td>{{ a.threshold }}</td>
            <td>
              <span class="status-badge" :style="{ background: a.is_ai_anomaly ? '#ff0055' : '#555' }">
                {{ a.is_ai_anomaly ? '是' : '否' }}
              </span>
            </td>
            <td>{{ a.created_at }}</td>
          </tr>
        </tbody>
      </table>
    </div>
    <p v-else>暂无告警记录，系统运行正常。</p>

    <!-- Pagination -->
    <div class="pagination" v-if="alertTotal > 0">
      <button :disabled="alertPage === 0" @click="alertPrevPage">上一页</button>
      <span>第 {{ alertPage + 1 }} / {{ alertTotalPages }} 页 (共 {{ alertTotal }} 条)</span>
      <button
        :disabled="(alertPage + 1) * 15 >= alertTotal"
        @click="alertNextPage"
      >下一页</button>
    </div>
  </div>
</template>
