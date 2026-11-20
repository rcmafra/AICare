
import { ScrollView } from 'react-native';
import MedicinesScreen from '../../features/medications/MedicinesScreen';
import { useTheme } from '../../features/theme/ThemeContext';

export default function MedicamentosRoute() {
  const { colors } = useTheme();

  return (
    <ScrollView
      style={{ flex: 1, backgroundColor: colors.background }}
      contentContainerStyle={{ padding: 24, paddingBottom: 40 }}
    >
      <MedicinesScreen />
    </ScrollView>
  );
}
