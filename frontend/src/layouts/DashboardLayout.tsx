import {
  Activity,
  Bell,
  Boxes,
  ChevronUp,
  Factory,
  Gauge,
  LogOut,
  Search,
  Settings,
  ShieldAlert,
  UserRound,
  Wrench,
} from 'lucide-react'
import {
  AnimatePresence,
  motion,
} from 'motion/react'
import {
  NavLink,
  useLocation,
  useNavigate,
  useOutlet,
} from 'react-router-dom'
import {
  useEffect,
  useState,
} from 'react'

import { useAuth } from '../auth/authContext'
import { CommandPalette } from '../components/shell/CommandPalette'
import { NotificationCenter } from '../components/shell/NotificationCenter'

const navigation = [
  {
    label: 'Overview',
    path: '/overview',
    icon: Gauge,
  },
  {
    label: 'Production',
    path: '/production',
    icon: Factory,
  },
  {
    label: 'Machines',
    path: '/machines',
    icon: Boxes,
  },
  {
    label: 'Alerts',
    path: '/alerts',
    icon: ShieldAlert,
  },
  {
    label: 'Maintenance',
    path: '/maintenance',
    icon: Wrench,
  },
]

const roleLabels: Record<string, string> = {
  admin: 'Administrator',
  manager: 'Manager',
  technician: 'Technician',
  operator: 'Operator',
}

function getInitials(fullName: string): string {
  const names = fullName
    .trim()
    .split(/\s+/)
    .filter(Boolean)

  if (names.length === 0) {
    return 'FP'
  }

  return names
    .slice(0, 2)
    .map((name) => name[0])
    .join('')
    .toUpperCase()
}

function getRoleLabel(
  roleName: string | null | undefined,
): string {
  if (!roleName) {
    return 'Unassigned role'
  }

  if (roleLabels[roleName]) {
    return roleLabels[roleName]
  }

  return roleName
    .replace(/[_-]/g, ' ')
    .replace(/\b\w/g, (character) =>
      character.toUpperCase(),
    )
}

