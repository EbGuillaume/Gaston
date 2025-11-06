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

        <button type="submit" class="btn btn-primary" :disabled="loading || scanning">
          {{ scanning ? 'Scan en cours...' : 'Scanner' }}
        </button>
      </form>

      <div v-if="scanning && scanProgress.total > 0" class="progress-info">
        <p>
          <strong>{{ scanProgress.current }}/{{ scanProgress.total }}</strong> fichiers scannés
        </p>
        <p class="current-file">{{ scanProgress.filename }}</p>
      </div>

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
const scanning = ref(false)
const scanProgress = ref({ current: 0, total: 0, filename: '' })

// Enrichissement
const enriching = ref(false)
const enrichProgress = ref(0)
const enrichResult = ref(null)

async function handleScan() {
  try {
    scanResult.value = null
    scanning.value = true
    scanProgress.value = { current: 0, total: 0, filename: '' }

    libraryStore.scanDirectoryStream(scanPath.value, {
      onStatus: (message) => {
        console.log('Status:', message)
      },
      onFound: (total) => {
        scanProgress.value.total = total
      },
      onProgress: (current, total, filename) => {
        scanProgress.value = { current, total, filename }
      },
      onComplete: (result) => {
        scanResult.value = result
        scanning.value = false
      },
      onError: (message) => {
        libraryStore.error = message
        scanning.value = false
      }
    })
  } catch (e) {
    console.error('Scan failed:', e)
    scanning.value = false
  }
}

async function handleEnrichAll() {
  try {
    enriching.value = true
    enrichProgress.value = 0
    enrichResult.value = null

    libraryStore.enrichAllStream({
      onFound: (total) => {
        console.log(`Found ${total} books to enrich`)
      },
      onProgress: (current, total, filename) => {
        enrichProgress.value = Math.round((current / total) * 100)
      },
      onComplete: (result) => {
        enrichResult.value = {
          success: result.success,
          failed: result.failed + result.skipped
        }
        enriching.value = false
      },
      onError: (message) => {
        libraryStore.error = message
        enriching.value = false
      }
    })
  } catch (e) {
    console.error('Enrich failed:', e)
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

.progress-info {
  margin-top: 1rem;
  padding: 1rem;
  background: #e3f2fd;
  border-radius: 4px;
  border-left: 4px solid var(--primary-color);
}

.progress-info p {
  margin: 0.5rem 0;
}

.current-file {
  font-family: monospace;
  color: #555;
  font-size: 0.9rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
