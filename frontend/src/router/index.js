import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '../views/Dashboard.vue'
import Chat from '../views/Chat.vue'
import Policy from '../views/Policy.vue'

const router = createRouter({
    history: createWebHistory(import.meta.env.BASE_URL),
    routes: [
        {
            path: '/',
            name: '仪表盘',
            component: Dashboard
        },
        {
            path: '/chat',
            name: '对话游乐场',
            component: Chat
        },
        {
            path: '/policy',
            name: '安全策略',
            component: Policy
        }
    ]
})

export default router
