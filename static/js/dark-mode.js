// static/js/dark-mode.js

document.addEventListener('DOMContentLoaded', () => {
    const body = document.body;
    const darkModeToggle = document.createElement('div'); // Cria o elemento do botão
    darkModeToggle.classList.add('dark-mode-toggle');
    darkModeToggle.innerHTML = '<i class="fas fa-moon"></i>'; // Ícone de lua

    // Adiciona o botão ao body
    body.appendChild(darkModeToggle);

    // Função para aplicar o tema
    function applyTheme(isDarkMode) {
        if (isDarkMode) {
            body.classList.add('dark-mode');
            darkModeToggle.innerHTML = '<i class="fas fa-sun"></i>'; // Ícone de sol
        } else {
            body.classList.remove('dark-mode');
            darkModeToggle.innerHTML = '<i class="fas fa-moon"></i>'; // Ícone de lua
        }
    }

    // Verifica a preferência do usuário armazenada no localStorage
    const savedTheme = localStorage.getItem('theme');

    if (savedTheme) {
        // Se houver uma preferência salva, aplica-a
        applyTheme(savedTheme === 'dark');
    } else {
        // Se não houver, verifica a preferência do sistema operacional
        const prefersDarkMode = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
        applyTheme(prefersDarkMode);
        // Salva a preferência inicial do sistema para futuras visitas
        localStorage.setItem('theme', prefersDarkMode ? 'dark' : 'light');
    }

    // Event listener para o botão de alternância
    darkModeToggle.addEventListener('click', () => {
        const isCurrentlyDarkMode = body.classList.contains('dark-mode');
        const newTheme = !isCurrentlyDarkMode;

        applyTheme(newTheme);
        localStorage.setItem('theme', newTheme ? 'dark' : 'light'); // Salva a nova preferência
    });
});