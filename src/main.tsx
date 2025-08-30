import { createRoot } from 'react-dom/client'
import { BrowserRouter, HashRouter } from 'react-router-dom'
import App from './App.tsx'
import './index.css'

const isElectron = !!(window as any).process?.versions?.electron
const Router = isElectron ? HashRouter : BrowserRouter

createRoot(document.getElementById("root")!).render(
  <Router>
    <App />
  </Router>
);
