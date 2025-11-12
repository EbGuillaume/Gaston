<template>
  <div class="metadata">
    <h1>📝 Métadonnées</h1>

    <div class="card">
      <div class="filters">
        <input
          v-model="searchQuery"
          type="text"
          class="input search-input"
          placeholder="Rechercher un livre..."
          @input="handleSearch"
        />

        <select v-model="filterMetadata" class="select" @change="loadBooks">
          <option :value="null">Tous les livres</option>
          <option :value="true">Avec métadonnées</option>
          <option :value="false">Sans métadonnées</option>
        </select>

        <button
          @click="enrichAllBooks"
          class="btn btn-success"
          :disabled="enrichingAll || loading"
          title="Enrichir tous les livres sans métadonnées"
        >
          {{ enrichingAll ? `⏳ ${enrichProgress.current}/${enrichProgress.total}` : '✨ Enrichir tous' }}
        </button>
      </div>

      <div v-if="enrichingAll" class="enrichment-progress">
        <div class="progress-bar-container">
          <div class="progress-bar" :style="{ width: enrichProgressPercent + '%' }"></div>
        </div>
        <div class="progress-text">
          Enrichissement en cours: {{ enrichProgress.current }} / {{ enrichProgress.total }} livres
          <span v-if="enrichProgress.currentBook" class="current-book">
            ({{ enrichProgress.currentBook }})
          </span>
        </div>
      </div>

      <div v-if="loading" class="loading">Chargement...</div>
      <div v-else-if="error" class="error">{{ error }}</div>

      <div v-else class="book-list">
        <div class="total-count">
          {{ totalBooks }} livre(s) au total
        </div>

        <div v-if="books.length === 0" class="no-results">
          Aucun livre trouvé
        </div>

        <table v-else class="metadata-table">
          <thead>
            <tr>
              <th class="sortable" @click="sortTable('id')">
                #
                <span class="sort-arrow" v-if="sortColumn === 'id'">
                  {{ sortOrder === 'asc' ? '↑' : '↓' }}
                </span>
              </th>
              <th class="sortable" @click="sortTable('filename')">
                Fichier
                <span class="sort-arrow" v-if="sortColumn === 'filename'">
                  {{ sortOrder === 'asc' ? '↑' : '↓' }}
                </span>
              </th>
              <th class="sortable" @click="sortTable('series_name')">
                Série
                <span class="sort-arrow" v-if="sortColumn === 'series_name'">
                  {{ sortOrder === 'asc' ? '↑' : '↓' }}
                </span>
              </th>
              <th class="sortable" @click="sortTable('volume_number')">
                Volume
                <span class="sort-arrow" v-if="sortColumn === 'volume_number'">
                  {{ sortOrder === 'asc' ? '↑' : '↓' }}
                </span>
              </th>
              <th class="sortable" @click="sortTable('title')">
                Titre
                <span class="sort-arrow" v-if="sortColumn === 'title'">
                  {{ sortOrder === 'asc' ? '↑' : '↓' }}
                </span>
              </th>
              <th class="sortable" @click="sortTable('publisher')">
                Éditeur
                <span class="sort-arrow" v-if="sortColumn === 'publisher'">
                  {{ sortOrder === 'asc' ? '↑' : '↓' }}
                </span>
              </th>
              <th class="sortable" @click="sortTable('confidence_score')">
                Confiance
                <span class="sort-arrow" v-if="sortColumn === 'confidence_score'">
                  {{ sortOrder === 'asc' ? '↑' : '↓' }}
                </span>
              </th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="book in books" :key="book.id" class="book-row">
              <td>{{ book.id }}</td>
              <td class="filename">
                <span :title="book.filename">{{ book.filename }}</span>
              </td>
              <td>{{ book.series_name || '-' }}</td>
              <td>{{ book.volume_number || '-' }}</td>
              <td>{{ book.title || '-' }}</td>
              <td>{{ book.publisher || '-' }}</td>
              <td>
                <span v-if="book.confidence_score" class="confidence" :class="getConfidenceClass(book.confidence_score)">
                  {{ (book.confidence_score * 100).toFixed(0) }}%
                </span>
                <span v-else>-</span>
              </td>
              <td class="actions">
                <button
                  v-if="book.has_metadata"
                  @click="editMetadata(book)"
                  class="btn btn-small btn-primary"
                  title="Éditer les métadonnées"
                >
                  ✏️ Éditer
                </button>
                <button
                  v-else
                  @click="enrichBook(book.id)"
                  class="btn btn-small btn-success"
                  title="Enrichir avec les métadonnées"
                  :disabled="enriching[book.id]"
                >
                  {{ enriching[book.id] ? '⏳' : '🔍' }} Enrichir
                </button>
              </td>
            </tr>
          </tbody>
        </table>

        <div v-if="totalBooks > limit" class="pagination">
          <button
            @click="loadPreviousPage"
            :disabled="currentPage === 1"
            class="btn btn-small"
          >
            ← Précédent
          </button>
          <span class="page-info">
            Page {{ currentPage }} / {{ totalPages }}
          </span>
          <button
            @click="loadNextPage"
            :disabled="currentPage >= totalPages"
            class="btn btn-small"
          >
            Suivant →
          </button>
        </div>
      </div>
    </div>

    <!-- Modal d'édition -->
    <div v-if="editingBook" class="modal-overlay" @click="closeModal">
      <div class="modal" @click.stop>
        <div class="modal-header">
          <h2>Éditer les métadonnées</h2>
          <button @click="closeModal" class="btn-close">×</button>
        </div>

        <div class="modal-body">
          <div v-if="loadingMetadata" class="loading">Chargement des métadonnées...</div>

          <form v-else @submit.prevent="saveMetadata">
            <div class="form-section">
              <h3>Informations principales</h3>

              <div class="form-group">
                <label>Nom de la série *</label>
                <input
                  v-model="editForm.series_name"
                  type="text"
                  class="input"
                  required
                  placeholder="Ex: Astérix"
                />
              </div>

              <div class="form-row">
                <div class="form-group">
                  <label>Volume</label>
                  <input
                    v-model.number="editForm.volume_number"
                    type="number"
                    class="input"
                    placeholder="Ex: 1"
                  />
                </div>

                <div class="form-group">
                  <label>Titre du volume</label>
                  <input
                    v-model="editForm.title"
                    type="text"
                    class="input"
                    placeholder="Ex: Astérix le Gaulois"
                  />
                </div>
              </div>

              <div class="form-group">
                <label>Résumé</label>
                <textarea
                  v-model="editForm.summary"
                  class="textarea"
                  rows="3"
                  placeholder="Description du livre..."
                ></textarea>
              </div>
            </div>

            <div class="form-section">
              <h3>Publication</h3>

              <div class="form-row">
                <div class="form-group">
                  <label>Éditeur</label>
                  <input
                    v-model="editForm.publisher"
                    type="text"
                    class="input"
                    placeholder="Ex: Dargaud"
                  />
                </div>

                <div class="form-group">
                  <label>Date de publication</label>
                  <input
                    v-model="editForm.publication_date"
                    type="text"
                    class="input"
                    placeholder="Ex: 2023-01-15"
                  />
                </div>
              </div>

              <div class="form-row">
                <div class="form-group">
                  <label>ISBN</label>
                  <input
                    v-model="editForm.isbn"
                    type="text"
                    class="input"
                    placeholder="Ex: 978-2-205-07678-9"
                  />
                </div>

                <div class="form-group">
                  <label>Nombre de pages</label>
                  <input
                    v-model.number="editForm.page_count"
                    type="number"
                    class="input"
                    placeholder="Ex: 48"
                  />
                </div>
              </div>
            </div>

            <div class="form-section">
              <h3>Créateurs</h3>

              <div class="form-group">
                <label>Scénariste(s)</label>
                <input
                  v-model="editForm.writers"
                  type="text"
                  class="input"
                  placeholder="Séparer par des virgules"
                />
              </div>

              <div class="form-group">
                <label>Dessinateur(s)</label>
                <input
                  v-model="editForm.pencillers"
                  type="text"
                  class="input"
                  placeholder="Séparer par des virgules"
                />
              </div>

              <div class="form-row">
                <div class="form-group">
                  <label>Encreur(s)</label>
                  <input
                    v-model="editForm.inkers"
                    type="text"
                    class="input"
                    placeholder="Séparer par des virgules"
                  />
                </div>

                <div class="form-group">
                  <label>Coloriste(s)</label>
                  <input
                    v-model="editForm.colorists"
                    type="text"
                    class="input"
                    placeholder="Séparer par des virgules"
                  />
                </div>
              </div>
            </div>

            <div class="form-section">
              <h3>Classification</h3>

              <div class="form-group">
                <label>Genres</label>
                <input
                  v-model="editForm.genres"
                  type="text"
                  class="input"
                  placeholder="Séparer par des virgules (ex: BD, Aventure, Humour)"
                />
              </div>

              <div class="form-group">
                <label>Tags</label>
                <input
                  v-model="editForm.tags"
                  type="text"
                  class="input"
                  placeholder="Séparer par des virgules"
                />
              </div>
            </div>

            <div class="modal-footer">
              <button type="button" @click="closeModal" class="btn btn-secondary">
                Annuler
              </button>
              <button type="submit" class="btn btn-primary" :disabled="saving">
                {{ saving ? 'Enregistrement...' : 'Enregistrer' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, reactive } from 'vue'

const books = ref([])
const totalBooks = ref(0)
const loading = ref(false)
const error = ref(null)
const searchQuery = ref('')
const filterMetadata = ref(null)
const sortColumn = ref('id')
const sortOrder = ref('asc')

const limit = 50
const currentPage = ref(1)

const totalPages = computed(() => Math.ceil(totalBooks.value / limit))

const editingBook = ref(null)
const loadingMetadata = ref(false)
const saving = ref(false)
const enriching = reactive({})
const enrichingAll = ref(false)
const enrichProgress = reactive({
  current: 0,
  total: 0,
  currentBook: ''
})

const enrichProgressPercent = computed(() => {
  if (enrichProgress.total === 0) return 0
  return Math.round((enrichProgress.current / enrichProgress.total) * 100)
})

const editForm = reactive({
  series_name: '',
  volume_number: null,
  title: '',
  summary: '',
  writers: '',
  pencillers: '',
  inkers: '',
  colorists: '',
  publisher: '',
  publication_date: '',
  isbn: '',
  page_count: null,
  genres: '',
  tags: ''
})

async function loadBooks() {
  loading.value = true
  error.value = null

  try {
    const params = new URLSearchParams()
    params.append('skip', (currentPage.value - 1) * limit)
    params.append('limit', limit)

    if (filterMetadata.value !== null) {
      params.append('has_metadata', filterMetadata.value)
    }

    if (searchQuery.value) {
      params.append('search', searchQuery.value)
    }

    const response = await fetch(`/api/books/?${params}`)
    if (!response.ok) throw new Error('Failed to fetch books')

    const data = await response.json()

    // Trier côté client selon sortColumn et sortOrder
    books.value = sortBooks(data.books)
    totalBooks.value = data.total
  } catch (e) {
    error.value = e.message
    console.error('Error loading books:', e)
  } finally {
    loading.value = false
  }
}

let searchTimeout = null
function handleSearch() {
  clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    currentPage.value = 1
    loadBooks()
  }, 300)
}

