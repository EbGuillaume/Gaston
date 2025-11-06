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
        <span v-if="scanResult.skipped_count > 0">, {{ scanResult.skipped_count }} doublons ignorés</span>
      </div>

      <div v-if="error" class="error">{{ error }}</div>
    </div>

    <div class="card">
      <h2>Enrichir les métadonnées</h2>
      <p>Enrichir automatiquement les métadonnées de tous les livres scannés</p>

      <button @click="handleEnrichAll" class="btn btn-secondary" :disabled="loading || enriching">
        {{ enriching ? `Enrichissement ${enrichProgress}%...` : '✨ Enrichir tous les livres' }}
      </button>

      <div v-if="enrichResult" :class="enrichResult.success > 0 ? 'success' : 'error'">
        {{ enrichResult.success > 0 ? '✓' : '✗' }} Enrichissement terminé: {{ enrichResult.success }} succès, {{ enrichResult.failed }} échecs
      </div>
    </div>

    <div v-if="scanResult" class="card">
      <h2>Résultats du dernier scan</h2>

      <div class="result-stats">
        <p><strong>Fichiers trouvés:</strong> {{ scanResult.total_files }}</p>
        <p><strong>Sauvegardés en DB:</strong> {{ scanResult.saved_to_db }}</p>
        <p><strong>Doublons ignorés:</strong> {{ scanResult.skipped_count }}</p>
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

// Enrichissement
const enriching = ref(false)
const enrichProgress = ref(0)
const enrichResult = ref(null)

async function handleScan() {
  try {
    scanResult.value = null
    const result = await libraryStore.scanDirectory(scanPath.value)
    scanResult.value = result
  } catch (e) {
    console.error('Scan failed:', e)
  }
}

async function handleEnrichAll() {
  enriching.value = true
  enrichProgress.value = 0
  enrichResult.value = null

  try {
    // Récupérer le nombre total de livres
    const statsResponse = await fetch('/api/organize/stats')
    const stats = await statsResponse.json()
    const totalBooks = stats.total_books

    if (totalBooks === 0) {
      alert('Aucun livre à enrichir. Scannez d\'abord un dossier!')
      return
    }

    let success = 0
    let failed = 0

    // Enrichir chaque livre
    for (let id = 1; id <= totalBooks; id++) {
      try {
        const response = await fetch(`/api/metadata/match/${id}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' }
        })

        const result = await response.json()

        if (response.ok && result.status === 'success') {
          success++
        } else {
          failed++
        }
      } catch (e) {
        failed++
      }

      // Mettre à jour la progression
      enrichProgress.value = Math.round((id / totalBooks) * 100)
    }

    enrichResult.value = { success, failed }

  } catch (e) {
    error.value = e.message
  } finally {
    enriching.value = false
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
