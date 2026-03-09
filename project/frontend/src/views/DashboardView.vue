<script setup>
import { onMounted, ref } from "vue";

import http, { extractErrorMessage } from "../api/http";

const loading = ref(false);
const errorText = ref("");
const stats = ref({
  herbCount: 0,
  formulaCount: 0,
  stockCount: 0,
  warningCount: 0,
});
const records = ref([]);

function totalFrom(payload) {
  return payload?.count ?? (Array.isArray(payload) ? payload.length : 0);
}

function listFrom(payload) {
  return Array.isArray(payload) ? payload : payload?.results || [];
}

async function fetchDashboard() {
  loading.value = true;
  errorText.value = "";
  try {
    const [herbs, formulas, stocks, warnings, recordRows] = await Promise.all([
      http.get("/api/herbs/?page=1"),
      http.get("/api/formulas/?page=1"),
      http.get("/api/inventory/stocks/?page=1"),
      http.get("/api/inventory/warnings/?warning_status=active&page=1"),
      http.get("/api/inventory/records/?page=1"),
    ]);
    stats.value.herbCount = totalFrom(herbs.data);
    stats.value.formulaCount = totalFrom(formulas.data);
    stats.value.stockCount = totalFrom(stocks.data);
    stats.value.warningCount = totalFrom(warnings.data);
    records.value = listFrom(recordRows.data).slice(0, 8);
  } catch (error) {
    errorText.value = extractErrorMessage(error, "Failed to load dashboard.");
  } finally {
    loading.value = false;
  }
}

onMounted(fetchDashboard);
</script>

<template>
  <div class="view-grid">
    <div class="card">
      <h2>Dashboard Overview</h2>
      <p class="muted">Live status of herbs, formulas, stock, and warnings.</p>
      <p v-if="errorText" class="error-text">{{ errorText }}</p>
      <div class="kpi-grid">
        <article class="kpi">
          <span>Total Herbs</span>
          <strong>{{ stats.herbCount }}</strong>
        </article>
        <article class="kpi">
          <span>Total Formulas</span>
          <strong>{{ stats.formulaCount }}</strong>
        </article>
        <article class="kpi">
          <span>Stock Items</span>
          <strong>{{ stats.stockCount }}</strong>
        </article>
        <article class="kpi warn">
          <span>Active Warnings</span>
          <strong>{{ stats.warningCount }}</strong>
        </article>
      </div>
      <button class="btn btn-muted" @click="fetchDashboard" :disabled="loading">
        {{ loading ? "Refreshing..." : "Refresh Data" }}
      </button>
    </div>

    <div class="card">
      <h2>Recent Inventory Records</h2>
      <table class="table">
        <thead>
          <tr>
            <th>Time</th>
            <th>Herb</th>
            <th>Type</th>
            <th>Qty</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in records" :key="item.id">
            <td>{{ (item.created_at || "").replace("T", " ").slice(0, 16) }}</td>
            <td>{{ item.herb_name }}</td>
            <td>{{ item.record_type }}</td>
            <td>{{ item.quantity }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
