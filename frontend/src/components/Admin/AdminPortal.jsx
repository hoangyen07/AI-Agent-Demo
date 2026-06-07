import { useState, useRef } from 'react'
import { X, Upload, FileText, CheckCircle, AlertCircle, Loader2, FolderPlus } from 'lucide-react'
import { uploadDocument, fetchProjects } from '../../services/api'
import { useGlobal } from '../../store/globalContext'

const ACCEPTED_TYPES = '.pdf,.docx,.doc,.md,.txt'

function FileDropzone({ onFiles }) {
  const [dragging, setDragging] = useState(false)
  const inputRef = useRef()

  const handleDrop = (e) => {
    e.preventDefault()
    setDragging(false)
    const files = Array.from(e.dataTransfer.files)
    onFiles(files)
  }

  return (
    <div
      onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
      onDragLeave={() => setDragging(false)}
      onDrop={handleDrop}
      onClick={() => inputRef.current.click()}
      className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all ${
        dragging
          ? 'border-blue-500 bg-blue-950/30'
          : 'border-slate-700 hover:border-slate-600 hover:bg-slate-800/30'
      }`}
    >
      <Upload size={28} className="mx-auto mb-3 text-slate-500" />
      <p className="text-slate-300 text-sm font-medium mb-1">Kéo thả file vào đây</p>
      <p className="text-slate-600 text-xs">hoặc click để chọn file</p>
      <p className="text-slate-700 text-xs mt-2">PDF, DOCX, MD, TXT — tối đa 20MB</p>
      <input
        ref={inputRef}
        type="file"
        multiple
        accept={ACCEPTED_TYPES}
        className="hidden"
        onChange={(e) => onFiles(Array.from(e.target.files))}
      />
    </div>
  )
}

function UploadItem({ file, status, message }) {
  return (
    <div className="flex items-center gap-3 py-2.5 border-b border-slate-800/60 last:border-0">
      <FileText size={15} className="text-slate-500 flex-shrink-0" />
      <div className="flex-1 min-w-0">
        <p className="text-sm text-slate-300 truncate">{file.name}</p>
        {message && (
          <p className={`text-xs mt-0.5 ${status === 'error' ? 'text-red-400' : 'text-slate-500'}`}>
            {message}
          </p>
        )}
      </div>
      <div className="flex-shrink-0">
        {status === 'pending' && <div className="w-4 h-4 rounded-full border-2 border-slate-700" />}
        {status === 'uploading' && <Loader2 size={16} className="animate-spin text-blue-400" />}
        {status === 'success' && <CheckCircle size={16} className="text-emerald-400" />}
        {status === 'error' && <AlertCircle size={16} className="text-red-400" />}
      </div>
    </div>
  )
}

export default function AdminPortal({ onClose }) {
  const { setProjects, selectProject } = useGlobal()
  const [projectId, setProjectId] = useState('')
  const [projectName, setProjectName] = useState('')
  const [files, setFiles] = useState([])
  const [uploadItems, setUploadItems] = useState([])
  const [uploading, setUploading] = useState(false)
  const [done, setDone] = useState(false)

  const handleFiles = (newFiles) => {
    setFiles(prev => {
      const existing = new Set(prev.map(f => f.name))
      const filtered = newFiles.filter(f => !existing.has(f.name))
      return [...prev, ...filtered]
    })
  }

  const handleUpload = async () => {
    if (!projectId.trim() || !projectName.trim() || files.length === 0) return

    setUploading(true)
    setUploadItems(files.map(f => ({ file: f, status: 'pending', message: '' })))

    for (let i = 0; i < files.length; i++) {
      setUploadItems(prev => {
        const updated = [...prev]
        updated[i] = { ...updated[i], status: 'uploading' }
        return updated
      })

      try {
        const result = await uploadDocument(projectId.trim(), projectName.trim(), files[i])
        setUploadItems(prev => {
          const updated = [...prev]
          updated[i] = { ...updated[i], status: 'success', message: `${result.chunks_added} chunks đã nạp` }
          return updated
        })
      } catch (err) {
        setUploadItems(prev => {
          const updated = [...prev]
          updated[i] = { ...updated[i], status: 'error', message: err.message }
          return updated
        })
      }
    }

    // Refresh project list and auto-select the new project
    try {
      const projects = await fetchProjects()
      setProjects(projects)
      selectProject(projectId.trim(), projectName.trim())
    } catch { /* ignore */ }

    setUploading(false)
    setDone(true)
  }

  const canUpload = projectId.trim() && projectName.trim() && files.length > 0 && !uploading

  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-slate-900 border border-slate-700 rounded-2xl w-full max-w-lg shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800">
          <div className="flex items-center gap-2.5">
            <FolderPlus size={18} className="text-blue-400" />
            <h2 className="font-semibold text-slate-100">Thêm dự án mới</h2>
          </div>
          <button onClick={onClose} className="text-slate-500 hover:text-slate-300 transition-colors">
            <X size={18} />
          </button>
        </div>

        <div className="px-6 py-5 space-y-5">
          {/* Project Info */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs text-slate-500 mb-1.5 font-medium">Mã dự án *</label>
              <input
                value={projectId}
                onChange={e => setProjectId(e.target.value.toLowerCase().replace(/\s+/g, '_'))}
                placeholder="fintech, ecommerce..."
                disabled={uploading}
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 placeholder-slate-600 outline-none focus:border-blue-500/60 font-mono"
              />
            </div>
            <div>
              <label className="block text-xs text-slate-500 mb-1.5 font-medium">Tên dự án *</label>
              <input
                value={projectName}
                onChange={e => setProjectName(e.target.value)}
                placeholder="App Mobile V2..."
                disabled={uploading}
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 placeholder-slate-600 outline-none focus:border-blue-500/60"
              />
            </div>
          </div>

          {/* Dropzone */}
          {!done && (
            <FileDropzone onFiles={handleFiles} />
          )}

          {/* File list */}
          {(files.length > 0 || done) && (
            <div className="bg-slate-800/40 rounded-xl px-4">
              {done
                ? uploadItems.map((item, i) => (
                    <UploadItem key={i} file={item.file} status={item.status} message={item.message} />
                  ))
                : files.map((file, i) => (
                    <UploadItem key={i} file={file} status="pending" message="" />
                  ))
              }
            </div>
          )}

          {/* Actions */}
          {!done ? (
            <button
              onClick={handleUpload}
              disabled={!canUpload}
              className="w-full py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 disabled:bg-slate-800 disabled:text-slate-600 text-white text-sm font-medium transition-all flex items-center justify-center gap-2"
            >
              {uploading ? (
                <><Loader2 size={16} className="animate-spin" /> Đang nạp tài liệu...</>
              ) : (
                <><Upload size={16} /> Upload & Nạp vào Agent</>
              )}
            </button>
          ) : (
            <button
              onClick={onClose}
              className="w-full py-2.5 rounded-xl bg-emerald-600/20 border border-emerald-500/40 text-emerald-400 text-sm font-medium hover:bg-emerald-600/30 transition-all"
            >
              ✓ Hoàn tất — Bắt đầu chat ngay
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
