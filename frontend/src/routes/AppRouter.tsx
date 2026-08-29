import {
  BrowserRouter,
  Navigate,
  Route,
  Routes,
} from 'react-router-dom'

import { AuthProvider } from '../auth/AuthProvider'
import { DashboardLayout } from '../layouts/DashboardLayout'
import { OverviewPage } from '../pages/OverviewPage'
import { PlaceholderPage } from '../pages/PlaceholderPage'
import { ProtectedRoute } from './ProtectedRoute'
import { LoginPage } from '../pages/LoginPage'

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
                element={
                  <PlaceholderPage
                    eyebrow="Production Intelligence"
                    title="Production"
                    description="Production runs, OEE, downtime, line performance, and operational trends will live here."
                  />
                }
              />

              <Route
                path="/machines"
                element={
                  <PlaceholderPage
                    eyebrow="Asset Intelligence"
                    title="Machines"
                    description="Machine reliability, MTTR, MTBF, sensors, health, and operational impact will live here."
                  />
                }
              />

              <Route
                path="/alerts"
                element={
                  <PlaceholderPage
                    eyebrow="Operational Awareness"
                    title="Alerts"
                    description="AI-generated alerts, severity, response state, and industrial events will live here."
                  />
                }
              />

              <Route
                path="/maintenance"
                element={
                  <PlaceholderPage
                    eyebrow="Maintenance Intelligence"
                    title="Maintenance"
                    description="Maintenance interventions, response effectiveness, assignments, and history will live here."
                  />
                }
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