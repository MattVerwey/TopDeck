# Seasonal Themes in TopDeck

TopDeck now features **dynamic seasonal theming** that automatically changes the UI colors and appearance based on the current date!

## 🎨 Available Themes

The application automatically detects the current season/festivity and applies an appropriate theme:

### 🎃 Halloween (October 1-31)
- **Colors**: Orange (#ff6b35), Brown (#8b4513)
- **Vibe**: Spooky and festive
- **Active**: Throughout October

### 🎄 Christmas (December 1-26)
- **Colors**: Red (#c41e3a), Green (#165b33), Gold (#ffd700)
- **Vibe**: Festive holiday cheer
- **Active**: First 26 days of December

### 💝 Valentine's Day (February 10-14)
- **Colors**: Pink (#ff1493), Magenta (#c71585)
- **Vibe**: Romantic and loving
- **Active**: February 10-14

### 🐰 Easter (April 1-20)
- **Colors**: Purple (#9b59b6), Blue (#3498db), Yellow (#f1c40f)
- **Vibe**: Spring celebration
- **Active**: Early April

### ☀️ Summer (June-August)
- **Colors**: Orange (#ffa500), Cyan (#00ced1), Yellow (#ffff00)
- **Vibe**: Bright and sunny
- **Active**: June 1 - August 31

### 🍂 Autumn (September)
- **Colors**: Brown (#d2691e), Orange (#ff8c00)
- **Vibe**: Cozy fall colors
- **Active**: Throughout September

### ❄️ Winter (January-February)
- **Colors**: Light Blue (#5dade2), Blue (#3498db)
- **Vibe**: Cool and crisp
- **Active**: January and early February (except Valentine's)

### 🌸 Spring (March-May)
- **Colors**: Green (#2ecc71), Yellow (#f1c40f)
- **Vibe**: Fresh and growing
- **Active**: March through May (except Easter period)

### 🚀 Default (Late December)
- **Colors**: Blue (#2196f3), Pink (#f50057)
- **Vibe**: Standard TopDeck theme
- **Active**: December 27-31

## How It Works

The theme system automatically:

1. **Detects the current date** when the app loads
2. **Selects the appropriate theme** based on the month and day
3. **Applies seasonal colors** to the UI components
4. **Displays a theme badge** in the top navigation bar showing the current theme

No configuration or manual changes required - just enjoy the seasonal vibes! ✨

## Theme Indicator

Look for the theme badge in the top-right of the navigation bar. It shows:
- An emoji representing the current season/festivity
- The name of the active theme

Example: `🎃 Halloween`

## Technical Details

The theming system is implemented in:
- **Theme Detector**: `/frontend/src/utils/themeDetector.ts`
- **App Component**: `/frontend/src/App.tsx`
- **Layout Component**: `/frontend/src/components/common/Layout.tsx`

### For Developers

To test different themes in development, you can temporarily modify the `getCurrentTheme()` function or use `getThemeByName()`:

```typescript
import { getThemeByName } from './utils/themeDetector';

// Force a specific theme for testing
const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: { main: getThemeByName('christmas').primary },
    // ... etc
  }
});
```

## Benefits

✅ **Automatic**: No manual theme switching needed
✅ **Engaging**: Keeps the UI fresh and relevant
✅ **Memorable**: Seasonal colors make the app more enjoyable
✅ **Professional**: Still maintains a professional look
✅ **Accessible**: All color combinations maintain proper contrast

## Future Enhancements

Possible future additions:
- User preference to disable seasonal themes
- Custom themes for specific events or organizations
- More granular festivity detection (e.g., New Year's, Thanksgiving)
- Theme preview in settings
