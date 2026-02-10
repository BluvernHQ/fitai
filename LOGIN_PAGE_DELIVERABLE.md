# Login Page Implementation

## Design Philosophy & Alignment

The `LoginView` component was designed to be indistinguishable from the core application.

### Visual Consistency

- **Dark Mode Architecture**: Utilized the core `bg-[#050505]` background to maintain the immersive dark theme.
- **Glassmorphism Cards**: Replicated the input fields using the same `bg-white/[0.03]` and `border-white/5` styling found in the `MetricInput` component. This ensures the inputs feel like part of the same "physical" system as the rest of the UI.
- **Typography Strategy**:
  - Used `Outfit` (Brand Font) for the "System Access" label and "Welcome Back" headline to align with other section headers.
  - Used `Inter` for input text to ensure readability, consistent with the rest of the application body text.
- **Accent Color**: Leveraged the `lime-400` highlight color for the primary action button and hover states, strictly strictly following the established palette.

### Interaction & Motion

- **Entrance Animation**: Implemented `framer-motion` with `initial={{ opacity: 0, y: 20 }}` to match the smooth, rising entrance of the `InputView`.
- **Micro-interactions**: Added a subtle `focus-within` glow to inputs (`bg-white/[0.08]`) to provide tactile feedback without being distracting.
- **Button Behavior**: Reused the "pill" button style with the sliding arrow animation (`group-hover:translate-x-1`) to ensure the "Enter System" action feels familiar.

## Component Structure

The implementation involved three key files:

1.  **`src/components/LoginView.jsx`**: The main UI component handling form state, validation, and integration with Firebase auth.
2.  **`src/App.jsx`**: Updated to acting as the "Gatekeeper", checking the `useAuth` state before allowing access to the main application.
3.  **`src/main.jsx`**: Wrapped the application in `AuthProvider` to ensure auth state is available globally.

This architecture ensures a seamless flow: `Loading` -> `Login` -> `Main App`, with no visual jarring or redirect flickers.