function sortBooks(booksArray) {
  const sorted = [...booksArray].sort((a, b) => {
    let valueA = a[sortColumn.value]
    let valueB = b[sortColumn.value]

    // Gérer les valeurs nulles/undefined
    if (valueA === null || valueA === undefined) valueA = ''
    if (valueB === null || valueB === undefined) valueB = ''

    // Tri numérique pour id, volume_number et confidence_score
    if (['id', 'volume_number', 'confidence_score'].includes(sortColumn.value)) {
      valueA = Number(valueA) || 0
      valueB = Number(valueB) || 0
      return sortOrder.value === 'asc' ? valueA - valueB : valueB - valueA
    }

    // Tri alphabétique pour les autres colonnes
    const comparison = String(valueA).localeCompare(String(valueB), 'fr', { numeric: true })
    return sortOrder.value === 'asc' ? comparison : -comparison
  })

  return sorted
}

function sortTable(column) {
  // Si on clique sur la même colonne, inverser l'ordre
  if (sortColumn.value === column) {
    sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc'
  } else {
    // Nouvelle colonne, ordre croissant par défaut
    sortColumn.value = column
    sortOrder.value = 'asc'
  }

  // Re-trier les livres actuels
  books.value = sortBooks(books.value)
}

function loadNextPage() {
  if (currentPage.value < totalPages.value) {
    currentPage.value++
    loadBooks()
  }
}

