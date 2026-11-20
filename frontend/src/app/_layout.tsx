
import { Stack } from 'expo-router';
import { AuthProvider } from '../features/auth/AuthContext';
import { PatientProvider } from '../features/patients/PatientContext';
import { MedicationProvider } from '../features/medications/MedicationContext';
import { ThemeProvider, useTheme } from '../features/theme/ThemeContext';

function AppStack() {
  const { colors } = useTheme();

  return (
    <Stack
      screenOptions={{
        headerShown: false,
        contentStyle: { backgroundColor: colors.background },
      }}
    >
      <Stack.Screen name="index" />
      <Stack.Screen name="(auth)" />
      <Stack.Screen name="(tabs)" />
      <Stack.Screen
        name="assistente-medicamentos"
        options={{ presentation: 'card' }}
      />
    </Stack>
  );
}

export default function RootLayout() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <PatientProvider>
          <MedicationProvider>
            <AppStack />
          </MedicationProvider>
        </PatientProvider>
      </AuthProvider>
    </ThemeProvider>
  );
}
