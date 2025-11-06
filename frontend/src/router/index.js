import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '../views/Dashboard.vue'
import Scanner from '../views/Scanner.vue'
import Library from '../views/Library.vue'
import Duplicates from '../views/Duplicates.vue'
import Metadata from '../views/Metadata.vue'

const routes = [
  {
    path: '/',
    name: 'Dashboard',
    component: Dashboard
  },
  {
    path: '/scanner',
    name: 'Scanner',
    component: Scanner
  },
  {
    path: '/library',
    name: 'Library',
    component: Library
  },
  {
    path: '/duplicates',
    name: 'Duplicates',
    component: Duplicates
  },
  {
    path: '/metadata',
    name: 'Metadata',
    component: Metadata
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
