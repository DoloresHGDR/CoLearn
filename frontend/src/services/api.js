import AsyncStorage from "@react-native-async-storage/async-storage";

// Cambiar por la IP local si se prueba en un dispositivo físico
const BASE_URL = "http://127.0.0.1:8000";

// Obtiene el token guardado y arma los headers de autenticación
async function authHeaders() {
  const token = await AsyncStorage.getItem("token");
  return {
    Authorization: `Bearer ${token}`,
    "Content-Type": "application/json",
  };
}

// Llamada GET autenticada
async function get(path) {
  const headers = await authHeaders();
  const res = await fetch(`${BASE_URL}${path}`, { headers });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Error en la solicitud");
  return data;
}

// Llamada POST autenticada con cuerpo JSON
async function post(path, body) {
  const headers = await authHeaders();
  const res = await fetch(`${BASE_URL}${path}`, {
    method: "POST",
    headers,
    body: JSON.stringify(body),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Error en la solicitud");
  return data;
}

// Llamada POST con FormData (para subir archivos)
async function postForm(path, formData) {
  const token = await AsyncStorage.getItem("token");
  const res = await fetch(`${BASE_URL}${path}`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: formData,
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Error en la solicitud");
  return data;
}

// --- Autenticación ---

export async function register(name, email, password, role) {
  const res = await fetch(`${BASE_URL}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, email, password, role }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Error al registrarse");
  return data;
}

export async function login(email, password) {
  const res = await fetch(`${BASE_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Email o contraseña incorrectos");
  return data;
}

export async function getMe() {
  return get("/auth/me");
}

// --- Clases ---

export async function getClasses() {
  return get("/classes");
}

export async function createClass(name, level, focuses, fileUri, fileName, fileType) {
  const formData = new FormData();
  formData.append("name", name);
  formData.append("level", level);
  focuses.forEach((f) => formData.append("focuses", f));
  formData.append("file", { uri: fileUri, name: fileName, type: fileType });
  return postForm("/classes", formData);
}

export async function joinClass(joinCode) {
  const formData = new FormData();
  formData.append("join_code", joinCode);
  return postForm("/classes/join", formData);
}

// --- Chat ---

export async function sendMessage(classId, message) {
  return post(`/classes/${classId}/chat`, { message });
}

export async function getChatHistory(classId) {
  return get(`/classes/${classId}/chat`);
}

// --- Preguntas y evaluación ---

export async function getQuestions(classId) {
  return get(`/classes/${classId}/questions`);
}

export async function submitAnswer(classId, questionId, answer) {
  return post(`/classes/${classId}/questions/${questionId}/answer`, { answer });
}

// --- Métricas ---

export async function getMetrics(classId) {
  return get(`/classes/${classId}/metrics`);
}
