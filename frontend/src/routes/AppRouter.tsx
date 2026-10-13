import {
  BrowserRouter,
  Navigate,
  Route,
  Routes,
} from 'react-router-dom'

import { AlertsPage } from '../pages/AlertsPage'
import { AuthProvider } from '../auth/AuthProvider'
import { DashboardLayout } from '../layouts/DashboardLayout'
import { OverviewPage } from '../pages/OverviewPage'
import { PlaceholderPage } from '../pages/PlaceholderPage'
import { ProtectedRoute } from './ProtectedRoute'
import { LoginPage } from '../pages/LoginPage'
import { ProductionPage } from '../pages/ProductionPage'
import { MachinesPage } from '../pages/MachinesPage'
import { MaintenancePage } from '../pages/MaintenancePage'

export function AppRouter() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route
            path="/login"
            element={<LoginPage />}
            />

          <Route element={<ProtectedRoute />}>
            <Route element={<DashboardLayout />}>
              <Route
                index
                element={
                  <Navigate
                    to="/overview"
                    replace
                  />
                }
              />


              <Route
                path="/profile"
                element={
                  <PlaceholderPage
                    eyebrow="Account"
                    title="Profile"
                    description="Manage your FactoryPulse account information and identity."
                  />
                }
              />

              <Route
                path="/settings"
                element={
                  <PlaceholderPage
                  eyebrow="Workspace"
                  title="Settings"
                  description="Configure FactoryPulse workspace and application preferences."
                  />
                }
              />

              <Route
                path="/overview"
                element={<OverviewPage />}
              />

              <Route
                path="/production"
                element={<ProductionPage />}
              />

              <Route
                path="/machines"
                element={<MachinesPage />}
              />

              <Route
                path="/alerts"
                element={<AlertsPage />}
              />

              <Route
                path="/maintenance"
                element={<MaintenancePage />}
              />
            </Route>
          </Route>

          <Route
            path="*"
            element={
              <Navigate
                to="/overview"
                replace
              />
            }
          />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  )
}