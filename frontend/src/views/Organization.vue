<template>
  <div class="organization">
    <h1>📦 Organisation</h1>

    <!-- Section Reset Database -->
    <div class="card danger-zone">
      <h2>⚠️ Zone de Danger</h2>

      <div class="reset-section">
        <h3>Reset de la base de données</h3>
        <p>Cette action supprimera <strong>TOUTES les données</strong> de la base de données (livres, métadonnées, séries).</p>

        <button @click="showResetConfirm = true" class="btn btn-danger">
          🗑️ Reset Database
        </button>
      </div>
    </div>

    <!-- Modal de confirmation Reset -->
    <div v-if="showResetConfirm" class="modal-overlay" @click="showResetConfirm = false">
      <div class="modal-content" @click.stop>
        <h3>⚠️ Confirmation requise</h3>
        <p>Êtes-vous sûr de vouloir reset la base de données ?</p>
        <p class="warning-text">
          Cette action est <strong>IRRÉVERSIBLE</strong> et supprimera toutes vos données.
        </p>

        <div class="modal-actions">
          <button @click="showResetConfirm = false" class="btn btn-secondary">
            Annuler
          </button>
          <button @click="handleReset" class="btn btn-danger" :disabled="loading">
            {{ loading ? 'Reset en cours...' : 'Confirmer le Reset' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Section Organisation des BD -->
    <div class="card">
      <h2>📚 Organiser la bibliothèque</h2>

      <form @submit.prevent="handleOrganize" class="organize-form">
        <div class="form-group">
          <label for="outputPath">Dossier de destination</label>
          <input
            id="outputPath"
            v-model="outputPath"
            type="text"
            class="input"
            placeholder="/home/user/organized_library"
            required
          />
          <p class="help-text">
            Les BD seront organisées dans ce dossier avec la structure Komga
          </p>
        </div>

        <div class="options-group">
          <label class="checkbox-label">
            <input v-model="copyInsteadOfMove" type="checkbox" />
            Copier au lieu de déplacer (garde les fichiers originaux)
          </label>

          <label class="checkbox-label">
            <input v-model="injectComicinfo" type="checkbox" checked />
            Injecter ComicInfo.xml dans les fichiers CBZ
          </label>

          <label class="checkbox-label">
            <input v-model="dryRun" type="checkbox" />
            Mode simulation (ne fait aucune modification)
          </label>
        </div>

        <button type="submit" class="btn btn-primary" :disabled="loading">
          {{ loading ? 'Organisation en cours...' : '🚀 Organiser' }}
        </button>
      </form>

      <div v-if="organizeResult" class="result-box" :class="organizeResult.status">
        <h3>{{ organizeResult.status === 'success' ? '✅ Succès' : '❌ Erreur' }}</h3>
        <p>{{ organizeResult.message }}</p>
        <div v-if="organizeResult.status === 'success'" class="result-stats">
          <p><strong>Organisés:</strong> {{ organizeResult.organized }}/{{ organizeResult.total_books }}</p>
          <p><strong>Échecs:</strong> {{ organizeResult.failed }}</p>
          <p><strong>Ignorés:</strong> {{ organizeResult.skipped }}</p>
        </div>
      </div>

      <div v-if="error" class="error">{{ error }}</div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const showResetConfirm = ref(false)
const loading = ref(false)
const error = ref(null)

// Organisation
const outputPath = ref('./organized_library')
const copyInsteadOfMove = ref(true)
const injectComicinfo = ref(true)
const dryRun = ref(false)
const organizeResult = ref(null)

async function handleReset() {
  loading.value = true
  error.value = null

  try {
    const response = await fetch('/api/database/reset', {
      method: 'POST'
    })

    if (!response.ok) throw new Error('Failed to reset database')

    const result = await response.json()

    // Fermer le modal
    showResetConfirm.value = false

    // Afficher un message de succès
    alert('✅ ' + result.message)

    // Recharger la page pour refleter le reset
    setTimeout(() => window.location.reload(), 1000)

  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

async function handleOrganize() {
  loading.value = true
  error.value = null
  organizeResult.value = null

  try {
    const response = await fetch('/api/organize/organize', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        output_path: outputPath.value,
        copy_instead_of_move: copyInsteadOfMove.value,
        inject_comicinfo: injectComicinfo.value,
        dry_run: dryRun.value
      })
    })

    if (!response.ok) throw new Error('Failed to organize library')

    organizeResult.value = await response.json()

  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.organization h1 {
  margin-bottom: 2rem;
}

.danger-zone {
  border: 2px solid var(--error-color);
  background: #fff5f5;
}

.danger-zone h2 {
  color: var(--error-color);
}

.reset-section {
  padding: 1rem 0;
}

.reset-section h3 {
  margin-bottom: 0.5rem;
}

.reset-section p {
  margin-bottom: 1rem;
  color: #666;
}

.btn-danger {
  background: var(--error-color);
  color: white;
}

.btn-danger:hover {
  background: #c0392b;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  padding: 2rem;
  border-radius: 8px;
  max-width: 500px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
}

.modal-content h3 {
  margin-bottom: 1rem;
  color: var(--error-color);
}

.warning-text {
  color: var(--error-color);
  font-weight: bold;
  margin: 1rem 0;
}

.modal-actions {
  display: flex;
  gap: 1rem;
  margin-top: 2rem;
}

.modal-actions button {
  flex: 1;
}

.organize-form {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
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

.help-text {
  font-size: 0.9rem;
  color: #666;
  margin: 0;
}

.options-group {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  padding: 1rem;
  background: #f8f9fa;
  border-radius: 4px;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
}

.checkbox-label input {
  cursor: pointer;
}

.result-box {
  margin-top: 1.5rem;
  padding: 1.5rem;
  border-radius: 8px;
}

.result-box.success {
  background: #e8f5e9;
  border: 2px solid var(--success-color);
}

.result-box.error {
  background: #ffebee;
  border: 2px solid var(--error-color);
}

.result-box h3 {
  margin: 0 0 1rem 0;
}

.result-stats p {
  margin: 0.5rem 0;
}
</style>
