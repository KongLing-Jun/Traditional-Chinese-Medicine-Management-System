<script setup>
import { computed, onMounted, reactive, ref } from "vue";

import http, { extractErrorMessage } from "../api/http";
import { useAuthStore } from "../stores/auth";

const auth = useAuthStore();
const loading = ref(false);
const submitting = ref(false);
const errorText = ref("");
const keyword = ref("");
const rows = ref([]);
const editingId = ref(null);

const canCreate = computed(() => auth.hasPermission("herb.create"));
const canUpdate = computed(() => auth.hasPermission("herb.update"));
const canDelete = computed(() => auth.hasPermission("herb.delete"));

const form = reactive({
  herb_code: "",
  herb_name: "",
  category: "",
  nature_taste: "",
  meridian_tropism: "",
  efficacy: "",
  indication: "",
  unit: "g",
  reference_price: "0.00",
  status: "enabled",
});

function listFrom(payload) {
  return Array.isArray(payload) ? payload : payload?.results || [];
}

async function fetchHerbs() {
  loading.value = true;
  errorText.value = "";
  try {
    const params = new URLSearchParams();
    if (keyword.value) params.set("search", keyword.value);
    const query = params.toString();
    const response = await http.get(`/api/herbs/${query ? `?${query}` : ""}`);
    rows.value = listFrom(response.data);
  } catch (error) {
    errorText.value = extractErrorMessage(error, "Failed to load herbs.");
  } finally {
    loading.value = false;
  }
}

function resetForm() {
  editingId.value = null;
  form.herb_code = "";
  form.herb_name = "";
  form.category = "";
  form.nature_taste = "";
  form.meridian_tropism = "";
  form.efficacy = "";
  form.indication = "";
  form.unit = "g";
  form.reference_price = "0.00";
  form.status = "enabled";
}

function startEdit(row) {
  editingId.value = row.id;
  form.herb_code = row.herb_code;
  form.herb_name = row.herb_name;
  form.category = row.category || "";
  form.nature_taste = row.nature_taste || "";
  form.meridian_tropism = row.meridian_tropism || "";
  form.efficacy = row.efficacy || "";
  form.indication = row.indication || "";
  form.unit = row.unit || "g";
  form.reference_price = String(row.reference_price ?? "0.00");
  form.status = row.status || "enabled";
}

async function submitForm() {
  submitting.value = true;
  errorText.value = "";
  try {
    const payload = {
      herb_code: form.herb_code,
      herb_name: form.herb_name,
      category: form.category,
      nature_taste: form.nature_taste,
      meridian_tropism: form.meridian_tropism,
      efficacy: form.efficacy,
      indication: form.indication,
      unit: form.unit,
      reference_price: form.reference_price,
      status: form.status,
    };
    if (editingId.value) {
      if (!canUpdate.value) throw new Error("No permission to update herbs.");
      await http.put(`/api/herbs/${editingId.value}/`, payload);
    } else {
      if (!canCreate.value) throw new Error("No permission to create herbs.");
      await http.post("/api/herbs/", payload);
    }
    resetForm();
    await fetchHerbs();
  } catch (error) {
    errorText.value = extractErrorMessage(error, "Herb operation failed.");
  } finally {
    submitting.value = false;
  }
}

async function removeHerb(row) {
  if (!canDelete.value) return;
  if (!window.confirm(`Delete herb "${row.herb_name}"?`)) return;
  try {
    await http.delete(`/api/herbs/${row.id}/`);
    await fetchHerbs();
  } catch (error) {
    errorText.value = extractErrorMessage(error, "Failed to delete herb.");
  }
}

onMounted(fetchHerbs);
</script>

<template>
  <div class="view-grid">
    <div class="card">
      <div class="toolbar">
        <div>
          <h2>Herb Management</h2>
          <p class="muted">Search and maintain herb master data.</p>
        </div>
        <div class="toolbar-right">
          <input v-model.trim="keyword" placeholder="Search herb name/code" @keyup.enter="fetchHerbs" />
          <button class="btn btn-muted" @click="fetchHerbs" :disabled="loading">
            {{ loading ? "Searching..." : "Search" }}
          </button>
        </div>
      </div>

      <p v-if="errorText" class="error-text">{{ errorText }}</p>
      <table class="table">
        <thead>
          <tr>
            <th>Code</th>
            <th>Name</th>
            <th>Category</th>
            <th>Nature/Taste</th>
            <th>Unit</th>
            <th>Ref Price</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in rows" :key="item.id">
            <td>{{ item.herb_code }}</td>
            <td>{{ item.herb_name }}</td>
            <td>{{ item.category }}</td>
            <td>{{ item.nature_taste || "-" }}</td>
            <td>{{ item.unit }}</td>
            <td>{{ item.reference_price }}</td>
            <td>{{ item.status }}</td>
            <td class="row-actions">
              <button class="btn btn-muted" @click="startEdit(item)" :disabled="!canUpdate">Edit</button>
              <button class="btn btn-danger" @click="removeHerb(item)" :disabled="!canDelete">Delete</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="card">
      <h2>{{ editingId ? `Edit Herb #${editingId}` : "Create Herb" }}</h2>
      <form class="inventory-form" @submit.prevent="submitForm">
        <label>
          <span>Herb Code</span>
          <input v-model.trim="form.herb_code" :disabled="Boolean(editingId)" required />
        </label>
        <label>
          <span>Herb Name</span>
          <input v-model.trim="form.herb_name" required />
        </label>
        <label>
          <span>Category</span>
          <input v-model.trim="form.category" required />
        </label>
        <label>
          <span>Nature/Taste</span>
          <input v-model.trim="form.nature_taste" />
        </label>
        <label>
          <span>Meridian</span>
          <input v-model.trim="form.meridian_tropism" />
        </label>
        <label>
          <span>Efficacy</span>
          <textarea v-model.trim="form.efficacy"></textarea>
        </label>
        <label>
          <span>Indication</span>
          <textarea v-model.trim="form.indication"></textarea>
        </label>
        <label>
          <span>Unit</span>
          <input v-model.trim="form.unit" />
        </label>
        <label>
          <span>Reference Price</span>
          <input v-model.trim="form.reference_price" type="number" min="0" step="0.01" />
        </label>
        <label>
          <span>Status</span>
          <select v-model="form.status">
            <option value="enabled">enabled</option>
            <option value="disabled">disabled</option>
          </select>
        </label>
        <div class="row-actions">
          <button class="btn btn-primary" :disabled="submitting">
            {{ submitting ? "Submitting..." : editingId ? "Save Changes" : "Create Herb" }}
          </button>
          <button class="btn btn-muted" type="button" @click="resetForm">Reset</button>
        </div>
      </form>
    </div>
  </div>
</template>
