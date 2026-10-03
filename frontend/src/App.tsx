import { useEffect, useMemo, useState } from 'react'
import type { FormEvent, ReactNode } from 'react'
import {
  Activity,
  ArrowLeft,
  ArrowRight,
  CalendarDays,
  Check,
  ChevronDown,
  CircleAlert,
  CircleUserRound,
  LayoutDashboard,
  LogOut,
  Menu,
  Pencil,
  Plus,
  Search,
  Stethoscope,
  Users,
} from 'lucide-react'
import {
  ApiError,
  appointmentsApi,
  authApi,
  dentistsApi,
  getErrorMessage,
  patientsApi,
  usersApi,
} from './api'
import type {
  Appointment,
  AppointmentFilters,
  AppointmentPayload,
  AppointmentStatus,
  AppointmentStatusChange,
  AuthUser,
  Dentist,
  Patient,
  PatientPayload,
  UserCreatePayload,
  UserRead,
  UserRole,
} from './api'

type View =
  | 'dashboard'
  | 'patients'
  | 'patient-form'
  | 'users'
  | 'user-form'
  | 'agenda'
  | 'appointment-form'
  | 'appointment'
  | 'record'
type AuthStatus = 'loading' | 'authenticated' | 'unauthenticated'
type Tone = 'blue' | 'green' | 'gray' | 'red' | 'amber'
type Toast = { message: string; tone: 'success' | 'error' }
type SelectOption = { id: number; full_name: string }

const ROLE_LABELS: Record<UserRole, string> = {
  ADMINISTRATOR: 'Administrador',
  RECEPTIONIST: 'Recepcionista',
  DENTIST: 'Dentista',
}

const ROLE_TONES: Record<UserRole, Tone> = {
  ADMINISTRATOR: 'blue',
  RECEPTIONIST: 'gray',
  DENTIST: 'green',
}

const APPOINTMENT_STATUS_LABELS: Record<AppointmentStatus, string> = {
  SCHEDULED: 'Agendada',
  CONFIRMED: 'Confirmada',
  COMPLETED: 'Concluída',
  CANCELED: 'Cancelada',
  NO_SHOW: 'Ausência',
}

const APPOINTMENT_STATUS_TONES: Record<AppointmentStatus, Tone> = {
  SCHEDULED: 'blue',
  CONFIRMED: 'green',
  COMPLETED: 'gray',
  CANCELED: 'red',
  NO_SHOW: 'amber',
}

// Espelha _ALLOWED_TRANSITIONS e _ROLE_STATUS_TARGETS de backend/app/appointments/service.py.
const APPOINTMENT_TRANSITIONS: Record<AppointmentStatus, AppointmentStatusChange[]> = {
  SCHEDULED: ['CONFIRMED', 'COMPLETED', 'CANCELED', 'NO_SHOW'],
  CONFIRMED: ['COMPLETED', 'CANCELED', 'NO_SHOW'],
  COMPLETED: [],
  CANCELED: [],
  NO_SHOW: [],
}

const STATUS_ACTIONS: Record<AppointmentStatusChange, {
  label: string
  success: string
  roles: UserRole[]
  confirmation?: string
}> = {
  CONFIRMED: {
    label: 'Confirmar',
    success: 'Consulta confirmada com sucesso.',
    roles: ['ADMINISTRATOR', 'RECEPTIONIST'],
  },
  COMPLETED: {
    label: 'Concluir',
    success: 'Consulta concluída com sucesso.',
    roles: ['ADMINISTRATOR', 'DENTIST'],
    confirmation: 'Deseja marcar esta consulta como concluída?',
  },
  CANCELED: {
    label: 'Cancelar',
    success: 'Consulta cancelada com sucesso.',
    roles: ['ADMINISTRATOR', 'RECEPTIONIST'],
    confirmation: 'Deseja realmente cancelar esta consulta? O registro será mantido no histórico.',
  },
  NO_SHOW: {
    label: 'Registrar ausência',
    success: 'Ausência registrada com sucesso.',
    roles: ['ADMINISTRATOR', 'RECEPTIONIST', 'DENTIST'],
    confirmation: 'Deseja registrar a ausência do paciente nesta consulta?',
  },
}

const ACTIVE_APPOINTMENT_STATUSES: AppointmentStatus[] = ['SCHEDULED', 'CONFIRMED']
// Conclusão e ausência só podem ser registradas após o início da consulta.
const STATUSES_AFTER_START: AppointmentStatusChange[] = ['COMPLETED', 'NO_SHOW']

const DURATION_OPTIONS = [15, 30, 45, 60, 90, 120]
const DEFAULT_DURATION = 30

const BRAZILIAN_STATES = [
  'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA', 'MT', 'MS', 'MG', 'PA',
  'PB', 'PR', 'PE', 'PI', 'RJ', 'RN', 'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO',
]

const DATE_FORMAT = new Intl.DateTimeFormat('pt-BR', {
  weekday: 'short',
  day: '2-digit',
  month: '2-digit',
  year: 'numeric',
})
const SHORT_DATE_FORMAT = new Intl.DateTimeFormat('pt-BR', { weekday: 'short', day: '2-digit', month: '2-digit' })
const TIME_FORMAT = new Intl.DateTimeFormat('pt-BR', { hour: '2-digit', minute: '2-digit' })

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

function onlyDigits(value: string) {
  return value.replace(/\D/g, '')
}

// As máscaras só inserem um separador quando há dígito depois dele, para o backspace não travar.
function formatCpf(value: string) {
  const digits = onlyDigits(value).slice(0, 11)
  if (digits.length <= 3) return digits
  if (digits.length <= 6) return `${digits.slice(0, 3)}.${digits.slice(3)}`
  if (digits.length <= 9) return `${digits.slice(0, 3)}.${digits.slice(3, 6)}.${digits.slice(6)}`
  return `${digits.slice(0, 3)}.${digits.slice(3, 6)}.${digits.slice(6, 9)}-${digits.slice(9)}`
}

function formatPhone(value: string) {
  const digits = onlyDigits(value).slice(0, 11)
  if (!digits) return ''
  if (digits.length <= 2) return `(${digits}`
  const local = digits.slice(2)
  const prefixLength = digits.length === 11 ? 5 : 4
  if (local.length <= prefixLength) return `(${digits.slice(0, 2)}) ${local}`
  return `(${digits.slice(0, 2)}) ${local.slice(0, prefixLength)}-${local.slice(prefixLength)}`
}

function formatCep(value: string) {
  const digits = onlyDigits(value).slice(0, 8)
  return digits.length <= 5 ? digits : `${digits.slice(0, 5)}-${digits.slice(5)}`
}

type AddressFields = {
  cep: string
  street: string
  number: string
  complement: string
  district: string
  city: string
  state: string
}

const EMPTY_ADDRESS: AddressFields = {
  cep: '', street: '', number: '', complement: '', district: '', city: '', state: '',
}

// A API guarda o endereço em um único texto. Os campos separados preparam a futura consulta
// de CEP, e o texto segue o formato "Rua, Nº - Compl., Bairro, Cidade - UF, CEP 00000-000".
function composeAddress(address: AddressFields): string | null {
  const field = (value: string) => value.trim()
  const streetLine = [field(address.street), field(address.number)].filter(Boolean).join(', ')
    + (field(address.complement) ? ` - ${field(address.complement)}` : '')
  const cityLine = [field(address.city), address.state].filter(Boolean).join(' - ')
  const cep = onlyDigits(address.cep) ? `CEP ${formatCep(address.cep)}` : ''
  return [streetLine, field(address.district), cityLine, cep].filter(Boolean).join(', ') || null
}

const ADDRESS_PATTERN = /^(.+?), ([^,]+?)(?: - ([^,]+))?(?:, ([^,]+))?, ([^,]+) - ([A-Z]{2})(?:, CEP (\d{5}-\d{3}))?$/

