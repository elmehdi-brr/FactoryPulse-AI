import {
  BellRing,
  Boxes,
  Factory,
  Gauge,
  Search,
  Settings,
  ShieldAlert,
  Wrench,
} from 'lucide-react'
import {
  AnimatePresence,
  motion,
} from 'motion/react'
import {
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react'
import type {
  KeyboardEvent as ReactKeyboardEvent,
} from 'react'
import { useNavigate } from 'react-router-dom'

type CommandPaletteProps = {
  open: boolean
  onClose: () => void
}

type CommandPaletteDialogProps = {
  onClose: () => void
}

const commands = [
  {
    label: 'Open overview',
    description: 'Operational command center',
    path: '/overview',
    icon: Gauge,
    keywords: 'dashboard overview command center',
  },
  {
    label: 'Open production',
    description: 'Production lines, OEE and downtime',
    path: '/production',
    icon: Factory,
    keywords: 'production oee downtime lines',
  },
  {
    label: 'Open machines',
    description: 'Reliability, MTTR, MTBF and sensors',
    path: '/machines',
    icon: Boxes,
    keywords: 'machines assets reliability mttr mtbf sensors',
  },
  {
    label: 'View alerts',
    description: 'Operational and AI-generated alerts',
    path: '/alerts',
    icon: ShieldAlert,
    keywords: 'alerts warnings critical ai',
  },
  {
    label: 'Open maintenance',
    description: 'Maintenance operations and effectiveness',
    path: '/maintenance',
    icon: Wrench,
    keywords: 'maintenance repairs interventions',
  },
  {
    label: 'Critical alerts',
    description: 'View items requiring immediate attention',
    path: '/alerts',
    icon: BellRing,
    keywords: 'critical urgent alerts attention',
  },
  {
    label: 'Settings',
    description: 'Configure your FactoryPulse workspace',
    path: '/settings',
    icon: Settings,
    keywords: 'settings preferences configuration',
  },
]

function CommandPaletteDialog({
  onClose,
}: CommandPaletteDialogProps) {
  const navigate = useNavigate()
  const inputRef = useRef<HTMLInputElement>(null)

  const [query, setQuery] = useState('')
  const [selectedIndex, setSelectedIndex] = useState(0)

  const filteredCommands = useMemo(() => {
    const normalizedQuery = query
      .trim()
      .toLowerCase()

    if (!normalizedQuery) {
      return commands
    }

    return commands.filter((command) => {
      const searchableText = [
        command.label,
        command.description,
        command.keywords,
      ]
        .join(' ')
        .toLowerCase()

      return searchableText.includes(normalizedQuery)
    })
  }, [query])

  useEffect(() => {
    const frame = requestAnimationFrame(() => {
      inputRef.current?.focus()
    })

    return () => {
      cancelAnimationFrame(frame)
    }
  }, [])

  function runCommand(path: string) {
    navigate(path)
    onClose()
  }

  function handleQueryChange(
    value: string,
  ) {
    setQuery(value)
    setSelectedIndex(0)
  }

  function handleKeyDown(
    event: ReactKeyboardEvent<HTMLInputElement>,
  ) {
    if (event.key === 'ArrowDown') {
      event.preventDefault()

      setSelectedIndex((current) => {
        if (filteredCommands.length === 0) {
          return 0
        }

        return (
          (current + 1)
          % filteredCommands.length
        )
      })

      return
    }

    if (event.key === 'ArrowUp') {
      event.preventDefault()

      setSelectedIndex((current) => {
        if (filteredCommands.length === 0) {
          return 0
        }

        return (
          current === 0
            ? filteredCommands.length - 1
            : current - 1
        )
      })

      return
    }

    if (event.key === 'Enter') {
      event.preventDefault()

      const command =
        filteredCommands[selectedIndex]

      if (command) {
        runCommand(command.path)
      }

      return
    }

    if (event.key === 'Escape') {
      event.preventDefault()
      onClose()
    }
  }

  return (
    <motion.div
      className="command-palette-layer"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
    >
      <motion.button
        type="button"
        className="command-palette-backdrop"
        aria-label="Close command palette"
        onClick={onClose}
      />

      <motion.section
        role="dialog"
        aria-modal="true"
        aria-label="FactoryPulse command palette"
        className="command-palette"
        initial={{
          opacity: 0,
          y: -18,
          scale: 0.97,
          filter: 'blur(8px)',
        }}
        animate={{
          opacity: 1,
          y: 0,
          scale: 1,
          filter: 'blur(0px)',
        }}
        exit={{
          opacity: 0,
          y: -10,
          scale: 0.98,
          filter: 'blur(5px)',
        }}
        transition={{
          duration: 0.22,
          ease: [0.22, 1, 0.36, 1],
        }}
      >
        <div className="command-search">
          <Search size={19} />

          <input
            ref={inputRef}
            value={query}
            onChange={(event) => {
              handleQueryChange(event.target.value)
            }}
            onKeyDown={handleKeyDown}
            placeholder="Search FactoryPulse..."
            aria-label="Search FactoryPulse"
          />

          <kbd>ESC</kbd>
        </div>

        <div className="command-content">
          <div className="command-section-label">
            {query
              ? 'Search results'
              : 'Quick actions'}
          </div>

          {filteredCommands.length > 0 ? (
            <div
              className="command-list"
              role="listbox"
            >
              {filteredCommands.map(
                (command, index) => {
                  const Icon = command.icon
                  const selected =
                    index === selectedIndex

                  return (
                    <motion.button
                      key={`${command.label}-${index}`}
                      type="button"
                      role="option"
                      aria-selected={selected}
                      className={`command-item ${
                        selected
                          ? 'command-item-selected'
                          : ''
                      }`}
                      onMouseEnter={() => {
                        setSelectedIndex(index)
                      }}
                      onClick={() => {
                        runCommand(command.path)
                      }}
                      whileTap={{
                        scale: 0.985,
                      }}
                    >
                      <span className="command-icon">
                        <Icon size={18} />
                      </span>

                      <span className="command-copy">
                        <strong>
                          {command.label}
                        </strong>

                        <span>
                          {command.description}
                        </span>
                      </span>

                      <span className="command-enter">
                        ↵
                      </span>
                    </motion.button>
                  )
                },
              )}
            </div>
          ) : (
            <div className="command-empty">
              <Search size={22} />

              <strong>No results found</strong>

              <span>
                Try searching for production,
                machines, alerts, or maintenance.
              </span>
            </div>
          )}
        </div>

        <footer className="command-footer">
          <div>
            <kbd>↑</kbd>
            <kbd>↓</kbd>
            <span>Navigate</span>
          </div>

          <div>
            <kbd>↵</kbd>
            <span>Open</span>
          </div>

          <div>
            <kbd>ESC</kbd>
            <span>Close</span>
          </div>
        </footer>
      </motion.section>
    </motion.div>
  )
}

export function CommandPalette({
  open,
  onClose,
}: CommandPaletteProps) {
  return (
    <AnimatePresence>
      {open && (
        <CommandPaletteDialog
          onClose={onClose}
        />
      )}
    </AnimatePresence>
  )
}