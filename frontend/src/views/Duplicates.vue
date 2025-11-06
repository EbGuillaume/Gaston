<template>
  <div class="duplicates">
    <h1>🔄 Doublons</h1>

    <div class="card">
      <h2>Gestion des doublons</h2>

      <div class="placeholder">
        <p>🚧 Détection et comparaison des doublons à venir</p>
        <ul style="text-align: left; max-width: 500px; margin: 1rem auto;">
          <li>Détection par hash MD5</li>
          <li>Comparaison format et taille</li>
          <li>Priorité: CBZ > CBR > PDF</li>
          <li>Sélection intelligente du meilleur fichier</li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script setup>
// Duplicates detection component
</script>

<style scoped>
.duplicates h1 {
  margin-bottom: 2rem;
}

.placeholder {
  text-align: center;
  padding: 3rem;
  color: #999;
  font-size: 1.1rem;
}

.placeholder ul {
  margin-top: 1rem;
  line-height: 2;
}
</style>
