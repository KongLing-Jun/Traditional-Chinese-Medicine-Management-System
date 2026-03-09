<script setup>
import { reactive, ref } from "vue";
import { useRouter } from "vue-router";

import { extractErrorMessage } from "../api/http";
import { useAuthStore } from "../stores/auth";

const router = useRouter();
const auth = useAuthStore();
const loading = ref(false);
const errorText = ref("");

const form = reactive({
  username: "admin",
  password: "admin123456",
});

async function onSubmit() {
  loading.value = true;
  errorText.value = "";
  try {
    await auth.login(form.username, form.password);
    router.push({ name: "dashboard" });
  } catch (error) {
    errorText.value = extractErrorMessage(error, "Login failed. Please check username/password.");
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <div class="login-page">
    <div class="login-card card">
      <div class="login-header">
        <h1>TCM Management System</h1>
        <p>Login with JWT and load role-based menus from backend.</p>
      </div>
      <form @submit.prevent="onSubmit" class="login-form">
        <label>
          <span>Username</span>
          <input v-model.trim="form.username" autocomplete="username" />
        </label>
        <label>
          <span>Password</span>
          <input v-model="form.password" type="password" autocomplete="current-password" />
        </label>
        <p v-if="errorText" class="error-text">{{ errorText }}</p>
        <button class="btn btn-primary" type="submit" :disabled="loading">
          {{ loading ? "Signing in..." : "Sign In" }}
        </button>
      </form>
    </div>
  </div>
</template>
