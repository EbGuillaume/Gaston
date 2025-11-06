import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useLibraryStore = defineStore('library', () => {
  // State
  const books = ref([])
  const stats = ref({
    total_books: 0,
    books_with_metadata: 0,
    total_size_bytes: 0,
    by_extension: {}
  })
  const loading = ref(false)
  const error = ref(null)

  // Getters
  const totalBooks = computed(() => stats.value.total_books)
  const booksWithMetadata = computed(() => stats.value.books_with_metadata)

  // Actions
  async function fetchStats() {
    loading.value = true
    error.value = null
    try {
      const response = await fetch('/api/organize/stats')
      if (!response.ok) throw new Error('Failed to fetch stats')
      stats.value = await response.json()
    } catch (e) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  async function fetchBooks() {
    loading.value = true
    error.value = null
    try {
      const response = await fetch('/api/books')
      if (!response.ok) throw new Error('Failed to fetch books')
      books.value = await response.json()
    } catch (e) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  async function scanDirectory(path) {
    loading.value = true
    error.value = null
    try {
      const response = await fetch('/api/scan/directory', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path, save_to_db: true })
      })
      if (!response.ok) throw new Error('Failed to scan directory')
      return await response.json()
    } catch (e) {
      error.value = e.message
      throw e
    } finally {
      loading.value = false
    }
  }

  function scanDirectoryStream(path, callbacks) {
    const eventSource = new EventSource(`/api/scan/directory-stream?path=${encodeURIComponent(path)}&save_to_db=true`)

    eventSource.addEventListener('message', (event) => {
      const data = JSON.parse(event.data)

      switch (data.type) {
        case 'status':
          callbacks.onStatus?.(data.message)
          break
        case 'found':
          callbacks.onFound?.(data.total)
          break
        case 'progress':
          callbacks.onProgress?.(data.current, data.total, data.filename)
          break
        case 'complete':
          callbacks.onComplete?.(data)
          eventSource.close()
          break
        case 'error':
          callbacks.onError?.(data.message)
          eventSource.close()
          break
      }
    })

    eventSource.onerror = (err) => {
      console.error('EventSource error:', err)
      callbacks.onError?.('Connection lost')
      eventSource.close()
    }

    return eventSource
  }

  return {
    // State
    books,
    stats,
    loading,
    error,
    // Getters
    totalBooks,
    booksWithMetadata,
    // Actions
    fetchStats,
    fetchBooks,
    scanDirectory,
    scanDirectoryStream
  }
})
