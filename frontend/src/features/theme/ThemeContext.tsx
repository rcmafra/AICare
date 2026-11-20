import {
  createContext,
  useContext,
  useCallback,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react';
import { useColorScheme } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import AsyncStorage from '@react-native-async-storage/async-storage';

type ThemeColors = {
  background: string;
  surface: string;
  surfaceAlt: string;
  text: string;
  muted: string;
  border: string;
  primary: string;
  primarySurface: string;
  successSurface: string;
  warningSurface: string;
  dangerSurface: string;
};

type ThemeValue = {
  isDark: boolean;
  colors: ThemeColors;
  themePreference: ThemePreference;
  themePreferenceLoaded: boolean;
  setThemePreference: (preference: ThemePreference) => Promise<void>;
};

export type ThemePreference = 'system' | 'light' | 'dark';

const THEME_PREFERENCE_KEY = '@aicare/theme-preference';

const LIGHT_COLORS: ThemeColors = {
  background: '#F4FAFC',
  surface: '#FFFFFF',
  surfaceAlt: '#F1F7F9',
  text: '#102F40',
  muted: '#6D8794',
  border: '#D8E3E8',
  primary: '#50A9C3',
  primarySurface: '#E8F6FA',
  successSurface: '#E5F5EC',
  warningSurface: '#FFF3DF',
  dangerSurface: '#FCE9E7',
};

const DARK_COLORS: ThemeColors = {
  background: '#0B1522',
  surface: '#162334',
  surfaceAlt: '#1D2D40',
  text: '#EAF0F6',
  muted: '#A8B6C5',
  border: '#334457',
  primary: '#50A9C3',
  primarySurface: '#193545',
  successSurface: '#173C2F',
  warningSurface: '#49371F',
  dangerSurface: '#482A2A',
};

const DARK_BACKGROUNDS: Record<string, string> = {
  '#f5fafc': DARK_COLORS.background,
  '#f4fafc': DARK_COLORS.background,
  '#f5f8f8': DARK_COLORS.background,
  '#ffffff': DARK_COLORS.surface,
  '#f1f7f9': DARK_COLORS.surfaceAlt,
  '#f1f5f6': DARK_COLORS.surfaceAlt,
  '#f4f8f9': DARK_COLORS.surfaceAlt,
  '#f8fafc': DARK_COLORS.surfaceAlt,
  '#edf4f4': DARK_COLORS.surfaceAlt,
  '#edf7f5': DARK_COLORS.surfaceAlt,
  '#e8f0f3': DARK_COLORS.surfaceAlt,
  '#e8f6fa': DARK_COLORS.primarySurface,
  '#eaf5f8': DARK_COLORS.primarySurface,
  '#ddf1ed': DARK_COLORS.primarySurface,
  '#e5f3f6': DARK_COLORS.primarySurface,
  '#f0f8fa': DARK_COLORS.primarySurface,
  '#e5f5ec': DARK_COLORS.successSurface,
  '#fff3df': DARK_COLORS.warningSurface,
  '#fff1df': DARK_COLORS.warningSurface,
  '#fff2d9': DARK_COLORS.warningSurface,
  '#fff8e8': DARK_COLORS.warningSurface,
  '#e5f2f7': DARK_COLORS.primarySurface,
  '#fce9e7': DARK_COLORS.dangerSurface,
  '#eeeeee': '#344459',
  'rgba(16, 47, 64, 0.75)': 'rgba(0, 0, 0, 0.82)',
  'rgba(16, 47, 64, 0.8)': 'rgba(0, 0, 0, 0.85)',
  'rgba(7, 30, 42, 0.48)': 'rgba(0, 0, 0, 0.72)',
};

const DARK_TEXT: Record<string, string> = {
  '#102f40': DARK_COLORS.text,
  '#0a293a': '#F3F7FA',
  '#183b45': DARK_COLORS.text,
  '#334155': DARK_COLORS.text,
  '#6d8794': DARK_COLORS.muted,
  '#64748b': DARK_COLORS.muted,
  '#8b9aa3': DARK_COLORS.muted,
  '#94a3b8': DARK_COLORS.muted,
  '#9aaeb7': DARK_COLORS.muted,
  '#27845a': '#7BD1A8',
  '#25865b': '#7BD1A8',
  '#b65b43': '#ED9C83',
  '#b64c42': '#F0877B',
  '#94651b': '#E8BE72',
  '#946200': '#E8BE72',
  '#a66a20': '#E8BE72',
  '#3676a8': '#82B8E5',
  '#287d94': '#79C6D8',
  '#b54a4a': '#F28A8A',
  '#805b16': '#E7C77E',
  '#b66a43': '#E3A783',
};

const DARK_BORDERS: Record<string, string> = {
  '#d8e3e8': DARK_COLORS.border,
  '#d5e8e4': DARK_COLORS.border,
  '#e2e8f0': DARK_COLORS.border,
  '#cbd5e1': DARK_COLORS.border,
  '#c8e3eb': DARK_COLORS.border,
  '#e5b6a8': '#79493F',
};

const ThemeContext = createContext<ThemeValue | null>(null);

function mapStyleColors(style: object): object {
  return Object.fromEntries(
    Object.entries(style).map(([property, value]) => {
      if (typeof value !== 'string') return [property, value];

      const normalizedValue = value.toLowerCase();
      if (property === 'backgroundColor') {
        return [
          property,
          DARK_BACKGROUNDS[normalizedValue] ?? value,
        ];
      }
      if (property === 'borderColor') {
        return [property, DARK_BORDERS[normalizedValue] ?? value];
      }
      if (property === 'color') {
        return [property, DARK_TEXT[normalizedValue] ?? value];
      }
      return [property, value];
    }),
  );
}

export function ThemeProvider({ children }: { children: ReactNode }) {
  const colorScheme = useColorScheme();
  const [themePreference, setThemePreferenceState] =
    useState<ThemePreference>('system');
  const [themePreferenceLoaded, setThemePreferenceLoaded] = useState(false);

  useEffect(() => {
    let active = true;

    const loadThemePreference = async () => {
      try {
        const savedPreference = await AsyncStorage.getItem(
          THEME_PREFERENCE_KEY,
        );

        if (
          savedPreference === 'system' ||
          savedPreference === 'light' ||
          savedPreference === 'dark'
        ) {
          if (active) setThemePreferenceState(savedPreference);
        } else if (savedPreference !== null) {
          console.warn('A preferência de tema salva é inválida.');
        }
      } catch (error) {
        console.error('Não foi possível carregar a preferência de tema.', error);
      } finally {
        if (active) setThemePreferenceLoaded(true);
      }
    };

    void loadThemePreference();
    return () => {
      active = false;
    };
  }, []);

  const setThemePreference = useCallback(
    async (preference: ThemePreference) => {
      await AsyncStorage.setItem(THEME_PREFERENCE_KEY, preference);
      setThemePreferenceState(preference);
    },
    [],
  );

  const isDark =
    themePreference === 'system'
      ? colorScheme === 'dark'
      : themePreference === 'dark';
  const colors = isDark ? DARK_COLORS : LIGHT_COLORS;
  const value = useMemo(
    () => ({
      isDark,
      colors,
      themePreference,
      themePreferenceLoaded,
      setThemePreference,
    }),
    [
      isDark,
      colors,
      themePreference,
      themePreferenceLoaded,
      setThemePreference,
    ],
  );

  return (
    <ThemeContext.Provider value={value}>
      <StatusBar style={isDark ? 'light' : 'dark'} />
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme deve ser usado dentro de ThemeProvider.');
  }
  return context;
}

export function useThemeStyles<T extends Record<string, object>>(
  styles: T,
): T {
  const { isDark } = useTheme();

  return useMemo(() => {
    if (!isDark) return styles;

    return Object.fromEntries(
      Object.entries(styles).map(([name, style]) => [
        name,
        mapStyleColors(style),
      ]),
    ) as T;
  }, [isDark, styles]);
}