function loadPreviousPage() {
  if (currentPage.value > 1) {
    currentPage.value--
    loadBooks()
  }
}

function getConfidenceClass(score) {
  if (score >= 0.9) return 'high'
  if (score >= 0.7) return 'medium'
  return 'low'
}

async function editMetadata(book) {
  editingBook.value = book
  loadingMetadata.value = true

  try {
    const response = await fetch(`/api/metadata/book/${book.id}`)
    if (!response.ok) throw new Error('Failed to fetch metadata')

    const data = await response.json()

    if (data.status === 'success' && data.metadata) {
      const meta = data.metadata
      editForm.series_name = meta.series_name || ''
      editForm.volume_number = meta.volume_number
      editForm.title = meta.title || ''
      editForm.summary = meta.summary || ''
      editForm.writers = Array.isArray(meta.writers) ? meta.writers.join(', ') : (meta.writers || '')
      editForm.pencillers = Array.isArray(meta.pencillers) ? meta.pencillers.join(', ') : (meta.pencillers || '')
      editForm.inkers = Array.isArray(meta.inkers) ? meta.inkers.join(', ') : (meta.inkers || '')
      editForm.colorists = Array.isArray(meta.colorists) ? meta.colorists.join(', ') : (meta.colorists || '')
      editForm.publisher = meta.publisher || ''
      editForm.publication_date = meta.publication_date || ''
      editForm.isbn = meta.isbn || ''
      editForm.page_count = meta.page_count
      editForm.genres = Array.isArray(meta.genres) ? meta.genres.join(', ') : (meta.genres || '')
      editForm.tags = Array.isArray(meta.tags) ? meta.tags.join(', ') : (meta.tags || '')
    } else {
      // Pas de métadonnées, formulaire vide
      resetEditForm()
    }
  } catch (e) {
    console.error('Error loading metadata:', e)
    error.value = e.message
  } finally {
    loadingMetadata.value = false
  }
}

