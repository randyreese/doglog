import { useState, useRef } from 'react'

const THRESHOLD = 72
const REVEAL_WIDTH = 80

export default function SwipeableRow({ onDelete, children }) {
  const [offset, setOffset] = useState(0)
  const startX = useRef(null)
  const suppressNextClick = useRef(false)

  function onTouchStart(e) {
    if (offset < -10) {
      setOffset(0)
      suppressNextClick.current = true
      startX.current = null
      return
    }
    startX.current = e.touches[0].clientX
  }

  function onTouchMove(e) {
    if (startX.current === null) return
    const dx = e.touches[0].clientX - startX.current
    if (dx < 0) setOffset(Math.max(dx, -(REVEAL_WIDTH + 20)))
  }

  function onTouchEnd() {
    if (startX.current === null) return
    if (offset <= -THRESHOLD) {
      setOffset(-REVEAL_WIDTH)
    } else {
      setOffset(0)
    }
    startX.current = null
  }

  function handleDelete(e) {
    e.stopPropagation()
    if (!window.confirm('Delete this entry?')) {
      setOffset(0)
      return
    }
    setOffset(0)
    onDelete()
  }

  function handleInnerClick(e) {
    if (suppressNextClick.current) {
      suppressNextClick.current = false
      e.stopPropagation()
    }
  }

  const isDragging = startX.current !== null

  return (
    <div data-swipeable="true" style={{ position: 'relative', overflow: 'hidden', marginBottom: 2, borderRadius: 4 }}>
      <div
        style={{
          position: 'absolute', right: 0, top: 0, bottom: 0, width: REVEAL_WIDTH,
          background: '#e53e3e', display: 'flex', alignItems: 'center', justifyContent: 'center',
          cursor: 'pointer',
        }}
        onClick={handleDelete}
      >
        <span style={{ color: '#fff', fontWeight: 700, fontSize: 14 }}>Delete</span>
      </div>
      <div
        style={{
          transform: `translateX(${offset}px)`,
          transition: isDragging ? 'none' : 'transform 0.2s ease-out',
          position: 'relative', zIndex: 1,
        }}
        onTouchStart={onTouchStart}
        onTouchMove={onTouchMove}
        onTouchEnd={onTouchEnd}
        onClick={handleInnerClick}
      >
        {children}
      </div>
    </div>
  )
}
