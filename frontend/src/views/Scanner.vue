<template>
  <div class="scanner">
    <h1>🔍 Scanner</h1>

    <div class="card">
      <h2>Scanner un nouveau dossier</h2>

      <form @submit.prevent="handleScan" class="scan-form">
        <div class="form-group">
          <label for="path">Chemin du dossier</label>
          <input
            id="path"
            v-model="scanPath"
            type="text"
            class="input"
            placeholder="/home/user/comics"
            required
          />
        </div>

        <button type="submit" class="btn btn-primary" :disabled="loading">
          {{ loading ? 'Scan en cours...' : 'Scanner' }}
        </button>
      </form>

      <div v-if="scanResult" class="success">
        ✓ Scan terminé: {{ scanResult.total_files }} fichiers trouvés,
        {{ scanResult.saved_to_db }} sauvegardés
      </div>

      <div v-if="error" class="error">{{ error }}</div>
    </div>

    <div v-if="scanResult" class="card">
      <h2>Résultats du dernier scan</h2>

      <div class="result-stats">
        <p><strong>Fichiers trouvés:</strong> {{ scanResult.total_files }}</p>
        <p><strong>Sauvegardés en DB:</strong> {{ scanResult.saved_to_db }}</p>
        <p><strong>Fichiers corrompus:</strong> {{ scanResult.corrupted_count }}</p>
        <p><strong>Taille totale:</strong> {{ formatSize(scanResult.total_size_bytes) }}</p>
      </div>

      <h3>Par extension</h3>
      <div class="format-list">
        <div v-for="(count, ext) in scanResult.by_extension" :key="ext" class="format-item">
          <span class="format-ext">{{ ext }}</span>
          <span class="format-count">{{ count }} fichiers</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { storeToRefs } from 'pinia'
import { useLibraryStore } from '../stores/library'

const libraryStore = useLibraryStore()
const { loading, error } = storeToRefs(libraryStore)

const scanPath = ref('')
const scanResult = ref(null)

async function handleScan() {
  try {
    scanResult.value = null
    const result = await libraryStore.scanDirectory(scanPath.value)
    scanResult.value = result
  } catch (e) {
    console.error('Scan failed:', e)
  }
}

function formatSize(bytes) {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i]
}
</script>

<style scoped>
.scanner h1 {
  margin-bottom: 2rem;
}

.scan-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-group label {
  font-weight: bold;
  color: var(--secondary-color);
}

.result-stats {
  margin-bottom: 1.5rem;
}

.result-stats p {
  padding: 0.5rem 0;
  border-bottom: 1px solid var(--border-color);
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
