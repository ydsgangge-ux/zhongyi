import { createRouter, createWebHistory } from 'vue-router'
import Inquiry from '../views/Inquiry.vue'
import Result from '../views/Result.vue'
import History from '../views/History.vue'
import Settings from '../views/Settings.vue'

const routes = [
  { path: '/', name: 'Inquiry', component: Inquiry },
  { path: '/result/:sessionId', name: 'Result', component: Result, props: true },
  { path: '/history', name: 'History', component: History },
  { path: '/settings', name: 'Settings', component: Settings },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
