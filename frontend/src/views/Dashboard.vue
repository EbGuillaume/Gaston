<template>
  <div class="dashboard">
    <h1>📊 Dashboard</h1>

    <div v-if="loading" class="loading">Chargement...</div>
    <div v-else-if="error" class="error">{{ error }}</div>

    <div v-else class="stats-grid">
      <div class="stat-card">
        <h3>{{ stats.total_books || 0 }}</h3>
        <p>Livres totaux</p>
      </div>

      <div class="stat-card">
        <h3>{{ stats.books_with_metadata || 0 }}</h3>
        <p>Avec métadonnées</p>
      </div>

      <div class="stat-card">
        <h3>{{ formatSize(stats.total_size_bytes || 0) }}</h3>
        <p>Taille totale</p>
      </div>

      <div class="stat-card">
        <h3>{{ stats.books_ready_to_organize || 0 }}</h3>
        <p>Prêts à organiser</p>
      </div>
    </div>

    <div class="card">
      <h2>Par Format</h2>
      <div class="format-list">
        <div v-for="(count, ext) in stats.by_extension" :key="ext" class="format-item">
          <span class="format-ext">{{ ext }}</span>
          <span class="format-count">{{ count }} fichiers</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { storeToRefs } from 'pinia'
import { useLibraryStore } from '../stores/library'

const libraryStore = useLibraryStore()
const { stats, loading, error } = storeToRefs(libraryStore)

onMounted(() => {
  libraryStore.fetchStats()
})

function formatSize(bytes) {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i]
}
</script>

<style scoped>
.dashboard h1 {
  margin-bottom: 2rem;
  color: var(--secondary-color);
}

.format-list {
  display: grid;
  gap: 0.5rem;
}

.format-item {
  display: flex;
  justify-content: space-between;
  padding: 0.75rem;
  background: #f8f9fa;
  border-radius: 4px;
}

.format-ext {
  font-weight: bold;
  color: var(--primary-color);
}

.format-count {
  color: #666;
}
</style>
