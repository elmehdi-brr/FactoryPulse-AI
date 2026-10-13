import {
  Activity,
  CalendarDays,
  Fingerprint,
  LogOut,
  Mail,
  Settings,
  ShieldCheck,
  UserRound,
} from 'lucide-react'
import { motion } from 'motion/react'
import { Link } from 'react-router-dom'

import { useAuth } from '../auth/authContext'

function formatAccountDate(value: string): string {
  const date = new Date(value)

  if (Number.isNaN(date.getTime())) {
    return 'Not available'
  }

  return date.toLocaleDateString([], {
    dateStyle: 'long',
  })
}

function formatRole(role: string | null): string {
  if (!role) {
    return 'Unassigned'
  }

  return role
    .replace(/[_-]+/g, ' ')
    .replace(/\b\w/g, (character) =>
      character.toUpperCase(),
    )
}

function getInitials(fullName: string): string {
  const parts = fullName.trim().split(/\s+/).filter(Boolean)

  if (parts.length === 0) {
    return 'FP'
  }

  return parts
    .slice(0, 2)
    .map((part) => part[0].toUpperCase())
    .join('')
}

export function ProfilePage() {
  const { user, logout } = useAuth()

  if (!user) {
    return (
      <div className="profile-page">
        <div className="dashboard-panel-state">
          Account information is unavailable. Please sign in again.
        </div>
      </div>
    )
  }

  return (
    <div className="profile-page">
      <section className="page-heading profile-heading">
        <div>
          <p className="page-eyebrow">
            Account
          </p>

          <h1>Your profile.</h1>

          <p>
            Review your FactoryPulse identity,
            account status, and access level.
          </p>
        </div>

        <div className="profile-heading-status">
          <span
            className={
              user.is_active
                ? 'profile-status-dot profile-status-dot-active'
                : 'profile-status-dot'
            }
          />

          {user.is_active ? 'Account active' : 'Account inactive'}
        </div>
      </section>

      <motion.section
        className="profile-identity-panel"
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <div className="profile-identity-main">
          <div className="profile-avatar">
            {getInitials(user.full_name)}
          </div>

          <div className="profile-identity-copy">
            <span className="panel-eyebrow">
              Signed-in user
            </span>

            <h2>{user.full_name}</h2>

            <p>{user.email}</p>

            <div className="profile-identity-badges">
              <span className="profile-role-badge">
                <ShieldCheck size={14} />
                {formatRole(user.role_name)}
              </span>

              <span className="profile-id-badge">
                Account #{user.id}
              </span>
            </div>
          </div>
        </div>

        <div className="profile-identity-indicator">
          <Activity size={17} />
          <span>
            {user.is_active
              ? 'Access enabled'
              : 'Access disabled'}
          </span>
        </div>
      </motion.section>

      <section className="profile-content-grid">
        <motion.article
          className="profile-details-panel"
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.05 }}
        >
          <div className="profile-panel-heading">
            <div className="profile-panel-icon">
              <UserRound size={19} />
            </div>

            <div>
              <span className="panel-eyebrow">
                Account information
              </span>

              <h2>Identity details</h2>
            </div>
          </div>

          <div className="profile-detail-row">
            <div className="profile-detail-icon">
              <UserRound size={17} />
            </div>

            <div className="profile-detail-copy">
              <span>Full name</span>
              <strong>{user.full_name}</strong>
            </div>
          </div>

          <div className="profile-detail-row">
            <div className="profile-detail-icon">
              <Mail size={17} />
            </div>

            <div className="profile-detail-copy">
              <span>Email address</span>
              <strong>{user.email}</strong>
            </div>
          </div>

          <div className="profile-detail-row">
            <div className="profile-detail-icon">
              <ShieldCheck size={17} />
            </div>

            <div className="profile-detail-copy">
              <span>Assigned role</span>
              <strong>{formatRole(user.role_name)}</strong>
            </div>
          </div>

          <div className="profile-detail-row">
            <div className="profile-detail-icon">
              <Fingerprint size={17} />
            </div>

            <div className="profile-detail-copy">
              <span>User ID</span>
              <strong>{user.id}</strong>
            </div>
          </div>

          <div className="profile-detail-row">
            <div className="profile-detail-icon">
              <CalendarDays size={17} />
            </div>

            <div className="profile-detail-copy">
              <span>Account created</span>
              <strong>
                {formatAccountDate(user.created_at)}
              </strong>
            </div>
          </div>
        </motion.article>

        <motion.aside
          className="profile-access-panel"
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <div className="profile-panel-heading">
            <div className="profile-panel-icon">
              <ShieldCheck size={19} />
            </div>

            <div>
              <span className="panel-eyebrow">
                Access and security
              </span>

              <h2>Your access</h2>
            </div>
          </div>

          <div className="profile-access-card">
            <span className="profile-access-label">
              Current role
            </span>

            <strong>
              {formatRole(user.role_name)}
            </strong>

            <p>
              Your assigned role determines which FactoryPulse
              features and operations you can access.
            </p>
          </div>

          <div className="profile-access-card">
            <span className="profile-access-label">
              Account status
            </span>

            <strong>
              {user.is_active ? 'Active' : 'Inactive'}
            </strong>

            <p>
              {user.is_active
                ? 'Your account is marked active.'
                : 'Your account is currently marked inactive.'}
            </p>
          </div>

          <div className="profile-notice">
            <ShieldCheck size={17} />

            <p>
              Profile details are currently managed by an
              administrator. Self-service profile editing and
              password changes are not available in this version.
            </p>
          </div>

          <div className="profile-actions">
            <Link
              to="/settings"
              className="profile-settings-link"
            >
              <Settings size={16} />
              Workspace settings
            </Link>

            <button
              type="button"
              className="profile-logout-button"
              onClick={logout}
            >
              <LogOut size={16} />
              Sign out
            </button>
          </div>
        </motion.aside>
      </section>
    </div>
  )
}