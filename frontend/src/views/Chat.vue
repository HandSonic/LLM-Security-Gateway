<template>
  <div class="chat-container">
    <div class="messages" ref="msgContainer">
        <div v-for="(msg, index) in messages" :key="index" :class="['message', msg.role]">
            <div class="message-content">
                <div v-if="msg.role === 'assistant' && msg.content.includes('请求被安全网关拦截')" class="blocked-alert">
                    <el-alert :title="msg.content" type="error" show-icon :closable="false" />
                </div>
                <div v-else>
                    {{ msg.content }}
                </div>
            </div>
        </div>
        <div v-if="loading && !streaming" class="message assistant">
             <div class="message-content">思考中...</div>
        </div>
    </div>
    
    <div class="input-area">
        <el-input 
            v-model="input" 
            placeholder="请输入您的问题..." 
            @keyup.enter="send"
            :disabled="loading"
        >
            <template #append>
                <el-button @click="send" :loading="loading">发送</el-button>
            </template>
        </el-input>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue'
import axios from 'axios'
import { getRiskName } from '../utils/risk_defs'

const messages = ref([])
const input = ref('')
const loading = ref(false)
const streaming = ref(false)
const msgContainer = ref(null)

const send = async () => {
    if (!input.value.trim()) return
    
    // Add user message
    messages.value.push({ role: 'user', content: input.value })
    const userMsgContent = input.value
    input.value = ''
    loading.value = true
    
    await nextTick()
    scrollToBottom()
    
    try {
        // Use fetch for streaming support
        const response = await fetch('/api/v1/chat/completions', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                model: 'gpt-3.5-turbo',
                messages: [{ role: 'user', content: userMsgContent }],
                stream: true // Enable streaming
            })
        })

        if (!response.ok) {
             throw new Error(`HTTP error! status: ${response.status}`)
        }

        // Push an empty assistant message into the reactive array FIRST
        messages.value.push({ role: 'assistant', content: '' })
        // Get the reactive proxy reference so Vue tracks changes
        const assistantMsg = messages.value[messages.value.length - 1]
        streaming.value = true

        const reader = response.body.getReader()
        const decoder = new TextDecoder()
        let isFirstChunk = true

        let done = false
        while (!done) {
            const { value, done: DONE } = await reader.read()
            done = DONE
            if (value) {
                const chunk = decoder.decode(value, { stream: true })

                // When the backend blocks a prompt, it returns standard JSON (not a stream)
                if (isFirstChunk && chunk.trim().startsWith('{')) {
                    isFirstChunk = false
                    try {
                        const json = JSON.parse(chunk)
                        if (json.choices && json.choices[0].message) {
                             const content = json.choices[0].message.content
                             if (content.startsWith('BLOCKED:')) {
                                const parts = content.split(':')
                                const code = parts[1]
                                const score = parseFloat(parts[2])
                                const riskName = getRiskName(code)
                                assistantMsg.content = `请求被安全网关拦截。检测到风险：【${riskName}】 (得分: ${(score * 100).toFixed(2)}%)，超过阈值。`
                                return
                             }
                        }
                    } catch(e) {}
                }
                isFirstChunk = false

                // Parse SSE stream lines
                const lines = chunk.split('\n')
                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        const data = line.slice(6)
                        if (data === '[DONE]') continue
                        try {
                            const json = JSON.parse(data)
                            if (json.choices && json.choices.length > 0) {
                                const delta = json.choices[0].delta
                                if (delta.content) {
                                    assistantMsg.content += delta.content
                                    scrollToBottom()
                                }
                            }
                        } catch (e) { }
                    }
                }
            }
        }
    } catch (e) {
        console.error(e)
         messages.value.push({ role: 'assistant', content: "Error: " + (e.message || "Network Error") })
    } finally {
        loading.value = false
        streaming.value = false
        scrollToBottom()
    }
}

const scrollToBottom = async () => {
    await nextTick()
    if (msgContainer.value) {
        msgContainer.value.scrollTop = msgContainer.value.scrollHeight
    }
}
</script>

<style scoped>
.chat-container {
    display: flex;
    flex-direction: column;
    height: 100%;
}
.messages {
    flex: 1;
    overflow-y: auto;
    padding: 20px;
    background: #f5f5f5;
    border-radius: 8px;
    margin-bottom: 20px;
}
.message {
    margin-bottom: 15px;
    display: flex;
}
.message.user {
    justify-content: flex-end;
}
.message-content {
    max-width: 70%;
    padding: 10px 15px;
    border-radius: 12px;
    background: white;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}
.message.user .message-content {
    background: #409eff;
    color: white;
}
.message.assistant .message-content {
    background: white;
    color: #333;
}
.input-area {
    padding: 0;
}
</style>
