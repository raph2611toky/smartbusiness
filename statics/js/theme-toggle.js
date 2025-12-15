document.addEventListener("DOMContentLoaded", () => {
  // Fonction pour changer le thème
  const toggleTheme = () => {
    const currentTheme = document.documentElement.getAttribute("data-theme") || "light"
    const newTheme = currentTheme === "light" ? "dark" : "light"

    // Appliquer le nouveau thème
    document.documentElement.setAttribute("data-theme", newTheme)

    // Sauvegarder la préférence
    localStorage.setItem("theme", newTheme)

    // Mettre à jour les icônes
    updateThemeIcons(newTheme)

    console.log("Thème changé en:", newTheme)
  }

  // Fonction pour mettre à jour l'affichage des icônes
  const updateThemeIcons = (theme) => {
    const lightIcons = document.querySelectorAll(".theme-light-icon")
    const darkIcons = document.querySelectorAll(".theme-dark-icon")

    if (theme === "dark") {
      lightIcons.forEach((icon) => (icon.style.display = "none"))
      darkIcons.forEach((icon) => (icon.style.display = "flex"))
    } else {
      lightIcons.forEach((icon) => (icon.style.display = "flex"))
      darkIcons.forEach((icon) => (icon.style.display = "none"))
    }
  }

  // Récupérer le thème sauvegardé ou utiliser le thème clair par défaut
  const savedTheme = localStorage.getItem("theme") || "light"

  // Appliquer le thème sauvegardé
  document.documentElement.setAttribute("data-theme", savedTheme)

  // Initialiser l'affichage des icônes
  updateThemeIcons(savedTheme)

  // Ajouter les écouteurs d'événements pour les icônes de thème
  const themeToggles = document.querySelectorAll(".theme-toggle-float")
  themeToggles.forEach((toggle) => {
    toggle.addEventListener("click", toggleTheme)
  })

  console.log("Script de thème initialisé. Thème actuel:", savedTheme)
})
