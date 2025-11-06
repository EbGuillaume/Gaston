<template>
  <div class="library">
    <h1>📚 Bibliothèque</h1>

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

        <select v-model="filterDuplicate" class="select" @change="loadBooks">
          <option :value="null">Tous</option>
          <option :value="false">Non-doublons</option>
          <option :value="true">Doublons</option>
        </select>
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

        <table v-else class="books-table">
          <thead>
            <tr>
              <th>#</th>
              <th>Fichier</th>
              <th>Série</th>
              <th>Volume</th>
              <th>Titre</th>
              <th>Éditeur</th>
              <th>Taille</th>
              <th>Confiance</th>
              <th>Statut</th>
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
              <td>{{ formatSize(book.file_size) }}</td>
              <td>
                <span v-if="book.confidence_score" class="confidence" :class="getConfidenceClass(book.confidence_score)">
                  {{ (book.confidence_score * 100).toFixed(0) }}%
                </span>
                <span v-else>-</span>
              </td>
              <td>
                <span v-if="book.has_metadata" class="badge badge-success">✓ Métadonnées</span>
                <span v-else class="badge badge-warning">⚠ Aucune</span>
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
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'

const books = ref([])
const totalBooks = ref(0)
const loading = ref(false)
const error = ref(null)
const searchQuery = ref('')
const filterMetadata = ref(null)
const filterDuplicate = ref(null)

const limit = 50
const currentPage = ref(1)

const totalPages = computed(() => Math.ceil(totalBooks.value / limit))

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

    if (filterDuplicate.value !== null) {
      params.append('is_duplicate', filterDuplicate.value)
    }

    if (searchQuery.value) {
      params.append('search', searchQuery.value)
    }

    const response = await fetch(`/api/books?${params}`)
    if (!response.ok) throw new Error('Failed to fetch books')

    const data = await response.json()
    books.value = data.books
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

function formatSize(bytes) {
  if (!bytes) return '-'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i]
}

function getConfidenceClass(score) {
  if (score >= 0.9) return 'high'
  if (score >= 0.7) return 'medium'
  return 'low'
}

onMounted(() => {
  loadBooks()
})
</script>

<style scoped>
.library h1 {
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

.books-table {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 1.5rem;
}

.books-table th {
  background: #f8f9fa;
  padding: 0.75rem;
  text-align: left;
  font-weight: bold;
  border-bottom: 2px solid var(--border-color);
}

.books-table td {
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

.badge {
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.85rem;
  font-weight: bold;
}

.badge-success {
  background: #d4edda;
  color: #155724;
}

.badge-warning {
  background: #fff3cd;
  color: #856404;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 1rem;
  margin-top: 1.5rem;
}

.btn-small {
  padding: 0.5rem 1rem;
  font-size: 0.9rem;
}

.page-info {
  font-weight: bold;
  color: var(--secondary-color);
}
</style>
