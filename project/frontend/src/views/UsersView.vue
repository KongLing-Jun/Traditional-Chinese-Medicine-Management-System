<script setup>
import { computed, onMounted, reactive, ref } from "vue";

import http, { extractErrorMessage } from "../api/http";
import { useAuthStore } from "../stores/auth";

const auth = useAuthStore();
const loading = ref(false);
const submitting = ref(false);
const errorText = ref("");
const rows = ref([]);
const roles = ref([]);
const editingId = ref(null);

const canCreate = computed(() => auth.hasPermission("user.create"));
const canUpdate = computed(() => auth.hasPermission("user.update"));
const canDelete = computed(() => auth.hasPermission("user.delete"));

const form = reactive({
  username: "",
  password: "",
  real_name: "",
  email: "",
  role: "",
  is_active: true,
});

function listFrom(payload) {
  return Array.isArray(payload) ? payload : payload?.results || [];
}

async function fetchUsers() {
  loading.value = true;
  errorText.value = "";
  try {
    const response = await http.get("/api/users/?ordering=-id");
    rows.value = listFrom(response.data);
  } catch (error) {
    errorText.value = extractErrorMessage(error, "Failed to load users.");
  } finally {
    loading.value = false;
  }
}

async function fetchRoles() {
  try {
    const response = await http.get("/api/roles/");
    roles.value = listFrom(response.data);
  } catch (error) {
    errorText.value = extractErrorMessage(error, "Failed to load roles.");
  }
}

function resetForm() {
  editingId.value = null;
  form.username = "";
  form.password = "";
  form.real_name = "";
  form.email = "";
  form.role = "";
  form.is_active = true;
}

function startEdit(row) {
  editingId.value = row.id;
  form.username = row.username;
  form.password = "";
  form.real_name = row.real_name || "";
  form.email = row.email || "";
  form.role = row.role || "";
  form.is_active = row.is_active;
}

async function submitForm() {
  submitting.value = true;
  errorText.value = "";
  try {
    if (editingId.value) {
      if (!canUpdate.value) throw new Error("No permission to update users.");
      const payload = {
        real_name: form.real_name,
        email: form.email,
        role: form.role || null,
        is_active: form.is_active,
      };
      if (form.password) payload.password = form.password;
      await http.patch(`/api/users/${editingId.value}/`, payload);
    } else {
      if (!canCreate.value) throw new Error("No permission to create users.");
      await http.post("/api/users/", {
        username: form.username,
        password: form.password,
        real_name: form.real_name,
        email: form.email,
        role: form.role || null,
        is_active: form.is_active,
      });
    }
    resetForm();
    await fetchUsers();
  } catch (error) {
    errorText.value = extractErrorMessage(error, "User operation failed.");
  } finally {
    submitting.value = false;
  }
}

async function toggleActive(row) {
  if (!canUpdate.value) return;
  try {
    await http.patch(`/api/users/${row.id}/`, { is_active: !row.is_active });
    await fetchUsers();
  } catch (error) {
    errorText.value = extractErrorMessage(error, "Failed to update user status.");
  }
}

async function removeUser(row) {
  if (!canDelete.value) return;
  if (!window.confirm(`Delete user "${row.username}"?`)) return;
  try {
    await http.delete(`/api/users/${row.id}/`);
    await fetchUsers();
  } catch (error) {
    errorText.value = extractErrorMessage(error, "Failed to delete user.");
  }
}

onMounted(async () => {
  await Promise.all([fetchRoles(), fetchUsers()]);
});
</script>

<template>
  <div class="view-grid">
    <div class="card">
      <div class="toolbar">
        <div>
          <h2>User Management</h2>
          <p class="muted">Create, update, disable, and delete users by role permissions.</p>
        </div>
        <button class="btn btn-muted" @click="fetchUsers" :disabled="loading">
          {{ loading ? "Refreshing..." : "Refresh" }}
        </button>
      </div>

      <p v-if="errorText" class="error-text">{{ errorText }}</p>

      <table class="table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Username</th>
            <th>Name</th>
            <th>Role</th>
            <th>Email</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in rows" :key="row.id">
            <td>{{ row.id }}</td>
            <td>{{ row.username }}</td>
            <td>{{ row.real_name || "-" }}</td>
            <td>{{ row.role_name || "-" }}</td>
            <td>{{ row.email || "-" }}</td>
            <td>{{ row.is_active ? "Active" : "Disabled" }}</td>
            <td class="row-actions">
              <button class="btn btn-muted" @click="startEdit(row)" :disabled="!canUpdate">Edit</button>
              <button class="btn btn-muted" @click="toggleActive(row)" :disabled="!canUpdate">
                {{ row.is_active ? "Disable" : "Enable" }}
              </button>
              <button class="btn btn-danger" @click="removeUser(row)" :disabled="!canDelete">Delete</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="card">
      <h2>{{ editingId ? `Edit User #${editingId}` : "Create User" }}</h2>
      <form class="inventory-form" @submit.prevent="submitForm">
        <label>
          <span>Username</span>
          <input v-model.trim="form.username" :disabled="Boolean(editingId)" required />
        </label>
        <label>
          <span>Password {{ editingId ? "(optional)" : "" }}</span>
          <input v-model="form.password" type="password" :required="!editingId" />
        </label>
        <label>
          <span>Real Name</span>
          <input v-model.trim="form.real_name" />
        </label>
        <label>
          <span>Email</span>
          <input v-model.trim="form.email" type="email" />
        </label>
        <label>
          <span>Role</span>
          <select v-model="form.role">
            <option value="">No role</option>
            <option v-for="role in roles" :key="role.id" :value="role.id">
              {{ role.role_name }} ({{ role.role_code }})
            </option>
          </select>
        </label>
        <label>
          <span>Status</span>
          <select v-model="form.is_active">
            <option :value="true">Active</option>
            <option :value="false">Disabled</option>
          </select>
        </label>
        <div class="row-actions">
          <button class="btn btn-primary" type="submit" :disabled="submitting">
            {{ submitting ? "Submitting..." : editingId ? "Save Changes" : "Create User" }}
          </button>
          <button class="btn btn-muted" type="button" @click="resetForm">Reset</button>
        </div>
      </form>
    </div>
  </div>
</template>