function resetEditForm() {
  editForm.series_name = ''
  editForm.volume_number = null
  editForm.title = ''
  editForm.summary = ''
  editForm.writers = ''
  editForm.pencillers = ''
  editForm.inkers = ''
  editForm.colorists = ''
  editForm.publisher = ''
  editForm.publication_date = ''
  editForm.isbn = ''
  editForm.page_count = null
  editForm.genres = ''
  editForm.tags = ''
}

async function saveMetadata() {
  if (!editingBook.value) return

  saving.value = true

  try {
    // Convertir les strings en arrays
    const payload = {
      book_id: editingBook.value.id,
      series_name: editForm.series_name,
      volume_number: editForm.volume_number || null,
      title: editForm.title || null,
      summary: editForm.summary || null,
      writers: editForm.writers ? editForm.writers.split(',').map(s => s.trim()).filter(s => s) : [],
      pencillers: editForm.pencillers ? editForm.pencillers.split(',').map(s => s.trim()).filter(s => s) : [],
      inkers: editForm.inkers ? editForm.inkers.split(',').map(s => s.trim()).filter(s => s) : [],
      colorists: editForm.colorists ? editForm.colorists.split(',').map(s => s.trim()).filter(s => s) : [],
      publisher: editForm.publisher || null,
      publication_date: editForm.publication_date || null,
      isbn: editForm.isbn || null,
      page_count: editForm.page_count || null,
      genres: editForm.genres ? editForm.genres.split(',').map(s => s.trim()).filter(s => s) : [],
      tags: editForm.tags ? editForm.tags.split(',').map(s => s.trim()).filter(s => s) : []
    }

    const response = await fetch('/api/metadata/manual', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(payload)
    })

    if (!response.ok) throw new Error('Failed to save metadata')

    const result = await response.json()
    console.log('Metadata saved:', result)

    // Recharger les livres
    await loadBooks()

    // Fermer le modal
    closeModal()
  } catch (e) {
    console.error('Error saving metadata:', e)
    error.value = e.message
  } finally {
    saving.value = false
  }
}

