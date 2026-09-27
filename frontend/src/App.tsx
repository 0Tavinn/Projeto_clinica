import { useEffect, useMemo, useState } from 'react'
import type { FormEvent, ReactNode } from 'react'
import {
  Activity,
  ArrowLeft,
  ArrowRight,
  CalendarDays,
  Check,
  ChevronDown,
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
  authApi,
  getErrorMessage,
  patientsApi,
  usersApi,
} from './api'
import type {
  AuthUser,
  Patient,
  PatientPayload,
  UserCreatePayload,
  UserRead,
  UserRole,
} from './api'

type View = 'dashboard' | 'patients' | 'patient-form' | 'users' | 'user-form' | 'agenda' | 'record'
type AuthStatus = 'loading' | 'authenticated' | 'unauthenticated'
type Tone = 'blue' | 'green' | 'gray'

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

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

function onlyDigits(value: string) {
  return value.replace(/\D/g, '')
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
  const [toast, setToast] = useState('')
  const [authError, setAuthError] = useState('')

  const isAdministrator = currentUser?.role === 'ADMINISTRATOR'
  const canDeactivatePatients = currentUser?.role === 'ADMINISTRATOR'
    || currentUser?.role === 'RECEPTIONIST'

  function notify(message: string) {
    setToast(message)
    window.setTimeout(() => setToast(''), 3200)
  }

  function endLocalSession(message?: string) {
    authApi.logout()
    setCurrentUser(null)
    setAuthStatus('unauthenticated')
    setPatients([])
    setTeam([])
    setSelectedPatient(null)
    setEditingPatient(null)
    setView('dashboard')
    if (message) setAuthError(message)
  }

  function handleRequestError(error: unknown) {
    const message = getErrorMessage(error)
    if (error instanceof ApiError && error.status === 401) {
      endLocalSession(message)
    } else {
      notify(message)
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
      notify('Seu perfil não pode inativar pacientes.')
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

  function navigate(nextView: View) {
    if ((nextView === 'users' || nextView === 'user-form') && !isAdministrator) {
      notify('Somente administradores podem acessar a gestão da equipe.')
      setView('dashboard')
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
        {view === 'agenda' && <OutOfScopePage title="Agenda" />}
        {view === 'record' && selectedPatient && (
          <PatientDetails patient={selectedPatient} onBack={() => navigate('patients')} />
        )}
      </main>
      {toast && <div className="toast"><Check size={18} />{toast}</div>}
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
      `${patient.full_name} ${patient.cpf} ${patient.phone ?? ''}`.toLowerCase().includes(normalized)
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
                  <td>{patient.cpf}</td>
                  <td>{patient.phone ?? '—'}</td>
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

type PatientFormState = {
  full_name: string
  cpf: string
  medical_record_number: string
  birth_date: string
  phone: string
  email: string
  address: string
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
    cpf: initial?.cpf ?? '',
    medical_record_number: initial?.medical_record_number ?? '',
    birth_date: initial?.birth_date ?? '',
    phone: initial?.phone ?? '',
    email: initial?.email ?? '',
    address: initial?.address ?? '',
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
    if (form.phone.length > 20) nextErrors.phone = 'Use no máximo 20 caracteres.'

    setErrors(nextErrors)
    if (Object.keys(nextErrors).length) return null

    return {
      full_name: form.full_name.trim(),
      cpf,
      medical_record_number: form.medical_record_number.trim(),
      birth_date: form.birth_date,
      phone: form.phone.trim() || null,
      email: form.email.trim().toLowerCase() || null,
      address: form.address.trim() || null,
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
            <input value={form.cpf} onChange={(event) => update('cpf', event.target.value)} inputMode="numeric" maxLength={14} />
          </FormField>
          <FormField label="Número do prontuário" error={errors.medical_record_number}>
            <input value={form.medical_record_number} onChange={(event) => update('medical_record_number', event.target.value)} maxLength={30} />
          </FormField>
          <FormField label="Data de nascimento" error={errors.birth_date}>
            <input type="date" value={form.birth_date} onChange={(event) => update('birth_date', event.target.value)} />
          </FormField>
          <FormField label="Telefone" error={errors.phone}>
            <input value={form.phone} onChange={(event) => update('phone', event.target.value)} maxLength={20} />
          </FormField>
          <FormField label="E-mail" error={errors.email}>
            <input type="email" value={form.email} onChange={(event) => update('email', event.target.value)} />
          </FormField>
          <FormField label="Endereço" className="full-field">
            <input value={form.address} onChange={(event) => update('address', event.target.value)} />
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
  })
  const [errors, setErrors] = useState<Partial<Record<keyof UserFormState, string>>>({})
  const [formError, setFormError] = useState('')
  const [submitting, setSubmitting] = useState(false)

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

    setErrors(nextErrors)
    if (Object.keys(nextErrors).length) return null

    return {
      full_name: form.full_name.trim(),
      cpf,
      phone: form.phone.trim() || null,
      email: form.email.trim().toLowerCase(),
      password: form.password,
      role: form.role,
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
          <p>{patient.phone ?? 'Sem telefone'} · {patient.email ?? 'Sem e-mail'}</p>
        </div>
        <span className="status-pill"><Activity size={15} /> Cadastro ativo</span>
      </section>
      <section className="panel out-of-scope-card">
        <span className="eyebrow">DADOS DO PACIENTE</span>
        <h2>Cadastro integrado</h2>
        <p>CPF: {patient.cpf}</p>
        <p>Data de nascimento: {patient.birth_date}</p>
        <p>Endereço: {patient.address ?? 'Não informado'}</p>
        <hr />
        <p>Prontuário clínico e evoluções permanecem fora do escopo desta Sprint.</p>
      </section>
    </>
  )
}

function OutOfScopePage({ title }: { title: string }) {
  return (
    <>
      <PageHeader title={title} subtitle="Módulo preservado para uma entrega futura." />
      <section className="panel out-of-scope-card">
        <CalendarDays size={38} />
        <h2>Fora do escopo da Sprint 04</h2>
        <p>Este módulo ainda não realiza operações e não apresenta dados fictícios.</p>
      </section>
    </>
  )
}

function EmptyState({ message }: { message: string }) {
  return <div className="empty-state">{message}</div>
}
