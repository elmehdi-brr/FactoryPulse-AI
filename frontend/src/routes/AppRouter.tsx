import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'

import { DashboardLayout } from '../layouts/DashboardLayout'
import { OverviewPage } from '../pages/OverviewPage'
import { PlaceholderPage } from '../pages/PlaceholderPage'

export function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<DashboardLayout />}>
          <Route index element={<Navigate to="/overview" replace />} />

          <Route path="/overview" element={<OverviewPage />} />

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

        <Route path="*" element={<Navigate to="/overview" replace />} />
      </Routes>
    </BrowserRouter>
  )
}