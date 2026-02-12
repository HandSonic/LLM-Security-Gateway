<template>
  <div class="dashboard">
    <el-row :gutter="20">
      <el-col :span="8">
        <el-card shadow="hover">
          <template #header>总请求数</template>
          <div class="stat-value">{{ stats.total_requests }}</div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover">
          <template #header>拦截请求数</template>
          <div class="stat-value text-danger">{{ stats.blocked_requests }}</div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover">
          <template #header>拦截率</template>
          <div class="stat-value">{{ (stats.block_rate * 100).toFixed(1) }}%</div>
        </el-card>
      </el-col>
    </el-row>

    <br />

    <el-card shadow="hover">
      <template #header>
        <div class="card-header">
          <span>最近审计日志</span>
          <el-button text @click="fetchLogs">刷新</el-button>
        </div>
      </template>
      <el-table :data="logs" style="width: 100%" stripe>
        <el-table-column prop="timestamp" label="时间" width="180">
            <template #default="scope">
                {{ new Date(scope.row.timestamp).toLocaleString() }}
            </template>
        </el-table-column>
        <el-table-column prop="user_input" label="用户输入" show-overflow-tooltip />
        <el-table-column prop="action" label="动作" width="120">
            <template #default="scope">
                <el-tag :type="scope.row.action === 'allow' ? 'success' : 'danger'">
                    {{ scope.row.action === 'allow' ? '通过' : (scope.row.action === 'block_prompt' ? '拦截请求' : '拦截响应') }}
                </el-tag>
            </template>
        </el-table-column>
        <el-table-column prop="risk_score" label="风险分" width="100">
             <template #default="scope">
                {{ scope.row.risk_score?.toFixed(4) || '-' }}
             </template>
        </el-table-column>
        <el-table-column label="详情">
            <template #default="scope">
                <el-popover placement="left" title="风险详情" :width="300" trigger="hover">
                    <template #reference>
                        <el-button size="small">查看</el-button>
                    </template>
                    <div v-if="scope.row.risk_details">
                        <div v-for="(score, code) in JSON.parse(scope.row.risk_details)" :key="code" class="risk-item">
                            <span class="risk-name">{{ getRiskName(code) }}:</span>
                            <span class="risk-score">{{ (score * 100).toFixed(2) }}%</span>
                        </div>
                    </div>
                    <div v-else>无详情</div>
                </el-popover>
            </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../api'
import { getRiskName } from '../utils/risk_defs'

const stats = ref({
  total_requests: 0,
  blocked_requests: 0,
  block_rate: 0
})

const logs = ref([])

const fetchStats = async () => {
    try {
        const res = await api.get('/stats')
        stats.value = res.data
    } catch (e) {
        console.error(e)
    }
}

const fetchLogs = async () => {
    try {
        const res = await api.get('/logs')
        logs.value = res.data
    } catch (e) {
         console.error(e)
    }
}

onMounted(() => {
    fetchStats()
    fetchLogs()
    // Poll every 5s
    setInterval(fetchStats, 5000)
    setInterval(fetchLogs, 5000)
})
</script>

<style scoped>
.stat-value {
    font-size: 24px;
    font-weight: bold;
    text-align: center;
}
.text-danger {
    color: #f56c6c;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.risk-item {
    display: flex;
    justify-content: space-between;
    margin-bottom: 5px;
    font-size: 14px;
}
.risk-name {
    font-weight: bold;
    color: #606266;
}
.risk-score {
    color: #f56c6c;
}
</style>
