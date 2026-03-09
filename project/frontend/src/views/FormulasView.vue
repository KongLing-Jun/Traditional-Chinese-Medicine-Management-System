<script setup>
import { computed, onMounted, reactive, ref } from "vue";

import http, { extractErrorMessage } from "../api/http";
import { useAuthStore } from "../stores/auth";

const auth = useAuthStore();
const loading = ref(false);
const submitting = ref(false);
const errorText = ref("");
const rows = ref([]);
const herbs = ref([]);
const editingId = ref(null);

const canCreate = computed(() => auth.hasPermission("formula.create"));
const canUpdate = computed(() => auth.hasPermission("formula.update"));
const canDelete = computed(() => auth.hasPermission("formula.delete"));

const form = reactive({
  formula_code: "",
  formula_name: "",
  source: "",
  efficacy: "",
  indication: "",
  usage_method: "",
  contraindication: "",
  status: "enabled",
  items: [],
});

function listFrom(payload) {
  return Array.isArray(payload) ? payload : payload?.results || [];
}

function emptyItem() {
  return {
    herb: "",
    dosage: "1.00",
    dosage_unit: "g",
    role_in_formula: "",
    sort_no: form.items.length + 1,
    remark: "",
  };
}

async function fetchFormulas() {
  loading.value = true;
  errorText.value = "";
  try {
    const response = await http.get("/api/formulas/?ordering=-id");
    rows.value = listFrom(response.data);
  } catch (error) {
    errorText.value = extractErrorMessage(error, "Failed to load formulas.");
  } finally {
    loading.value = false;
  }
}

async function fetchHerbs() {
  try {
    const response = await http.get("/api/herbs/?page_size=200");
    herbs.value = listFrom(response.data);
  } catch (error) {
    errorText.value = extractErrorMessage(error, "Failed to load herb list.");
  }
}

function resetForm() {
  editingId.value = null;
  form.formula_code = "";
  form.formula_name = "";
  form.source = "";
  form.efficacy = "";
  form.indication = "";
  form.usage_method = "";
  form.contraindication = "";
  form.status = "enabled";
  form.items = [emptyItem()];
}

function startEdit(row) {
  editingId.value = row.id;
  form.formula_code = row.formula_code || "";
  form.formula_name = row.formula_name || "";
  form.source = row.source || "";
  form.efficacy = row.efficacy || "";
  form.indication = row.indication || "";
  form.usage_method = row.usage_method || "";
  form.contraindication = row.contraindication || "";
  form.status = row.status || "enabled";
  form.items = (row.items_detail || []).map((item, index) => ({
    herb: String(item.herb),
    dosage: String(item.dosage),
    dosage_unit: item.dosage_unit || "g",
    role_in_formula: item.role_in_formula || "",
    sort_no: item.sort_no || index + 1,
    remark: item.remark || "",
  }));
  if (form.items.length === 0) form.items = [emptyItem()];
}

function addItem() {
  form.items.push(emptyItem());
}

function removeItem(index) {
  form.items.splice(index, 1);
  if (form.items.length === 0) form.items.push(emptyItem());
}

async function submitForm() {
  submitting.value = true;
  errorText.value = "";
  try {
    const payload = {
      formula_code: form.formula_code,
      formula_name: form.formula_name,
      source: form.source,
      efficacy: form.efficacy,
      indication: form.indication,
      usage_method: form.usage_method,
      contraindication: form.contraindication,
      status: form.status,
      items: form.items
        .filter((item) => item.herb && item.dosage)
        .map((item, index) => ({
          herb: Number(item.herb),
          dosage: item.dosage,
          dosage_unit: item.dosage_unit || "g",
          role_in_formula: item.role_in_formula || "",
          sort_no: Number(item.sort_no || index + 1),
          remark: item.remark || "",
        })),
    };
    if (editingId.value) {
      if (!canUpdate.value) throw new Error("No permission to update formulas.");
      await http.put(`/api/formulas/${editingId.value}/`, payload);
    } else {
      if (!canCreate.value) throw new Error("No permission to create formulas.");
      await http.post("/api/formulas/", payload);
    }
    resetForm();
    await fetchFormulas();
  } catch (error) {
    errorText.value = extractErrorMessage(error, "Formula operation failed.");
  } finally {
    submitting.value = false;
  }
}

