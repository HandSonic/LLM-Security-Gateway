<template>
  <div class="policy">
    <el-table :data="policies" style="width: 100%" v-loading="loading" height="100%">
      <el-table-column prop="risk_category" label="风险代码" width="90" />
      <el-table-column label="风险类别" width="140">
          <template #default="scope">
              {{ getRiskName(scope.row.risk_category) }}
          </template>
      </el-table-column>

      <el-table-column label="拦截阈值" min-width="250">
        <template #default="scope">
            <div class="slider-block">
                <el-slider
                    v-model="scope.row.threshold"
                    :min="0" :max="1" :step="0.01"
                    show-input
                    :show-input-controls="false"
                    @change="updatePolicy(scope.row)"
                />
            </div>
        </template>
      </el-table-column>

      <el-table-column label="启用状态" width="100" align="center">
         <template #default="scope">
            <el-switch
                v-model="scope.row.enabled"
                active-text="开"
                inactive-text="关"
                inline-prompt
                @change="updatePolicy(scope.row)"
            />
         </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../api'
import { ElMessage } from 'element-plus'
import { getRiskName } from '../utils/risk_defs'

const policies = ref([])
const loading = ref(false)

const fetchPolicies = async () => {
    loading.value = true
    try {
        const res = await api.get('/policies')
        policies.value = res.data
    } catch (e) {
        ElMessage.error('加载策略失败')
    } finally {
        loading.value = false
    }
}

const updatePolicy = async (policy) => {
    try {
        await api.put(`/policies/${policy.id}`, policy)
        ElMessage.success('策略已更新')
    } catch (e) {
        ElMessage.error('更新策略失败')
    }
}

onMounted(fetchPolicies)
</script>

<style scoped>
.slider-block {
    display: flex;
    align-items: center;
}
</style>
