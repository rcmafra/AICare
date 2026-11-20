import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from 'react';
import {
  administerDoseOnApi,
  createMedicineOnApi,
  deleteMedicineFromApi,
  fetchMedicationSchedule,
  fetchMedicationState,
  fetchMedicines,
  replenishMedicationStockOnApi,
  toggleMedicineOnApi,
  undoDoseOnApi,
  updateMedicineOnApi,
} from '../../../api';
import { useAuth } from '../auth/AuthContext';
import type {
  DoseRecord,
  InventoryMovement,
  Medicine,
  MedicineDose,
  MedicineDraft,
} from '../../types/medication';

type MedicationContextData = {
  medicines: Medicine[];
  doseRecords: DoseRecord[];
  inventoryMovements: InventoryMovement[];
  todayDoses: MedicineDose[];
  loading: boolean;
  refreshMedicines: () => Promise<void>;
  addMedicine: (draft: MedicineDraft) => Promise<void>;
  updateMedicine: (id: string, draft: MedicineDraft) => Promise<void>;
  deleteMedicine: (id: string) => Promise<void>;
  toggleMedicine: (id: string) => Promise<void>;
  administerDose: (doseId: string) => Promise<void>;
  undoDose: (doseId: string) => Promise<void>;
  replenishStock: (
    medicineId: string,
    quantity: number,
    description?: string,
  ) => Promise<void>;
};

const MedicationContext = createContext<MedicationContextData | undefined>(
  undefined,
);

function getTodayKey() {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, '0');
  const day = String(now.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

function getTimeZone() {
  return Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC';
}

export function MedicationProvider({ children }: { children: ReactNode }) {
  const { user, loading: authLoading } = useAuth();
  const familyId = user?.familyId;
  const [medicines, setMedicines] = useState<Medicine[]>([]);
  const [doseRecords, setDoseRecords] = useState<DoseRecord[]>([]);
  const [inventoryMovements, setInventoryMovements] = useState<InventoryMovement[]>([]);
  const [todayDoses, setTodayDoses] = useState<MedicineDose[]>([]);
  const [loading, setLoading] = useState(true);

  const refreshMedicines = useCallback(async () => {
    if (authLoading) return;
    if (!familyId) {
      setMedicines([]);
      setDoseRecords([]);
      setInventoryMovements([]);
      setTodayDoses([]);
      setLoading(false);
      return;
    }

    setLoading(true);
    try {
      const [medicationList, medicationState, schedule] = await Promise.all([
        fetchMedicines<Medicine>(familyId),
        fetchMedicationState<DoseRecord, InventoryMovement>(familyId),
        fetchMedicationSchedule<MedicineDose>(
          familyId,
          getTodayKey(),
          getTimeZone(),
        ),
      ]);
      setMedicines(medicationList);
      setDoseRecords(medicationState.doseRecords);
      setInventoryMovements(medicationState.inventoryMovements);
      setTodayDoses(schedule);
    } catch (error) {
      setMedicines([]);
      setDoseRecords([]);
      setInventoryMovements([]);
      setTodayDoses([]);
      throw error;
    } finally {
      setLoading(false);
    }
  }, [authLoading, familyId]);

  useEffect(() => {
    const timer = setTimeout(() => {
      void refreshMedicines().catch((error: unknown) => {
        console.error('Erro ao carregar medicamentos:', error);
      });
    }, 0);
    return () => clearTimeout(timer);
  }, [refreshMedicines]);

  const requireFamily = () => {
    if (!familyId) throw new Error('Nenhum acompanhamento está selecionado.');
    return familyId;
  };

  const addMedicine = async (draft: MedicineDraft) => {
    const activeFamilyId = requireFamily();
    const medicine: Omit<Medicine, 'id'> = {
      ...draft,
      active: true,
      administered: false,
    };
    await createMedicineOnApi<Medicine>(activeFamilyId, {
      ...medicine,
    });
    await refreshMedicines();
  };

  const updateMedicine = async (id: string, draft: MedicineDraft) => {
    const activeFamilyId = requireFamily();
    const currentMedicine = medicines.find((medicine) => medicine.id === id);
    if (!currentMedicine) throw new Error('Medicamento não encontrado.');
    await updateMedicineOnApi(activeFamilyId, id, {
      ...currentMedicine,
      ...draft,
    });
    await refreshMedicines();
  };

  const deleteMedicine = async (id: string) => {
    await deleteMedicineFromApi(requireFamily(), id);
    await refreshMedicines();
  };

  const toggleMedicine = async (id: string) => {
    const activeFamilyId = requireFamily();
    await toggleMedicineOnApi(activeFamilyId, id);
    await refreshMedicines();
  };

  const administerDose = async (doseId: string) => {
    await administerDoseOnApi(
      requireFamily(),
      doseId,
      getTodayKey(),
      getTimeZone(),
    );
    await refreshMedicines();
  };

  const undoDose = async (doseId: string) => {
    await undoDoseOnApi(requireFamily(), doseId);
    await refreshMedicines();
  };

  const replenishStock = async (
    medicineId: string,
    quantity: number,
    description?: string,
  ) => {
    await replenishMedicationStockOnApi(
      requireFamily(),
      medicineId,
      quantity,
      description,
    );
    await refreshMedicines();
  };

  return (
    <MedicationContext.Provider
      value={{
        medicines,
        doseRecords,
        inventoryMovements,
        todayDoses,
        loading,
        refreshMedicines,
        addMedicine,
        updateMedicine,
        deleteMedicine,
        toggleMedicine,
        administerDose,
        undoDose,
        replenishStock,
      }}
    >
      {children}
    </MedicationContext.Provider>
  );
}

export function useMedications() {
  const context = useContext(MedicationContext);
  if (!context) {
    throw new Error('useMedications deve ser usado dentro de MedicationProvider.');
  }
  return context;
}
