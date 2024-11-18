"use client"

import * as React from "react"
import { useTheme } from "next-themes"
import { Laptop } from "lucide-react"
import { MoonIcon, SunIcon } from "@radix-ui/react-icons"

export function DarkModeToggleComponent() {
  const { theme, setTheme } = useTheme()
  const [mounted, setMounted] = React.useState(false)

  // useEffect to avoid hydration mismatch
  React.useEffect(() => {
    setMounted(true)
  }, [])

  if (!mounted) {
    return null
  }

  return (
    <div className="flex items-center justify-center p-4">
      <div className="relative inline-flex items-center rounded-full bg-gray-200 dark:bg-gray-700 p-1 w-[200px]">
        <button
          onClick={() => setTheme("light")}
          className={`flex items-center justify-center w-1/3 h-8 rounded-full transition-all duration-300 focus:outline-none ${
            theme === "light" ? "bg-white shadow-md" : ""
          }`}
          aria-label="Light mode"
        >
          <SunIcon className={`w-4 h-4 ${theme === "light" ? "text-yellow-500" : "text-gray-500"}`} />
        </button>
        <button
          onClick={() => setTheme("system")}
          className={`flex items-center justify-center w-1/3 h-8 rounded-full transition-all duration-300 focus:outline-none ${
            theme === "system" ? "bg-white shadow-md dark:bg-gray-600" : ""
          }`}
          aria-label="System mode"
        >
          <Laptop className={`w-4 h-4 ${theme === "system" ? "text-blue-500" : "text-gray-500"}`} />
        </button>
        <button
          onClick={() => setTheme("dark")}
          className={`flex items-center justify-center w-1/3 h-8 rounded-full transition-all duration-300 focus:outline-none ${
            theme === "dark" ? "bg-gray-600 shadow-md" : ""
          }`}
          aria-label="Dark mode"
        >
          <MoonIcon className={`w-4 h-4 ${theme === "dark" ? "text-indigo-500" : "text-gray-500"}`} />
        </button>
      </div>
    </div>
  )
}