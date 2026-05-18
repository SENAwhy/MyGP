<script setup>
import { useAuth } from '@/composables/useAuth'

const { loginUser, loginPass, loginError, isLoggingIn, doLogin } = useAuth()
</script>

<template>
  <div class="login-box">
    <h2 style="text-align:center; color:#00ffcc; margin-bottom:20px;">
      AIOps 分布式监控
    </h2>
    <input
      class="login-input"
      v-model="loginUser"
      type="text"
      placeholder="账号"
      autocomplete="username"
      @keyup.enter="doLogin"
    />
    <input
      class="login-input"
      v-model="loginPass"
      type="password"
      placeholder="密码"
      autocomplete="current-password"
      @keyup.enter="doLogin"
    />
    <button class="login-btn" @click="doLogin" :disabled="isLoggingIn">
      {{ isLoggingIn ? '验证中...' : '接入中枢系统' }}
    </button>
    <p style="color: #ff4757; text-align: center; margin-top: 12px; min-height: 20px;">
      {{ loginError }}
    </p>
  </div>
</template>
