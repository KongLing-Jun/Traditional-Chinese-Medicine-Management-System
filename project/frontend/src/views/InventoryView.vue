<script setup>
import { onMounted, reactive, ref } from "vue";

import http, { extractErrorMessage } from "../api/http";

const loading = ref(false);
const submitting = ref(false);
const errorText = ref("");
const stocks = ref([]);
const warnings = ref([]);
const records = ref([]);

const actionForm = reactive({
  herb_id: "",
  quantity: "",
  type: "inbound",
  remark: "",
});

const recordFilters = reactive({
  record_type: "",
  herb: "",
});

function listFrom(payload) {
  return Array.isArray(payload) ? payload : payload?.results || [];
}

async function fetchInventory() {
  loading.value = true;
  errorText.value = "";
  try {
    const [stockRes, warningRes] = await Promise.all([
      http.get("/api/inventory/stocks/"),
      http.get("/api/inventory/warnings/?warning_status=active"),
    ]);
    stocks.value = listFrom(stockRes.data);
    warnings.value = listFrom(warningRes.data);
    if (!actionForm.herb_id && stocks.value.length > 0) {
      actionForm.herb_id = String(stocks.value[0].herb);
    }
    if (!recordFilters.herb && stocks.value.length > 0) {
      recordFilters.herb = String(stocks.value[0].herb);
    }
  } catch (error) {
    errorText.value = extractErrorMessage(error, "Failed to load inventory.");
  } finally {
    loading.value = false;
  }
}

async function fetchRecords() {
  try {
    const params = new URLSearchParams();
    if (recordFilters.record_type) params.set("record_type", recordFilters.record_type);
    if (recordFilters.herb) params.set("herb", recordFilters.herb);
    const query = params.toString();
    const response = await http.get(`/api/inventory/records/${query ? `?${query}` : ""}`);
    records.value = listFrom(response.data);
  } catch (error) {
    errorText.value = extractErrorMessage(error, "Failed to load inventory records.");
  }
}

async function submitAction() {
  submitting.value = true;
  errorText.value = "";
  try {
    let endpoint = "/api/inventory/inbound/";
    let payload = {
      herb_id: actionForm.herb_id,
      quantity: actionForm.quantity,
      remark: actionForm.remark,
    };
    if (actionForm.type === "outbound") {
      endpoint = "/api/inventory/outbound/";
    } else if (actionForm.type === "check") {
      endpoint = "/api/inventory/check/";
      payload = {
        herb_id: actionForm.herb_id,
        checked_quantity: actionForm.quantity,
        remark: actionForm.remark,
      };
    }
    await http.post(endpoint, payload);
    actionForm.quantity = "";
    actionForm.remark = "";
    await Promise.all([fetchInventory(), fetchRecords()]);
  } catch (error) {
    errorText.value = extractErrorMessage(error, "Inventory action failed.");
  } finally {
    submitting.value = false;
  }
}

onMounted(async () => {
  await fetchInventory();
  await fetchRecords();
});
</script>

<template>
  <div class="view-grid">
    <div class="card">
      <div class="toolbar">
        <div>
          <h2>Inventory Management</h2>
          <p class="muted">Track stock levels, warnings, and inbound/outbound/check actions.</p>
        </div>
        <button class="btn btn-muted" @click="fetchInventory" :disabled="loading">
          {{ loading ? "Refreshing..." : "Refresh" }}
        </button>
      </div>
      <p v-if="errorText" class="error-text">{{ errorText }}</p>
      <table class="table">
        <thead>
          <tr>
            <th>Herb</th>
            <th>Current</th>
            <th>Safe</th>
            <th>Location</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in stocks" :key="item.id">
            <td>{{ item.herb_name }} ({{ item.herb_code }})</td>
            <td>{{ item.current_quantity }} {{ item.unit }}</td>
            <td>{{ item.safe_quantity }} {{ item.unit }}</td>
            <td>{{ item.warehouse_location || "-" }}</td>
            <td>{{ item.stock_status }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="card">
      <h2>Stock Action</h2>
      <form class="inventory-form" @submit.prevent="submitAction">
        <label>
          <span>Action Type</span>
          <select v-model="actionForm.type">
            <option value="inbound">Inbound</option>
            <option value="outbound">Outbound</option>
            <option value="check">Stock Check</option>
          </select>
        </label>
        <label>
          <span>Herb</span>
          <select v-model="actionForm.herb_id">
            <option v-for="item in stocks" :key="item.herb" :value="String(item.herb)">
              {{ item.herb_name }} ({{ item.herb_code }})
            </option>
          </select>
        </label>
        <label>
          <span>{{ actionForm.type === "check" ? "Checked Quantity" : "Quantity" }}</span>
          <input v-model.trim="actionForm.quantity" type="number" min="0.01" step="0.01" required />
        </label>
        <label>
          <span>Remark</span>
          <input v-model.trim="actionForm.remark" />
        </label>
        <button class="btn btn-primary" type="submit" :disabled="submitting || !actionForm.herb_id">
          {{ submitting ? "Submitting..." : "Submit" }}
        </button>
      </form>

      <h3>Active Low-Stock Warnings</h3>
      <ul class="warning-list">
        <li v-for="item in warnings" :key="item.id">
          {{ item.herb_name }}: current {{ item.current_quantity }} / safe {{ item.safe_quantity }}
        </li>
        <li v-if="warnings.length === 0">No active warnings.</li>
      </ul>
    </div>

    <div class="card">
      <div class="toolbar">
        <h2>Inventory Records</h2>
        <div class="toolbar-right">
          <select v-model="recordFilters.record_type">
            <option value="">All types</option>
            <option value="inbound">Inbound</option>
            <option value="outbound">Outbound</option>
            <option value="check">Check</option>
          </select>
          <select v-model="recordFilters.herb">
            <option value="">All herbs</option>
            <option v-for="item in stocks" :key="item.herb" :value="String(item.herb)">
              {{ item.herb_name }}
            </option>
          </select>
          <button class="btn btn-muted" @click="fetchRecords">Filter</button>
        </div>
      </div>

      <table class="table">
        <thead>
          <tr>
            <th>Time</th>
            <th>Herb</th>
            <th>Type</th>
            <th>Before</th>
            <th>After</th>
            <th>Operator</th>
            <th>Remark</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in records" :key="item.id">
            <td>{{ (item.created_at || "").replace("T", " ").slice(0, 19) }}</td>
            <td>{{ item.herb_name }}</td>
            <td>{{ item.record_type }}</td>
            <td>{{ item.before_quantity }}</td>
            <td>{{ item.after_quantity }}</td>
            <td>{{ item.operator_name || "-" }}</td>
            <td>{{ item.remark || "-" }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