async function enrichBook(bookId) {
  enriching[bookId] = true

  try {
    const response = await fetch(`/api/metadata/match/${bookId}?auto_validate_threshold=0.80`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      }
    })

    if (!response.ok) throw new Error('Failed to enrich book')

    const result = await response.json()
    console.log('Enrichment result:', result)

    // Recharger les livres
    await loadBooks()
  } catch (e) {
    console.error('Error enriching book:', e)
    error.value = e.message
  } finally {
    enriching[bookId] = false
  }
}

async function enrichAllBooks() {
  try {
    enrichingAll.value = true
    enrichProgress.current = 0
    enrichProgress.total = 0
    enrichProgress.currentBook = ''

    // Récupérer tous les livres sans métadonnées
    const response = await fetch('/api/books/?has_metadata=false&limit=1000')
    if (!response.ok) throw new Error('Failed to fetch books')

    const data = await response.json()
    const booksToEnrich = data.books

    if (booksToEnrich.length === 0) {
      alert('Aucun livre à enrichir')
      return
    }

    enrichProgress.total = booksToEnrich.length

    // Enrichir les livres un par un
    for (const book of booksToEnrich) {
      enrichProgress.currentBook = book.filename

      try {
        const enrichResponse = await fetch(`/api/metadata/match/${book.id}?auto_validate_threshold=0.80`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          }
        })

        if (enrichResponse.ok) {
          console.log(`Book ${book.id} enriched successfully`)
        } else {
          console.error(`Failed to enrich book ${book.id}`)
        }
      } catch (e) {
        console.error(`Error enriching book ${book.id}:`, e)
      }

      enrichProgress.current++

      // Recharger les livres pour mettre à jour l'affichage
      await loadBooks()
    }

    alert(`Enrichissement terminé: ${enrichProgress.current}/${enrichProgress.total} livres traités`)
  } catch (e) {
    console.error('Error during batch enrichment:', e)
    error.value = e.message
  } finally {
    enrichingAll.value = false
    enrichProgress.current = 0
    enrichProgress.total = 0
    enrichProgress.currentBook = ''
  }
}

function closeModal() {
  editingBook.value = null
  resetEditForm()
}

onMounted(() => {
  loadBooks()
})
</script>

<style scoped>
.metadata h1 {
  margin-bottom: 2rem;
}

