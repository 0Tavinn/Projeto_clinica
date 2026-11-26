import { useEffect, useRef, useState } from 'react'
import type { KeyboardEvent, MouseEvent, ReactNode } from 'react'
import { Menu, X } from 'lucide-react'
import './AppNavigation.css'

const MOBILE_QUERY = '(max-width: 760px)'
const MENU_ID = 'mobile-navigation'

type AppNavigationProps = {
  brand: ReactNode
  sidebar: (closeMenu: () => void) => ReactNode
  children: ReactNode
}

export function AppNavigation({ brand, sidebar, children }: AppNavigationProps) {
  const [isMobile, setIsMobile] = useState(() => window.matchMedia(MOBILE_QUERY).matches)
  const [isOpen, setIsOpen] = useState(false)
  const dialogRef = useRef<HTMLDialogElement>(null)
  const triggerRef = useRef<HTMLButtonElement>(null)
  const closeRef = useRef<HTMLButtonElement>(null)
  const desktopRef = useRef<HTMLDivElement>(null)

  function closeMenu() {
    setIsOpen(false)
  }

  useEffect(() => {
    const media = window.matchMedia(MOBILE_QUERY)
    function updateLayout() {
      setIsMobile(media.matches)
      if (!media.matches) setIsOpen(false)
    }
    updateLayout()
    media.addEventListener('change', updateLayout)
    return () => media.removeEventListener('change', updateLayout)
  }, [])

  useEffect(() => {
    if (!isOpen || !isMobile || !dialogRef.current) return

    const dialog = dialogRef.current
    const previousOverflow = document.body.style.overflow
    // O diálogo nativo contém o foco e impede interação com o conteúdo de fundo.
    dialog.showModal()
    document.body.style.overflow = 'hidden'
    closeRef.current?.focus()

    return () => {
      if (dialog.open) dialog.close()
      document.body.style.overflow = previousOverflow
      if (window.matchMedia(MOBILE_QUERY).matches) {
        triggerRef.current?.focus({ preventScroll: true })
      } else {
        desktopRef.current?.querySelector<HTMLButtonElement>('.nav-item.active')?.focus({ preventScroll: true })
      }
    }
  }, [isOpen, isMobile])

  function handleMenuKeyDown(event: KeyboardEvent<HTMLDialogElement>) {
    if (event.key !== 'Tab' || event.ctrlKey || event.altKey || event.metaKey) return
    const buttons = event.currentTarget.querySelectorAll<HTMLButtonElement>('button:not([disabled])')
    const first = buttons[0]
    const last = buttons[buttons.length - 1]
    // Evita que Tab atravesse os limites do painel e alcance a interface do navegador.
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault()
      last?.focus()
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault()
      first?.focus()
    }
  }

  function handleBackdropClick(event: MouseEvent<HTMLDialogElement>) {
    if (event.target !== event.currentTarget) return
    const bounds = event.currentTarget.getBoundingClientRect()
    if (event.clientX < bounds.left || event.clientX > bounds.right
      || event.clientY < bounds.top || event.clientY > bounds.bottom) closeMenu()
  }

  return (
    <div className="app-shell">
      {!isMobile && <div ref={desktopRef} className="desktop-navigation">{sidebar(closeMenu)}</div>}
      {isMobile && (
        <dialog
          ref={dialogRef}
          id={MENU_ID}
          className="app-navigation-dialog"
          aria-label="Menu principal"
          onCancel={(event) => { event.preventDefault(); closeMenu() }}
          onClose={closeMenu}
          onClick={handleBackdropClick}
          onKeyDown={handleMenuKeyDown}
        >
          <button ref={closeRef} type="button" className="icon-button app-navigation-close" aria-label="Fechar menu" onClick={closeMenu}>
            <X size={22} aria-hidden="true" />
          </button>
          {sidebar(closeMenu)}
        </dialog>
      )}
      <main className="main-content">
        <div className="mobile-header">
          <button
            ref={triggerRef}
            type="button"
            className="icon-button"
            aria-label="Abrir menu"
            aria-expanded={isMobile && isOpen}
            aria-controls={isMobile ? MENU_ID : undefined}
            aria-haspopup="dialog"
            onClick={() => setIsOpen(true)}
          >
            <Menu size={22} aria-hidden="true" />
          </button>
          {brand}
        </div>
        {children}
      </main>
    </div>
  )
}
