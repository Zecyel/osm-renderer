<script setup lang="ts">
import Leaflet from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { onMounted, ref } from 'vue';

const officialTile = 'https://tile.openstreetmap.org/{z}/{x}/{y}.png';
const myTile = window.location.origin + '/{z}/{x}/{y}.png';

const mapEl = ref<HTMLElement | null>(null);

onMounted(() => {
  const map = Leaflet.map(mapEl.value!).setView([31.3, 121.5], 13);
  Leaflet.tileLayer(myTile, {
    minZoom: 5,
    maxZoom: 18,
  }).addTo(map);
  map.addControl(Leaflet.control.scale());
})
</script>

<template>
  <div ref="mapEl" id="map" />
</template>

<style scoped>
#map {
  position: fixed;
  inset: 0;
}
</style>
