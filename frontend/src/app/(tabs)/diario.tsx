import { ScrollView, StyleSheet, Text } from 'react-native';
import DiaryScreen from '../../features/diary/DiaryScreen';
import { useThemeStyles } from '../../features/theme/ThemeContext';

export default function DiaryRoute() {
  const styles = useThemeStyles(baseStyles);

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
    >
      <DiaryScreen />

      <Text style={styles.disclaimer}>
        AICare · TCC · Dados demonstrativos
      </Text>
    </ScrollView>
  );
}

const baseStyles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F4FAFC',
  },
  content: {
    paddingHorizontal: 24,
    paddingTop: 24,
    paddingBottom: 22,
    gap: 24,
  },
  disclaimer: {
    color: '#8B9AA3',
    fontSize: 10,
    textAlign: 'center',
  },
});