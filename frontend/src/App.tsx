import { useState, useEffect } from 'react'
import './App.css'

interface JanResponse {
  jan_code: string
  url: string
  brand?: string
  product_name?: string
}

interface Config {
  apiUrl: string
}

function App() {
  const [janCode, setJanCode] = useState('')
  const [result, setResult] = useState<JanResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [apiUrl, setApiUrl] = useState<string>('http://localhost:8000')

  useEffect(() => {
    // Load config.json on startup
    fetch('/config.json')
      .then(res => res.json())
      .then((config: Config) => {
        setApiUrl(config.apiUrl)
      })
      .catch(() => {
        // Fallback to localhost if config.json not found
        console.warn('config.json not found, using localhost')
      })
  }, [])

  const handleSearch = async () => {
    if (!janCode.trim()) {
      setError('JANコードを入力してください')
      return
    }

    setLoading(true)
    setError(null)
    setResult(null)

    try {
      const response = await fetch(`${apiUrl}/api/convert?jan=${janCode}`)

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'エラーが発生しました')
      }

      const data: JanResponse = await response.json()
      setResult(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : '不明なエラーが発生しました')
    } finally {
      setLoading(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch()
    }
  }

  return (
    <div className="app">
      <div className="container">
        <h1>JAN-URL 変換システム</h1>
        <p className="subtitle">JANコードから商品URLを検索</p>

        <div className="search-box">
          <input
            type="text"
            value={janCode}
            onChange={(e) => setJanCode(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="JANコードを入力 (例: 4571657070839)"
            className="jan-input"
            disabled={loading}
          />
          <button
            onClick={handleSearch}
            className="search-button"
            disabled={loading}
          >
            {loading ? '検索中...' : '検索'}
          </button>
        </div>

        {error && (
          <div className="error-message">
            ⚠️ {error}
          </div>
        )}

        {result && (
          <div className="result-card">
            <h2>検索結果</h2>
            <div className="result-item">
              <span className="label">JANコード:</span>
              <span className="value">{result.jan_code}</span>
            </div>
            {result.brand && (
              <div className="result-item">
                <span className="label">ブランド:</span>
                <span className="value">{result.brand}</span>
              </div>
            )}
            {result.product_name && (
              <div className="result-item">
                <span className="label">商品名:</span>
                <span className="value">{result.product_name}</span>
              </div>
            )}
            <div className="result-item">
              <span className="label">URL:</span>
              <a
                href={result.url}
                target="_blank"
                rel="noopener noreferrer"
                className="url-link"
              >
                {result.url}
              </a>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default App
