/**
 * Theme detector that determines the current season/festivity theme
 * based on the current date
 */

export type ThemeName = 
  | 'halloween' 
  | 'christmas' 
  | 'valentines' 
  | 'easter' 
  | 'summer' 
  | 'autumn' 
  | 'winter' 
  | 'spring'
  | 'default';

export interface SeasonalTheme {
  name: ThemeName;
  displayName: string;
  primary: string;
  secondary: string;
  accent: string;
  background: string;
  paper: string;
  emoji: string;
}

/**
 * Get the current theme based on today's date
 */
export function getCurrentTheme(): SeasonalTheme {
  const now = new Date();
  const month = now.getMonth(); // 0-11
  const day = now.getDate();

  // Halloween (October 1-31)
  if (month === 9) {
    return {
      name: 'halloween',
      displayName: 'Halloween',
      primary: '#ff6b35',
      secondary: '#8b4513',
      accent: '#ff9500',
      background: '#1a0f0a',
      paper: '#2d1810',
      emoji: '🎃'
    };
  }

  // Christmas (December 1-26)
  if (month === 11 && day <= 26) {
    return {
      name: 'christmas',
      displayName: 'Christmas',
      primary: '#c41e3a',
      secondary: '#165b33',
      accent: '#ffd700',
      background: '#0a1214',
      paper: '#1a2428',
      emoji: '🎄'
    };
  }

  // Valentine's Day (February 10-14)
  if (month === 1 && day >= 10 && day <= 14) {
    return {
      name: 'valentines',
      displayName: "Valentine's Day",
      primary: '#ff1493',
      secondary: '#c71585',
      accent: '#ff69b4',
      background: '#1a0a14',
      paper: '#2d1428',
      emoji: '💝'
    };
  }

  // Easter (April 1-20 approximately)
  if (month === 3 && day <= 20) {
    return {
      name: 'easter',
      displayName: 'Easter',
      primary: '#9b59b6',
      secondary: '#3498db',
      accent: '#f1c40f',
      background: '#0f0a1a',
      paper: '#1d1428',
      emoji: '🐰'
    };
  }

  // Summer (June-August)
  if (month >= 5 && month <= 7) {
    return {
      name: 'summer',
      displayName: 'Summer',
      primary: '#ffa500',
      secondary: '#00ced1',
      accent: '#ffff00',
      background: '#0a1419',
      paper: '#14282d',
      emoji: '☀️'
    };
  }

  // Autumn (September-October, excluding October for Halloween)
  if (month === 8) {
    return {
      name: 'autumn',
      displayName: 'Autumn',
      primary: '#d2691e',
      secondary: '#8b4513',
      accent: '#ff8c00',
      background: '#120f0a',
      paper: '#241e14',
      emoji: '🍂'
    };
  }

  // Winter (January-February, excluding Valentine's)
  if (month <= 1 && !(month === 1 && day >= 10 && day <= 14)) {
    return {
      name: 'winter',
      displayName: 'Winter',
      primary: '#5dade2',
      secondary: '#3498db',
      accent: '#aed6f1',
      background: '#0a1219',
      paper: '#14242d',
      emoji: '❄️'
    };
  }

  // Spring (March-May, excluding Easter)
  if ((month >= 2 && month <= 4) && !(month === 3 && day <= 20)) {
    return {
      name: 'spring',
      displayName: 'Spring',
      primary: '#2ecc71',
      secondary: '#27ae60',
      accent: '#f1c40f',
      background: '#0a190f',
      paper: '#142d1a',
      emoji: '🌸'
    };
  }

  // Default theme (late December after Christmas)
  return {
    name: 'default',
    displayName: 'Default',
    primary: '#2196f3',
    secondary: '#f50057',
    accent: '#00bcd4',
    background: '#0a1929',
    paper: '#132f4c',
    emoji: '🚀'
  };
}

/**
 * Get a specific theme by name (useful for testing)
 */
export function getThemeByName(themeName: ThemeName): SeasonalTheme {
  const themes: Record<ThemeName, SeasonalTheme> = {
    halloween: {
      name: 'halloween',
      displayName: 'Halloween',
      primary: '#ff6b35',
      secondary: '#8b4513',
      accent: '#ff9500',
      background: '#1a0f0a',
      paper: '#2d1810',
      emoji: '🎃'
    },
    christmas: {
      name: 'christmas',
      displayName: 'Christmas',
      primary: '#c41e3a',
      secondary: '#165b33',
      accent: '#ffd700',
      background: '#0a1214',
      paper: '#1a2428',
      emoji: '🎄'
    },
    valentines: {
      name: 'valentines',
      displayName: "Valentine's Day",
      primary: '#ff1493',
      secondary: '#c71585',
      accent: '#ff69b4',
      background: '#1a0a14',
      paper: '#2d1428',
      emoji: '💝'
    },
    easter: {
      name: 'easter',
      displayName: 'Easter',
      primary: '#9b59b6',
      secondary: '#3498db',
      accent: '#f1c40f',
      background: '#0f0a1a',
      paper: '#1d1428',
      emoji: '🐰'
    },
    summer: {
      name: 'summer',
      displayName: 'Summer',
      primary: '#ffa500',
      secondary: '#00ced1',
      accent: '#ffff00',
      background: '#0a1419',
      paper: '#14282d',
      emoji: '☀️'
    },
    autumn: {
      name: 'autumn',
      displayName: 'Autumn',
      primary: '#d2691e',
      secondary: '#8b4513',
      accent: '#ff8c00',
      background: '#120f0a',
      paper: '#241e14',
      emoji: '🍂'
    },
    winter: {
      name: 'winter',
      displayName: 'Winter',
      primary: '#5dade2',
      secondary: '#3498db',
      accent: '#aed6f1',
      background: '#0a1219',
      paper: '#14242d',
      emoji: '❄️'
    },
    spring: {
      name: 'spring',
      displayName: 'Spring',
      primary: '#2ecc71',
      secondary: '#27ae60',
      accent: '#f1c40f',
      background: '#0a190f',
      paper: '#142d1a',
      emoji: '🌸'
    },
    default: {
      name: 'default',
      displayName: 'Default',
      primary: '#2196f3',
      secondary: '#f50057',
      accent: '#00bcd4',
      background: '#0a1929',
      paper: '#132f4c',
      emoji: '🚀'
    }
  };

  return themes[themeName];
}