async function removeFormula(row) {
  if (!canDelete.value) return;
  if (!window.confirm(`Delete formula "${row.formula_name}"?`)) return;
  try {
    await http.delete(`/api/formulas/${row.id}/`);
    await fetchFormulas();
  } catch (error) {
    errorText.value = extractErrorMessage(error, "Failed to delete formula.");
  }
}

onMounted(async () => {
  await Promise.all([fetchHerbs(), fetchFormulas()]);
  resetForm();
});
</script>

<template>
  <div class="view-grid">
    <div class="card">
      <div class="toolbar">
        <div>
          <h2>Formula Management</h2>
          <p class="muted">Maintain formulas and herb composition details.</p>
        </div>
        <button class="btn btn-muted" @click="fetchFormulas" :disabled="loading">
          {{ loading ? "Refreshing..." : "Refresh" }}
        </button>
      </div>
      <p v-if="errorText" class="error-text">{{ errorText }}</p>

      <div class="formula-list">
        <article v-for="item in rows" :key="item.id" class="formula-card">
          <h3>{{ item.formula_name }} <small>{{ item.formula_code }}</small></h3>
          <p><strong>Source:</strong> {{ item.source || "-" }}</p>
          <p><strong>Efficacy:</strong> {{ item.efficacy || "-" }}</p>
          <p><strong>Indication:</strong> {{ item.indication || "-" }}</p>
          <p>
            <strong>Items:</strong>
            {{
              (item.items_detail || [])
                .map((x) => `${x.herb_name} ${x.dosage}${x.dosage_unit}`)
                .join(", ") || "-"
            }}
          </p>
          <div class="row-actions">
            <button class="btn btn-muted" @click="startEdit(item)" :disabled="!canUpdate">Edit</button>
            <button class="btn btn-danger" @click="removeFormula(item)" :disabled="!canDelete">Delete</button>
          </div>
        </article>
      </div>
    </div>

    <div class="card">
      <h2>{{ editingId ? `Edit Formula #${editingId}` : "Create Formula" }}</h2>
      <form class="inventory-form" @submit.prevent="submitForm">
        <label>
          <span>Formula Code</span>
          <input v-model.trim="form.formula_code" :disabled="Boolean(editingId)" required />
        </label>
        <label>
          <span>Formula Name</span>
          <input v-model.trim="form.formula_name" required />
        </label>
        <label>
          <span>Source</span>
          <input v-model.trim="form.source" />
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
          <span>Usage</span>
          <textarea v-model.trim="form.usage_method"></textarea>
        </label>
        <label>
          <span>Contraindication</span>
          <textarea v-model.trim="form.contraindication"></textarea>
        </label>
        <label>
          <span>Status</span>
          <select v-model="form.status">
            <option value="enabled">enabled</option>
            <option value="disabled">disabled</option>
          </select>
        </label>

        <h3>Composition</h3>
        <div v-for="(item, index) in form.items" :key="index" class="compose-row">
          <select v-model="item.herb">
            <option value="">Select herb</option>
            <option v-for="herb in herbs" :key="herb.id" :value="String(herb.id)">
              {{ herb.herb_name }} ({{ herb.herb_code }})
            </option>
          </select>
          <input v-model.trim="item.dosage" type="number" min="0.01" step="0.01" placeholder="Dosage" />
          <input v-model.trim="item.dosage_unit" placeholder="Unit" />
          <input v-model.trim="item.role_in_formula" placeholder="Role (jun/chen/zuo/shi)" />
          <button class="btn btn-danger" type="button" @click="removeItem(index)">Remove</button>
        </div>
        <button class="btn btn-muted" type="button" @click="addItem">Add Herb Item</button>

        <div class="row-actions">
          <button class="btn btn-primary" :disabled="submitting">
            {{ submitting ? "Submitting..." : editingId ? "Save Changes" : "Create Formula" }}
          </button>
          <button class="btn btn-muted" type="button" @click="resetForm">Reset</button>
        </div>
      </form>
    </div>
  </div>
</template>
