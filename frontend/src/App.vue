<template>
  <div id="app">
    <nav class="navbar">
      <div class="navbar-brand">
        <h1>📚 Gaston</h1>
        <p>Smart Comic Library</p>
      </div>
      <div class="navbar-menu">
        <router-link to="/">Dashboard</router-link>
        <router-link to="/scanner">Scanner</router-link>
        <router-link to="/library">Bibliothèque</router-link>
        <router-link to="/duplicates">Doublons</router-link>
        <router-link to="/metadata">Métadonnées</router-link>
      </div>
    </nav>

    <main class="container">
      <router-view />
    </main>
  </div>
</template>

<script setup>
// App root component
</script>

<style scoped>
.navbar {
  background: #2c3e50;
  color: white;
  padding: 1rem 2rem;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.navbar-brand h1 {
  margin: 0;
  font-size: 1.8rem;
}

.navbar-brand p {
  margin: 0;
  font-size: 0.9rem;
  opacity: 0.8;
}

.navbar-menu {
  display: flex;
  gap: 1rem;
  margin-top: 1rem;
}

.navbar-menu a {
  color: white;
  text-decoration: none;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  transition: background 0.3s;
}

.navbar-menu a:hover {
  background: rgba(255,255,255,0.1);
}

.navbar-menu a.router-link-active {
  background: #42b983;
}

.container {
  max-width: 1200px;
  margin: 2rem auto;
  padding: 0 2rem;
}
</style>
