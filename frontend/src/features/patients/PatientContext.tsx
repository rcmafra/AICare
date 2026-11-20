import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from 'react';
import { useAuth } from '../auth/AuthContext';
import { ApiError, deletePatientFromApi, fetchPatient, savePatientToApi } from '../../../api';

export type Patient = {
  id: string;
  familyId: string;
  name: string;
  birthDate: string;
  relationship: string;
  notes: string;
  createdAt: string;
  updatedAt: string;
};

export type PatientDraft = {
  name: string;
  birthDate: string;
  relationship: string;
  notes: string;
};

type PatientContextData = {
  patient: Patient | null;
  loading: boolean;
  savePatient: (data: PatientDraft) => Promise<Patient>;
  deletePatient: () => Promise<void>;
};

const PatientContext = createContext<PatientContextData | undefined>(undefined);

export function PatientProvider({ children }: { children: React.ReactNode }) {
  const { user, loading: authLoading } = useAuth();
  const [patient, setPatient] = useState<Patient | null>(null);
  const [loading, setLoading] = useState(true);
  const familyId = user?.familyId;

  const refreshPatient = useCallback(async () => {
    if (authLoading) return;
    if (!familyId) {
      setPatient(null);
      setLoading(false);
      return;
    }

    setLoading(true);
    try {
      setPatient(await fetchPatient(familyId));
    } catch (error) {
      if (error instanceof ApiError && error.status === 404) {
        setPatient(null);
      } else {
        setPatient(null);
        console.error('Erro ao carregar paciente:', error);
      }
    } finally {
      setLoading(false);
    }
  }, [authLoading, familyId]);

  useEffect(() => {
    const timer = setTimeout(() => {
      void refreshPatient();
    }, 0);
    return () => clearTimeout(timer);
  }, [refreshPatient]);

  const savePatient = useCallback(
    async (data: PatientDraft) => {
      if (!familyId) throw new Error('Família não identificada.');
      const savedPatient = await savePatientToApi({
        familyId,
        name: data.name,
        birthDate: data.birthDate,
        relationship: data.relationship,
        notes: data.notes,
      });
      setPatient(savedPatient);
      return savedPatient;
    },
    [familyId],
  );

  const deletePatient = useCallback(async () => {
    if (!familyId) throw new Error('Família não identificada.');
    await deletePatientFromApi(familyId);
    setPatient(null);
  }, [familyId]);

  return (
    <PatientContext.Provider
      value={{ patient, loading: loading || authLoading, savePatient, deletePatient }}
    >
      {children}
    </PatientContext.Provider>
  );
}

export function usePatient() {
  const context = useContext(PatientContext);
  if (!context) {
    throw new Error('usePatient deve ser utilizado dentro de PatientProvider.');
  }
  return context;
}
