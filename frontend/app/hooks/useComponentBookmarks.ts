'use client'

import { useState, useEffect } from 'react'

export function useComponentBookmarks(scanId: string) {
  const [bookmarkedComponents, setBookmarkedComponents] = useState<string[]>([])
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
      return `component_bookmarks_${user.email}_${scanId}`
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
        setBookmarkedComponents(JSON.parse(stored))
      }
    } catch (err) {
      console.error('Failed to load component bookmarks:', err)
    }
  }

  const saveBookmarks = (bookmarks: string[]) => {
    const key = getStorageKey()
    if (!key) return

    try {
      localStorage.setItem(key, JSON.stringify(bookmarks))
      setBookmarkedComponents(bookmarks)
    } catch (err) {
      console.error('Failed to save component bookmarks:', err)
    }
  }

  const toggleBookmark = (componentName: string): boolean => {
    const isBookmarked = bookmarkedComponents.includes(componentName)

    if (isBookmarked) {
      // Remove bookmark
      const updated = bookmarkedComponents.filter(c => c !== componentName)
      saveBookmarks(updated)
      return false
    } else {
      // Add bookmark (check limit)
      if (bookmarkedComponents.length >= MAX_BOOKMARKS) {
        return false // Can't add more
      }
      const updated = [...bookmarkedComponents, componentName]
      saveBookmarks(updated)
      return true
    }
  }

  const isBookmarked = (componentName: string): boolean => {
    return bookmarkedComponents.includes(componentName)
  }

  const canAddMoreBookmarks = (): boolean => {
    return bookmarkedComponents.length < MAX_BOOKMARKS
  }

  const getBookmarkCount = (): number => {
    return bookmarkedComponents.length
  }

  return {
    bookmarkedComponents,
    toggleBookmark,
    isBookmarked,
    canAddMoreBookmarks,
    getBookmarkCount,
    MAX_BOOKMARKS,
  }
}
