/**
 * Theme Demo - Shows how themes change throughout the year
 * This is for demonstration purposes to show the seasonal themes
 */

import { getThemeByName, ThemeName } from './themeDetector';

/**
 * Get all available themes with their active periods
 */
export function getAllThemesInfo() {
  const themes: Array<{
    name: ThemeName;
    period: string;
    theme: ReturnType<typeof getThemeByName>;
  }> = [
    {
      name: 'halloween',
      period: 'October 1-31',
      theme: getThemeByName('halloween')
    },
    {
      name: 'christmas',
      period: 'December 1-26',
      theme: getThemeByName('christmas')
    },
    {
      name: 'valentines',
      period: 'February 10-14',
      theme: getThemeByName('valentines')
    },
    {
      name: 'easter',
      period: 'April 1-20',
      theme: getThemeByName('easter')
    },
    {
      name: 'summer',
      period: 'June 1 - August 31',
      theme: getThemeByName('summer')
    },
    {
      name: 'autumn',
      period: 'September',
      theme: getThemeByName('autumn')
    },
    {
      name: 'winter',
      period: 'January - early February',
      theme: getThemeByName('winter')
    },
    {
      name: 'spring',
      period: 'March - May (except Easter)',
      theme: getThemeByName('spring')
    },
    {
      name: 'default',
      period: 'Late December (after Christmas)',
      theme: getThemeByName('default')
    }
  ];

  return themes;
}

/**
 * Print all themes to console (for demo purposes)
 */
export function printAllThemes() {
  console.log('\n🎨 TopDeck Seasonal Themes\n');
  console.log('═'.repeat(60));
  
  const themes = getAllThemesInfo();
  
  themes.forEach(({ theme, period }) => {
    console.log(`\n${theme.emoji} ${theme.displayName}`);
    console.log(`   Period: ${period}`);
    console.log(`   Primary Color: ${theme.primary}`);
    console.log(`   Secondary Color: ${theme.secondary}`);
    console.log(`   Background: ${theme.background}`);
  });
  
  console.log('\n' + '═'.repeat(60));
  console.log('\nThe theme automatically changes based on the current date!');
  console.log('No configuration needed - just enjoy the seasonal vibes! ✨\n');
}