.filters {
  display: flex;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.search-input {
  flex: 1;
}

.select {
  padding: 0.5rem;
  border: 1px solid var(--border-color);
  border-radius: 4px;
  background: white;
}

.total-count {
  font-weight: bold;
  margin-bottom: 1rem;
  color: var(--secondary-color);
}

.no-results {
  text-align: center;
  padding: 3rem;
  color: #999;
  font-size: 1.1rem;
}

.metadata-table {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 1.5rem;
}

.metadata-table th {
  background: #f8f9fa;
  padding: 0.75rem;
  text-align: left;
}

.metadata-table th.sortable {
  cursor: pointer;
  user-select: none;
  position: relative;
  transition: background-color 0.2s;
}

.metadata-table th.sortable:hover {
  background: #e9ecef;
}

.sort-arrow {
  margin-left: 0.5rem;
  font-size: 0.875rem;
  color: var(--primary-color);
  font-weight: bold;
}

.metadata-table td {
  padding: 0.75rem;
  border-bottom: 1px solid var(--border-color);
}

.book-row:hover {
  background: #f8f9fa;
}

.filename {
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.confidence {
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.9rem;
  font-weight: bold;
}

.confidence.high {
  background: #d4edda;
  color: #155724;
}

.confidence.medium {
  background: #fff3cd;
  color: #856404;
}

.confidence.low {
  background: #f8d7da;
  color: #721c24;
}

.actions {
  white-space: nowrap;
}

.btn-small {
  padding: 0.4rem 0.8rem;
  font-size: 0.85rem;
}

.btn-primary {
  background: var(--primary-color);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #0056b3;
}

.btn-success {
  background: #28a745;
  color: white;
}

.btn-success:hover:not(:disabled) {
  background: #218838;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 1rem;
  margin-top: 1.5rem;
}

.page-info {
  font-weight: bold;
  color: var(--secondary-color);
}

/* Modal */
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

.modal {
  background: white;
  border-radius: 8px;
  max-width: 800px;
  width: 90%;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 1px solid var(--border-color);
}

.modal-header h2 {
  margin: 0;
  font-size: 1.5rem;
}

.btn-close {
  background: none;
  border: none;
  font-size: 2rem;
  cursor: pointer;
  color: #999;
  padding: 0;
  width: 2rem;
  height: 2rem;
  display: flex;
  align-items: center;
  justify-content: center;
}

.btn-close:hover {
  color: #333;
}

.modal-body {
  padding: 1.5rem;
}

.form-section {
  margin-bottom: 2rem;
}

.form-section h3 {
  margin-bottom: 1rem;
  font-size: 1.2rem;
  color: var(--secondary-color);
  border-bottom: 1px solid var(--border-color);
  padding-bottom: 0.5rem;
}

.form-group {
  margin-bottom: 1rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
  color: #333;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.input,
.textarea {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid var(--border-color);
  border-radius: 4px;
  font-size: 1rem;
}

.textarea {
  resize: vertical;
  font-family: inherit;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
  padding: 1.5rem;
  border-top: 1px solid var(--border-color);
}

.btn-secondary {
  background: #6c757d;
  color: white;
}

.btn-secondary:hover {
  background: #5a6268;
}

.enrichment-progress {
  margin-bottom: 1.5rem;
  padding: 1rem;
  background: #f8f9fa;
  border-radius: 4px;
  border-left: 4px solid var(--primary-color);
}

.progress-bar-container {
  width: 100%;
  height: 24px;
  background: #e9ecef;
  border-radius: 12px;
  overflow: hidden;
  margin-bottom: 0.5rem;
}

.progress-bar {
  height: 100%;
  background: linear-gradient(90deg, var(--primary-color), var(--accent-color));
  transition: width 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: 500;
  font-size: 0.875rem;
}

.progress-text {
  font-size: 0.9rem;
  color: #555;
}

.current-book {
  display: block;
  margin-top: 0.25rem;
  font-family: monospace;
  font-size: 0.85rem;
  color: #777;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.btn-success {
  background: #28a745;
  color: white;
  white-space: nowrap;
}

.btn-success:hover:not(:disabled) {
  background: #218838;
  opacity: 1;
}

.btn-success:disabled {
  background: #6c757d;
  opacity: 0.65;
  cursor: not-allowed;
}
</style>
