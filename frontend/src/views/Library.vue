<template>
  <div class="library">
    <h1>📚 Bibliothèque</h1>

    <div class="card">
      <h2>Liste des livres</h2>

      <div v-if="loading" class="loading">Chargement...</div>
      <div v-else-if="error" class="error">{{ error }}</div>

      <div v-else class="book-list">
        <p class="placeholder">
          🚧 Liste des livres à venir<br />
          Total: {{ totalBooks }} livres
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, computed } from 'vue'
import { storeToRefs } from 'pinia'
import { useLibraryStore } from '../stores/library'

const libraryStore = useLibraryStore()
const { loading, error, stats } = storeToRefs(libraryStore)

const totalBooks = computed(() => stats.value.total_books || 0)

onMounted(() => {
  libraryStore.fetchStats()
})
</script>

<style scoped>
.library h1 {
  margin-bottom: 2rem;
}

.placeholder {
  text-align: center;
  padding: 3rem;
  color: #999;
  font-size: 1.1rem;
}
</style>
