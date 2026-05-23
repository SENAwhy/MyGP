/**
 * AIOps 监控大屏 Max (Pro+) — 前端应用逻辑
 * 技术栈: Vue 3 (CDN) + ECharts 5
 */

const { createApp, ref, computed, onMounted, onUnmounted, nextTick } = Vue;

createApp({
    setup() {
        // ==================== 状态 ====================

        // 认证
        const isLoggedIn = ref(false);
        const loginUser = ref("");
        const loginPass = ref("");
        const loginError = ref("");
        const isLoggingIn = ref(false);
        const token = ref(localStorage.getItem("aiops_token") || "");

        // 导航
        const activeTab = ref("monitor");
        const currentHost = ref("");

        // 实时数据
        const cpu = ref(0);
        const memory = ref(0);
        const netUp = ref(0);
        const netDown = ref(0);
        const swapPercent = ref(0);
        const diskPercent = ref(0);
        const diskRead = ref(0);
        const diskWrite = ref(0);
        const netConnections = ref(0);
        const topProcs = ref([]);
        const dockerContainers = ref([]);
        const hostname = ref("获取中...");
        const localIp = ref("0.0.0.0");
        const isAiAnomaly = ref(false);
        const anomalyDetail = ref({});
        const triggeredAlerts = ref([]);
        const isHistoryMode = ref(false);

        // AI 诊断
        const isDiagnosing = ref(false);
        const reportData = ref("");

        // 计算属性
        const isAlert = computed(
            () => cpu.value > 80 || memory.value > 90
        );

        // 图表
        let myChart = null;
        const timeData = [];
        const cpuData = [];
        const memData = [];
        let monitorTimer = null;

        // 告警历史
        const alertItems = ref([]);
        const alertTotal = ref(0);
        const alertPage = ref(0);
        const alertPageSize = 15;

        // 系统信息
        const sysInfo = ref({});
        const modelInfo = ref({});
        const alertRules = ref([]);

        // 摘要
        const summary = ref({});

        // ==================== 工具函数 ====================

        const getAuthHeaders = () => ({
            Authorization: `Bearer ${token.value}`,
        });

        const apiFetch = async (path, options = {}) => {
            // 合并 headers：优先使用 options.headers，但保留 Authorization
            const optHeaders = options.headers || {};
            const mergedHeaders = { ...getAuthHeaders(), ...optHeaders };
            const url = `${path}`;
            const res = await fetch(url, {
                ...options,
                headers: mergedHeaders,
            });
            if (res.status === 401) {
                doLogout();
                throw new Error("认证过期");
            }
            return res.json();
        };

        // ==================== 认证 ====================

        const doLogin = async () => {
            isLoggingIn.value = true;
            loginError.value = "";
            try {
                const formData = new URLSearchParams();
                formData.append("username", loginUser.value);
                formData.append("password", loginPass.value);
                const response = await fetch(`/api/login`, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/x-www-form-urlencoded",
                    },
                    body: formData,
                });
                if (response.ok) {
                    const data = await response.json();
                    token.value = data.access_token;
                    localStorage.setItem("aiops_token", token.value);
                    isLoggedIn.value = true;
                    nextTick(() => {
                        initChart();
                        startMonitor();
                    });
                } else {
                    loginError.value = "身份核对失败，访问被拒绝！";
                }
            } catch (e) {
                loginError.value = "无法连接到服务器，请检查后端是否启动。";
            } finally {
                isLoggingIn.value = false;
            }
        };

        const doLogout = () => {
            localStorage.removeItem("aiops_token");
            token.value = "";
            isLoggedIn.value = false;
            timeData.length = 0;
            cpuData.length = 0;
            memData.length = 0;
            stopMonitor();
        };

        // ==================== 图表 ====================

        const initChart = () => {
            const chartDom = document.getElementById("chart-container");
            if (chartDom && !myChart) {
                myChart = echarts.init(chartDom);
                myChart.setOption({
                    tooltip: { trigger: "axis" },
                    legend: {
                        data: ["CPU %", "内存 %", "磁盘 %"],
                        textStyle: { color: "#fff" },
                    },
                    xAxis: {
                        type: "category",
                        data: timeData,
                        axisLabel: { color: "#fff" },
                    },
                    yAxis: {
                        type: "value",
                        max: 100,
                        axisLabel: { color: "#fff" },
                    },
                    series: [
                        {
                            name: "CPU %",
                            type: "line",
                            data: cpuData,
                            smooth: true,
                            itemStyle: { color: "#00ffcc" },
                        },
                        {
                            name: "内存 %",
                            type: "line",
                            data: memData,
                            smooth: true,
                            itemStyle: { color: "#ff4757" },
                        },
                        {
                            name: "磁盘 %",
                            type: "line",
                            data: [],
                            smooth: true,
                            itemStyle: { color: "#ffa502" },
                        },
                    ],
                });
            }
        };

        const diskData = [];

        const updateChart = (cpuVal, memVal, diskVal, timeVal) => {
            if (timeData.length > 20) {
                timeData.shift();
                cpuData.shift();
                memData.shift();
                diskData.shift();
            }
            timeData.push(timeVal);
            cpuData.push(cpuVal);
            memData.push(memVal);
            diskData.push(diskVal);

            if (myChart) {
                const cpuColor = isAiAnomaly.value ? "#ff0055" : "#00ffcc";
                myChart.setOption({
                    xAxis: { data: timeData },
                    series: [
                        { data: cpuData, itemStyle: { color: cpuColor } },
                        { data: memData },
                        { data: diskData },
                    ],
                });
            }
        };

        // ==================== 数据获取 ====================

        const switchHost = () => {
            timeData.length = 0;
            cpuData.length = 0;
            memData.length = 0;
            diskData.length = 0;
            isAiAnomaly.value = false;
            triggeredAlerts.value = [];
            if (myChart) {
                myChart.setOption({
                    xAxis: { data: timeData },
                    series: [
                        { data: cpuData },
                        { data: memData },
                        { data: diskData },
                    ],
                });
            }
        };

        const getData = async () => {
            if (!isLoggedIn.value || isHistoryMode.value) return;
            try {
                let url = `/api/system_status`;
                if (currentHost.value) {
                    url += `?host=${encodeURIComponent(currentHost.value)}`;
                }
                const result = await apiFetch(url);
                if (result.status === "success") {
                    cpu.value = result.cpu_usage;
                    memory.value = result.memory_usage;
                    netUp.value = result.net_upload;
                    netDown.value = result.net_download;
                    topProcs.value = result.top_processes || [];
                    dockerContainers.value = result.docker_containers || [];
                    hostname.value = result.hostname;
                    localIp.value = result.local_ip;
                    diskPercent.value = result.disk_percent;
                    swapPercent.value = result.swap_percent || 0;
                    diskRead.value = result.disk_read_mbps || 0;
                    diskWrite.value = result.disk_write_mbps || 0;
                    netConnections.value = result.net_connections || 0;
                    isAiAnomaly.value = result.is_anomaly || false;
                    anomalyDetail.value = result.anomaly_detail || {};
                    triggeredAlerts.value = result.triggered_alerts || [];

                    if (!isHistoryMode.value) {
                        updateChart(
                            result.cpu_usage,
                            result.memory_usage,
                            result.disk_percent,
                            result.time
                        );
                    }
                }
            } catch (e) {
                // 静默处理网络错误
            }
        };

        const startMonitor = () => {
            stopMonitor();
            getData();
            monitorTimer = setInterval(getData, 2000);
        };

        const stopMonitor = () => {
            if (monitorTimer) {
                clearInterval(monitorTimer);
                monitorTimer = null;
            }
        };

        // ==================== 历史模式 ====================

        const toggleHistory = async () => {
            isHistoryMode.value = !isHistoryMode.value;
            timeData.length = 0;
            cpuData.length = 0;
            memData.length = 0;
            diskData.length = 0;

            if (isHistoryMode.value) {
                try {
                    const result = await apiFetch("/api/history?limit=200");
                    if (result.status === "success") {
                        const items = result.items || [];
                        items.forEach((item) => {
                            timeData.push(item.time);
                            cpuData.push(item.cpu);
                            memData.push(item.mem);
                            diskData.push(item.disk || 0);
                        });
                        if (myChart) {
                            myChart.setOption({
                                xAxis: { data: timeData },
                                series: [
                                    { data: cpuData },
                                    { data: memData },
                                    { data: diskData },
                                ],
                            });
                        }
                    }
                } catch (e) {
                    console.error("历史数据读取失败:", e);
                }
            }
        };

        // ==================== AI 诊断 ====================

        const getAIReport = async () => {
            if (isDiagnosing.value) return;
            isDiagnosing.value = true;
            reportData.value = "正在深度扫描系统进程，请稍候...";
            try {
                const result = await apiFetch("/api/diagnose");
                if (result.status === "success") {
                    reportData.value = result.report;
                } else {
                    reportData.value =
                        "诊断失败：" + (result.report || "未知错误");
                }
            } catch (e) {
                reportData.value =
                    "无法连接到 AI 诊断中枢，请检查后端服务器是否正常运行。";
            } finally {
                isDiagnosing.value = false;
            }
        };

        const showDetail = (p) => {
            alert(
                `进程深挖\n名字：${p.name}\nPID: ${p.pid}\n内存: ${p.mem_mb} MB\n路径: ${p.path}`
            );
        };

        // ==================== 桌面通知 ====================

        const requestNotifyPermission = () => {
            if ("Notification" in window) {
                Notification.requestPermission().then((permission) => {
                    if (permission === "granted") {
                        alert("桌面预警已开启。");
                    }
                });
            } else {
                alert("当前浏览器不支持桌面通知。");
            }
        };

        // ==================== Tab 切换 ====================

        const switchTab = (tab) => {
            activeTab.value = tab;
            if (tab === "alerts") {
                loadAlertHistory();
            } else if (tab === "info") {
                loadSystemInfo();
                loadAlertRules();
                loadSummary();
            }
        };

        // ==================== 告警历史 ====================

        const loadAlertHistory = async () => {
            try {
                const offset = alertPage.value * alertPageSize;
                const result = await apiFetch(
                    `/api/alerts?limit=${alertPageSize}&offset=${offset}`
                );
                alertItems.value = result.items || [];
                alertTotal.value = result.total || 0;
            } catch (e) {
                console.error("加载告警历史失败:", e);
            }
        };

        const alertTotalPages = computed(() =>
            Math.max(1, Math.ceil(alertTotal.value / alertPageSize))
        );

        const alertPrevPage = () => {
            if (alertPage.value > 0) {
                alertPage.value--;
                loadAlertHistory();
            }
        };

        const alertNextPage = () => {
            if (
                (alertPage.value + 1) * alertPageSize <
                alertTotal.value
            ) {
                alertPage.value++;
                loadAlertHistory();
            }
        };

        // ==================== 系统信息 ====================

        const loadSystemInfo = async () => {
            try {
                const result = await apiFetch("/api/system_info");
                if (result.status === "success") {
                    sysInfo.value = result;
                    modelInfo.value = result.model_info || {};
                }
            } catch (e) {
                console.error("加载系统信息失败:", e);
            }
        };

        const loadSummary = async () => {
            try {
                const result = await apiFetch("/api/dashboard_summary");
                if (result.status === "success") {
                    summary.value = result;
                }
            } catch (e) {
                console.error("加载摘要失败:", e);
            }
        };

        // ==================== 告警规则管理 ====================

        const loadAlertRules = async () => {
            try {
                const result = await apiFetch("/api/alert_rules");
                alertRules.value = result.rules || [];
            } catch (e) {
                console.error("加载规则失败:", e);
            }
        };

        const toggleRule = async (ruleId, currentEnabled) => {
            try {
                const newState = !currentEnabled;
                await apiFetch(
                    `/api/alert_rules/${ruleId}?enabled=${newState}`,
                    { method: "PUT" }
                );
                await loadAlertRules();
            } catch (e) {
                console.error("切换规则失败:", e);
            }
        };

        // ==================== 生命周期 ====================

        onMounted(() => {
            if (token.value) {
                isLoggedIn.value = true;
                nextTick(() => {
                    initChart();
                    startMonitor();
                });
            }
        });

        onUnmounted(() => {
            stopMonitor();
            if (myChart) {
                myChart.dispose();
                myChart = null;
            }
        });

        // ==================== 暴露给模板 ====================

        return {
            // 认证
            isLoggedIn,
            loginUser,
            loginPass,
            doLogin,
            doLogout,
            isLoggingIn,
            loginError,
            // 导航
            activeTab,
            switchTab,
            currentHost,
            switchHost,
            // 实时数据
            cpu,
            memory,
            netUp,
            netDown,
            swapPercent,
            diskPercent,
            diskRead,
            diskWrite,
            netConnections,
            topProcs,
            dockerContainers,
            hostname,
            localIp,
            isAlert,
            isAiAnomaly,
            anomalyDetail,
            triggeredAlerts,
            isHistoryMode,
            toggleHistory,
            // AI 诊断
            isDiagnosing,
            reportData,
            getAIReport,
            showDetail,
            // 桌面通知
            requestNotifyPermission,
            // 告警历史
            alertItems,
            alertTotal,
            alertPage,
            alertTotalPages,
            alertPrevPage,
            alertNextPage,
            // 系统信息
            sysInfo,
            modelInfo,
            alertRules,
            toggleRule,
            // 摘要
            summary,
        };
    },
}).mount("#app");
