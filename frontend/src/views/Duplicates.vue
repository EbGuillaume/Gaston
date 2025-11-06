<template>
  <div class="duplicates">
    <h1>🔄 Doublons</h1>

    <div class="card">
      <h2>Gestion intelligente des doublons</h2>

      <div class="info-box success">
        <h3>✅ Système actif</h3>
        <p>Le système de gestion des doublons est <strong>opérationnel</strong> !</p>
      </div>

      <div class="features">
        <h3>Fonctionnalités implémentées:</h3>
        <ul>
          <li>✅ <strong>Détection automatique</strong> lors du scan (hash MD5)</li>
          <li>✅ <strong>Comparaison intelligente</strong> des formats et tailles</li>
          <li>✅ <strong>Priorité des formats:</strong> CBZ (meilleur) > CBR > PDF</li>
          <li>✅ <strong>Sélection automatique</strong> du fichier optimal lors de l'organisation</li>
          <li>✅ <strong>Pas de doublons</strong> dans la bibliothèque organisée</li>
        </ul>
      </div>

      <div class="placeholder">
        <p>🚧 Interface de visualisation et gestion manuelle à venir</p>
        <p style="font-size: 0.9rem; margin-top: 1rem;">
          Le système fonctionne automatiquement en arrière-plan.<br/>
          Une interface de gestion sera ajoutée dans une future mise à jour.
        </p>
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

.info-box {
  padding: 1.5rem;
  border-radius: 8px;
  margin-bottom: 2rem;
  text-align: center;
}

.info-box.success {
  background: #e8f5e9;
  border: 2px solid var(--success-color);
}

.info-box h3 {
  margin: 0 0 0.5rem 0;
  color: var(--success-color);
}

.info-box p {
  margin: 0;
  color: #2d5016;
}

.features {
  margin-bottom: 2rem;
}

.features h3 {
  margin-bottom: 1rem;
  color: var(--secondary-color);
}

.features ul {
  list-style: none;
  padding: 0;
}

.features li {
  padding: 0.75rem;
  margin-bottom: 0.5rem;
  background: #f8f9fa;
  border-left: 4px solid var(--success-color);
  border-radius: 4px;
}

.placeholder {
  text-align: center;
  padding: 2rem;
  color: #999;
  background: #f8f9fa;
  border-radius: 8px;
}

.placeholder p {
  margin-bottom: 0.5rem;
}
</style>
