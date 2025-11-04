'use client'

import { useState, useEffect } from 'react'

export function useApiBookmarks(scanId: string) {
  const [bookmarkedRoutes, setBookmarkedRoutes] = useState<string[]>([])
  const MAX_BOOKMARKS = 5

  useEffect(() => {
    loadBookmarks()
  }, [scanId])

  const getStorageKey = () => {
    // Get user from localStorage
    const userStr = localStorage.getItem('user')
    if (!userStr) return null

    try {
      const user = JSON.parse(userStr)
      return `api_bookmarks_${user.email}_${scanId}`
    } catch {
      return null
    }
  }

  const loadBookmarks = () => {
    const key = getStorageKey()
    if (!key) return

    try {
      const stored = localStorage.getItem(key)
      if (stored) {
        setBookmarkedRoutes(JSON.parse(stored))
      }
    } catch (err) {
      console.error('Failed to load API bookmarks:', err)
    }
  }

  const saveBookmarks = (bookmarks: string[]) => {
    const key = getStorageKey()
    if (!key) return

    try {
      localStorage.setItem(key, JSON.stringify(bookmarks))
      setBookmarkedRoutes(bookmarks)
    } catch (err) {
      console.error('Failed to save API bookmarks:', err)
    }
  }

  const toggleBookmark = (routeKey: string): boolean => {
    const isBookmarked = bookmarkedRoutes.includes(routeKey)

    if (isBookmarked) {
      // Remove bookmark
      const updated = bookmarkedRoutes.filter(r => r !== routeKey)
      saveBookmarks(updated)
      return false
    } else {
      // Add bookmark (check limit)
      if (bookmarkedRoutes.length >= MAX_BOOKMARKS) {
        return false // Can't add more
      }
      const updated = [...bookmarkedRoutes, routeKey]
      saveBookmarks(updated)
      return true
    }
  }

  const isBookmarked = (routeKey: string): boolean => {
    return bookmarkedRoutes.includes(routeKey)
  }

  const canAddMoreBookmarks = (): boolean => {
    return bookmarkedRoutes.length < MAX_BOOKMARKS
  }

  const getBookmarkCount = (): number => {
    return bookmarkedRoutes.length
  }

  return {
    bookmarkedRoutes,
    toggleBookmark,
    isBookmarked,
    canAddMoreBookmarks,
    getBookmarkCount,
    MAX_BOOKMARKS,
  }
}