export function DashboardLayout() {
  const location = useLocation()
  const navigate = useNavigate()
  const outlet = useOutlet()

  const {
    user,
    logout,
  } = useAuth()

  const [
    commandPaletteOpen,
    setCommandPaletteOpen,
  ] = useState(false)

  const [
    notificationCenterOpen,
    setNotificationCenterOpen,
  ] = useState(false)

  const [
    accountMenuOpen,
    setAccountMenuOpen,
  ] = useState(false)

  const [
    unreadNotificationCount,
    setUnreadNotificationCount,
  ] = useState(3)

  const isMac =
    typeof navigator !== 'undefined'
    && /Mac|iPhone|iPad/.test(
      navigator.userAgent,
    )

  const shortcutLabel =
    isMac ? '⌘ K' : 'Ctrl K'

  const fullName =
    user?.full_name ?? 'FactoryPulse User'

  const email =
    user?.email ?? 'Authenticated session'

  const initials =
    getInitials(fullName)

  const roleLabel =
    getRoleLabel(user?.role_name)

  useEffect(() => {
    function handleKeyboardShortcut(
      event: KeyboardEvent,
    ) {
      const commandPressed =
        event.ctrlKey || event.metaKey

      if (
        commandPressed
        && event.key.toLowerCase() === 'k'
      ) {
        event.preventDefault()

        setNotificationCenterOpen(false)
        setAccountMenuOpen(false)

        setCommandPaletteOpen(
          (current) => !current,
        )
      }

      if (event.key === 'Escape') {
        if (commandPaletteOpen) {
          setCommandPaletteOpen(false)
        }

        if (notificationCenterOpen) {
          setNotificationCenterOpen(false)
        }

        if (accountMenuOpen) {
          setAccountMenuOpen(false)
        }
      }
    }

    window.addEventListener(
      'keydown',
      handleKeyboardShortcut,
    )

    return () => {
      window.removeEventListener(
        'keydown',
        handleKeyboardShortcut,
      )
    }
  }, [
    accountMenuOpen,
    commandPaletteOpen,
    notificationCenterOpen,
  ])

  function openAccountMenu() {
    setCommandPaletteOpen(false)
    setNotificationCenterOpen(false)

    setAccountMenuOpen(
      (current) => !current,
    )
  }

  function handleAccountNavigation(
    destination: string,
  ) {
    setAccountMenuOpen(false)

    navigate(destination)
  }

  function handleLogout() {
    setAccountMenuOpen(false)

    logout()

    navigate('/login', {
      replace: true,
    })
  }

  return (
    <div className="dashboard-shell">
      <aside className="sidebar">
        <div className="sidebar-brand">
          <motion.div
            className="sidebar-brand-mark"
            initial={{
              scale: 0.85,
              opacity: 0,
            }}
            animate={{
              scale: 1,
              opacity: 1,
            }}
            transition={{
              duration: 0.45,
            }}
          >
            <Activity
              size={19}
              strokeWidth={2.4}
            />
          </motion.div>

          <div>
            <div className="sidebar-brand-name">
              FactoryPulse
            </div>

            <div className="sidebar-brand-subtitle">
              Industrial AI
            </div>
          </div>
        </div>

        <nav className="sidebar-navigation">
          <div className="sidebar-section-label">
            Workspace
          </div>

          {navigation.map((item) => {
            const Icon = item.icon

            return (
              <NavLink
                key={item.path}
                to={item.path}
                className="sidebar-link"
                onClick={() => {
                  setAccountMenuOpen(false)
                }}
              >
                {({ isActive }) => (
                  <>
                    {isActive && (
                      <motion.div
                        layoutId="active-navigation"
                        className="sidebar-link-active"
                        transition={{
                          type: 'spring',
                          stiffness: 420,
                          damping: 34,
                        }}
                      />
                    )}

                    <Icon size={18} />

                    <span>
                      {item.label}
                    </span>

                    {item.label === 'Alerts'
                      && (
                        <span className="navigation-badge">
                          7
                        </span>
                      )}
                  </>
                )}
              </NavLink>
            )
          })}
        </nav>

        <div className="sidebar-footer">
          <button
            className="sidebar-settings"
            type="button"
            onClick={() => {
              setAccountMenuOpen(false)
              navigate('/settings')
            }}
          >
            <Settings size={18} />
            <span>Settings</span>
          </button>

          <div className="sidebar-account">
            <AnimatePresence>
              {accountMenuOpen && (
                <>
                  <motion.button
                    className="account-menu-scrim"
                    type="button"
                    aria-label="Close account menu"
                    onClick={() => {
                      setAccountMenuOpen(false)
                    }}
                    initial={{
                      opacity: 0,
                    }}
                    animate={{
                      opacity: 1,
                    }}
                    exit={{
                      opacity: 0,
                    }}
                  />

                  <motion.div
                    className="sidebar-account-menu"
                    role="menu"
                    initial={{
                      opacity: 0,
                      y: 8,
                      scale: 0.97,
                    }}
                    animate={{
                      opacity: 1,
                      y: 0,
                      scale: 1,
                    }}
                    exit={{
                      opacity: 0,
                      y: 6,
                      scale: 0.98,
                    }}
                    transition={{
                      duration: 0.17,
                      ease: [0.22, 1, 0.36, 1],
                    }}
                  >
                    <div className="account-menu-identity">
                      <div className="account-menu-avatar">
                        {initials}
                      </div>

                      <div>
                        <span className="account-menu-eyebrow">
                          Signed in as
                        </span>

                        <strong>
                          {fullName}
                        </strong>

                        <span className="account-menu-email">
                          {email}
                        </span>
                      </div>
                    </div>

                    <div className="account-role-pill">
                      <span />
                      {roleLabel}
                    </div>

                    <div className="account-menu-divider" />

                    <button
                      type="button"
                      role="menuitem"
                      className="account-menu-item"
                      onClick={() => {
                        handleAccountNavigation(
                          '/profile',
                        )
                      }}
                    >
                      <UserRound size={17} />

                      <div>
                        <strong>Profile</strong>
                        <span>
                          Account information
                        </span>
                      </div>
                    </button>

                    <button
                      type="button"
                      role="menuitem"
                      className="account-menu-item"
                      onClick={() => {
                        handleAccountNavigation(
                          '/settings',
                        )
                      }}
                    >
                      <Settings size={17} />

                      <div>
                        <strong>Settings</strong>
                        <span>
                          Workspace preferences
                        </span>
                      </div>
                    </button>

                    <div className="account-menu-divider" />

                    <button
                      type="button"
                      role="menuitem"
                      className="account-menu-item account-menu-logout"
                      onClick={handleLogout}
                    >
                      <LogOut size={17} />

                      <div>
                        <strong>Sign out</strong>
                        <span>
                          End this secure session
                        </span>
                      </div>
                    </button>
                  </motion.div>
                </>
              )}
            </AnimatePresence>

            <button
              className="sidebar-account-trigger"
              type="button"
              aria-haspopup="menu"
              aria-expanded={accountMenuOpen}
              onClick={openAccountMenu}
            >
              <div className="sidebar-user-avatar">
                {initials}
              </div>

              <div className="sidebar-user-details">
                <strong>
                  {fullName}
                </strong>

                <span>
                  {roleLabel}
                </span>
              </div>

              <ChevronUp
                className={
                  accountMenuOpen
                    ? 'sidebar-account-chevron sidebar-account-chevron-open'
                    : 'sidebar-account-chevron'
                }
                size={16}
              />
            </button>
          </div>
        </div>
      </aside>

      <section className="workspace">
        <header className="topbar">
          <div className="topbar-context">
            <span className="context-status">
              <span className="context-status-dot" />
              Systems operational
            </span>

            <span className="context-divider" />

            <span className="context-location">
              Factory HQ
            </span>
          </div>

          <div className="topbar-actions">
            <button
              className="search-trigger"
              type="button"
              onClick={() => {
                setNotificationCenterOpen(false)
                setAccountMenuOpen(false)
                setCommandPaletteOpen(true)
              }}
            >
              <Search size={17} />

              <span>
                Search anything...
              </span>

              <kbd>
                {shortcutLabel}
              </kbd>
            </button>

            <button
              className="icon-button"
              type="button"
              aria-label="Notifications"
              aria-expanded={
                notificationCenterOpen
              }
              onClick={() => {
                setCommandPaletteOpen(false)
                setAccountMenuOpen(false)

                setNotificationCenterOpen(
                  (current) => !current,
                )
              }}
            >
              <Bell size={18} />

              {unreadNotificationCount > 0 && (
                <span className="notification-count">
                  {unreadNotificationCount}
                </span>
              )}
            </button>
          </div>
        </header>

        <AnimatePresence mode="wait">
          <motion.main
            key={location.pathname}
            className="page-content"
            initial={{
              opacity: 0,
              y: 10,
              filter: 'blur(4px)',
            }}
            animate={{
              opacity: 1,
              y: 0,
              filter: 'blur(0px)',
            }}
            exit={{
              opacity: 0,
              y: -5,
              filter: 'blur(3px)',
            }}
            transition={{
              duration: 0.28,
              ease: [0.22, 1, 0.36, 1],
            }}
          >
            {outlet}
          </motion.main>
        </AnimatePresence>
      </section>

      <NotificationCenter
        open={notificationCenterOpen}
        onClose={() => {
          setNotificationCenterOpen(false)
        }}
        onUnreadCountChange={
          setUnreadNotificationCount
        }
      />

      <CommandPalette
        open={commandPaletteOpen}
        onClose={() => {
          setCommandPaletteOpen(false)
        }}
      />
    </div>
  )
}