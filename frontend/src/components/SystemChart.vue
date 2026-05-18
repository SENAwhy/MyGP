<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'

const chartRef = ref(null)
let myChart = null

function getChartOption() {
  return {
    tooltip: { trigger: 'axis' },
    legend: {
      data: ['CPU %', '内存 %', '磁盘 %'],
      textStyle: { color: '#fff' },
    },
    xAxis: {
      type: 'category',
      data: [],
      axisLabel: { color: '#fff' },
    },
    yAxis: {
      type: 'value',
      max: 100,
      axisLabel: { color: '#fff' },
    },
    series: [
      { name: 'CPU %', type: 'line', smooth: true, data: [], itemStyle: { color: '#00ffcc' } },
      { name: '内存 %', type: 'line', smooth: true, data: [], itemStyle: { color: '#ff4757' } },
      { name: '磁盘 %', type: 'line', smooth: true, data: [], itemStyle: { color: '#ffa502' } },
    ],
  }
}

function setOption(timeLabels, cpuArr, memArr, diskArr, isAiAnomaly) {
  if (!myChart) return
  const cpuColor = isAiAnomaly ? '#ff0055' : '#00ffcc'
  myChart.setOption({
    xAxis: { data: timeLabels },
    series: [
      { data: cpuArr, itemStyle: { color: cpuColor } },
      { data: memArr },
      { data: diskArr },
    ],
  })
}

function clearData() {
  if (!myChart) return
  myChart.setOption({
    xAxis: { data: [] },
    series: [{ data: [] }, { data: [] }, { data: [] }],
  })
}

function handleResize() {
  myChart?.resize()
}

onMounted(() => {
  if (chartRef.value) {
    myChart = echarts.init(chartRef.value)
    myChart.setOption(getChartOption())
    window.addEventListener('resize', handleResize)
  }
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  myChart?.dispose()
  myChart = null
})

defineExpose({ setOption, clearData })
</script>

<template>
  <div ref="chartRef" id="chart-container" style="width:100%; height:260px;"></div>
</template>
