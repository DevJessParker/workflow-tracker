'use client'

import { useState, useEffect } from 'react'

export function useTableBookmarks(scanId: string) {
  const [bookmarkedTables, setBookmarkedTables] = useState<string[]>([])
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
      return `table_bookmarks_${user.email}_${scanId}`
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
        setBookmarkedTables(JSON.parse(stored))
      }
    } catch (err) {
      console.error('Failed to load bookmarks:', err)
    }
  }

  const saveBookmarks = (bookmarks: string[]) => {
    const key = getStorageKey()
    if (!key) return

    try {
      localStorage.setItem(key, JSON.stringify(bookmarks))
      setBookmarkedTables(bookmarks)
    } catch (err) {
      console.error('Failed to save bookmarks:', err)
    }
  }

  const toggleBookmark = (tableName: string): boolean => {
    const isBookmarked = bookmarkedTables.includes(tableName)

    if (isBookmarked) {
      // Remove bookmark
      const updated = bookmarkedTables.filter(t => t !== tableName)
      saveBookmarks(updated)
      return false
    } else {
      // Add bookmark (check limit)
      if (bookmarkedTables.length >= MAX_BOOKMARKS) {
        return false // Can't add more
      }
      const updated = [...bookmarkedTables, tableName]
      saveBookmarks(updated)
      return true
    }
  }

  const isBookmarked = (tableName: string): boolean => {
    return bookmarkedTables.includes(tableName)
  }

  const canAddMoreBookmarks = (): boolean => {
    return bookmarkedTables.length < MAX_BOOKMARKS
  }

  const getBookmarkCount = (): number => {
    return bookmarkedTables.length
  }

  return {
    bookmarkedTables,
    toggleBookmark,
    isBookmarked,
    canAddMoreBookmarks,
    getBookmarkCount,
    MAX_BOOKMARKS,
  }
}
