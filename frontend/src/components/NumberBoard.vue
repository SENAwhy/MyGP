<script setup>
defineProps({
  cpu: Number,
  memory: Number,
  netUp: Number,
  netDown: Number,
  diskRead: Number,
  diskWrite: Number,
})
</script>

<template>
  <div class="number-board">
    <div class="number-item">
      <div class="data-label">CPU 负载</div>
      <div class="data-text" :class="{ 'alert-text': cpu > 80 }">{{ cpu }}%</div>
    </div>
    <div class="number-item">
      <div class="data-label">内存使用</div>
      <div class="data-text" :class="{ 'alert-text': memory > 90 }">{{ memory }}%</div>
    </div>
    <div class="number-item">
      <div class="data-label">上传</div>
      <div class="data-text" style="color: #ffa502;">{{ netUp }} MB/s</div>
    </div>
    <div class="number-item">
      <div class="data-label">下载</div>
      <div class="data-text" style="color: #00a8ff;">{{ netDown }} MB/s</div>
    </div>
    <div class="number-item">
      <div class="data-label">磁盘读</div>
      <div class="data-text" style="color: #ffa502;">{{ diskRead }} MB/s</div>
    </div>
    <div class="number-item">
      <div class="data-label">磁盘写</div>
      <div class="data-text" style="color: #00a8ff;">{{ diskWrite }} MB/s</div>
    </div>
  </div>
</template>