// Endereços fora do formato (cadastros antigos) ficam inteiros no logradouro, sem perda de dados.
function parseAddress(value: string | null): AddressFields {
  if (!value) return EMPTY_ADDRESS
  const match = ADDRESS_PATTERN.exec(value)
  if (!match) return { ...EMPTY_ADDRESS, street: value }
  const [, street, number, complement = '', district = '', city, state, cep = ''] = match
  return { cep, street, number, complement, district, city, state }
}

function pad(value: number) {
  return String(value).padStart(2, '0')
}

function toDateInput(date: Date) {
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`
}

function toTimeInput(date: Date) {
  return `${pad(date.getHours())}:${pad(date.getMinutes())}`
}

function addDays(date: Date, days: number) {
  const next = new Date(date)
  next.setDate(next.getDate() + days)
  return next
}

function defaultAppointmentFilters(): AppointmentFilters {
  const today = new Date()
  return { start_date: toDateInput(today), end_date: toDateInput(addDays(today, 6)) }
}

function hasInvalidPeriod(filters: AppointmentFilters) {
  return Boolean(filters.start_date && filters.end_date && filters.end_date < filters.start_date)
}

// Bancos sem fuso (MySQL/SQLite) devolvem horários "naive"; a API os trata como UTC.
function appointmentStart(appointment: Appointment) {
  const value = appointment.scheduled_at
  return new Date(/(Z|[+-]\d{2}:?\d{2})$/i.test(value) ? value : `${value}Z`)
}

function formatTimeRange(appointment: Appointment) {
  const start = appointmentStart(appointment)
  const end = new Date(start.getTime() + appointment.duration_minutes * 60000)
  return `${TIME_FORMAT.format(start)} às ${TIME_FORMAT.format(end)}`
}

function isActiveAppointment(appointment: Appointment) {
  return ACTIVE_APPOINTMENT_STATUSES.includes(appointment.status)
}

function availableStatusActions(appointment: Appointment, role: UserRole) {
  return APPOINTMENT_TRANSITIONS[appointment.status].filter((status) => (
    STATUS_ACTIONS[status].roles.includes(role)
    && (!STATUSES_AFTER_START.includes(status) || appointmentStart(appointment) <= new Date())
  ))
}

function initials(name: string) {
  return name
    .trim()
    .split(/\s+/)
    .slice(0, 2)
    .map((part) => part[0] ?? '')
    .join('')
    .toUpperCase()
}

export default function App() {
  const [authStatus, setAuthStatus] = useState<AuthStatus>('loading')
  const [currentUser, setCurrentUser] = useState<AuthUser | null>(null)
  const [view, setView] = useState<View>('dashboard')
  const [patients, setPatients] = useState<Patient[]>([])
  const [team, setTeam] = useState<UserRead[]>([])
  const [selectedPatient, setSelectedPatient] = useState<Patient | null>(null)
  const [editingPatient, setEditingPatient] = useState<Patient | null>(null)
  const [loadingPatients, setLoadingPatients] = useState(false)
  const [loadingTeam, setLoadingTeam] = useState(false)
  const [appointments, setAppointments] = useState<Appointment[]>([])
  const [dentists, setDentists] = useState<Dentist[]>([])
  const [appointmentFilters, setAppointmentFilters] = useState<AppointmentFilters>(defaultAppointmentFilters)
  const [selectedAppointment, setSelectedAppointment] = useState<Appointment | null>(null)
  const [editingAppointment, setEditingAppointment] = useState<Appointment | null>(null)
  const [loadingAppointments, setLoadingAppointments] = useState(false)
  const [toast, setToast] = useState<Toast | null>(null)
  const [authError, setAuthError] = useState('')

  const isAdministrator = currentUser?.role === 'ADMINISTRATOR'
  const canDeactivatePatients = currentUser?.role === 'ADMINISTRATOR'
    || currentUser?.role === 'RECEPTIONIST'
  const canManageAppointments = currentUser?.role === 'ADMINISTRATOR'
    || currentUser?.role === 'RECEPTIONIST'
  const inAgenda = view === 'agenda'

  function notify(message: string, tone: Toast['tone'] = 'success') {
    setToast({ message, tone })
    window.setTimeout(() => setToast(null), 3200)
  }

  function endLocalSession(message?: string) {
    authApi.logout()
    setCurrentUser(null)
    setAuthStatus('unauthenticated')
    setPatients([])
    setTeam([])
    setSelectedPatient(null)
    setEditingPatient(null)
    setAppointments([])
    setDentists([])
    setAppointmentFilters(defaultAppointmentFilters())
    setSelectedAppointment(null)
    setEditingAppointment(null)
    setView('dashboard')
    if (message) setAuthError(message)
  }

  function handleRequestError(error: unknown) {
    const message = getErrorMessage(error)
    if (error instanceof ApiError && error.status === 401) {
      endLocalSession(message)
    } else {
      notify(message, 'error')
    }
    return message
  }

  useEffect(() => {
    let active = true

    authApi.restoreSession()
      .then((user) => {
        if (!active) return
        setCurrentUser(user)
        setAuthStatus(user ? 'authenticated' : 'unauthenticated')
      })
      .catch((error) => {
        if (!active) return
        setAuthError(getErrorMessage(error))
        setAuthStatus('unauthenticated')
      })

    return () => {
      active = false
    }
  }, [])

  useEffect(() => {
    if (!currentUser) return
    let active = true

    setLoadingPatients(true)
    patientsApi.list()
      .then((items) => {
        if (active) setPatients(items)
      })
      .catch((error) => {
        if (active) handleRequestError(error)
      })
      .finally(() => {
        if (active) setLoadingPatients(false)
      })

    if (currentUser.role === 'ADMINISTRATOR') {
      setLoadingTeam(true)
      usersApi.list()
        .then((items) => {
          if (active) setTeam(items)
        })
        .catch((error) => {
          if (active) handleRequestError(error)
        })
        .finally(() => {
          if (active) setLoadingTeam(false)
        })
    } else {
      setTeam([])
    }

    return () => {
      active = false
    }
  }, [currentUser?.id])

  useEffect(() => {
    if (!currentUser || !inAgenda || hasInvalidPeriod(appointmentFilters)) return
    let active = true

    setLoadingAppointments(true)
    appointmentsApi.list(appointmentFilters)
      .then((items) => {
        if (active) setAppointments(items)
      })
      .catch((error) => {
        if (active) handleRequestError(error)
      })
      .finally(() => {
        if (active) setLoadingAppointments(false)
      })

    return () => {
      active = false
    }
  }, [currentUser?.id, inAgenda, appointmentFilters])

  useEffect(() => {
    if (!currentUser || !inAgenda || currentUser.role === 'DENTIST') return
    let active = true

    dentistsApi.list()
      .then((items) => {
        if (active) setDentists(items)
      })
      .catch((error) => {
        if (active) handleRequestError(error)
      })

    return () => {
      active = false
    }
  }, [currentUser?.id, inAgenda])

  async function signIn(email: string, password: string) {
    const user = await authApi.signIn(email, password)
    setAuthError('')
    setCurrentUser(user)
    setAuthStatus('authenticated')
    setView('dashboard')
  }

  async function reloadPatients() {
    setLoadingPatients(true)
    try {
      setPatients(await patientsApi.list())
    } finally {
      setLoadingPatients(false)
    }
  }

  async function reloadTeam() {
    if (!isAdministrator) return
    setLoadingTeam(true)
    try {
      setTeam(await usersApi.list())
    } finally {
      setLoadingTeam(false)
    }
  }

  async function savePatient(payload: PatientPayload) {
    try {
      if (editingPatient) {
        await patientsApi.update(editingPatient.id, payload)
        notify('Paciente atualizado com sucesso.')
      } else {
        await patientsApi.create(payload)
        notify('Paciente cadastrado com sucesso.')
      }
      await reloadPatients()
      setEditingPatient(null)
      setView('patients')
    } catch (error) {
      handleRequestError(error)
      throw error
    }
  }

  async function deactivatePatient(id: number) {
    if (!canDeactivatePatients) {
      notify('Seu perfil não pode inativar pacientes.', 'error')
      return
    }
    if (!window.confirm('Deseja realmente inativar este paciente?')) return

    try {
      await patientsApi.deactivate(id)
      await reloadPatients()
      if (selectedPatient?.id === id) setSelectedPatient(null)
      notify('Paciente inativado com sucesso.')
    } catch (error) {
      handleRequestError(error)
    }
  }

  async function openPatient(id: number) {
    try {
      setSelectedPatient(await patientsApi.get(id))
      setView('record')
    } catch (error) {
      handleRequestError(error)
    }
  }

  async function createUser(payload: UserCreatePayload) {
    if (!isAdministrator) {
      throw new Error('Somente administradores podem cadastrar usuários.')
    }

    try {
      await usersApi.create(payload)
      await reloadTeam()
      setView('users')
      notify('Usuário cadastrado com sucesso.')
    } catch (error) {
      handleRequestError(error)
      throw error
    }
  }

  async function reloadAppointments() {
    if (hasInvalidPeriod(appointmentFilters)) return
    setLoadingAppointments(true)
    try {
      setAppointments(await appointmentsApi.list(appointmentFilters))
    } finally {
      setLoadingAppointments(false)
    }
  }

  async function saveAppointment(payload: AppointmentPayload) {
    try {
      if (editingAppointment) {
        const rescheduled = payload.dentist_id !== editingAppointment.dentist_id
          || new Date(payload.scheduled_at).getTime() !== appointmentStart(editingAppointment).getTime()
          || payload.duration_minutes !== editingAppointment.duration_minutes
        await appointmentsApi.update(editingAppointment.id, payload)
        notify(rescheduled ? 'Consulta reagendada com sucesso.' : 'Consulta atualizada com sucesso.')
      } else {
        await appointmentsApi.create(payload)
        notify('Consulta agendada com sucesso.')
      }
      setEditingAppointment(null)
      setSelectedAppointment(null)
      setView('agenda')
    } catch (error) {
      handleRequestError(error)
      throw error
    }
  }

  async function changeAppointmentStatus(appointment: Appointment, status: AppointmentStatusChange) {
    if (!currentUser || !availableStatusActions(appointment, currentUser.role).includes(status)) {
      notify('Seu perfil não pode alterar a situação desta consulta.', 'error')
      return
    }
    const action = STATUS_ACTIONS[status]
    if (action.confirmation && !window.confirm(action.confirmation)) return

    try {
      const updated = await appointmentsApi.updateStatus(appointment.id, status)
      if (selectedAppointment?.id === updated.id) setSelectedAppointment(updated)
      await reloadAppointments()
      notify(action.success)
    } catch (error) {
      handleRequestError(error)
    }
  }

  async function openAppointment(id: number) {
    try {
      setSelectedAppointment(await appointmentsApi.get(id))
      setView('appointment')
    } catch (error) {
      handleRequestError(error)
    }
  }

  function navigate(nextView: View) {
    if ((nextView === 'users' || nextView === 'user-form') && !isAdministrator) {
      notify('Somente administradores podem acessar a gestão da equipe.', 'error')
      setView('dashboard')
      return
    }
    if (nextView === 'appointment-form' && !canManageAppointments) {
      notify('Seu perfil não pode cadastrar ou alterar consultas.', 'error')
      setView('agenda')
      return
    }
    setView(nextView)
  }

  if (authStatus === 'loading') {
    return <LoadingScreen />
  }

  if (authStatus === 'unauthenticated' || !currentUser) {
    return <Login onLogin={signIn} initialError={authError} />
  }

  return (
    <div className="app-shell">
      <Sidebar
        view={view}
        user={currentUser}
        onNavigate={navigate}
        onLogout={() => endLocalSession()}
      />
      <main className="main-content">
        <div className="mobile-header">
          <button className="icon-button" aria-label="Abrir menu"><Menu size={22} /></button>
          <Brand compact />
        </div>

        {view === 'dashboard' && (
          <Dashboard
            user={currentUser}
            patientCount={patients.length}
            teamCount={team.length}
            onNavigate={navigate}
          />
        )}
        {view === 'patients' && (
          <Patients
            patients={patients}
            loading={loadingPatients}
            canDeactivate={canDeactivatePatients}
            onNew={() => {
              setEditingPatient(null)
              navigate('patient-form')
            }}
            onOpen={openPatient}
            onEdit={(patient) => {
              setEditingPatient(patient)
              navigate('patient-form')
            }}
            onDeactivate={deactivatePatient}
          />
        )}
        {view === 'patient-form' && (
          <PatientForm
            initial={editingPatient}
            onCancel={() => navigate('patients')}
            onSave={savePatient}
          />
        )}
        {view === 'users' && isAdministrator && (
          <UsersPage
            team={team}
            loading={loadingTeam}
            onNew={() => navigate('user-form')}
          />
        )}
        {view === 'user-form' && isAdministrator && (
          <UserForm onCancel={() => navigate('users')} onSave={createUser} />
        )}
        {view === 'agenda' && (
          <Agenda
            user={currentUser}
            appointments={appointments}
            dentists={dentists}
            filters={appointmentFilters}
            loading={loadingAppointments}
            canManage={canManageAppointments}
            onFiltersChange={setAppointmentFilters}
            onNew={() => {
              setEditingAppointment(null)
              navigate('appointment-form')
            }}
            onOpen={openAppointment}
            onEdit={(appointment) => {
              setEditingAppointment(appointment)
              navigate('appointment-form')
            }}
            onChangeStatus={changeAppointmentStatus}
          />
        )}
        {view === 'appointment-form' && canManageAppointments && (
          <AppointmentForm
            initial={editingAppointment}
            patients={patients}
            dentists={dentists}
            onCancel={() => navigate('agenda')}
            onSave={saveAppointment}
          />
        )}
        {view === 'appointment' && selectedAppointment && (
          <AppointmentDetails
            appointment={selectedAppointment}
            user={currentUser}
            canManage={canManageAppointments}
            onBack={() => navigate('agenda')}
            onEdit={(appointment) => {
              setEditingAppointment(appointment)
              navigate('appointment-form')
            }}
            onChangeStatus={changeAppointmentStatus}
          />
        )}
        {view === 'record' && selectedPatient && (
          <PatientDetails patient={selectedPatient} onBack={() => navigate('patients')} />
        )}
      </main>
      {toast && (
        <div className={`toast ${toast.tone}`} role={toast.tone === 'error' ? 'alert' : 'status'}>
          {toast.tone === 'error' ? <CircleAlert size={18} /> : <Check size={18} />}
          {toast.message}
        </div>
      )}
    </div>
  )
}

function LoadingScreen() {
  return (
    <div className="loading-screen">
      <Brand />
      <p>Verificando sua sessão…</p>
    </div>
  )
}

function Brand({ compact = false }: { compact?: boolean }) {
  return (
    <div className={`brand ${compact ? 'brand-compact' : ''}`}>
      <strong>Lumina</strong>
      <span>ODONTO</span>
    </div>
  )
}

function Sidebar({
  view,
  user,
  onNavigate,
  onLogout,
}: {
  view: View
  user: AuthUser
  onNavigate: (view: View) => void
  onLogout: () => void
}) {
  const items = [
    { id: 'dashboard' as View, label: 'Dashboard', icon: LayoutDashboard },
    { id: 'patients' as View, label: 'Pacientes', icon: Users },
    ...(user.role === 'ADMINISTRATOR'
      ? [{ id: 'users' as View, label: 'Equipe', icon: CircleUserRound }]
      : []),
    { id: 'agenda' as View, label: 'Agenda', icon: CalendarDays },
  ]

  return (
    <aside className="sidebar">
      <Brand />
      <nav>
        {items.map(({ id, label, icon: Icon }) => {
          const active = id === view
            || (id === 'patients' && ['patient-form', 'record'].includes(view))
            || (id === 'users' && view === 'user-form')
            || (id === 'agenda' && ['appointment-form', 'appointment'].includes(view))
          return (
            <button
              key={id}
              className={`nav-item ${active ? 'active' : ''}`}
              onClick={() => onNavigate(id)}
            >
              <span className="nav-icon"><Icon size={18} /></span>
              {label}
            </button>
          )
        })}
      </nav>
      <div className="sidebar-footer">
        <div className="user-chip">
          <span className="avatar small">{initials(user.full_name)}</span>
          <span>
            <b>{user.full_name}</b>
            <small>{ROLE_LABELS[user.role]}</small>
          </span>
          <ChevronDown size={16} />
        </div>
        <button className="logout" onClick={onLogout}><LogOut size={17} /> Sair</button>
      </div>
    </aside>
  )
}

function PageHeader({ title, subtitle, action }: { title: string; subtitle?: string; action?: ReactNode }) {
  return (
    <header className="page-header">
      <div className="header-row">
        <div>
          <h1>{title}</h1>
          {subtitle && <p>{subtitle}</p>}
        </div>
        {action}
      </div>
    </header>
  )
}

function Button({
  children,
  variant = 'primary',
  onClick,
  type = 'button',
  disabled = false,
}: {
  children: ReactNode
  variant?: 'primary' | 'secondary' | 'ghost'
  onClick?: () => void
  type?: 'button' | 'submit'
  disabled?: boolean
}) {
  return (
    <button type={type} className={`button ${variant}`} onClick={onClick} disabled={disabled}>
      {children}
    </button>
  )
}

function Login({
  onLogin,
  initialError,
}: {
  onLogin: (email: string, password: string) => Promise<void>
  initialError: string
}) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState(initialError)
  const [submitting, setSubmitting] = useState(false)

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError('')

    if (!EMAIL_PATTERN.test(email.trim())) {
      setError('Informe um e-mail válido.')
      return
    }
    if (!password) {
      setError('Informe sua senha.')
      return
    }

    setSubmitting(true)
    try {
      await onLogin(email.trim(), password)
    } catch (requestError) {
      setError(getErrorMessage(requestError))
      setPassword('')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="login-page">
      <section className="login-visual">
        <Brand />
        <div className="visual-orb orb-one" />
        <div className="visual-orb orb-two" />
        <div className="visual-copy">
          <span>GESTÃO ODONTOLÓGICA</span>
          <h1>Cuidado inteligente<br />para cada sorriso.</h1>
          <p>Gestão simples, segura e próxima da sua clínica.</p>
        </div>
      </section>
      <section className="login-panel">
        <div className="login-card">
          <div className="login-heading">
            <span className="mobile-kicker">LUMINA ODONTO</span>
            <h2>Acesso da clínica</h2>
            <p>Entre com o usuário cadastrado pela administração.</p>
          </div>
          <form onSubmit={submit} noValidate>
            <label>
              E-mail
              <input
                type="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                autoComplete="email"
                disabled={submitting}
                required
              />
            </label>
            <label>
              Senha
              <input
                type="password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                autoComplete="current-password"
                disabled={submitting}
                required
              />
            </label>
            {error && <p className="form-error" role="alert">{error}</p>}
            <Button type="submit" disabled={submitting}>
              {submitting ? 'Entrando…' : 'Entrar'} <ArrowRight size={18} />
            </Button>
          </form>
          <small className="login-note">Acesso destinado a usuários autorizados.</small>
        </div>
      </section>
    </div>
  )
}

function Dashboard({
  user,
  patientCount,
  teamCount,
  onNavigate,
}: {
  user: AuthUser
  patientCount: number
  teamCount: number
  onNavigate: (view: View) => void
}) {
  const firstName = user.full_name.trim().split(/\s+/)[0]
  const isAdmin = user.role === 'ADMINISTRATOR'

  return (
    <>
      <PageHeader
        title={`Olá, ${firstName}`}
        subtitle={`Você está conectado como ${ROLE_LABELS[user.role]}.`}
      />
      <div className="stats-grid">
        <Stat title="Pacientes ativos" value={String(patientCount)} detail="Dados carregados da API" icon={<Users />} />
        <Stat title="Seu perfil" value={ROLE_LABELS[user.role]} detail="Permissões aplicadas" icon={<Stethoscope />} />
        <Stat
          title="Equipe"
          value={isAdmin ? String(teamCount) : '—'}
          detail={isAdmin ? 'Usuários da clínica' : 'Acesso administrativo'}
          icon={<CircleUserRound />}
        />
      </div>
      <div className="dashboard-grid">
        <section className="panel">
          <div className="panel-heading">
            <div><span className="eyebrow">ACESSO RÁPIDO</span><h2>Módulos da Sprint 04</h2></div>
          </div>
          <div className="module-actions">
            <Button onClick={() => onNavigate('patients')}><Users size={18} /> Gerenciar pacientes</Button>
            {isAdmin && (
              <Button variant="secondary" onClick={() => onNavigate('users')}>
                <CircleUserRound size={18} /> Gerenciar equipe
              </Button>
            )}
          </div>
        </section>
        <section className="panel daily-summary">
          <span className="eyebrow">SESSÃO AUTENTICADA</span>
          <h2>{user.full_name}</h2>
          <p>{user.email}</p>
          <div className="summary-stat"><strong>#{user.clinic_id}</strong><span>Clínica vinculada</span></div>
          <div className="summary-stat"><strong>Ativa</strong><span>Sessão validada pela API</span></div>
        </section>
      </div>
    </>
  )
}

function Stat({ title, value, detail, icon }: { title: string; value: string; detail: string; icon: ReactNode }) {
  return (
    <section className="stat-card">
      <div className="stat-top"><span>{title}</span><span className="stat-icon">{icon}</span></div>
      <strong className={value.length > 8 ? 'stat-text' : ''}>{value}</strong>
      <small>{detail}</small>
    </section>
  )
}

function Patients({
  patients,
  loading,
  canDeactivate,
  onNew,
  onOpen,
  onEdit,
  onDeactivate,
}: {
  patients: Patient[]
  loading: boolean
  canDeactivate: boolean
  onNew: () => void
  onOpen: (id: number) => Promise<void>
  onEdit: (patient: Patient) => void
  onDeactivate: (id: number) => Promise<void>
}) {
  const [query, setQuery] = useState('')
  const filtered = useMemo(() => {
    const normalized = query.toLowerCase()
    return patients.filter((patient) => (
      `${patient.full_name} ${patient.cpf} ${formatCpf(patient.cpf)} ${patient.phone ?? ''} ${formatPhone(patient.phone ?? '')}`.toLowerCase().includes(normalized)
    ))
  }, [patients, query])

  return (
    <>
      <PageHeader
        title="Pacientes"
        subtitle="Dados ativos da clínica, sincronizados com a API."
        action={<Button onClick={onNew}><Plus size={18} /> Novo paciente</Button>}
      />
      <div className="toolbar">
        <label className="search-field">
          <Search size={19} />
          <input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Pesquisar por nome, CPF ou telefone"
          />
        </label>
        <span className="result-count">{loading ? 'Carregando…' : `${filtered.length} pacientes ativos`}</span>
      </div>
      <section className="panel table-panel">
        <div className="table-wrap">
          <table>
            <thead><tr><th>Nome</th><th>CPF</th><th>Telefone</th><th>Ações</th></tr></thead>
            <tbody>
              {!loading && filtered.map((patient) => (
                <tr key={patient.id}>
                  <td>
                    <button className="table-name" onClick={() => void onOpen(patient.id)}>
                      {patient.full_name}
                    </button>
                    <small>Prontuário nº {patient.medical_record_number}</small>
                  </td>
                  <td>{formatCpf(patient.cpf)}</td>
                  <td>{patient.phone ? formatPhone(patient.phone) : '—'}</td>
                  <td>
                    <div className="table-actions">
                      <button onClick={() => void onOpen(patient.id)}>Ver</button>
                      <button onClick={() => onEdit(patient)}><Pencil size={14} /> Editar</button>
                      {canDeactivate && (
                        <button className="danger" onClick={() => void onDeactivate(patient.id)}>Inativar</button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {!loading && filtered.length === 0 && <EmptyState message="Nenhum paciente encontrado." />}
        </div>
      </section>
    </>
  )
}

type PatientFormState = AddressFields & {
  full_name: string
  cpf: string
  medical_record_number: string
  birth_date: string
  phone: string
  email: string
}

function PatientForm({
  initial,
  onCancel,
  onSave,
}: {
  initial: Patient | null
  onCancel: () => void
  onSave: (payload: PatientPayload) => Promise<void>
}) {
  const [form, setForm] = useState<PatientFormState>({
    full_name: initial?.full_name ?? '',
    cpf: formatCpf(initial?.cpf ?? ''),
    medical_record_number: initial?.medical_record_number ?? '',
    birth_date: initial?.birth_date ?? '',
    phone: formatPhone(initial?.phone ?? ''),
    email: initial?.email ?? '',
    ...parseAddress(initial?.address ?? null),
  })
  const [errors, setErrors] = useState<Partial<Record<keyof PatientFormState, string>>>({})
  const [formError, setFormError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  function update(field: keyof PatientFormState, value: string) {
    setForm((current) => ({ ...current, [field]: value }))
    setErrors((current) => ({ ...current, [field]: undefined }))
    setFormError('')
  }

  function validate(): PatientPayload | null {
    const nextErrors: Partial<Record<keyof PatientFormState, string>> = {}
    const cpf = onlyDigits(form.cpf)
    const phone = onlyDigits(form.phone)
    const address = composeAddress(form)

    if (!form.full_name.trim()) nextErrors.full_name = 'Informe o nome completo.'
    if (form.full_name.trim().length > 150) nextErrors.full_name = 'Use no máximo 150 caracteres.'
    if (cpf.length !== 11) nextErrors.cpf = 'O CPF deve conter 11 dígitos.'
    if (!form.medical_record_number.trim()) nextErrors.medical_record_number = 'Informe o número do prontuário.'
    if (form.medical_record_number.trim().length > 30) nextErrors.medical_record_number = 'Use no máximo 30 caracteres.'
    if (!form.birth_date) {
      nextErrors.birth_date = 'Informe a data de nascimento.'
    } else {
      const birthDate = new Date(`${form.birth_date}T00:00:00`)
      if (Number.isNaN(birthDate.getTime()) || birthDate > new Date()) {
        nextErrors.birth_date = 'Informe uma data de nascimento válida.'
      }
    }
    if (form.email && !EMAIL_PATTERN.test(form.email.trim())) nextErrors.email = 'Informe um e-mail válido.'
    if (phone && phone.length !== 10 && phone.length !== 11) nextErrors.phone = 'Informe o telefone com DDD.'

    // Endereços antigos que não foram alterados não são revalidados campo a campo.
    if (address && address !== (initial?.address ?? null)) {
      const cep = onlyDigits(form.cep)
      if (cep && cep.length !== 8) nextErrors.cep = 'O CEP deve conter 8 dígitos.'
      if (!form.street.trim()) nextErrors.street = 'Informe o logradouro.'
      if (!form.number.trim()) nextErrors.number = 'Informe o número ou S/N.'
      if (!form.city.trim()) nextErrors.city = 'Informe a cidade.'
      if (!form.state) nextErrors.state = 'Selecione a UF.'
    }

    setErrors(nextErrors)
    if (Object.keys(nextErrors).length) return null

    return {
      full_name: form.full_name.trim(),
      cpf,
      medical_record_number: form.medical_record_number.trim(),
      birth_date: form.birth_date,
      phone: phone || null,
      email: form.email.trim().toLowerCase() || null,
      address,
    }
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const payload = validate()
    if (!payload) return

    setSubmitting(true)
    setFormError('')
    try {
      await onSave(payload)
    } catch (error) {
      setFormError(getErrorMessage(error))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <>
      <button className="back-link" onClick={onCancel}><ArrowLeft size={18} /> Voltar para pacientes</button>
      <PageHeader
        title={initial ? 'Editar paciente' : 'Cadastrar paciente'}
        subtitle="Mantenha os dados do paciente sempre atualizados."
      />
      <section className="panel form-panel">
        <div className="section-title">
          <span className="section-number">01</span>
          <div><h2>Dados pessoais</h2><p>Informações exigidas pelo cadastro da API.</p></div>
        </div>
        <form className="form-grid" onSubmit={submit} noValidate>
          <FormField label="Nome completo" error={errors.full_name}>
            <input value={form.full_name} onChange={(event) => update('full_name', event.target.value)} maxLength={150} />
          </FormField>
          <FormField label="CPF" error={errors.cpf}>
            <input
              value={form.cpf}
              onChange={(event) => update('cpf', formatCpf(event.target.value))}
              inputMode="numeric"
              placeholder="000.000.000-00"
              maxLength={14}
            />
          </FormField>
          <FormField label="Número do prontuário" error={errors.medical_record_number}>
            <input value={form.medical_record_number} onChange={(event) => update('medical_record_number', event.target.value)} maxLength={30} />
          </FormField>
          <FormField label="Data de nascimento" error={errors.birth_date}>
            <input type="date" value={form.birth_date} onChange={(event) => update('birth_date', event.target.value)} />
          </FormField>
          <FormField label="Telefone" error={errors.phone}>
            <input
              value={form.phone}
              onChange={(event) => update('phone', formatPhone(event.target.value))}
              inputMode="tel"
              placeholder="(00) 00000-0000"
              maxLength={15}
            />
          </FormField>
          <FormField label="E-mail" error={errors.email}>
            <input type="email" value={form.email} onChange={(event) => update('email', event.target.value)} />
          </FormField>
          <div className="section-title form-subsection full-field">
            <span className="section-number">02</span>
            <div><h2>Endereço</h2><p>Opcional. Organizado para a futura consulta automática por CEP.</p></div>
          </div>
          <FormField label="CEP" error={errors.cep}>
            <input
              value={form.cep}
              onChange={(event) => update('cep', formatCep(event.target.value))}
              inputMode="numeric"
              placeholder="00000-000"
              maxLength={9}
            />
          </FormField>
          <FormField label="UF" error={errors.state}>
            <select value={form.state} onChange={(event) => update('state', event.target.value)}>
              <option value="">Selecione</option>
              {BRAZILIAN_STATES.map((state) => <option key={state} value={state}>{state}</option>)}
            </select>
          </FormField>
          <FormField label="Cidade" error={errors.city}>
            <input value={form.city} onChange={(event) => update('city', event.target.value)} maxLength={100} />
          </FormField>
          <FormField label="Bairro" error={errors.district}>
            <input value={form.district} onChange={(event) => update('district', event.target.value)} maxLength={100} />
          </FormField>
          <FormField label="Logradouro" error={errors.street} className="full-field">
            <input value={form.street} onChange={(event) => update('street', event.target.value)} placeholder="Rua, avenida, travessa…" />
          </FormField>
          <FormField label="Número" error={errors.number}>
            <input value={form.number} onChange={(event) => update('number', event.target.value)} maxLength={20} />
          </FormField>
          <FormField label="Complemento" error={errors.complement}>
            <input value={form.complement} onChange={(event) => update('complement', event.target.value)} maxLength={100} />
          </FormField>
          {formError && <p className="form-error full-field" role="alert">{formError}</p>}
          <FormActions cancel={onCancel} label={initial ? 'Salvar alterações' : 'Salvar paciente'} disabled={submitting} />
        </form>
      </section>
    </>
  )
}

function UsersPage({ team, loading, onNew }: { team: UserRead[]; loading: boolean; onNew: () => void }) {
  return (
    <>
      <PageHeader
        title="Equipe"
        subtitle="Usuários da clínica retornados pela API."
        action={<Button onClick={onNew}><Plus size={18} /> Novo usuário</Button>}
      />
      <section className="panel table-panel">
        <div className="table-wrap">
          <table>
            <thead><tr><th>Nome</th><th>E-mail</th><th>Perfil</th><th>Situação</th></tr></thead>
            <tbody>
              {!loading && team.map((user) => (
                <tr key={user.id}>
                  <td className="person-cell">
                    <span className="avatar small">{initials(user.full_name)}</span>
                    <b>{user.full_name}</b>
                  </td>
                  <td>{user.email}</td>
                  <td><span className={`role-pill ${ROLE_TONES[user.role]}`}>{ROLE_LABELS[user.role]}</span></td>
                  <td>{user.is_active ? 'Ativo' : 'Inativo'}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {loading && <EmptyState message="Carregando equipe…" />}
          {!loading && team.length === 0 && <EmptyState message="Nenhum usuário cadastrado." />}
        </div>
      </section>
    </>
  )
}

type UserFormState = {
  full_name: string
  cpf: string
  phone: string
  email: string
  password: string
  role: UserRole
  cro_number: string
  cro_state: string
  specialty: string
}

function UserForm({
  onCancel,
  onSave,
}: {
  onCancel: () => void
  onSave: (payload: UserCreatePayload) => Promise<void>
}) {
  const [form, setForm] = useState<UserFormState>({
    full_name: '',
    cpf: '',
    phone: '',
    email: '',
    password: '',
    role: 'RECEPTIONIST',
    cro_number: '',
    cro_state: '',
    specialty: '',
  })
  const [errors, setErrors] = useState<Partial<Record<keyof UserFormState, string>>>({})
  const [formError, setFormError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const isDentist = form.role === 'DENTIST'

  function update<K extends keyof UserFormState>(field: K, value: UserFormState[K]) {
    setForm((current) => ({ ...current, [field]: value }))
    setErrors((current) => ({ ...current, [field]: undefined }))
    setFormError('')
  }

  function validate(): UserCreatePayload | null {
    const nextErrors: Partial<Record<keyof UserFormState, string>> = {}
    const cpf = onlyDigits(form.cpf)

    if (!form.full_name.trim()) nextErrors.full_name = 'Informe o nome completo.'
    if (form.full_name.trim().length > 150) nextErrors.full_name = 'Use no máximo 150 caracteres.'
    if (cpf.length !== 11) nextErrors.cpf = 'O CPF deve conter 11 dígitos.'
    if (!EMAIL_PATTERN.test(form.email.trim())) nextErrors.email = 'Informe um e-mail válido.'
    if (form.password.length < 8) nextErrors.password = 'A senha deve ter pelo menos 8 caracteres.'
    if (form.password.length > 128) nextErrors.password = 'A senha deve ter no máximo 128 caracteres.'
    if (form.phone.length > 20) nextErrors.phone = 'Use no máximo 20 caracteres.'
    if (isDentist) {
      if (!form.cro_number.trim()) nextErrors.cro_number = 'Informe o número do CRO.'
      if (form.cro_number.trim().length > 30) nextErrors.cro_number = 'Use no máximo 30 caracteres.'
      if (!form.cro_state) nextErrors.cro_state = 'Selecione a UF do CRO.'
      if (form.specialty.trim().length > 100) nextErrors.specialty = 'Use no máximo 100 caracteres.'
    }

    setErrors(nextErrors)
    if (Object.keys(nextErrors).length) return null

    return {
      full_name: form.full_name.trim(),
      cpf,
      phone: form.phone.trim() || null,
      email: form.email.trim().toLowerCase(),
      password: form.password,
      role: form.role,
      ...(isDentist
        ? {
          cro_number: form.cro_number.trim().toUpperCase(),
          cro_state: form.cro_state,
          specialty: form.specialty.trim() || null,
        }
        : {}),
    }
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const payload = validate()
    if (!payload) return

    setSubmitting(true)
    setFormError('')
    try {
      await onSave(payload)
    } catch (error) {
      setFormError(getErrorMessage(error))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <>
      <button className="back-link" onClick={onCancel}><ArrowLeft size={18} /> Voltar para equipe</button>
      <PageHeader title="Novo usuário" subtitle="Cadastre um profissional e defina seu perfil de acesso." />
      <section className="panel form-panel">
        <div className="section-title">
          <span className="section-number">02</span>
          <div><h2>Dados de acesso</h2><p>Somente administradores podem concluir este cadastro.</p></div>
        </div>
        <form className="form-grid" onSubmit={submit} noValidate>
          <FormField label="Nome completo" error={errors.full_name}>
            <input value={form.full_name} onChange={(event) => update('full_name', event.target.value)} maxLength={150} />
          </FormField>
          <FormField label="CPF" error={errors.cpf}>
            <input value={form.cpf} onChange={(event) => update('cpf', event.target.value)} inputMode="numeric" maxLength={14} />
          </FormField>
          <FormField label="E-mail" error={errors.email}>
            <input type="email" value={form.email} onChange={(event) => update('email', event.target.value)} />
          </FormField>
          <FormField label="Telefone" error={errors.phone}>
            <input value={form.phone} onChange={(event) => update('phone', event.target.value)} maxLength={20} />
          </FormField>
          <FormField label="Senha de acesso" error={errors.password}>
            <input
              type="password"
              value={form.password}
              onChange={(event) => update('password', event.target.value)}
              autoComplete="new-password"
              minLength={8}
              maxLength={128}
            />
          </FormField>
          <FormField label="Perfil" error={errors.role}>
            <select value={form.role} onChange={(event) => update('role', event.target.value as UserRole)}>
              <option value="ADMINISTRATOR">Administrador</option>
              <option value="RECEPTIONIST">Recepcionista</option>
              <option value="DENTIST">Dentista</option>
            </select>
          </FormField>
          {isDentist && (
            <>
              <FormField label="Número do CRO" error={errors.cro_number}>
                <input value={form.cro_number} onChange={(event) => update('cro_number', event.target.value)} maxLength={30} />
              </FormField>
              <FormField label="UF do CRO" error={errors.cro_state}>
                <select value={form.cro_state} onChange={(event) => update('cro_state', event.target.value)}>
                  <option value="">Selecione a UF</option>
                  {BRAZILIAN_STATES.map((state) => <option key={state} value={state}>{state}</option>)}
                </select>
              </FormField>
              <FormField label="Especialidade (opcional)" error={errors.specialty} className="full-field">
                <input value={form.specialty} onChange={(event) => update('specialty', event.target.value)} maxLength={100} />
              </FormField>
            </>
          )}
          {formError && <p className="form-error full-field" role="alert">{formError}</p>}
          <FormActions cancel={onCancel} label="Criar usuário" disabled={submitting} />
        </form>
      </section>
    </>
  )
}

function FormField({
  label,
  error,
  className = '',
  children,
}: {
  label: string
  error?: string
  className?: string
  children: ReactNode
}) {
  return (
    <label className={className}>
      {label}
      {children}
      {error && <span className="field-error">{error}</span>}
    </label>
  )
}

function FormActions({
  cancel,
  label,
  disabled,
}: {
  cancel: () => void
  label: string
  disabled: boolean
}) {
  return (
    <div className="form-actions">
      <Button variant="secondary" onClick={cancel} disabled={disabled}>Cancelar</Button>
      <Button type="submit" disabled={disabled}>
        <Check size={18} /> {disabled ? 'Salvando…' : label}
      </Button>
    </div>
  )
}

function PatientDetails({ patient, onBack }: { patient: Patient; onBack: () => void }) {
  return (
    <>
      <button className="back-link" onClick={onBack}><ArrowLeft size={18} /> Pacientes</button>
      <section className="patient-hero panel">
        <span className="avatar hero-avatar">{initials(patient.full_name)}</span>
        <div>
          <span className="eyebrow">PRONTUÁRIO Nº {patient.medical_record_number}</span>
          <h1>{patient.full_name}</h1>
          <p>{patient.phone ? formatPhone(patient.phone) : 'Sem telefone'} · {patient.email ?? 'Sem e-mail'}</p>
        </div>
        <span className="status-pill"><Activity size={15} /> Cadastro ativo</span>
      </section>
      <section className="panel out-of-scope-card">
        <span className="eyebrow">DADOS DO PACIENTE</span>
        <h2>Cadastro integrado</h2>
        <p>CPF: {formatCpf(patient.cpf)}</p>
        <p>Data de nascimento: {patient.birth_date}</p>
        <p>Endereço: {patient.address ?? 'Não informado'}</p>
        <hr />
        <p>Prontuário clínico e evoluções permanecem fora do escopo desta Sprint.</p>
      </section>
    </>
  )
}

function AppointmentStatusPill({ status }: { status: AppointmentStatus }) {
  return (
    <span className={`role-pill ${APPOINTMENT_STATUS_TONES[status]}`}>
      {APPOINTMENT_STATUS_LABELS[status]}
    </span>
  )
}

function Agenda({
  user,
  appointments,
  dentists,
  filters,
  loading,
  canManage,
  onFiltersChange,
  onNew,
  onOpen,
  onEdit,
  onChangeStatus,
}: {
  user: AuthUser
  appointments: Appointment[]
  dentists: Dentist[]
  filters: AppointmentFilters
  loading: boolean
  canManage: boolean
  onFiltersChange: (filters: AppointmentFilters) => void
  onNew: () => void
  onOpen: (id: number) => Promise<void>
  onEdit: (appointment: Appointment) => void
  onChangeStatus: (appointment: Appointment, status: AppointmentStatusChange) => Promise<void>
}) {
  const isDentist = user.role === 'DENTIST'
  const invalidPeriod = hasInvalidPeriod(filters)
  const sorted = useMemo(() => (
    [...appointments].sort((a, b) => appointmentStart(a).getTime() - appointmentStart(b).getTime())
  ), [appointments])

  function update<K extends keyof AppointmentFilters>(field: K, value: AppointmentFilters[K]) {
    onFiltersChange({ ...filters, [field]: value })
  }

  return (
    <>
      <PageHeader
        title="Agenda"
        subtitle={isDentist
          ? 'Seus atendimentos, sincronizados com a API.'
          : 'Consultas da clínica, sincronizadas com a API.'}
        action={canManage ? <Button onClick={onNew}><Plus size={18} /> Nova consulta</Button> : undefined}
      />
      <div className="agenda-filters">
        <label>
          Data inicial
          <input
            type="date"
            value={filters.start_date ?? ''}
            onChange={(event) => update('start_date', event.target.value || undefined)}
          />
        </label>
        <label>
          Data final
          <input
            type="date"
            value={filters.end_date ?? ''}
            onChange={(event) => update('end_date', event.target.value || undefined)}
          />
        </label>
        {!isDentist && (
          <label>
            Dentista
            <select
              value={filters.dentist_id ?? ''}
              onChange={(event) => update('dentist_id', event.target.value ? Number(event.target.value) : undefined)}
            >
              <option value="">Todos os dentistas</option>
              {dentists.map((dentist) => (
                <option key={dentist.id} value={dentist.id}>{dentist.full_name}</option>
              ))}
            </select>
          </label>
        )}
        <label>
          Situação
          <select
            value={filters.status ?? ''}
            onChange={(event) => update('status', (event.target.value || undefined) as AppointmentStatus | undefined)}
          >
            <option value="">Todas as situações</option>
            {(Object.entries(APPOINTMENT_STATUS_LABELS) as [AppointmentStatus, string][]).map(([status, label]) => (
              <option key={status} value={status}>{label}</option>
            ))}
          </select>
        </label>
      </div>
      {invalidPeriod
        ? <p className="form-error agenda-feedback" role="alert">A data final deve ser igual ou posterior à data inicial.</p>
        : <p className="result-count agenda-feedback">{loading ? 'Carregando…' : `${sorted.length} consultas encontradas`}</p>}
      <section className="panel table-panel">
        <div className="table-wrap">
          <table className="agenda-table">
            <thead>
              <tr>
                <th>Data e horário</th>
                <th>Paciente</th>
                {!isDentist && <th>Dentista</th>}
                <th>Situação</th>
                <th>Ações</th>
              </tr>
            </thead>
            <tbody>
              {!loading && sorted.map((appointment) => (
                <tr key={appointment.id}>
                  <td>
                    <button className="table-name" onClick={() => void onOpen(appointment.id)}>
                      {SHORT_DATE_FORMAT.format(appointmentStart(appointment))}
                    </button>
                    <small>{formatTimeRange(appointment)} · {appointment.duration_minutes} min</small>
                  </td>
                  <td>{appointment.patient_name}</td>
                  {!isDentist && <td>{appointment.dentist_name}</td>}
                  <td><AppointmentStatusPill status={appointment.status} /></td>
                  <td>
                    <div className="table-actions">
                      <button onClick={() => void onOpen(appointment.id)}>Ver</button>
                      {canManage && isActiveAppointment(appointment) && (
                        <button onClick={() => onEdit(appointment)}><Pencil size={14} /> Editar</button>
                      )}
                      {availableStatusActions(appointment, user.role).map((status) => (
                        <button
                          key={status}
                          className={status === 'CANCELED' ? 'danger' : ''}
                          onClick={() => void onChangeStatus(appointment, status)}
                        >
                          {STATUS_ACTIONS[status].label}
                        </button>
                      ))}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {loading && <EmptyState message="Carregando agenda…" />}
          {!loading && sorted.length === 0 && <EmptyState message="Nenhuma consulta encontrada para os filtros selecionados." />}
        </div>
      </section>
    </>
  )
}

type AppointmentFormState = {
  patient_id: string
  dentist_id: string
  date: string
  time: string
  duration_minutes: string
  notes: string
}

function AppointmentForm({
  initial,
  patients,
  dentists,
  onCancel,
  onSave,
}: {
  initial: Appointment | null
  patients: Patient[]
  dentists: Dentist[]
  onCancel: () => void
  onSave: (payload: AppointmentPayload) => Promise<void>
}) {
  const initialStart = initial ? appointmentStart(initial) : null
  const [form, setForm] = useState<AppointmentFormState>({
    patient_id: initial ? String(initial.patient_id) : '',
    dentist_id: initial ? String(initial.dentist_id) : '',
    date: initialStart ? toDateInput(initialStart) : '',
    time: initialStart ? toTimeInput(initialStart) : '',
    duration_minutes: String(initial?.duration_minutes ?? DEFAULT_DURATION),
    notes: initial?.notes ?? '',
  })
  const [errors, setErrors] = useState<Partial<Record<keyof AppointmentFormState, string>>>({})
  const [formError, setFormError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const patientOptions: SelectOption[] = patients.map(({ id, full_name }) => ({ id, full_name }))
  if (initial && !patientOptions.some((patient) => patient.id === initial.patient_id)) {
    patientOptions.push({ id: initial.patient_id, full_name: initial.patient_name })
  }
  const dentistOptions: SelectOption[] = dentists
    .filter((dentist) => dentist.is_active)
    .map(({ id, full_name, specialty }) => ({ id, full_name: specialty ? `${full_name} · ${specialty}` : full_name }))
  if (initial && !dentistOptions.some((dentist) => dentist.id === initial.dentist_id)) {
    dentistOptions.push({ id: initial.dentist_id, full_name: initial.dentist_name })
  }
  const durationOptions = initial && !DURATION_OPTIONS.includes(initial.duration_minutes)
    ? [...DURATION_OPTIONS, initial.duration_minutes].sort((a, b) => a - b)
    : DURATION_OPTIONS

  function update(field: keyof AppointmentFormState, value: string) {
    setForm((current) => ({ ...current, [field]: value }))
    setErrors((current) => ({ ...current, [field]: undefined }))
    setFormError('')
  }

  function validate(): AppointmentPayload | null {
    const nextErrors: Partial<Record<keyof AppointmentFormState, string>> = {}
    const duration = Number(form.duration_minutes)
    const scheduledAt = new Date(`${form.date}T${form.time}:00`)

    if (!form.patient_id) nextErrors.patient_id = 'Selecione o paciente.'
    if (!form.dentist_id) nextErrors.dentist_id = 'Selecione o dentista.'
    if (!form.date) nextErrors.date = 'Informe a data da consulta.'
    if (!form.time) nextErrors.time = 'Informe o horário da consulta.'
    if (form.date && form.time) {
      if (Number.isNaN(scheduledAt.getTime())) {
        nextErrors.date = 'Informe uma data válida.'
      } else if (scheduledAt <= new Date()) {
        // A API revalida o horário em qualquer alteração, inclusive quando só as observações mudam.
        nextErrors.time = 'Escolha uma data e um horário futuros.'
      }
    }
    if (!Number.isInteger(duration) || duration <= 0) nextErrors.duration_minutes = 'Informe uma duração válida.'

    setErrors(nextErrors)
    if (Object.keys(nextErrors).length) return null

    return {
      patient_id: Number(form.patient_id),
      dentist_id: Number(form.dentist_id),
      scheduled_at: scheduledAt.toISOString(),
      duration_minutes: duration,
      notes: form.notes.trim() || null,
    }
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const payload = validate()
    if (!payload) return

    setSubmitting(true)
    setFormError('')
    try {
      await onSave(payload)
    } catch (error) {
      if (error instanceof ApiError && error.status === 409) {
        setErrors((current) => ({ ...current, time: 'Horário indisponível para o dentista selecionado.' }))
      }
      setFormError(getErrorMessage(error))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <>
      <button className="back-link" onClick={onCancel}><ArrowLeft size={18} /> Voltar para agenda</button>
      <PageHeader
        title={initial ? 'Editar consulta' : 'Nova consulta'}
        subtitle={initial
          ? 'Atualize os dados ou reagende o atendimento.'
          : 'Agende um atendimento para um paciente da clínica.'}
      />
      <section className="panel form-panel">
        <div className="section-title">
          <span className="section-number">01</span>
          <div><h2>Dados da consulta</h2><p>Paciente, profissional e horário do atendimento.</p></div>
        </div>
        <form className="form-grid" onSubmit={submit} noValidate>
          <FormField label="Paciente" error={errors.patient_id}>
            <select value={form.patient_id} onChange={(event) => update('patient_id', event.target.value)}>
              <option value="">Selecione o paciente</option>
              {patientOptions.map((patient) => (
                <option key={patient.id} value={patient.id}>{patient.full_name}</option>
              ))}
            </select>
          </FormField>
          <FormField label="Dentista" error={errors.dentist_id}>
            <select value={form.dentist_id} onChange={(event) => update('dentist_id', event.target.value)}>
              <option value="">{dentistOptions.length ? 'Selecione o dentista' : 'Nenhum dentista disponível'}</option>
              {dentistOptions.map((dentist) => (
                <option key={dentist.id} value={dentist.id}>{dentist.full_name}</option>
              ))}
            </select>
          </FormField>
          <FormField label="Data" error={errors.date}>
            <input
              type="date"
              value={form.date}
              min={initial ? undefined : toDateInput(new Date())}
              onChange={(event) => update('date', event.target.value)}
            />
          </FormField>
          <FormField label="Horário" error={errors.time}>
            <input type="time" value={form.time} onChange={(event) => update('time', event.target.value)} />
          </FormField>
          <FormField label="Duração" error={errors.duration_minutes}>
            <select value={form.duration_minutes} onChange={(event) => update('duration_minutes', event.target.value)}>
              {durationOptions.map((minutes) => (
                <option key={minutes} value={minutes}>{minutes} minutos</option>
              ))}
            </select>
          </FormField>
          <FormField label="Observações" className="full-field">
            <textarea value={form.notes} onChange={(event) => update('notes', event.target.value)} rows={4} />
          </FormField>
          {formError && <p className="form-error full-field" role="alert">{formError}</p>}
          <FormActions cancel={onCancel} label={initial ? 'Salvar alterações' : 'Agendar consulta'} disabled={submitting} />
        </form>
      </section>
    </>
  )
}

function AppointmentDetails({
  appointment,
  user,
  canManage,
  onBack,
  onEdit,
  onChangeStatus,
}: {
  appointment: Appointment
  user: AuthUser
  canManage: boolean
  onBack: () => void
  onEdit: (appointment: Appointment) => void
  onChangeStatus: (appointment: Appointment, status: AppointmentStatusChange) => Promise<void>
}) {
  const statusActions = availableStatusActions(appointment, user.role)
  const editable = canManage && isActiveAppointment(appointment)

  return (
    <>
      <button className="back-link" onClick={onBack}><ArrowLeft size={18} /> Agenda</button>
      <PageHeader
        title={appointment.patient_name}
        subtitle={`${DATE_FORMAT.format(appointmentStart(appointment))} · ${formatTimeRange(appointment)}`}
        action={<AppointmentStatusPill status={appointment.status} />}
      />
      <section className="panel">
        <div className="section-title">
          <span className="section-number"><CalendarDays size={16} /></span>
          <div><h2>Detalhes da consulta</h2><p>Consulta nº {appointment.id}</p></div>
        </div>
        <dl className="details-grid">
          <div><dt>Paciente</dt><dd>{appointment.patient_name}</dd></div>
          <div><dt>Dentista</dt><dd>{appointment.dentist_name}</dd></div>
          <div><dt>Data</dt><dd>{DATE_FORMAT.format(appointmentStart(appointment))}</dd></div>
          <div><dt>Horário</dt><dd>{formatTimeRange(appointment)}</dd></div>
          <div><dt>Duração</dt><dd>{appointment.duration_minutes} minutos</dd></div>
          <div><dt>Situação</dt><dd>{APPOINTMENT_STATUS_LABELS[appointment.status]}</dd></div>
          <div className="full-field"><dt>Observações</dt><dd>{appointment.notes ?? 'Nenhuma observação registrada.'}</dd></div>
        </dl>
        {(editable || statusActions.length > 0) && (
          <div className="form-actions">
            {editable && (
              <Button variant="secondary" onClick={() => onEdit(appointment)}><Pencil size={16} /> Editar</Button>
            )}
            {statusActions.map((status) => (
              <Button
                key={status}
                variant={status === 'CANCELED' || status === 'NO_SHOW' ? 'secondary' : 'primary'}
                onClick={() => void onChangeStatus(appointment, status)}
              >
                {STATUS_ACTIONS[status].label}
              </Button>
            ))}
          </div>
        )}
      </section>
    </>
  )
}

function EmptyState({ message }: { message: string }) {
  return <div className="empty-state">{message}</div>
}
