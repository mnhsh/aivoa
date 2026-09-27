import { useRef, useState, useEffect } from 'react'
import { NavLink, Route, Routes, useNavigate } from 'react-router-dom'
import { useDispatch, useSelector } from 'react-redux'
import {
  AlertCircle,
  Bell,
  Bot,
  Check,
  ChevronRight,
  FileText,
  Filter,
  Plus,
  Search,
  Send,
  ShieldCheck,
  Sparkles,
  UploadCloud,
  Zap,
} from 'lucide-react'
import type { RootState, AppDispatch } from './store'
import {
  applyExtractedFields,
  setConfidenceScores,
  clearHighlights,
  resetForm,
  setField,
  submit,
  setExtractionProgress,
} from './store'
import { extractDeviationData } from './utils/extractor'
import { extractTextFromPdf } from './utils/pdfParser'
import { deviations as mockDeviations } from './data'

const cx = (...items: (string | false | undefined)[]) => items.filter(Boolean).join(' ')

function Header() {
  return (
    <header className="app-header">
      <div className="header-left">
        <NavLink to="/" className="brand-wrap">
          <div className="brand-logo-mark">
            <span />
            <span />
          </div>
          <span className="brand-text">AIVOA</span>
          <small className="brand-subtext">Deviation Intelligence</small>
        </NavLink>
        <nav className="header-nav">
          <NavLink to="/deviations/new" className={({ isActive }) => cx('nav-link', isActive && 'active')}>
            Log Deviation
          </NavLink>
          <NavLink to="/deviations" end className={({ isActive }) => cx('nav-link', isActive && 'active')}>
            All Deviations
          </NavLink>
        </nav>
      </div>
      <div className="header-right">
        <div className="ai-status-indicator">
          <span className="pulse-green-dot" />
          <span>AI Copilot Active</span>
        </div>
        <button className="icon-btn" aria-label="Notifications" title="Notifications">
          <Bell size={18} />
          <span className="bell-dot" />
        </button>
        <div className="user-avatar" title="MH User">MH</div>
      </div>
    </header>
  )
}

