import AsyncStorage from '@react-native-async-storage/async-storage';
import Constants from 'expo-constants';
import { Platform } from 'react-native';

const configuredApiUrl = process.env.EXPO_PUBLIC_API_URL;
const expoHostUri = Constants.expoConfig?.hostUri;
const developmentApiUrl = __DEV__ && expoHostUri
  ? (() => {
      const url = new URL(`http://${expoHostUri}`);
      url.port = '8000';
      return url.origin;
    })()
  : null;

export const API_URL = (
  configuredApiUrl ||
  developmentApiUrl ||
  (Platform.OS === 'android'
    ? 'http://10.0.2.2:8000'
    : 'http://localhost:8000')
).replace(/\/+$/, '');
const API_TOKEN_KEY = '@aicare:api-token';
let apiToken: string | null = null;

export async function setApiToken(token: string | null) {
  apiToken = token;
  if (token) {
    await AsyncStorage.setItem(API_TOKEN_KEY, token);
  } else {
    await AsyncStorage.removeItem(API_TOKEN_KEY);
  }
}

export async function getStoredApiToken() {
  apiToken = await AsyncStorage.getItem(API_TOKEN_KEY);
  return apiToken;
}

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

async function request<T>(
  path: string,
  init?: RequestInit,
): Promise<T> {
  let response: Response;

  try {
    const token = apiToken ?? await AsyncStorage.getItem(API_TOKEN_KEY);
    apiToken = token;
    response = await fetch(`${API_URL}${path}`, {
      ...init,
      headers: {
        ...(init?.body ? { 'Content-Type': 'application/json' } : {}),
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...init?.headers,
      },
    });
  } catch (error) {
    const message =
      error instanceof Error ? error.message : 'Falha de conexão com a API.';
    throw new ApiError(message, 0);
  }

  if (!response.ok) {
    const responseText = await response.text();
    let message = responseText || `Erro HTTP ${response.status}`;

    try {
      const body = JSON.parse(responseText) as { detail?: string };
      message = body.detail || message;
    } catch {
      // Mantém a resposta textual quando ela não contém JSON.
    }

    throw new ApiError(message, response.status);
  }

  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

function familyPath(familyId: string) {
  return `/families/${encodeURIComponent(familyId)}`;
}

export function registerWithApi(data: {
  name: string;
  email: string;
  password: string;
  inviteCode?: string;
  id?: string;
}) {
  return request<ApiSession>('/auth/register', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export function loginWithApi(email: string, password: string) {
  return request<ApiSession>('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  });
}

export function validateApiSession() {
  return request<{ user: ApiSession['user'] }>('/auth/session');
}

export type ApiSession = {
  user: {
    id: string;
    name: string;
    email: string;
    role: 'Familiar' | 'Administrador';
    familyId: string;
    inviteCode?: string;
  };
  accessToken: string;
};

export function logoutFromApi() {
  return request<void>('/auth/logout', { method: 'POST' });
}

export function fetchPatient(familyId: string) {
  return request<{
    id: string;
    familyId: string;
    name: string;
    birthDate: string;
    relationship: string;
    notes: string;
    createdAt: string;
    updatedAt: string;
  }>(`${familyPath(familyId)}/patient`);
}

export function savePatientToApi(patient: {
  familyId: string;
  name: string;
  birthDate: string;
  relationship: string;
  notes: string;
}) {
  return request<{
    id: string;
    familyId: string;
    name: string;
    birthDate: string;
    relationship: string;
    notes: string;
    createdAt: string;
    updatedAt: string;
  }>(`${familyPath(patient.familyId)}/patient`, {
    method: 'PUT',
    body: JSON.stringify(patient),
  });
}

export function deletePatientFromApi(familyId: string) {
  return request<void>(`${familyPath(familyId)}/patient`, {
    method: 'DELETE',
  });
}

export type ApiInvite = {
  id: string;
  code: string;
  role: 'Familiar' | 'Administrador';
  createdAt: string;
  expiresAt: string;
  status:
    | 'Pendente'
    | 'Revogado'
    | 'accepted'
    | 'aceito'
    | 'utilizado'
    | 'used';
  name: string;
  familyId?: string;
};

export function fetchInvites(familyId: string) {
  return request<ApiInvite[]>(`${familyPath(familyId)}/invites`);
}

export function createInviteOnApi(
  familyId: string,
  invite: Pick<ApiInvite, 'role' | 'name'>,
) {
  return request<ApiInvite>(`${familyPath(familyId)}/invites`, {
    method: 'POST',
    body: JSON.stringify(invite),
  });
}

export function updateInviteOnApi(
  familyId: string,
  inviteId: string,
  status: string,
) {
  const query = new URLSearchParams({ status }).toString();
  return request<ApiInvite>(
    `${familyPath(familyId)}/invites/${encodeURIComponent(inviteId)}?${query}`,
    { method: 'PATCH' },
  );
}

export type ApiMedicine = {
  id: string;
  [key: string]: unknown;
};

export function fetchMedicines<T extends { id: string } = ApiMedicine>(
  familyId: string,
) {
  return request<T[]>(
    `${familyPath(familyId)}/medications`,
  );
}

export function createMedicineOnApi<T extends { id: string }>(
  familyId: string,
  medicine: Omit<T, 'id'>,
) {
  return request<T>(`${familyPath(familyId)}/medications`, {
    method: 'POST',
    body: JSON.stringify(medicine),
  });
}

export function updateMedicineOnApi<T extends { id: string }>(
  familyId: string,
  medicineId: string,
  medicine: T,
) {
  return request<T>(
    `${familyPath(familyId)}/medications/${encodeURIComponent(medicineId)}`,
    { method: 'PUT', body: JSON.stringify(medicine) },
  );
}

export function deleteMedicineFromApi(
  familyId: string,
  medicineId: string,
) {
  return request<void>(
    `${familyPath(familyId)}/medications/${encodeURIComponent(medicineId)}`,
    { method: 'DELETE' },
  );
}

export function toggleMedicineOnApi(familyId: string, medicineId: string) {
  return request<ApiMedicine>(
    `${familyPath(familyId)}/medications/${encodeURIComponent(medicineId)}/toggle`,
    { method: 'POST' },
  );
}

export function fetchMedicationState<
  DoseRecordType extends object = Record<string, unknown>,
  MovementType extends object = Record<string, unknown>,
>(familyId: string) {
  return request<{
    doseRecords: DoseRecordType[];
    inventoryMovements: MovementType[];
  }>(`${familyPath(familyId)}/medication-state`);
}

export function fetchMedicationSchedule<T>(
  familyId: string,
  date: string,
  timezone: string,
) {
  const query = new URLSearchParams({ date, timezone }).toString();
  return request<T[]>(
    `${familyPath(familyId)}/medication-schedule?${query}`,
  );
}

export function administerDoseOnApi(
  familyId: string,
  doseId: string,
  date: string,
  timezone: string,
) {
  return request<{ doseId: string }>(
    `${familyPath(familyId)}/medication-doses/administer`,
    {
      method: 'POST',
      body: JSON.stringify({ doseId, date, timezone }),
    },
  );
}

export function undoDoseOnApi(familyId: string, doseId: string) {
  return request<{ doseId: string }>(
    `${familyPath(familyId)}/medication-doses/undo`,
    {
      method: 'POST',
      body: JSON.stringify({ doseId }),
    },
  );
}

export function replenishMedicationStockOnApi(
  familyId: string,
  medicineId: string,
  quantity: number,
  description?: string,
) {
  return request<ApiMedicine>(
    `${familyPath(familyId)}/medications/${encodeURIComponent(medicineId)}/replenishments`,
    {
      method: 'POST',
      body: JSON.stringify({ quantity, description: description ?? '' }),
    },
  );
}

export type MedicationAssistantStep =
  | 'medication'
  | 'startDate'
  | 'continuous'
  | 'endDate'
  | 'stockQuantity'
  | 'stockUnit'
  | 'unitsPerDose'
  | 'minimumStock'
  | 'instructions'
  | 'finished';

export function processMedicationAssistantAnswer<Draft>(
  familyId: string,
  step: MedicationAssistantStep,
  answer: string,
  draft: Draft,
) {
  return request<{
    step: MedicationAssistantStep;
    draft: Draft;
    assistantText: string;
  }>(`${familyPath(familyId)}/medication-assistant/answer`, {
    method: 'POST',
    body: JSON.stringify({ step, answer, draft }),
  });
}

export type ApiDiaryRecord = {
  date: string;
  observation: string;
  createdAt: string;
  updatedAt?: string | null;
  imageData?: string | null;
  timezone: string;
};

export function fetchDiaryRecords(familyId: string) {
  return request<ApiDiaryRecord[]>(`${familyPath(familyId)}/diary`);
}

export function fetchDiaryPhotoStatus(familyId: string, recordDate: string) {
  return request<{ hasPhoto: boolean }>(
    `${familyPath(familyId)}/diary/${encodeURIComponent(recordDate)}/photo`,
  );
}

export function saveDiaryRecordToApi(
  familyId: string,
  record: ApiDiaryRecord,
) {
  return request<ApiDiaryRecord>(
    `${familyPath(familyId)}/diary/${encodeURIComponent(record.date)}`,
    {
      method: 'PUT',
      body: JSON.stringify(record),
    },
  );
}

export function deleteDiaryRecordFromApi(
  familyId: string,
  recordDate: string,
) {
  return request<void>(
    `${familyPath(familyId)}/diary/${encodeURIComponent(recordDate)}`,
    { method: 'DELETE' },
  );
}
