import { useEffect, useRef, useState } from 'react'

const SOCKET_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws/claims'
const MAX_RETRY_MS = 15000

export function useClaimsSocket() {
  const [connection, setConnection] = useState('connecting')
  const [lastMessageAt, setLastMessageAt] = useState(null)
  const retryRef = useRef(500)

  useEffect(() => {
    let socket
    let retryTimer
    let disposed = false

    const connect = () => {
      if (disposed) return
      setConnection('connecting')
      socket = new WebSocket(SOCKET_URL)

      socket.onopen = () => {
        retryRef.current = 500
        setConnection('connected')
      }

      socket.onmessage = (message) => {
        setLastMessageAt(new Date())
        try {
          const event = JSON.parse(message.data)
          window.dispatchEvent(new CustomEvent('claimguard:socket-event', { detail: event }))
        } catch {
          console.warn('ClaimGuard received an invalid WebSocket message')
        }
      }

      socket.onerror = () => socket.close()
      socket.onclose = () => {
        if (disposed) return
        setConnection('disconnected')
        const delay = retryRef.current
        retryRef.current = Math.min(delay * 2, MAX_RETRY_MS)
        retryTimer = window.setTimeout(connect, delay)
      }
    }

    connect()
    return () => {
      disposed = true
      window.clearTimeout(retryTimer)
      socket?.close()
    }
  }, [])

  return { connection, lastMessageAt }
}