function AllDeviationsPage() {
  const navigate = useNavigate()
  const [searchTerm, setSearchTerm] = useState('')
  const [severityFilter, setSeverityFilter] = useState<string>('All')

  const filtered = mockDeviations.filter((item) => {
    const matchesSearch =
      item.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.product.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.batch.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.owner.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesSeverity = severityFilter === 'All' || item.severity.toLowerCase() === severityFilter.toLowerCase()
    return matchesSearch && matchesSeverity
  })

  return (
    <div className="all-deviations-container">
      <div className="all-header">
        <div>
          <h1>All Deviation Records</h1>
          <p>Monitor, investigate and review deviation logs across your quality workspace.</p>
        </div>
        <button className="btn btn-primary" onClick={() => navigate('/deviations/new')}>
          <Plus size={16} /> Log New Deviation
        </button>
      </div>

      <div className="table-toolbar">
        <div className="search-bar">
          <Search size={16} className="search-icon" />
          <input
            type="text"
            placeholder="Search by ID, title, product, batch, or owner..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>

        <div className="filter-pills">
          <span className="filter-label"><Filter size={13} /> Severity:</span>
          {['All', 'Critical', 'High', 'Medium', 'Low'].map((sev) => (
            <button
              key={sev}
              className={cx('filter-pill', severityFilter === sev && 'active')}
              onClick={() => setSeverityFilter(sev)}
            >
              {sev}
            </button>
          ))}
        </div>
      </div>

      <div className="table-card shadow-card">
        <table className="deviations-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Deviation Title</th>
              <th>Product</th>
              <th>Batch</th>
              <th>Severity</th>
              <th>Status</th>
              <th>Created</th>
              <th>Owner</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((item) => (
              <tr key={item.id} onClick={() => navigate(`/deviations/new`)}>
                <td className="mono-id">{item.id}</td>
                <td>
                  <div className="title-cell">
                    <strong>{item.title}</strong>
                    {item.aiAssisted && <span className="ai-badge"><Sparkles size={11} /> AI Assisted</span>}
                  </div>
                </td>
                <td>{item.product}</td>
                <td className="mono-batch">{item.batch}</td>
                <td>
                  <span className={cx('badge-severity', item.severity.toLowerCase())}>
                    {item.severity}
                  </span>
                </td>
                <td>
                  <span className={cx('badge-status', item.status.toLowerCase().replace(/\s+/g, '-'))}>
                    {item.status}
                  </span>
                </td>
                <td>{item.created}</td>
                <td>
                  <div className="owner-cell">
                    <div className="avatar-mini">{item.owner.split(' ').map((n) => n[0]).join('')}</div>
                    <span>{item.owner}</span>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function LogDeviationPage() {
  const dispatch = useDispatch<AppDispatch>()
  const navigate = useNavigate()
  const { form, applied, submitted, isExtracting, extractionProgress, highlightedFields, confidenceScores } = useSelector(
    (s: RootState) => s.deviation
  )

  const [activeTab, setActiveTab] = useState<'upload' | 'chips' | 'reasoning' | 'chat'>('upload')
  const [pasteText, setPasteText] = useState('')
  const [chatInput, setChatInput] = useState('')
  const [selectedFileName, setSelectedFileName] = useState<string | null>(null)
  const [aiResponseText, setAiResponseText] = useState<string | null>(null)
  const [chatMessages, setChatMessages] = useState<Array<{ role: 'assistant' | 'user'; text: string }>>([
    {
      role: 'assistant',
      text: 'Hello! I am your AI Quality Assistant. Drag & drop a PDF report, paste raw incident notes, or click ⚡ Load Sample Excursion above to auto-extract structured deviation fields.',
    },
  ])

  const fileInputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (highlightedFields.length > 0) {
      const timer = setTimeout(() => {
        dispatch(clearHighlights())
      }, 2000)
      return () => clearTimeout(timer)
    }
  }, [highlightedFields, dispatch])

  const handleFieldChange = (key: keyof typeof form) => (value: string) => {
    dispatch(setField({ key, value }))
  }

  const runExtraction = (rawText: string, fileName?: string) => {
    dispatch(setExtractionProgress({ isExtracting: true, progress: 15 }))
    let progress = 15

    const interval = setInterval(() => {
      progress += 25
      if (progress >= 100) {
        progress = 100
        clearInterval(interval)
        dispatch(setExtractionProgress({ isExtracting: false, progress: 100 }))

        const result = extractDeviationData(rawText)
        const stringFields: Record<string, string> = {
          site: result.site,
          occurrenceDate: result.occurrenceDate,
          title: result.title,
          source: result.source,
          product: result.product,
          batch: result.batch,
          description: result.description,
          initialImpact: result.initialImpact,
          initialSeverity: result.initialSeverity,
          aiReasoning: result.aiReasoning,
        }
        dispatch(applyExtractedFields(stringFields))
        dispatch(setConfidenceScores(result.confidenceScores))

        const count = Object.keys(stringFields).filter((k) => Boolean(stringFields[k])).length
        const msg = fileName
          ? `Parsed PDF document "${fileName}". Extracted ${count} field(s) & generated severity reasoning!`
          : `Extracted ${count} field(s) from provided details. Form & severity reasoning updated live!`

        setAiResponseText(msg)
        setChatMessages((prev) => [
          ...prev,
          { role: 'assistant', text: msg },
        ])
        setActiveTab('reasoning')
      } else {
        dispatch(setExtractionProgress({ isExtracting: true, progress }))
      }
    }, 180)
  }

  const handleSampleLoad = () => {
    const sampleText = `DEVIATION INCIDENT REPORT
Site: Unit-1 API Manufacturing Plant
Date: 2026-09-27
Title: Temperature Excursion in Reactor 3 during API Batch Processing
Product: API-ACM-01
Batch: B240918
Source: Internal Deviation
Impact: Potential Quality Impact
Severity: High
Description: During API-ACM-01 batch B240918 processing in Unit-1, reactor temperature reached 86.5°C and remained above the approved limit of 82°C for 18 minutes. Heating was halted and QA notified.`
    setSelectedFileName('Sample_Excursion_Report.pdf')
    runExtraction(sampleText, 'Sample_Excursion_Report.pdf')
  }

  const handleFileDrop = async (file?: File) => {
    if (!file) return
    setSelectedFileName(file.name)

    let content = ''
    if (file.name.toLowerCase().endsWith('.pdf') || file.type === 'application/pdf') {
      content = await extractTextFromPdf(file)
    } else {
      content = await file.text()
    }

    runExtraction(content, file.name)
  }

  const handlePasteExtract = () => {
    if (!pasteText.trim()) return
    runExtraction(pasteText)
  }

  const handleChatSend = () => {
    if (!chatInput.trim()) return
    const msg = chatInput.trim()
    setChatInput('')

    setChatMessages((prev) => [...prev, { role: 'user', text: msg }])

    const lower = msg.toLowerCase()
    const matchVal = msg.match(/(?:to|as|is|=)\s+(.+)$/i)
    const val = matchVal?.[1]?.replace(/[.!]+$/, '').trim()

    let reply = ''
    if (val && (lower.includes('batch') || lower.includes('lot'))) {
      dispatch(setField({ key: 'batch', value: val }))
      reply = `Updated Batch / Lot Number to "${val}".`
    } else if (val && (lower.includes('product') || lower.includes('material'))) {
      dispatch(setField({ key: 'product', value: val }))
      reply = `Updated Product / Material to "${val}".`
    } else if (val && (lower.includes('site') || lower.includes('plant'))) {
      dispatch(setField({ key: 'site', value: val }))
      reply = `Updated Site / Plant to "${val}".`
    } else if (val && (lower.includes('title') || lower.includes('description'))) {
      dispatch(setField({ key: 'title', value: val }))
      reply = `Updated Title / Short Description to "${val}".`
    } else {
      runExtraction(msg)
      return
    }

    setChatMessages((prev) => [...prev, { role: 'assistant', text: reply }])
  }

  const handleReset = () => {
    dispatch(resetForm())
    setSelectedFileName(null)
    setPasteText('')
    setAiResponseText(null)
    setActiveTab('upload')
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  const handleSave = () => {
    dispatch(submit())
    setTimeout(() => {
      navigate('/deviations')
    }, 1200)
  }

  const isHighlighted = (fieldName: string) => highlightedFields.includes(fieldName)

  return (
    <div className="log-deviation-container">
      {/* Title & Quick Action Bar */}
      <div className="log-header-bar">
        <div>
          <div className="title-with-badge">
            <h1>Log Deviation</h1>
            <span className="badge-draft">Draft</span>
          </div>
          <p className="subtitle">
            Record any unexpected event, out-of-specification result or non-conformance.
          </p>
        </div>
        <div className="header-quick-actions">
          <button type="button" className="btn btn-sample" onClick={handleSampleLoad}>
            <Zap size={15} /> ⚡ Load Sample Excursion
          </button>
        </div>
      </div>

      {submitted && (
        <div className="success-banner">
          <Check size={18} />
          <span>Deviation record saved successfully! Form submitted. Redirecting to All Deviations...</span>
        </div>
      )}

      {/* Main 2-Column Layout Grid */}
      <div className="deviation-grid">
        {/* LEFT COLUMN: Log Deviation Form */}
        <div className="form-card-main">
          {/* 1. DEVIATION INFORMATION */}
          <div className="form-section">
            <div className="section-header-row">
              <span className="section-pill">01</span>
              <h2 className="section-title">DEVIATION INFORMATION</h2>
            </div>

            <div className="fields-grid">
              <div className={cx('field-group', isHighlighted('site') && 'ai-populated-glow')}>
                <label>Site / Plant <span className="req">*</span></label>
                <input
                  type="text"
                  placeholder="e.g. Unit-1 API Manufacturing Plant"
                  value={form.site}
                  onChange={(e) => handleFieldChange('site')(e.target.value)}
                />
              </div>

              <div className={cx('field-group', isHighlighted('occurrenceDate') && 'ai-populated-glow')}>
                <label>Date of Occurrence <span className="req">*</span></label>
                <input
                  type="date"
                  value={form.occurrenceDate || ''}
                  onChange={(e) => handleFieldChange('occurrenceDate')(e.target.value)}
                />
              </div>

              <div className={cx('field-group span-full', isHighlighted('title') && 'ai-populated-glow')}>
                <label>Title / Short Description <span className="req">*</span></label>
                <input
                  type="text"
                  placeholder="e.g. Temperature excursion in Reactor 3 during API batch processing"
                  value={form.title}
                  onChange={(e) => handleFieldChange('title')(e.target.value)}
                />
              </div>

              <div className={cx('field-group', isHighlighted('source') && 'ai-populated-glow')}>
                <label>Source <span className="req">*</span></label>
                <select
                  value={form.source || 'Internal Deviation'}
                  onChange={(e) => handleFieldChange('source')(e.target.value)}
                >
                  <option value="Internal Deviation">Internal Deviation</option>
                  <option value="Customer Complaint">Customer Complaint</option>
                  <option value="Audit Observation">Audit Observation</option>
                  <option value="Vendor Deviation">Vendor Deviation</option>
                </select>
              </div>

              <div className={cx('field-group', isHighlighted('product') && 'ai-populated-glow')}>
                <label>Related Product / Material</label>
                <div className="input-with-icon">
                  <input
                    type="text"
                    list="product-suggestions"
                    placeholder="Search or enter product..."
                    value={form.product}
                    onChange={(e) => handleFieldChange('product')(e.target.value)}
                  />
                  <Search size={15} className="search-icon" />
                  <datalist id="product-suggestions">
                    <option value="API-ACM-01" />
                    <option value="Paracetamol API" />
                    <option value="Ibuprofen Granules" />
                    <option value="Metformin HCl" />
                  </datalist>
                </div>
              </div>

              <div className={cx('field-group', isHighlighted('batch') && 'ai-populated-glow')}>
                <label>Batch / Lot Number</label>
                <input
                  type="text"
                  placeholder="e.g. B240918"
                  value={form.batch}
                  onChange={(e) => handleFieldChange('batch')(e.target.value)}
                />
              </div>
            </div>
          </div>

          {/* 2. DEVIATION DETAILS */}
          <div className="form-section margin-top">
            <div className="section-header-row">
              <span className="section-pill">02</span>
              <h2 className="section-title">DEVIATION DETAILS</h2>
            </div>

            <div className="fields-grid">
              <div className={cx('field-group span-full', isHighlighted('description') && 'ai-populated-glow')}>
                <div className="label-row">
                  <label>Detailed Description <span className="req">*</span></label>
                  <span className="char-count">{form.description.length}/2000</span>
                </div>
                <textarea
                  rows={4}
                  maxLength={2000}
                  placeholder="Describe what occurred, immediate actions taken, and operating conditions..."
                  value={form.description}
                  onChange={(e) => handleFieldChange('description')(e.target.value)}
                />
              </div>

              <div className={cx('field-group', isHighlighted('initialImpact') && 'ai-populated-glow')}>
                <label>Initial Impact <span className="req">*</span></label>
                <select
                  value={form.initialImpact || 'Potential Quality Impact'}
                  onChange={(e) => handleFieldChange('initialImpact')(e.target.value)}
                >
                  <option value="Minor Impact">Minor Impact</option>
                  <option value="Potential Quality Impact">Potential Quality Impact</option>
                  <option value="Major Product Impact">Major Product Impact</option>
                  <option value="Critical Safety Risk">Critical Safety Risk</option>
                </select>
              </div>

              <div className={cx('field-group', isHighlighted('initialSeverity') && 'ai-populated-glow')}>
                <label>Initial Severity <span className="req">*</span></label>
                <div className="severity-pill-group">
                  {['Low', 'Medium', 'High', 'Critical'].map((level) => (
                    <button
                      key={level}
                      type="button"
                      className={cx(
                        'severity-pill',
                        level.toLowerCase(),
                        (form.initialSeverity || 'High').toLowerCase() === level.toLowerCase() && 'selected'
                      )}
                      onClick={() => handleFieldChange('initialSeverity')(level)}
                    >
                      {level}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Form Bottom Action Controls */}
          <div className="form-actions">
            <button type="button" className="btn btn-outline" onClick={handleReset}>
              Reset Form
            </button>
            <button type="button" className="btn btn-primary" onClick={handleSave}>
              Save Deviation
            </button>
          </div>
        </div>

        {/* RIGHT COLUMN: AI Deviation Assistant Panel */}
        <div className="ai-panel-card">
          <div className="ai-panel-header">
            <div className="ai-title-wrap">
              <Bot size={18} className="ai-icon" />
              <h3>AI Deviation Assistant</h3>
              <span className="badge-beta">BETA</span>
            </div>
          </div>

          {/* AI Panel Mode Navigation Tabs */}
          <div className="ai-panel-tabs">
            <button
              type="button"
              className={cx('ai-tab', activeTab === 'upload' && 'active')}
              onClick={() => setActiveTab('upload')}
            >
              <UploadCloud size={14} /> Document
            </button>
            <button
              type="button"
              className={cx('ai-tab', activeTab === 'reasoning' && 'active')}
              onClick={() => setActiveTab('reasoning')}
            >
              <ShieldCheck size={14} /> Severity Reasoning {applied && <b className="dot-badge" />}
            </button>
            <button
              type="button"
              className={cx('ai-tab', activeTab === 'chips' && 'active')}
              onClick={() => setActiveTab('chips')}
            >
              <Sparkles size={14} /> Entities
            </button>
            <button
              type="button"
              className={cx('ai-tab', activeTab === 'chat' && 'active')}
              onClick={() => setActiveTab('chat')}
            >
              <Send size={14} /> Chat
            </button>
          </div>

          <div className="ai-panel-body">
            <input
              type="file"
              ref={fileInputRef}
              className="visually-hidden"
              accept=".pdf,.docx,.txt,.xls,.jpg,.png,text/plain,application/pdf"
              onChange={(e) => handleFileDrop(e.target.files?.[0])}
            />

            {/* TAB 1: UPLOAD / PASTE */}
            {activeTab === 'upload' && (
              <div className="tab-content">
                <div
                  className="dropzone"
                  onClick={() => fileInputRef.current?.click()}
                  onDragOver={(e) => e.preventDefault()}
                  onDrop={(e) => {
                    e.preventDefault()
                    handleFileDrop(e.dataTransfer.files?.[0])
                  }}
                >
                  <div className="dropzone-icon">
                    <UploadCloud size={24} />
                  </div>
                  <p className="dropzone-text">
                    {selectedFileName ? (
                      <strong>Loaded: {selectedFileName}</strong>
                    ) : (
                      <>
                        <strong>Drag & drop supporting document here</strong> or click to browse
                      </>
                    )}
                  </p>
                </div>

                <div className="paste-area">
                  <div className="paste-header">
                    <span>Or paste deviation details / ReportLab PDF snippet below:</span>
                  </div>
                  <textarea
                    rows={4}
                    placeholder="Paste incident email, ReportLab code stream (%PDF-1.4...), or observation text..."
                    value={pasteText}
                    onChange={(e) => setPasteText(e.target.value)}
                  />
                  <button
                    type="button"
                    className="btn btn-sm btn-primary"
                    disabled={!pasteText.trim()}
                    onClick={handlePasteExtract}
                  >
                    <Sparkles size={13} /> Extract Structure & Assess
                  </button>
                </div>

                <div className="formats-bar">
                  <Check size={13} className="check-icon" />
                  <span>Supported formats: PDF, DOCX, TXT, XLS, JPG, PNG | Max file size: 10MB</span>
                </div>
              </div>
            )}

            {/* TAB 2: SEVERITY REASONING CARD */}
            {activeTab === 'reasoning' && (
              <div className="tab-content">
                <div className="reasoning-card-wrapper">
                  <div className="reasoning-header">
                    <ShieldCheck size={16} className="shield-icon" />
                    <div>
                      <h4>AI Severity & Impact Assessment</h4>
                      <span>Automated justification based on QA risk criteria</span>
                    </div>
                  </div>

                  <div className="reasoning-badges-row">
                    <div className="reasoning-badge-group">
                      <span>Assessed Severity</span>
                      <span className={cx('badge-severity-pill', (form.initialSeverity || 'High').toLowerCase())}>
                        {form.initialSeverity || 'High'}
                      </span>
                    </div>
                    <div className="reasoning-badge-group">
                      <span>Assessed Impact</span>
                      <span className="badge-impact-pill">
                        {form.initialImpact || 'Potential Quality Impact'}
                      </span>
                    </div>
                  </div>

                  <div className="reasoning-body">
                    <h5>AI Justification & Rationale</h5>
                    <p>
                      {form.aiReasoning ||
                        'Assessed as High severity with Potential Quality Impact. The process parameter exceeded approved limits for an extended period, requiring QA investigation per SOP-DEV-004.'}
                    </p>
                  </div>

                  <div className="sop-reference-footer">
                    <FileText size={13} />
                    <span>Governing Procedure: <strong>SOP-DEV-004 (Classification Rules Sec 4.2)</strong></span>
                  </div>
                </div>
              </div>
            )}

            {/* TAB 3: EXTRACTED ENTITIES CHIPS */}
            {activeTab === 'chips' && (
              <div className="tab-content">
                <div className="chips-header">
                  <Sparkles size={15} className="sparkles-icon" />
                  <strong>Extracted Field Entities</strong>
                </div>

                {applied ? (
                  <div className="chips-grid">
                    {[
                      ['Site / Plant', form.site, confidenceScores.site || 95],
                      ['Date', form.occurrenceDate, confidenceScores.occurrenceDate || 92],
                      ['Title', form.title, confidenceScores.title || 94],
                      ['Source', form.source, confidenceScores.source || 98],
                      ['Product', form.product, confidenceScores.product || 96],
                      ['Batch / Lot', form.batch, confidenceScores.batch || 98],
                      ['Initial Impact', form.initialImpact, confidenceScores.initialImpact || 93],
                      ['Severity', form.initialSeverity, confidenceScores.initialSeverity || 95],
                    ].map(([label, val, conf]) => (
                      <div key={label as string} className="entity-chip">
                        <div className="chip-top">
                          <span>{label}</span>
                          <small>{conf}% confidence</small>
                        </div>
                        <strong>{val || '(empty)'}</strong>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="empty-chips">
                    <AlertCircle size={20} />
                    <p>No document parsed yet. Upload a PDF, paste text, or click ⚡ Load Sample Excursion.</p>
                  </div>
                )}
              </div>
            )}

            {/* TAB 4: CHAT ASSISTANT */}
            {activeTab === 'chat' && (
              <div className="tab-content chat-tab">
                <div className="chat-messages-container">
                  {chatMessages.map((m, idx) => (
                    <div key={idx} className={cx('chat-bubble', m.role)}>
                      <div className="bubble-role">
                        {m.role === 'assistant' ? <><Sparkles size={12} /> AI Copilot</> : 'You'}
                      </div>
                      <p>{m.text}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Extraction Progress Indicator */}
            <div className="extraction-progress-box">
              <div className="progress-header">
                <span>EXTRACTION PROGRESS</span>
                <strong>{extractionProgress}%</strong>
              </div>
              <div className="progress-track">
                <div className="progress-fill" style={{ width: `${extractionProgress}%` }} />
              </div>
              {isExtracting && <span className="extract-status">Parsing PDF & generating severity rationale...</span>}
            </div>

            {/* AI Assistant Output Summary Card */}
            <div className="ai-response-box">
              <div className="ai-response-header">
                <Sparkles size={15} className="sparkles-icon" />
                <strong>Assistant Status</strong>
              </div>
              <p className="ai-response-text">
                {aiResponseText ? (
                  aiResponseText
                ) : applied ? (
                  'Fields extracted & severity reasoning generated. Form updated live.'
                ) : (
                  'Ready for input. Drag & drop a PDF, paste incident notes, or load a sample.'
                )}
              </p>
            </div>
          </div>

          {/* Bottom Chat Bar */}
          <div className="ai-chat-footer">
            <div className="chat-input-row">
              <input
                type="text"
                placeholder="Ask me anything or edit fields (e.g. 'change batch to B-901')..."
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleChatSend()}
              />
              <button
                type="button"
                className="chat-send-btn"
                onClick={handleChatSend}
                disabled={!chatInput.trim()}
                title="Send instruction"
              >
                <Send size={15} />
              </button>
            </div>
            <p className="chat-disclaimer">AI can make mistakes. Verify important information.</p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default function App() {
  return (
    <div className="app-container">
      <Header />
      <main className="main-viewport">
        <Routes>
          <Route path="/" element={<LogDeviationPage />} />
          <Route path="/deviations" element={<AllDeviationsPage />} />
          <Route path="/deviations/new" element={<LogDeviationPage />} />
          <Route path="*" element={<LogDeviationPage />} />
        </Routes>
      </main>
    </div>
  )
}
