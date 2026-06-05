import AsyncStorage from "@react-native-async-storage/async-storage";

// IP local de la PC — debe coincidir con la IP en la red del celular
export const BASE_URL = "http://192.168.0.111:8000";

// Timeout por defecto — operaciones pesadas (subir archivo, generar con IA) usan TIMEOUT_LONG
const TIMEOUT_MS = 10000;
const TIMEOUT_LONG = 90000;

// Fetch con timeout — lanza error si no responde en el tiempo dado
async function fetchWithTimeout(url, options = {}, timeoutMs = TIMEOUT_MS) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const res = await fetch(url, { ...options, signal: controller.signal });
    return res;
  } catch (e) {
    if (e.name === "AbortError") throw new Error("El servidor no responde. Verificá tu conexión.");
    throw e;
  } finally {
    clearTimeout(timer);
  }
}

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
  const res = await fetchWithTimeout(`${BASE_URL}${path}`, { headers });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Error en la solicitud");
  return data;
}

// Llamada POST autenticada con cuerpo JSON
async function post(path, body) {
  const headers = await authHeaders();
  const res = await fetchWithTimeout(`${BASE_URL}${path}`, {
    method: "POST",
    headers,
    body: JSON.stringify(body),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Error en la solicitud");
  return data;
}

// Llamada POST con FormData — timeout extendido por procesamiento de IA
async function postForm(path, formData) {
  const token = await AsyncStorage.getItem("token");
  const res = await fetchWithTimeout(`${BASE_URL}${path}`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: formData,
  }, TIMEOUT_LONG);
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Error en la solicitud");
  return data;
}

// --- Autenticación ---

export async function register(name, email, password, role) {
  const res = await fetchWithTimeout(`${BASE_URL}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, email, password, role }),
  });
  const data = await res.json();
  if (!res.ok) {
    // FastAPI puede devolver detail como string o como lista de errores de validación
    const detail = Array.isArray(data.detail)
      ? data.detail.map((e) => e.msg).join(", ")
      : data.detail;
    throw new Error(detail || "Error al registrarse");
  }
  return data;
}

export async function login(email, password) {
  const res = await fetchWithTimeout(`${BASE_URL}/auth/login`, {
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
  // El chat llama a OpenRouter — puede tardar más que el timeout por defecto
  const headers = await authHeaders();
  const res = await fetchWithTimeout(`${BASE_URL}/classes/${classId}/chat`, {
    method: "POST",
    headers,
    body: JSON.stringify({ message }),
  }, TIMEOUT_LONG);
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Error en la solicitud");
  return data;
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

// Eliminar clase (solo docente — cascade para todos)
export async function deleteClass(classId) {
  const headers = await authHeaders();
  const res = await fetchWithTimeout(`${BASE_URL}/classes/${classId}`, { method: "DELETE", headers });
  if (!res.ok) {
    const data = await res.json();
    throw new Error(data.detail || "Error al eliminar la clase");
  }
}

// Alumno sale de una clase
export async function leaveClass(classId) {
  const headers = await authHeaders();
  const res = await fetchWithTimeout(`${BASE_URL}/classes/${classId}/leave`, { method: "DELETE", headers });
  if (!res.ok) {
    const data = await res.json();
    throw new Error(data.detail || "Error al salir de la clase");
  }
}

// Progreso propio del alumno (para dificultad adaptativa)
export async function getMyProgress(classId) {
  return get(`/classes/${classId}/my-progress`);
}

// Preguntas únicas generadas para la clase (solo docente)
export async function getTeacherQuestions(classId) {
  return get(`/classes/${classId}/teacher-questions`);
}

// Devuelve la URL y headers para descargar el archivo de la clase
export async function getClassFile(classId) {
  const token = await AsyncStorage.getItem("token");
  const uri = `${BASE_URL}/classes/${classId}/file`;
  return { uri, headers: { Authorization: `Bearer ${token}` } };
}
