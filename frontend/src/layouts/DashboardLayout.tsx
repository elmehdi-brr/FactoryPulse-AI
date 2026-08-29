import {
  Activity,
  Bell,
  Boxes,
  Factory,
  Gauge,
  Search,
  Settings,
  ShieldAlert,
  Wrench,
} from 'lucide-react'
import { AnimatePresence, motion } from 'motion/react'
import {
  NavLink,
  useLocation,
  useOutlet,
} from 'react-router-dom'
import {
  useEffect,
  useState,
} from 'react'
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

export function DashboardLayout() {
  const location = useLocation()
  const outlet = useOutlet()

  const [commandPaletteOpen, setCommandPaletteOpen] =
  useState(false)

const isMac =
  typeof navigator !== 'undefined'
  && /Mac|iPhone|iPad/.test(navigator.userAgent)

const shortcutLabel = isMac ? '⌘ K' : 'Ctrl K'
const [
  notificationCenterOpen,
  setNotificationCenterOpen,
] = useState(false)

const [
  unreadNotificationCount,
  setUnreadNotificationCount,
] = useState(3)

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

      setCommandPaletteOpen((current) => !current)
    }

    if (event.key === 'Escape') {
        if (commandPaletteOpen) {
            setCommandPaletteOpen(false)
        }

        if (notificationCenterOpen) {
            setNotificationCenterOpen(false)
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
}, [commandPaletteOpen,   notificationCenterOpen,])

  return (
    <div className="dashboard-shell">
      <aside className="sidebar">
        <div className="sidebar-brand">
          <motion.div
            className="sidebar-brand-mark"
            initial={{ scale: 0.85, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ duration: 0.45 }}
          >
            <Activity size={19} strokeWidth={2.4} />
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

                    <span>{item.label}</span>

                    {item.label === 'Alerts' && (
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
          >
            <Settings size={18} />
            <span>Settings</span>
          </button>

          <div className="sidebar-user">
            <div className="sidebar-user-avatar">
              EM
            </div>

            <div className="sidebar-user-details">
              <strong>El Mehdi</strong>
              <span>Administrator</span>
            </div>
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
                    setCommandPaletteOpen(true)
                }}
            >
              <Search size={17} />

              <span>Search anything...</span>

              <kbd>{shortcutLabel}</kbd>
            </button>

            <button
                className="icon-button"
                type="button"
                aria-label="Notifications"
                aria-expanded={notificationCenterOpen}
                onClick={() => {
                    setCommandPaletteOpen(false)

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