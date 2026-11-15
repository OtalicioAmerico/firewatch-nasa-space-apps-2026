import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import '@fontsource/inter/latin-400.css'
import '@fontsource/inter/latin-500.css'
import '@fontsource/inter/latin-600.css'
import '@fontsource/inter/latin-700.css'
import './design/aurora/tokens.css'
import './design/aurora/themes.css'
import './design/aurora/base.css'
import './design/product-tokens.css'
import './styles/app.css'
import './styles/pages.css'
import App from './App'
import { AppProvider } from './state/AppState'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <AppProvider>
      <App />
    </AppProvider>
  </StrictMode>,
)
