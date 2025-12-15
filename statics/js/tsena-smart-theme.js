document.addEventListener("DOMContentLoaded", () => {
  // Theme toggle functionality
  const setupThemeToggle = () => {
    const themeToggle = document.getElementById("theme-toggle")
    if (!themeToggle) return

    // Check for saved theme preference or use system preference
    const savedTheme = localStorage.getItem("theme")
    const systemPrefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches

    // Set initial theme
    if (savedTheme === "dark" || (!savedTheme && systemPrefersDark)) {
      document.documentElement.setAttribute("data-theme", "dark")
      themeToggle.checked = true
    }

    // Toggle theme when switch is clicked
    themeToggle.addEventListener("change", function () {
      if (this.checked) {
        document.documentElement.setAttribute("data-theme", "dark")
        localStorage.setItem("theme", "dark")
      } else {
        document.documentElement.removeAttribute("data-theme")
        localStorage.setItem("theme", "light")
      }
    })
  }

  // Mobile menu toggle
  const setupMobileMenu = () => {
    const mobileMenuBtn = document.querySelector(".mobile-menu-btn")
    const sidebar = document.querySelector(".sidebar")
    const mainContent = document.querySelector(".main-content")

    if (!mobileMenuBtn || !sidebar || !mainContent) return

    mobileMenuBtn.addEventListener("click", () => {
      sidebar.classList.toggle("open")
    })

    document.addEventListener("click", (event) => {
      if (
        !sidebar.contains(event.target) &&
        !mobileMenuBtn.contains(event.target) &&
        sidebar.classList.contains("open")
      ) {
        sidebar.classList.remove("open")
      }
    })
  }

  const handleResize = () => {
    const sidebar = document.querySelector(".sidebar")
    const mainContent = document.querySelector(".main-content")

    if (!sidebar || !mainContent) return

    if (window.innerWidth < 768) {
      sidebar.classList.remove("open")
      mainContent.style.marginLeft = "0"
    } else {
      mainContent.style.marginLeft = "250px"
    }
  }

  const initStatsAnimation = () => {
    const statCards = document.querySelectorAll(".stat-card")

    statCards.forEach((card, index) => {
      card.style.animationDelay = `${index * 0.1}s`
      card.classList.add("fade-in")
    })
  }

  const initTableAnimation = () => {
    const tableRows = document.querySelectorAll("tbody tr")

    tableRows.forEach((row, index) => {
      row.style.animationDelay = `${index * 0.05}s`
      row.classList.add("slide-in")
    })
  }

  const updateLastUpdateTime = () => {
    const lastUpdateEl = document.getElementById("last-update")
    if (!lastUpdateEl) return

    lastUpdateEl.textContent = "à l'instant"
    setTimeout(() => {
      lastUpdateEl.textContent = "il y a 1 minute"
    }, 60000)
  }

  const setupSearch = () => {
    const searchInput = document.querySelector(".search-input")
    if (!searchInput) return

    searchInput.addEventListener("input", function () {
      const searchTerm = this.value.toLowerCase()
      const tableRows = document.querySelectorAll("tbody tr")

      tableRows.forEach((row) => {
        const text = row.textContent.toLowerCase()
        if (text.includes(searchTerm)) {
          row.style.display = ""
        } else {
          row.style.display = "none"
        }
      })
    })
  }

  const enhanceDjangoAdmin = () => {
    const header = document.getElementById("header")
    if (header) {
      const mobileBtn = document.createElement("button")
      mobileBtn.className = "mobile-menu-btn"
      mobileBtn.innerHTML = '<i class="fas fa-bars"></i>'
      header.insertBefore(mobileBtn, header.firstChild)
    }

    const userTools = document.getElementById("user-tools")
    if (userTools) {
      const themeToggleContainer = document.createElement("div")
      themeToggleContainer.className = "theme-toggle-container"
      themeToggleContainer.innerHTML = `
        <span class="mr-2 text-sm">Thème</span>
        <label class="switch">
          <input type="checkbox" id="theme-toggle">
          <span class="slider">
            <i class="fas fa-moon moon"></i>
            <i class="fas fa-sun sun"></i>
          </span>
        </label>
      `
      userTools.appendChild(themeToggleContainer)
    }

    const changeLists = document.querySelectorAll("#changelist-form .results")
    changeLists.forEach((changeList) => {
      changeList.classList.add("data-card")

      const table = changeList.querySelector("table")
      if (table) {
        table.classList.add("table-container")
      }
    })

    // Add icons to Django admin links
    const addIcons = () => {
      const iconMap = {
        Accueil: "fa-home",
        Ajouter: "fa-plus",
        Modifier: "fa-edit",
        Supprimer: "fa-trash",
        Voir: "fa-eye",
        Utilisateurs: "fa-users",
        Groupes: "fa-user-friends",
        Paramètres: "fa-cog",
        Déconnexion: "fa-sign-out-alt",
      }

      document.querySelectorAll("a").forEach((link) => {
        const text = link.textContent.trim()
        if (iconMap[text] && !link.querySelector("i")) {
          const icon = document.createElement("i")
          icon.className = `fas ${iconMap[text]} mr-2`
          link.insertBefore(icon, link.firstChild)
        }
      })
    }

    addIcons()
  }

  // Initialize all functions
  setupThemeToggle()
  setupMobileMenu()
  handleResize()
  initStatsAnimation()
  initTableAnimation()
  updateLastUpdateTime()
  setupSearch()
  enhanceDjangoAdmin()

  // Add window resize event listener
  window.addEventListener("resize", handleResize)
})
