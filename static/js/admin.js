// Função para obter valor de um elemento
function getValue(elementId) {
    const el = document.getElementById(elementId);
    if (el) {
        if (el.type === 'checkbox') {
            return el.checked;
        }
        return el.value;
    }
    return '';
}

// Função para converter HEX para RGBA para aplicar opacidade
function hexToRgba(hex, alpha) {
    if (typeof hex !== 'string') hex = '#000000'; // Cor padrão se indefinida

    hex = hex.replace(/^#/, '');

    if (hex.toLowerCase().startsWith('rgba')) {
        return hex.replace(/[\d\.]+\)$/g, alpha + ')');
    }
    if (hex.toLowerCase().startsWith('rgb')) {
        return hex.replace('rgb', 'rgba').replace(')', `, ${alpha})`);
    }

    let r = 0, g = 0, b = 0;
    if (hex.length === 3) {
        r = parseInt(hex[0] + hex[0], 16);
        g = parseInt(hex[1] + hex[1], 16);
        b = parseInt(hex[2] + hex[2], 16);
    } else if (hex.length === 6) {
        r = parseInt(hex.substring(0, 2), 16);
        g = parseInt(hex.substring(2, 4), 16);
        b = parseInt(hex.substring(4, 6), 16);
    } else {
        console.warn("Cor HEX inválida fornecida para hexToRgba:", hex, ". Usando preto como fallback.");
        return `rgba(0, 0, 0, ${alpha})`;
    }

    if (isNaN(r) || isNaN(g) || isNaN(b)) {
        return `rgba(0, 0, 0, ${alpha})`;
    }
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}


// Função para atualizar preview de texto genérico
function updateTextPreview(previewElementId, text, font, color) {
    const previewEl = document.getElementById(previewElementId);
    if (previewEl) {
        previewEl.textContent = text || 'Prévia...';
        previewEl.style.fontFamily = font || 'Inter, sans-serif';

        if (previewElementId.includes('card_')) {
            previewEl.style.backgroundColor = '#444'; // Cor de fundo específica para prévias do cartão
            previewEl.style.color = color || '#FFFFFF'; // Cor de texto específica para prévias do cartão
        } else {
            // Para outras prévias (nome, bio), usa as variáveis CSS do modo atual (light/dark)
            previewEl.style.backgroundColor = getComputedStyle(document.documentElement).getPropertyValue('--input-bg-light').trim();
            previewEl.style.color = color || getComputedStyle(document.documentElement).getPropertyValue('--text-color-light').trim();
        }
    }
}

function updateCardLinkItemPreview(itemElement) {
    const atTextInput = itemElement.querySelector('.card-link-item-at-text');
    const fontSelect = itemElement.querySelector('.card-link-item-font');
    const colorInput = itemElement.querySelector('.card-link-item-color');
    const previewDiv = itemElement.querySelector('.card-link-item-preview');

    if (!atTextInput || !fontSelect || !colorInput || !previewDiv) {
        // console.warn("Elementos faltando para preview do link do cartão:", itemElement);
        return;
    }

    const text = atTextInput.value.trim() || '@texto';
    const font = fontSelect.value || DEFAULT_FONT_JS;
    const color = colorInput.value || DEFAULT_TEXT_COLOR_CARD_JS;

    previewDiv.textContent = text;
    previewDiv.style.fontFamily = font;
    previewDiv.style.color = color;
    previewDiv.style.backgroundColor = '#555'; // Fundo fixo para a prévia do link no admin
    previewDiv.style.borderColor = color; // Borda com a cor do texto para destaque
}


function previewImage(input, previewId, fileInfoId) {
    const previewContainer = document.getElementById(previewId + '_container');
    const previewImageEl = document.getElementById(previewId);
    const fileInfoEl = document.getElementById(fileInfoId);
    const fileWrapper = input.closest('.file-upload-wrapper');
    // Botão específico para remover imagem de fundo do CARTÃO (card_background_image_preview)
    const removeCardBgImageBtn = document.getElementById('remove_card_background_image_btn');


    if (input.files && input.files[0]) {
        const reader = new FileReader();
        reader.onload = function (e) {
            if (previewImageEl) {
                previewImageEl.src = e.target.result;
                previewImageEl.style.display = 'block';
            }
            if (previewContainer) {
                previewContainer.style.display = 'block'; // Ou 'flex' se for para centralizar
                previewContainer.classList.add('preview-active');
            }
            if (fileInfoEl) fileInfoEl.textContent = input.files[0].name;
            if (fileWrapper) fileWrapper.classList.add('has-file');

            // Lógica específica para o botão de remover imagem de fundo do CARTÃO
            if (previewId === 'card_background_image_preview' && removeCardBgImageBtn) {
                removeCardBgImageBtn.style.display = 'inline-flex';
                const hiddenRemoveInput = document.getElementById('remove_card_background_image');
                if (hiddenRemoveInput) hiddenRemoveInput.value = 'false';
            }

            // Se a imagem sendo atualizada é a de fundo da PÁGINA, precisamos re-aplicar o overlay de escurecimento
            if (previewId === 'background_preview_page') {
                updatePageBackgroundDarkenPreview();
            }
        };
        reader.readAsDataURL(input.files[0]);
    } else { // Se nenhum arquivo for selecionado (ex: usuário cancela a seleção)
        if (previewImageEl) {
            // Não limpa o src se já houver uma imagem salva (identificada por não ser blob)
            // A limpeza do src deve ocorrer apenas se o usuário explicitamente remover a imagem
            // ou se a intenção for realmente limpar a prévia ao cancelar.
            // Por ora, se cancelar, a prévia da imagem salva (se houver) permanece.
        }
        if (fileInfoEl && (!previewImageEl || !previewImageEl.src || previewImageEl.src.includes('blob:') || previewImageEl.src === window.location.href)) {
            // fileInfoEl.textContent = 'Nenhum arquivo selecionado'; // Isso será tratado pelo carregamento inicial
        }
        // if (fileWrapper) fileWrapper.classList.remove('has-file'); // Idem
    }
}

function escapeHtml(text) {
    if (typeof text !== 'string') {
        return '';
    }
    const map = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' };
    return text.replace(/[&<>"']/g, function (m) { return map[m]; });
}

// Variáveis globais para o modal de botões
let editingButtonData = null;
let currentButtonModalPurpose = 'add';


document.addEventListener('DOMContentLoaded', function () {
    updateTextPreview('nome_preview', getValue('nome'), getValue('nome_font'), getValue('nome_color'));
    updateTextPreview('bio_preview', getValue('bio'), getValue('bio_font'), getValue('bio_color'));
    updateTextPreview('card_nome_preview', getValue('card_nome'), getValue('card_nome_font'), getValue('card_nome_color'));
    updateTextPreview('card_titulo_preview', getValue('card_titulo'), getValue('card_titulo_font'), getValue('card_titulo_color'));
    updateTextPreview('card_registro_preview', getValue('card_registro_profissional'), getValue('card_registro_font'), getValue('card_registro_color'));
    updateTextPreview('card_endereco_preview', getValue('card_endereco'), getValue('card_endereco_font'), getValue('card_endereco_color'));

    // Lista de imagens para carregar fileInfo e preview no início
    const fotosParaPreviewInicial = [
        { id: 'foto_preview', infoId: 'foto_info', uploadId: 'foto_upload' }, // Perfil
        { id: 'card_background_image_preview', infoId: 'card_background_info', uploadId: 'card_background_upload' }, // Fundo do Cartão
        { id: 'background_preview_page', infoId: 'background_info_page', uploadId: 'background_upload'} // Fundo da Página
    ];

    fotosParaPreviewInicial.forEach(item => {
        const previewElement = document.getElementById(item.id);
        const infoElement = document.getElementById(item.infoId);
        const containerElement = document.getElementById(item.id + '_container');
        const uploadInput = document.getElementById(item.uploadId);
        const fileWrapper = uploadInput ? uploadInput.closest('.file-upload-wrapper') : null;

        if (previewElement && previewElement.src && previewElement.src !== window.location.href && !previewElement.src.includes('blob:') && previewElement.src.trim() !== '') {
            if (containerElement) {
                // Para background_preview_page_container, o display é 'block' ou 'none' baseado na img.src
                // Para outros, pode ser 'block' ou 'flex' dependendo do CSS
                containerElement.style.display = containerElement.id === 'background_preview_page_container' && !previewElement.src ? 'none' : 'block';
                 if (previewElement.src && previewElement.src !== window.location.href && !previewElement.src.includes('blob:')) {
                    containerElement.classList.add('preview-active'); // Adiciona se tiver imagem real
                 } else {
                    containerElement.classList.remove('preview-active');
                 }

            }
            if (infoElement) {
                try {
                    const urlParts = previewElement.src.split('/');
                    const fileNameWithQuery = urlParts[urlParts.length - 1];
                    const fileName = fileNameWithQuery.split('?')[0]; // Remove query params se houver
                    infoElement.textContent = `Atual: ${decodeURIComponent(fileName)}`;
                } catch (e) {
                    infoElement.textContent = 'Imagem atual carregada';
                }
            }
            if (fileWrapper) fileWrapper.classList.add('has-file');

            // Lógica específica para o botão de remover imagem de fundo do CARTÃO
            if (item.id === 'card_background_image_preview') {
                const removeBtn = document.getElementById('remove_card_background_image_btn');
                if (removeBtn) removeBtn.style.display = 'inline-flex';
            }
        } else { // Se não há imagem salva (src está vazio, é blob, ou é a URL da página)
            if (infoElement) infoElement.textContent = 'Nenhum arquivo selecionado';
            if (containerElement) {
                containerElement.style.display = 'none';
                containerElement.classList.remove('preview-active');
            }
             // Lógica específica para o botão de remover imagem de fundo do CARTÃO
            if (item.id === 'card_background_image_preview') {
                const removeBtn = document.getElementById('remove_card_background_image_btn');
                if (removeBtn) removeBtn.style.display = 'none';
            }
        }
    });


    // Lógica para remover imagem de fundo do CARTÃO (já existente)
    const removeCardBgBtn = document.getElementById('remove_card_background_image_btn');
    const cardBgUploadInput = document.getElementById('card_background_upload');
    const cardBgImagePreview = document.getElementById('card_background_image_preview');
    const cardBgImagePreviewContainer = document.getElementById('card_background_image_preview_container');
    const removeCardBgHiddenInput = document.getElementById('remove_card_background_image');
    const cardBgInfo = document.getElementById('card_background_info');

    if (removeCardBgBtn) {
        removeCardBgBtn.addEventListener('click', () => {
            if (cardBgUploadInput) cardBgUploadInput.value = ''; // Limpa o input file
            if (cardBgImagePreview) {
                cardBgImagePreview.src = '';
                cardBgImagePreview.style.display = 'none';
            }
            if (cardBgImagePreviewContainer) {
                cardBgImagePreviewContainer.classList.remove('preview-active');
                cardBgImagePreviewContainer.style.display = 'none';
            }
            if (cardBgInfo) cardBgInfo.textContent = 'Nenhum arquivo selecionado';

            const cardBgUploadWrapper = cardBgUploadInput ? cardBgUploadInput.closest('.file-upload-wrapper') : null;
            if (cardBgUploadWrapper) cardBgUploadWrapper.classList.remove('has-file');

            if (removeCardBgHiddenInput) removeCardBgHiddenInput.value = 'true'; // Marca para remoção no backend
            removeCardBgBtn.style.display = 'none';
        });
    }

    const iconModal = document.getElementById('icon-modal');
    const buttonModal = document.getElementById('button-modal');
    const iconModalContent = iconModal ? iconModal.querySelector('.modal-content') : null;
    const buttonModalContent = buttonModal ? buttonModal.querySelector('.modal-content') : null;

    if (iconModalContent) iconModalContent.addEventListener('click', (e) => e.stopPropagation());
    if (buttonModalContent) buttonModalContent.addEventListener('click', (e) => e.stopPropagation());

    const socialIconsContainer = document.getElementById('social-icons-container');
    const customButtonsContainer = document.getElementById('custom-buttons-container');
    const cardLinksContainer = document.getElementById('card-links-container');

    if (socialIconsContainer) new Sortable(socialIconsContainer, { animation: 150, ghostClass: 'sortable-ghost', chosenClass: 'sortable-chosen', handle: '.drag-handle' });
    if (customButtonsContainer) new Sortable(customButtonsContainer, { animation: 150, ghostClass: 'sortable-ghost', chosenClass: 'sortable-chosen', handle: '.drag-handle' });
    if (cardLinksContainer) new Sortable(cardLinksContainer, { animation: 150, ghostClass: 'sortable-ghost', chosenClass: 'sortable-chosen', handle: '.drag-handle' });

    const addIconBtn = document.getElementById('add-icon-btn');
    const addCardLinkBtn = document.getElementById('add-card-link-btn');
    const iconModalCloseBtn = iconModal ? iconModal.querySelector('.icon-modal-close') : null;
    const iconsGrid = iconModal ? iconModal.querySelector('.icons-grid') : null;
    const iconSearchInput = document.getElementById('icon-search');
    const prevIconPageBtn = document.getElementById('prev-icon-page');
    const nextIconPageBtn = document.getElementById('next-icon-page');
    const currentPageSpan = document.getElementById('current-page');
    let currentIconModalPurpose = ''; // 'social', 'card_link', 'button_icon_selector'
    let selectedIconNameForButtonModal = ''; // Armazena o nome do ARQUIVO do ícone (ex: 'instagram.png')

    // ... (array allSocialIcons - extenso, mantido como no original)
    const allSocialIcons = [
        { name: 'instagram', path: '/static/icons/instagram.png' },
        { name: 'instagram-redondo', path: '/static/icons/instagram-redondo.png' },
        { name: 'linkedin', path: '/static/icons/linkedin.png' },
        { name: 'linkedin-redondo', path: '/static/icons/linkedin-redondo.png' },
        { name: 'linkedin-preto', path: '/static/icons/linkedin-preto' },
        { name: 'github', path: '/static/icons/github.png' },
        { name: 'github-redondo', path: '/static/icons/github-redondo.png' },
        { name: 'email', path: '/static/icons/email.png' },
        { name: 'email-preto', path: '/static/icons/email-preto.png' },
        { name: 'gmail', path: '/static/icons/gmail.png' },
        { name: 'gmail-redondo', path: '/static/icons/gmail-redondo.png' },
        { name: 'gmail-preto', path: '/static/icons/gmail-redondo.png' }, // Note: original tinha gmail-redondo aqui, verificar se é intencional
        { name: 'whatsapp', path: '/static/icons/whatsapp.png' },
        { name: 'whatsapp-v-p', path: '/static/icons/whatsapp-v-p.png' },
        { name: 'whatsapp-preto', path: '/static/icons/whatsapp-preto.png' },
        { name: 'twitter', path: '/static/icons/twitter.png' }, // Considere 'x-twitter.png' se atualizado
        { name: 'facebook', path: '/static/icons/facebook.png' },
        { name: 'facebook-redondo', path: '/static/icons/facebook-redondo.png' },
        { name: 'youtube', path: '/static/icons/youtube.png' },
        { name: 'youtube-preto', path: '/static/icons/youtube-preto.png' },
        { name: 'youtube-r', path: '/static/icons/youtube-r.png' },
        { name: 'youtube-p-r', path: '/static/icons/youtube-p-r.png' },
        { name: 'telegram', path: '/static/icons/telegram.png' },
        { name: 'telegrama-p', path: '/static/icons/telegrama-p.png' },
        { name: 'tiktok', path: '/static/icons/tiktok.png' },
        { name: 'tiktok-r', path: '/static/icons/tiktok-r.png' },
        { name: 'pinterest', path: '/static/icons/pinterest.png' },
        { name: 'pinterest-p', path: '/static/icons/pinterest-p.png' },
        { name: 'twitch', path: '/static/icons/twitch.png' },
        { name: 'twitch-r', path: '/static/icons/twitch-r.png' },
        { name: 'discord', path: '/static/icons/discord.png' },
        { name: 'discord-p', path: '/static/icons/discord-p.png' },
        { name: 'discord-p-r', path: '/static/icons/discord-p-r.png' },
        { name: 'discord-r', path: '/static/icons/discord-r.png' },
        { name: 'snapchat', path: '/static/icons/snapchat.png' },
        { name: 'snapchat-r', path: '/static/icons/snapchat-r.png' },
        { name: 'reddit', path: '/static/icons/reddit.png' },
        { name: 'reddit-p', path: '/static/icons/reddit-p.png' },
        { name: 'vimeo', path: '/static/icons/vimeo.png' },
        { name: 'spotify', path: '/static/icons/spotify.png' },
        { name: 'spotify-p', path: '/static/icons/spotify-p.png' },
        { name: 'soundcloud', path: '/static/icons/soundcloud.png' },
        { name: 'soundcloud-p', path: '/static/icons/soundcloud-p.png' },
        { name: 'behance', path: '/static/icons/behance.png' },
        { name: 'behance-p', path: '/static/icons/behance-p.png' },
        { name: 'flickr', path: '/static/icons/flickr.png' },
        { name: 'paypal', path: '/static/icons/paypal.png' },
        { name: 'paypal-p', path: '/static/icons/paypal-p.png' },
        { name: 'paypal-p-r', path: '/static/icons/paypal-p-r.png' },
        { name: 'paypal-r', path: '/static/icons/paypal-r.png' },
        { name: 'google-drive', path: '/static/icons/google-drive.png' },
        { name: 'google-drive-r', path: '/static/icons/google-drive-r.png' },
        { name: 'google-drive-r-p', path: '/static/icons/google-drive-r-p.png' },
        { name: 'dropbox', path: '/static/icons/dropbox.png' },
        { name: 'dropbox-p', path: '/static/icons/dropbox-p.png' },
        { name: 'link', path: '/static/icons/link.png' },
        { name: 'link-1', path: '/static/icons/link-1.png' },
        { name: 'link-2', path: '/static/icons/link-2.png' },
        { name: 'website', path: '/static/icons/website.png' },
        { name: 'website-p', path: '/static/icons/website-p.png' },
        { name: 'gitlab', path: '/static/icons/gitlab.png' },
        { name: 'gitlab-p-r', path: '/static/icons/gitlab-p-r.png' },
        { name: 'gitlab-r', path: '/static/icons/gitlab-r.png' },
        { name: 'gitlab-rv-p', path: '/static/icons/gitlab-rv-p.png' },
        { name: 'codepen', path: '/static/icons/codepen.png' },
        { name: 'codepen-p-r', path: '/static/icons/codepen-p-r.png' },
        { name: 'codepen-r-b', path: '/static/icons/codepen-r-b.png' },
        { name: 'patreon', path: '/static/icons/patreon.png' },
        { name: 'patreon-c', path: '/static/icons/patreon-c.png' },
        { name: 'patreon-r', path: '/static/icons/patreon-r.png' },
        { name: 'patreon-r-p', path: '/static/icons/patreon-r-p.png' },
        { name: 'buymeacoffee', path: '/static/icons/buymeacoffee.png' },
        { name: 'buymeacoffee-p', path: '/static/icons/buymeacoffee-p.png' },
        { name: 'ko-fi', path: '/static/icons/ko-fi.png' },
        { name: 'ko-fi-p', path: '/static/icons/ko-fi-p.png' },
        { name: 'slack', path: '/static/icons/slack.png' },
        { name: 'slack-r', path: '/static/icons/slack-r.png' },
        { name: 'slack-r-p', path: '/static/icons/slack-r-p.png' },
        { name: 'teams', path: '/static/icons/teams.png' },
        { name: 'teams-r', path: '/static/icons/teams-r.png' },
        { name: 'teams-r-p', path: '/static/icons/teams-r-p.png' },
        { name: 'skype', path: '/static/icons/skype.png' },
        { name: 'skype-o', path: '/static/icons/skype-o.png' },
        { name: 'skype-o-p', path: '/static/icons/skype-o-p.png' },
        { name: 'skype-p', path: '/static/icons/skype-p.png' },
        { name: 'academia-edu', path: '/static/icons/academia-edu.png' },
        { name: 'bluesky-r-p', path: '/static/icons/bluesky-r-p.png' },
        { name: 'closefans-r', path: '/static/icons/closefans-r.png' }, // Verificar se colsefans-r-p deve ser closefans-r-p
        { name: 'colsefans-r-p', path: '/static/icons/colsefans-r-p.png' }, // Potencial typo: colsefans
        { name: 'kwai', path: '/static/icons/kwai.png' },
        { name: 'kwai-p', path: '/static/icons/kwai-p.png' },
        { name: 'kwai-r', path: '/static/icons/kwai-r.png' },
        { name: 'kwai-r-p', path: '/static/icons/kwai-r-p.png' },
        { name: 'kwai-rb-p', path: '/static/icons/kwai-rb-p.png' },
        { name: 'kwai-vr-p', path: '/static/icons/kwai-vr-p.png' },
        { name: 'onlyfans', path: '/static/icons/onlyfans.png' },
        { name: 'onlyfans-r', path: '/static/icons/onlyfans-r.png' },
        { name: 'onlyfans-r-p', path: '/static/icons/onlyfans-r-p.png' },
        { name: 'onlyfans-rv-p', path: '/static/icons/onlyfans-rv-p.png' },
        { name: 'privacy', path: '/static/icons/privacy.png' }, // Nome genérico, pode precisar de mais contexto
        { name: 'privacy-r', path: '/static/icons/privacy-r.png' },
        { name: 'privacy-r-p', path: '/static/icons/privacy-r-p.png' },
        { name: 'privacy-rv-p', path: '/static/icons/privacy-rv-p.png' },
        { name: 'x-twitter', path: '/static/icons/x-twitter.png' },
        { name: 'x-twitter-r', path: '/static/icons/x-twitter-r.png' },
    ].sort((a, b) => a.name.localeCompare(b.name)); // Ordena por nome

    let filteredIcons = [...allSocialIcons];
    let currentPage = 1;
    const iconsPerPage = 9; // Ou 12 para 4 colunas (3x4 ou 4x3)

    function renderIcons() {
        if (!iconsGrid || !currentPageSpan) return;
        iconsGrid.innerHTML = '';
        const start = (currentPage - 1) * iconsPerPage;
        const end = start + iconsPerPage;
        const paginatedIcons = filteredIcons.slice(start, end);

        paginatedIcons.forEach(icon => {
            const iconDiv = document.createElement('div');
            iconDiv.className = 'icon-option';
            iconDiv.dataset.iconName = icon.name; // Usar o 'name' para identificação interna
            iconDiv.dataset.iconPath = icon.path; // Armazenar o path completo
            iconDiv.innerHTML = `
                <img src="${icon.path.startsWith('/static') ? icon.path : STATIC_ICONS_PATH + icon.path}" alt="${icon.name.replace(/-/g, ' ')}">
                <p>${icon.name.replace(/-/g, ' ')}</p>
            `;
            iconDiv.addEventListener('click', function () {
                document.querySelectorAll('#icon-modal .icon-option.selected').forEach(sel => sel.classList.remove('selected'));
                this.classList.add('selected');
            });
            iconsGrid.appendChild(iconDiv);
        });
        currentPageSpan.textContent = currentPage;
        updatePaginationControls();
    }

    function updatePaginationControls() {
        if (!prevIconPageBtn || !nextIconPageBtn) return;
        const totalPages = Math.ceil(filteredIcons.length / iconsPerPage);
        prevIconPageBtn.disabled = currentPage === 1;
        nextIconPageBtn.disabled = currentPage === totalPages || totalPages === 0;
    }

    function filterAndRenderIcons() {
        if (!iconSearchInput) return;
        const searchTerm = iconSearchInput.value.toLowerCase();
        filteredIcons = allSocialIcons.filter(icon => icon.name.toLowerCase().includes(searchTerm));
        currentPage = 1;
        renderIcons();
    }

    function closeModals() {
        if (iconModal) {
            iconModal.classList.remove('active', 'show', 'modal-on-top');
        }
        if (buttonModal) {
            buttonModal.classList.remove('active', 'show');
        }
        document.body.classList.remove('modal-open');
        currentIconModalPurpose = '';
        selectedIconNameForButtonModal = ''; // Limpa o ícone selecionado para o modal de botão
         // Limpar seleção no grid de ícones
        const selectedIconInGrid = iconModal ? iconModal.querySelector('.icon-option.selected') : null;
        if (selectedIconInGrid) {
            selectedIconInGrid.classList.remove('selected');
        }
    }

    if (iconSearchInput) iconSearchInput.addEventListener('input', filterAndRenderIcons);
    if (prevIconPageBtn) prevIconPageBtn.addEventListener('click', () => { if (currentPage > 1) { currentPage--; renderIcons(); } });
    if (nextIconPageBtn) nextIconPageBtn.addEventListener('click', () => { const totalPages = Math.ceil(filteredIcons.length / iconsPerPage); if (currentPage < totalPages) { currentPage++; renderIcons(); } });

    function openIconModal(purpose) {
        currentIconModalPurpose = purpose;
        if (iconSearchInput) iconSearchInput.value = ''; // Limpa a busca
        filterAndRenderIcons(); // Renderiza todos os ícones
        if (iconModal) {
            if (purpose === 'button_icon_selector') {
                iconModal.classList.add('modal-on-top'); // Garante que o modal de ícones fique sobre o de botões
            }
            iconModal.classList.add('show');
            document.body.classList.add('modal-open');
            setTimeout(() => iconModal.classList.add('active'), 50); // Pequeno delay para transição CSS
        }
    }

    if (addIconBtn) {
        addIconBtn.addEventListener('click', () => openIconModal('social'));
    }
    if (addCardLinkBtn) {
        addCardLinkBtn.addEventListener('click', () => {
            if (document.querySelectorAll('#card-links-container .card-link-item').length < 3) {
                openIconModal('card_link');
            } else {
                alert('Você pode adicionar no máximo 3 links ao cartão.');
            }
        });
    }

    const saveIconBtn = document.getElementById('save-icon');
    if (saveIconBtn) {
        saveIconBtn.addEventListener('click', function () {
            const selectedIconDiv = iconModal ? iconModal.querySelector('.icon-option.selected') : null;
            if (!selectedIconDiv) {
                alert('Por favor, selecione um ícone.');
                return;
            }
            const iconNameFromDataset = selectedIconDiv.dataset.iconName; // Ex: 'instagram' (nome amigável/chave)
            const iconPathFromDataset = selectedIconDiv.dataset.iconPath; // Ex: '/static/icons/instagram.png'
            
            // O nome do arquivo é a última parte do path
            const iconFileNameOnly = iconPathFromDataset.split('/').pop();


            if (currentIconModalPurpose === 'social') {
                const socialItem = document.createElement('div');
                socialItem.className = 'social-item';
                socialItem.innerHTML = `
                    <i class="fas fa-grip-vertical drag-handle" title="Arrastar para reordenar"></i>
                    <img src="${iconPathFromDataset.startsWith('/static') ? iconPathFromDataset : STATIC_ICONS_PATH + iconFileNameOnly}" alt="${iconNameFromDataset}" width="24" height="24">
                    <input type="hidden" name="social_icon_name[]" value="${iconFileNameOnly}"> {/* Salva o NOME DO ARQUIVO */}
                    <input type="text" name="social_icon_url[]" placeholder="Insira o link para ${iconNameFromDataset.replace(/-/g, ' ')}" class="form-input" required>
                    <span class="remove-item" title="Remover este ícone"><i class="fas fa-times"></i></span>
                `;
                if(socialIconsContainer) socialIconsContainer.appendChild(socialItem);
                socialItem.querySelector('.remove-item').addEventListener('click', function () { this.closest('.social-item').remove(); });
                closeModals();
            } else if (currentIconModalPurpose === 'card_link') {
                const cardLinkItem = document.createElement('div');
                cardLinkItem.className = 'card-link-item';
                cardLinkItem.innerHTML = `
                    <i class="fas fa-grip-vertical drag-handle" title="Arrastar para reordenar"></i>
                    <img src="${iconPathFromDataset.startsWith('/static') ? iconPathFromDataset : STATIC_ICONS_PATH + iconFileNameOnly}" alt="${iconNameFromDataset}" width="24" height="24">
                    <input type="hidden" name="card_icon_name[]" value="${iconFileNameOnly}"> {/* Salva o NOME DO ARQUIVO */}
                    <div class="input-group">
                        <input type="url" name="card_icon_url[]" placeholder="URL do Link (Opcional)" class="form-input">
                        <input type="text" name="card_icon_at_text[]" placeholder="Texto exibido (ex: @usuario)" class="form-input card-link-item-at-text">
                    </div>
                    <div class="card-link-style-controls">
                        <input type="hidden" name="card_icon_font[]" value="${DEFAULT_FONT_JS}">
                        <select class="form-input card-link-item-font" title="Fonte do texto do link">
                            <option value="Inter, sans-serif" ${DEFAULT_FONT_JS === 'Inter, sans-serif' ? 'selected' : ''}>Padrão (Inter)</option>
                            <option value="Arial, sans-serif" ${DEFAULT_FONT_JS === 'Arial, sans-serif' ? 'selected' : ''}>Arial</option>
                            <option value="Verdana, sans-serif" ${DEFAULT_FONT_JS === 'Verdana, sans-serif' ? 'selected' : ''}>Verdana</option>
                            <option value="Georgia, serif" ${DEFAULT_FONT_JS === 'Georgia, serif' ? 'selected' : ''}>Georgia</option>
                            <option value="'Times New Roman', Times, serif" ${DEFAULT_FONT_JS === "'Times New Roman', Times, serif" ? 'selected' : ''}>Times New Roman</option>
                            <option value="'Courier New', Courier, monospace" ${DEFAULT_FONT_JS === "'Courier New', Courier, monospace" ? 'selected' : ''}>Courier New</option>
                            <option value="Roboto, sans-serif" ${DEFAULT_FONT_JS === 'Roboto, sans-serif' ? 'selected' : ''}>Roboto</option>
                            <option value="'Open Sans', sans-serif" ${DEFAULT_FONT_JS === "'Open Sans', sans-serif" ? 'selected' : ''}>Open Sans</option>
                            <option value="Lato, sans-serif" ${DEFAULT_FONT_JS === 'Lato, sans-serif' ? 'selected' : ''}>Lato</option>
                            <option value="Montserrat, sans-serif" ${DEFAULT_FONT_JS === 'Montserrat, sans-serif' ? 'selected' : ''}>Montserrat</option>
                        </select>
                        <input type="hidden" name="card_icon_color[]" value="${getValue('card_link_text_color') || DEFAULT_TEXT_COLOR_CARD_JS}">
                        <input type="color" class="card-link-item-color" title="Cor do texto do link" value="${getValue('card_link_text_color') || DEFAULT_TEXT_COLOR_CARD_JS}">
                    </div>
                    <div class="card-link-item-preview" title="Prévia do texto do link"></div>
                    <span class="remove-item" title="Remover este link do cartão"><i class="fas fa-times"></i></span>
                `;
                if(cardLinksContainer) cardLinksContainer.appendChild(cardLinkItem);
                updateCardLinkItemPreview(cardLinkItem); // Atualiza a prévia do novo item
                cardLinkItem.querySelector('.remove-item').addEventListener('click', function () { this.closest('.card-link-item').remove(); });

                // Adicionar listeners para os novos inputs do link do cartão
                const atTextInputNew = cardLinkItem.querySelector('.card-link-item-at-text');
                const fontSelectNew = cardLinkItem.querySelector('.card-link-item-font');
                const colorInputNew = cardLinkItem.querySelector('.card-link-item-color');
                const hiddenFontInputNew = cardLinkItem.querySelector('input[name="card_icon_font[]"]');
                const hiddenColorInputNew = cardLinkItem.querySelector('input[name="card_icon_color[]"]');

                if (atTextInputNew) atTextInputNew.addEventListener('input', () => updateCardLinkItemPreview(cardLinkItem));
                if (fontSelectNew && hiddenFontInputNew) fontSelectNew.addEventListener('change', () => { hiddenFontInputNew.value = fontSelectNew.value; updateCardLinkItemPreview(cardLinkItem); });
                if (colorInputNew && hiddenColorInputNew) colorInputNew.addEventListener('input', () => { hiddenColorInputNew.value = colorInputNew.value; updateCardLinkItemPreview(cardLinkItem); });
                closeModals();
            } else if (currentIconModalPurpose === 'button_icon_selector') {
                selectedIconNameForButtonModal = iconFileNameOnly; // Salva o NOME DO ARQUIVO (ex: 'instagram.png')

                const buttonModalActualIconType = document.getElementById('button-modal-actual-icon-type');
                const buttonModalActualIconValue = document.getElementById('button-modal-actual-icon-value');
                const libraryIconNamePreview = document.getElementById('button-library-icon-name-preview');

                if (buttonModalActualIconType) buttonModalActualIconType.value = 'library_icon';
                if (buttonModalActualIconValue) buttonModalActualIconValue.value = selectedIconNameForButtonModal; // Salva o NOME DO ARQUIVO
                if (libraryIconNamePreview) libraryIconNamePreview.textContent = `Ícone selecionado: ${iconNameFromDataset.replace(/-/g, ' ')}`;

                updateButtonPreview(); // Atualiza a prévia do botão no modal de botões

                // Fecha APENAS o iconModal, mantendo o buttonModal aberto
                if (iconModal) {
                    iconModal.classList.remove('active', 'show', 'modal-on-top');
                }
                // Não remove 'modal-open' do body aqui, pois o buttonModal ainda está ativo
                currentIconModalPurpose = ''; // Resetar o propósito para o próximo uso
                // Limpar seleção no grid de ícones
                const selectedIconInGrid = iconModal ? iconModal.querySelector('.icon-option.selected') : null;
                if (selectedIconInGrid) {
                    selectedIconInGrid.classList.remove('selected');
                }
            } else {
                closeModals();
            }
        });
    }


    // Inicializar prévias para links de cartão existentes
    document.querySelectorAll('#card-links-container .card-link-item').forEach(item => {
        updateCardLinkItemPreview(item); // Atualiza a prévia ao carregar
        const atTextInput = item.querySelector('.card-link-item-at-text');
        const fontSelect = item.querySelector('.card-link-item-font');
        const colorInput = item.querySelector('.card-link-item-color');
        const hiddenFontInput = item.querySelector('input[name="card_icon_font[]"]');
        const hiddenColorInput = item.querySelector('input[name="card_icon_color[]"]');

        if (atTextInput) atTextInput.addEventListener('input', () => updateCardLinkItemPreview(item));
        if (fontSelect && hiddenFontInput) fontSelect.addEventListener('change', () => { hiddenFontInput.value = fontSelect.value; updateCardLinkItemPreview(item); });
        if (colorInput && hiddenColorInput) colorInput.addEventListener('input', () => { hiddenColorInput.value = colorInput.value; updateCardLinkItemPreview(item); });
    });


    const addButtonBtn = document.getElementById('add-button-btn');
    const buttonModalCloseBtn = buttonModal ? buttonModal.querySelector('.button-modal-close') : null;

    const liveButtonPreview = document.getElementById('live-button-preview');
    const liveButtonTextPreview = liveButtonPreview ? liveButtonPreview.querySelector('.button-text-preview') : null;
    const liveButtonIconPreview = liveButtonPreview ? liveButtonPreview.querySelector('.button-icon-preview') : null;

    const buttonTextInput = document.getElementById('button-text');
    const buttonLinkInput = document.getElementById('button-link');
    const buttonStyleSelect = document.getElementById('button-style-select');
    const buttonIconTypeSelect = document.getElementById('button-icon-type-select');

    const buttonIconUrlExternalGroup = document.getElementById('button-icon-url-external-group');
    const buttonIconUrlExternalInput = document.getElementById('button-icon-url-external-input');
    const buttonNewImageFileGroup = document.getElementById('button-new-image-file-group');
    const buttonNewImageFileInput = document.getElementById('button-new-image-file-input');
    const buttonNewImageFileInfo = document.getElementById('button-new-image-file-info');
    const buttonSelectLibraryIconGroup = document.getElementById('button-select-library-icon-group');
    const buttonSelectLibraryIconBtn = document.getElementById('button-select-library-icon-btn');
    const libraryIconNamePreview = document.getElementById('button-library-icon-name-preview');
    const buttonIconRoundedGroup = document.getElementById('button-icon-rounded-group');
    const buttonIconRoundedCheckbox = document.getElementById('button-icon-rounded');

    const buttonColorInput = document.getElementById('button-color');
    const buttonOpacitySlider = document.getElementById('button-opacity');
    const opacityValueSpan = document.getElementById('opacity-value');
    const buttonRadiusInput = document.getElementById('button-radius');
    const radiusValueSpan = document.getElementById('radius-value');
    const buttonTextColorInput = document.getElementById('button-text-color');
    const buttonTextBoldCheckbox = document.getElementById('button-text-bold');
    const buttonTextItalicCheckbox = document.getElementById('button-text-italic');
    const buttonFontSizeInput = document.getElementById('button-font-size');
    const buttonHasBorderCheckbox = document.getElementById('button-has-border');
    const borderOptionsGroup = document.getElementById('border-options-group');
    const buttonBorderColorInput = document.getElementById('button-border-color');
    const buttonBorderWidthInput = document.getElementById('button-border-width');
    const buttonHasHoverCheckbox = document.getElementById('button-has-hover');
    const buttonShadowTypeSelect = document.getElementById('button-shadow-type');

    // Inputs ocultos para armazenar o tipo e valor REAL do ícone do botão
    const buttonModalActualIconType = document.getElementById('button-modal-actual-icon-type');
    const buttonModalActualIconValue = document.getElementById('button-modal-actual-icon-value');


    function manageButtonIconFieldsVisibility() {
        if(!buttonIconTypeSelect || !buttonIconUrlExternalGroup || !buttonNewImageFileGroup || !buttonSelectLibraryIconGroup || !buttonIconRoundedGroup || !buttonIconUrlExternalInput || !buttonNewImageFileInput || !libraryIconNamePreview || !buttonIconRoundedCheckbox) return;

        const selectedType = buttonIconTypeSelect.value;

        buttonIconUrlExternalGroup.style.display = selectedType === 'image_url_external' ? 'block' : 'none';
        buttonNewImageFileGroup.style.display = selectedType === 'image_upload_new' ? 'block' : 'none';
        buttonSelectLibraryIconGroup.style.display = selectedType === 'library_icon' ? 'block' : 'none';
        // Mostrar arredondamento para URL externa e upload novo. Para ícones da lib, geralmente não se arredonda a menos que seja desejado.
        buttonIconRoundedGroup.style.display = (selectedType === 'image_url_external' || selectedType === 'image_upload_new' || selectedType === 'library_icon') ? 'flex' : 'none';


        // Limpar campos não selecionados e 'actual' values
        if (selectedType !== 'image_url_external') buttonIconUrlExternalInput.value = '';
        if (selectedType !== 'image_upload_new') {
            buttonNewImageFileInput.value = ''; // Limpa o input file
            if (buttonNewImageFileInfo) buttonNewImageFileInfo.textContent = 'Nenhum arquivo selecionado';
        }
        if (selectedType !== 'library_icon') {
            if (libraryIconNamePreview) libraryIconNamePreview.textContent = ''; // Limpa nome do ícone da lib
            selectedIconNameForButtonModal = ''; // Limpa a variável JS
        }

        // Atualizar 'actual' values baseado na seleção (antes de limpar)
        // Se o tipo selecionado é diferente do 'actual type', então o 'actual value' deve ser limpo.
        if (buttonModalActualIconType && buttonModalActualIconType.value !== selectedType) {
            if(buttonModalActualIconValue) buttonModalActualIconValue.value = '';
        }
        if (selectedType === 'none') {
            if(buttonModalActualIconType) buttonModalActualIconType.value = 'none';
            if(buttonModalActualIconValue) buttonModalActualIconValue.value = '';
            buttonIconRoundedCheckbox.checked = false; // Desmarcar arredondamento se nenhum ícone
        } else if (selectedType === 'library_icon' && selectedIconNameForButtonModal) {
            // Se mudou para library_icon E já havia um selecionado, restaura
            if(buttonModalActualIconType) buttonModalActualIconType.value = 'library_icon';
            if(buttonModalActualIconValue) buttonModalActualIconValue.value = selectedIconNameForButtonModal;
        } else if (selectedType === 'image_url_external') {
            // Se mudou para URL externa, o actual value virá do input
            if(buttonModalActualIconType) buttonModalActualIconType.value = 'image_url_external';
            if(buttonModalActualIconValue) buttonModalActualIconValue.value = buttonIconUrlExternalInput.value;
        }
        // Para 'image_upload_new', o actual value é setado no evento 'change' do input file.

        updateButtonPreview();
    }

    if (buttonIconTypeSelect) {
        buttonIconTypeSelect.addEventListener('change', manageButtonIconFieldsVisibility);
    }

    if (buttonSelectLibraryIconBtn) {
        buttonSelectLibraryIconBtn.addEventListener('click', () => {
            openIconModal('button_icon_selector');
        });
    }

    async function uploadButtonImageAJAX(file) {
        if (!file) return null;
        const formData = new FormData();
        formData.append('button_image', file); // Nome do campo esperado pelo backend

        if (liveButtonIconPreview) liveButtonIconPreview.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';


        try {
            const response = await fetch(UPLOAD_BUTTON_IMAGE_URL, { // UPLOAD_BUTTON_IMAGE_URL é uma var global
                method: 'POST',
                body: formData,
                // Não defina Content-Type aqui, o browser faz isso com FormData
            });
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ error: 'Erro desconhecido no upload.' }));
                throw new Error(errorData.error || `Erro ${response.status}`);
            }
            const data = await response.json();
            if (data.url) {
                return data.url; // URL pública do Supabase
            } else {
                throw new Error(data.error || 'URL da imagem não retornada.');
            }
        } catch (error) {
            console.error('Erro no upload da imagem do botão:', error);
            alert(`Erro ao enviar imagem: ${error.message}`);
            if (liveButtonIconPreview) liveButtonIconPreview.innerHTML = ''; // Limpa o spinner
            return null;
        }
    }


    if (buttonNewImageFileInput) {
        buttonNewImageFileInput.addEventListener('change', async function () {
            if (this.files && this.files[0]) {
                const file = this.files[0];
                if (buttonNewImageFileInfo) buttonNewImageFileInfo.textContent = file.name;

                const uploadedUrl = await uploadButtonImageAJAX(file);
                if (uploadedUrl) {
                    if (buttonModalActualIconType) buttonModalActualIconType.value = 'image_uploaded'; // Tipo especial para saber que é do storage
                    if (buttonModalActualIconValue) buttonModalActualIconValue.value = uploadedUrl;
                    updateButtonPreview();
                } else { // Falha no upload
                    this.value = ''; // Limpa o input file
                    if (buttonNewImageFileInfo) buttonNewImageFileInfo.textContent = 'Falha no envio. Nenhum arquivo selecionado.';
                    if (buttonModalActualIconType && buttonModalActualIconType.value === 'image_uploaded') {
                        buttonModalActualIconType.value = 'none'; // Reverte para 'none'
                        if(buttonModalActualIconValue) buttonModalActualIconValue.value = '';
                    }
                    updateButtonPreview();
                }
            } else { // Nenhum arquivo selecionado (ex: cancelou)
                if (buttonNewImageFileInfo) buttonNewImageFileInfo.textContent = 'Nenhum arquivo selecionado';
                // Se o tipo atual era 'image_uploaded', e o usuário cancela, precisa resetar
                if (buttonModalActualIconType && buttonModalActualIconType.value === 'image_uploaded') {
                    buttonModalActualIconType.value = 'none';
                    if(buttonModalActualIconValue) buttonModalActualIconValue.value = '';
                }
                updateButtonPreview();
            }
        });
    }
    if (buttonIconUrlExternalInput) {
        buttonIconUrlExternalInput.addEventListener('input', function () {
            // Só atualiza o 'actual' se o tipo selecionado for realmente 'image_url_external'
            if (buttonIconTypeSelect && buttonIconTypeSelect.value === 'image_url_external') {
                if (buttonModalActualIconType) buttonModalActualIconType.value = 'image_url_external';
                if (buttonModalActualIconValue) buttonModalActualIconValue.value = this.value; // this.value é a URL
                updateButtonPreview();
            }
        });
    }


    function updateButtonPreview() {
        if (!liveButtonPreview || !liveButtonTextPreview || !liveButtonIconPreview || !buttonTextInput || !buttonColorInput || !buttonRadiusInput || !radiusValueSpan || !buttonTextColorInput || !buttonTextBoldCheckbox || !buttonTextItalicCheckbox || !buttonFontSizeInput || !buttonHasBorderCheckbox || !buttonBorderColorInput || !buttonBorderWidthInput || !buttonHasHoverCheckbox || !buttonShadowTypeSelect || !buttonOpacitySlider || !opacityValueSpan || !buttonIconTypeSelect || !buttonStyleSelect || !buttonIconRoundedCheckbox || !borderOptionsGroup || !buttonModalActualIconType || !buttonModalActualIconValue) {
            console.warn("updateButtonPreview: Elementos de preview ou controle não encontrados.");
            return;
        }

        liveButtonTextPreview.textContent = buttonTextInput.value.trim() || 'Texto do Botão';

        const bgColor = buttonColorInput.value;
        const bgOpacity = parseFloat(buttonOpacitySlider.value);
        if (opacityValueSpan) opacityValueSpan.textContent = bgOpacity.toFixed(2);
        liveButtonPreview.style.backgroundColor = hexToRgba(bgColor, bgOpacity);

        const borderRadiusPx = `${buttonRadiusInput.value}px`;
        liveButtonPreview.style.borderRadius = borderRadiusPx;
        if (radiusValueSpan) radiusValueSpan.textContent = borderRadiusPx;

        liveButtonPreview.style.color = buttonTextColorInput.value;
        liveButtonPreview.style.fontWeight = buttonTextBoldCheckbox.checked ? 'bold' : 'normal';
        liveButtonPreview.style.fontStyle = buttonTextItalicCheckbox.checked ? 'italic' : 'normal';
        liveButtonPreview.style.fontSize = `${buttonFontSizeInput.value}px`;

        if (buttonHasBorderCheckbox.checked) {
            liveButtonPreview.style.border = `${buttonBorderWidthInput.value}px solid ${buttonBorderColorInput.value}`;
        } else {
            liveButtonPreview.style.border = 'none'; // Ou '1px solid transparent' se preferir manter o layout
        }

        // Limpar classes de estilo e sombra antes de aplicar as novas
        liveButtonPreview.className = 'button-style-default'; // Reset para classe base do preview
        // Adiciona a classe do estilo principal (ex: button-style-default, button-style-solid_shadow)
        const selectedButtonStyle = buttonStyleSelect.value;
        liveButtonPreview.classList.add(`button-style-${selectedButtonStyle}`);

        // Controlar visibilidade dos campos de estilo "default" (sombra, hover)
        const defaultStyleControlsElements = document.querySelectorAll('[data-style-target="default"]');

        if (selectedButtonStyle === 'default') {
            defaultStyleControlsElements.forEach(el => el.style.display = 'block'); // ou 'flex' se for inline
             // Aplicar sombra e hover apenas se o estilo for 'default'
            if (buttonShadowTypeSelect.value !== 'none') {
                liveButtonPreview.classList.add(`shadow-${buttonShadowTypeSelect.value}`);
            }
            if (buttonHasHoverCheckbox.checked) {
                liveButtonPreview.classList.add('hover-effect-preview'); // Classe para simular hover no preview
            }
        } else {
            defaultStyleControlsElements.forEach(el => el.style.display = 'none');
        }


        // Lógica do Ícone
        const actualIconType = buttonModalActualIconType.value; // 'none', 'image_url_external', 'image_uploaded', 'library_icon'
        const actualIconValue = buttonModalActualIconValue.value.trim(); // URL ou nome do arquivo do ícone da lib
        const iconRounded = buttonIconRoundedCheckbox.checked;

        liveButtonIconPreview.innerHTML = ''; // Limpa ícone anterior

        if (actualIconType !== 'none' && actualIconValue) {
            const img = document.createElement('img');
            if (actualIconType === 'image_url_external' || actualIconType === 'image_uploaded') {
                img.src = actualIconValue; // URL direta
            } else if (actualIconType === 'library_icon') {
                img.src = `${STATIC_ICONS_PATH}${actualIconValue}`; // Constrói URL para ícone da lib
            }
            img.alt = 'Ícone';
            if (iconRounded) img.classList.add('rounded');
            liveButtonIconPreview.appendChild(img);
            liveButtonIconPreview.style.marginRight = liveButtonTextPreview.textContent ? '8px' : '0'; // Espaço se houver texto
        } else {
            liveButtonIconPreview.style.marginRight = '0';
        }
    }


    if (buttonHasBorderCheckbox) {
        buttonHasBorderCheckbox.addEventListener('change', function () {
            if (borderOptionsGroup) borderOptionsGroup.style.display = this.checked ? 'flex' : 'none';
            updateButtonPreview();
        });
         // Estado inicial do borderOptionsGroup
        if (borderOptionsGroup) borderOptionsGroup.style.display = buttonHasBorderCheckbox.checked ? 'flex' : 'none';
    }

    const elementsForButtonPreviewUpdate = [
        buttonTextInput, buttonColorInput, buttonRadiusInput, buttonTextColorInput,
        buttonTextBoldCheckbox, buttonTextItalicCheckbox, buttonFontSizeInput,
        buttonHasBorderCheckbox, buttonBorderColorInput, buttonBorderWidthInput,
        buttonHasHoverCheckbox, buttonShadowTypeSelect, buttonStyleSelect,
        buttonOpacitySlider, buttonIconTypeSelect, buttonIconUrlExternalInput, // buttonNewImageFileInput atualiza via seu próprio listener
        buttonIconRoundedCheckbox
    ];

    elementsForButtonPreviewUpdate.forEach(el => {
        if (el) {
            const eventType = (el.type === 'checkbox' || el.tagName === 'SELECT' || el.type === 'range') ? 'change' : 'input';
            el.addEventListener(eventType, updateButtonPreview);
        }
    });

    function openButtonModal(data = null, index = -1) {
        currentButtonModalPurpose = data ? 'edit' : 'add';
        editingButtonData = data; // Armazena os dados do botão que está sendo editado
        document.getElementById('button-modal-editing-index').value = index; // Para saber qual item atualizar na lista

        // Resetar ou preencher campos do modal
        buttonTextInput.value = data ? data.text : '';
        buttonLinkInput.value = data ? data.link : '';
        buttonStyleSelect.value = data ? data.buttonStyle : DEFAULT_BUTTON_STYLE_JS;

        // Lógica para ícones ao abrir modal
        const currentIconType = data ? data.iconType : DEFAULT_BUTTON_ICON_TYPE_JS;
        const currentIconUrl = data ? data.iconUrl : DEFAULT_BUTTON_ICON_URL_JS; // Pode ser URL ou nome do arquivo da lib
        
        buttonModalActualIconType.value = currentIconType; // Define o tipo real do ícone
        buttonModalActualIconValue.value = currentIconUrl; // Define o valor real (URL ou nome do arquivo)

        // Ajusta o seletor de tipo de ícone
        buttonIconTypeSelect.value = currentIconType;
        if (currentIconType === 'image_url_external') {
            buttonIconUrlExternalInput.value = currentIconUrl;
        } else if (currentIconType === 'library_icon') {
            selectedIconNameForButtonModal = currentIconUrl; // Nome do arquivo do ícone da lib
            if(libraryIconNamePreview) libraryIconNamePreview.textContent = `Ícone atual: ${currentIconUrl.split('.')[0].replace(/-/g, ' ')}`;
        } else if (currentIconType === 'image_uploaded') {
            // Para image_uploaded, o valor é a URL do Supabase. O input file não será preenchido.
            if (buttonNewImageFileInfo) buttonNewImageFileInfo.textContent = `Atual: ${currentIconUrl.split('/').pop().split('?')[0]}`;
        } else { // 'none' ou default
            buttonIconTypeSelect.value = 'none';
        }
        manageButtonIconFieldsVisibility(); // Mostra/esconde os campos corretos de ícone

        buttonIconRoundedCheckbox.checked = data ? data.iconRounded : DEFAULT_BUTTON_ICON_ROUNDED_JS;
        buttonColorInput.value = data ? data.color : '#4CAF50'; // Default color
        buttonOpacitySlider.value = data ? data.opacity : DEFAULT_BUTTON_OPACITY_JS;
        buttonRadiusInput.value = data ? data.radius : '10'; // Default radius
        buttonTextColorInput.value = data ? data.textColor : '#FFFFFF'; // Default text color
        buttonTextBoldCheckbox.checked = data ? data.bold : false;
        buttonTextItalicCheckbox.checked = data ? data.italic : false;
        buttonFontSizeInput.value = data ? data.fontSize : '16'; // Default font size
        buttonHasBorderCheckbox.checked = data ? data.hasBorder : false;
        if (borderOptionsGroup) borderOptionsGroup.style.display = buttonHasBorderCheckbox.checked ? 'flex' : 'none';
        buttonBorderColorInput.value = data ? data.borderColor : '#000000';
        buttonBorderWidthInput.value = data ? data.borderWidth : '2';
        buttonHasHoverCheckbox.checked = data ? (data.buttonStyle === 'default' ? data.hasHoverEffect : false) : false;
        buttonShadowTypeSelect.value = data ? (data.buttonStyle === 'default' ? data.shadowType : 'none') : 'none';


        updateButtonPreview(); // Atualiza a prévia com os dados carregados/resetados
        if (buttonModal) {
            buttonModal.classList.add('show');
            document.body.classList.add('modal-open');
            setTimeout(() => buttonModal.classList.add('active'), 50);
        }
    }


    if (addButtonBtn) {
        addButtonBtn.addEventListener('click', () => openButtonModal()); // Abre para adicionar novo
    }

    const saveButtonModalBtn = document.getElementById('save-button');
    if (saveButtonModalBtn) {
        saveButtonModalBtn.addEventListener('click', function (event) {
            event.preventDefault(); // Previne submissão do formulário principal

            const btnText = buttonTextInput.value.trim();
            const btnLinkValue = buttonLinkInput.value.trim();

            if (!btnText) {
                alert('Por favor, preencha o texto do botão!');
                if (buttonTextInput) {
                    buttonTextInput.focus();
                }
                return;
            }

            if (buttonLinkInput && btnLinkValue && !buttonLinkInput.checkValidity()) { // Valida URL se preenchida
                buttonLinkInput.reportValidity();
                return;
            }
            const btnLink = btnLinkValue; // Pode ser vazia se não obrigatória

            const newButtonData = {
                text: btnText,
                link: btnLink,
                buttonStyle: buttonStyleSelect.value,
                iconType: buttonModalActualIconType.value, // Usa o valor "real" do tipo de ícone
                iconUrl: buttonModalActualIconValue.value,  // Usa o valor "real" do ícone (URL ou nome do arquivo)
                iconRounded: buttonIconRoundedCheckbox.checked,
                color: buttonColorInput.value,
                opacity: parseFloat(buttonOpacitySlider.value),
                radius: parseInt(buttonRadiusInput.value),
                textColor: buttonTextColorInput.value,
                bold: buttonTextBoldCheckbox.checked,
                italic: buttonTextItalicCheckbox.checked,
                fontSize: parseInt(buttonFontSizeInput.value),
                hasBorder: buttonHasBorderCheckbox.checked,
                borderColor: buttonBorderColorInput.value,
                borderWidth: parseInt(buttonBorderWidthInput.value),
                hasHoverEffect: buttonStyleSelect.value === 'default' ? buttonHasHoverCheckbox.checked : false,
                shadowType: buttonStyleSelect.value === 'default' ? buttonShadowTypeSelect.value : 'none',
            };

            const editingIndex = parseInt(document.getElementById('button-modal-editing-index').value);
            if (editingIndex > -1) { // Editando um botão existente
                const items = customButtonsContainer.querySelectorAll('.custom-button-item');
                if (items[editingIndex]) {
                    items[editingIndex].remove(); // Remove o item antigo da DOM
                    renderCustomButton(newButtonData, editingIndex); // Re-renderiza na mesma posição
                } else { // Caso não encontre o item (improvável), adiciona no final
                    renderCustomButton(newButtonData);
                }
            } else { // Adicionando novo botão
                renderCustomButton(newButtonData);
            }
            closeModals(); // Fecha o modal de botão (e o de ícones, se aberto)
        });
    }

    function renderCustomButton(buttonData, index = -1) {
        if (!customButtonsContainer) return;

        const buttonField = document.createElement('div');
        buttonField.className = 'custom-button-item';

        // Sanitizar e definir defaults para todos os campos de buttonData
        const text = escapeHtml(buttonData.text || 'Botão');
        const link = escapeHtml(buttonData.link || '#');
        const buttonStyle = escapeHtml(buttonData.buttonStyle || DEFAULT_BUTTON_STYLE_JS);
        const iconType = escapeHtml(buttonData.iconType || DEFAULT_BUTTON_ICON_TYPE_JS);
        const iconUrl = escapeHtml(buttonData.iconUrl || DEFAULT_BUTTON_ICON_URL_JS); // Pode ser URL ou nome de arquivo da lib
        const iconRounded = buttonData.iconRounded || DEFAULT_BUTTON_ICON_ROUNDED_JS;
        const color = escapeHtml(buttonData.color || '#4CAF50');
        const opacity = typeof buttonData.opacity === 'number' ? buttonData.opacity : DEFAULT_BUTTON_OPACITY_JS;
        const radius = parseInt(buttonData.radius) || 10;
        const textColor = escapeHtml(buttonData.textColor || '#FFFFFF');
        const bold = buttonData.bold || false;
        const italic = buttonData.italic || false;
        const fontSize = parseInt(buttonData.fontSize) || 16;
        const hasBorder = buttonData.hasBorder || false;
        const borderColor = escapeHtml(buttonData.borderColor || '#000000');
        const borderWidth = parseInt(buttonData.borderWidth) || 2;
        const hasHoverEffect = buttonStyle === 'default' ? (buttonData.hasHoverEffect || false) : false;
        const shadowType = buttonStyle === 'default' ? (escapeHtml(buttonData.shadowType || 'none')) : 'none';


        let borderStyleCSS = '';
        let buttonPreviewClasses = ['button-preview', `button-style-${buttonStyle}`]; // Adiciona classe de estilo principal
        if (hasBorder) {
            borderStyleCSS = `border: ${borderWidth}px solid ${borderColor};`;
            buttonPreviewClasses.push('has-border-preview'); // Classe para estilização de borda se necessário
        }
        if (buttonStyle === 'default') {
            if (hasHoverEffect) buttonPreviewClasses.push('hover-effect-preview');
            if (shadowType !== 'none') buttonPreviewClasses.push(`shadow-${shadowType}`);
        }


        let iconHtmlInList = '';
        if (iconType !== 'none' && iconUrl) {
            let imgSrc = '';
            if (iconType === 'image_url_external' || iconType === 'image_uploaded') {
                imgSrc = iconUrl; // URL direta
            } else if (iconType === 'library_icon') {
                imgSrc = `${STATIC_ICONS_PATH}${iconUrl}`; // Constrói URL para ícone da lib
            }
            if (imgSrc) {
                iconHtmlInList = `<img src="${imgSrc}" alt="Ícone" class="button-embedded-icon ${iconRounded ? 'rounded' : ''}">`;
            }
        }

        const finalButtonBgWithOpacity = hexToRgba(color, opacity);

        buttonField.innerHTML = `
            <i class="fas fa-grip-vertical drag-handle" title="Arrastar para reordenar"></i>
            <div style="flex-grow: 1;">
                <div class="${buttonPreviewClasses.join(' ')}"
                    style="background-color: ${finalButtonBgWithOpacity}; border-radius: ${radius}px; padding: 8px; margin-bottom: 8px; color: ${textColor}; font-weight: ${bold ? 'bold' : 'normal'}; font-style: ${italic ? 'italic' : 'normal'}; font-size: ${fontSize}px; ${borderStyleCSS}">
                    ${iconHtmlInList}
                    <span class="button-text-content">${text}</span>
                </div>
                <input type="hidden" name="custom_button_text[]" value="${text}">
                <input type="hidden" name="custom_button_link[]" value="${link}">
                <input type="hidden" name="custom_button_color[]" value="${color}">
                <input type="hidden" name="custom_button_radius[]" value="${radius}">
                <input type="hidden" name="custom_button_text_color[]" value="${textColor}">
                <input type="hidden" name="custom_button_text_bold[]" value="${bold}">
                <input type="hidden" name="custom_button_text_italic[]" value="${italic}">
                <input type="hidden" name="custom_button_font_size[]" value="${fontSize}">
                <input type="hidden" name="custom_button_has_border[]" value="${hasBorder}">
                <input type="hidden" name="custom_button_border_color[]" value="${borderColor}">
                <input type="hidden" name="custom_button_border_width[]" value="${borderWidth}">
                <input type="hidden" name="custom_button_has_hover[]" value="${hasHoverEffect}">
                <input type="hidden" name="custom_button_shadow_type[]" value="${shadowType}">
                <input type="hidden" name="custom_button_opacity[]" value="${opacity}">
                <input type="hidden" name="custom_button_icon_url[]" value="${iconUrl}">
                <input type="hidden" name="custom_button_icon_type[]" value="${iconType}">
                <input type="hidden" name="custom_button_icon_rounded[]" value="${iconRounded}">
                <input type="hidden" name="custom_button_style[]" value="${buttonStyle}">
            </div>
            <button type="button" class="edit-item-btn" title="Editar este botão"><i class="fas fa-edit"></i></button>
            <span class="remove-item" title="Remover este botão"><i class="fas fa-times"></i></span>
        `;

        // Inserir o novo/editado item na posição correta ou no final
        if (index > -1 && customButtonsContainer.childNodes[index]) {
            customButtonsContainer.insertBefore(buttonField, customButtonsContainer.childNodes[index]);
        } else {
            customButtonsContainer.appendChild(buttonField);
        }

        // Adicionar listeners para os botões de editar/remover do novo item
        buttonField.querySelector('.remove-item').addEventListener('click', function () {
            this.closest('.custom-button-item').remove();
        });
        buttonField.querySelector('.edit-item-btn').addEventListener('click', function () {
            const currentItem = this.closest('.custom-button-item');
            const parent = currentItem.parentNode;
            const itemIndex = Array.prototype.indexOf.call(parent.children, currentItem);

            // Recriar o objeto de dados para edição a partir dos inputs hidden
            const dataToEdit = {
                text: currentItem.querySelector('input[name="custom_button_text[]"]').value,
                link: currentItem.querySelector('input[name="custom_button_link[]"]').value,
                buttonStyle: currentItem.querySelector('input[name="custom_button_style[]"]').value,
                iconType: currentItem.querySelector('input[name="custom_button_icon_type[]"]').value,
                iconUrl: currentItem.querySelector('input[name="custom_button_icon_url[]"]').value,
                iconRounded: currentItem.querySelector('input[name="custom_button_icon_rounded[]"]').value === 'true',
                color: currentItem.querySelector('input[name="custom_button_color[]"]').value,
                opacity: parseFloat(currentItem.querySelector('input[name="custom_button_opacity[]"]').value),
                radius: parseInt(currentItem.querySelector('input[name="custom_button_radius[]"]').value),
                textColor: currentItem.querySelector('input[name="custom_button_text_color[]"]').value,
                bold: currentItem.querySelector('input[name="custom_button_text_bold[]"]').value === 'true',
                italic: currentItem.querySelector('input[name="custom_button_text_italic[]"]').value === 'true',
                fontSize: parseInt(currentItem.querySelector('input[name="custom_button_font_size[]"]').value),
                hasBorder: currentItem.querySelector('input[name="custom_button_has_border[]"]').value === 'true',
                borderColor: currentItem.querySelector('input[name="custom_button_border_color[]"]').value,
                borderWidth: parseInt(currentItem.querySelector('input[name="custom_button_border_width[]"]').value),
                hasHoverEffect: currentItem.querySelector('input[name="custom_button_has_hover[]"]').value === 'true',
                shadowType: currentItem.querySelector('input[name="custom_button_shadow_type[]"]').value
            };
            openButtonModal(dataToEdit, itemIndex);
        });
    }


    if (iconModalCloseBtn) iconModalCloseBtn.addEventListener('click', closeModals);
    if (buttonModalCloseBtn) buttonModalCloseBtn.addEventListener('click', closeModals);
    window.addEventListener('click', function (event) {
        if (event.target === iconModal || event.target === buttonModal) {
            closeModals();
        }
    });
    window.addEventListener('keydown', function (event) {
        if (event.key === 'Escape') {
            if (iconModal && iconModal.classList.contains('active')) {
                // Se o modal de ícones estiver sobre o modal de botões, fecha só ele
                if (iconModal.classList.contains('modal-on-top')) {
                     iconModal.classList.remove('active', 'show', 'modal-on-top');
                     currentIconModalPurpose = '';
                     const selectedIconInGrid = iconModal.querySelector('.icon-option.selected');
                     if (selectedIconInGrid) selectedIconInGrid.classList.remove('selected');
                     // Não remove modal-open do body, pois o buttonModal ainda pode estar ativo
                } else {
                    closeModals(); // Fecha todos se for o único modal ativo
                }
            } else if (buttonModal && buttonModal.classList.contains('active')) {
                closeModals();
            }
        }
    });


    // Adicionar listeners para botões de remover e editar JÁ EXISTENTES na página
    document.querySelectorAll('.social-item .remove-item, .custom-button-item .remove-item, .card-link-item .remove-item').forEach(item => {
        item.addEventListener('click', function () {
            this.closest('.social-item, .custom-button-item, .card-link-item').remove();
        });
    });

    document.querySelectorAll('#custom-buttons-container .custom-button-item').forEach((buttonItemHtml) => {
        const editBtn = buttonItemHtml.querySelector('.edit-item-btn');
        if (editBtn) { // Verifica se o botão de editar já existe
            editBtn.addEventListener('click', function () {
                const currentItem = this.closest('.custom-button-item');
                const parent = currentItem.parentNode;
                const itemIndex = Array.prototype.indexOf.call(parent.children, currentItem);
                const dataToEdit = { /* ... (lógica para extrair dados dos inputs hidden, igual a renderCustomButton) ... */
                    text: currentItem.querySelector('input[name="custom_button_text[]"]').value,
                    link: currentItem.querySelector('input[name="custom_button_link[]"]').value,
                    buttonStyle: currentItem.querySelector('input[name="custom_button_style[]"]').value,
                    iconType: currentItem.querySelector('input[name="custom_button_icon_type[]"]').value,
                    iconUrl: currentItem.querySelector('input[name="custom_button_icon_url[]"]').value,
                    iconRounded: currentItem.querySelector('input[name="custom_button_icon_rounded[]"]').value === 'true',
                    color: currentItem.querySelector('input[name="custom_button_color[]"]').value,
                    opacity: parseFloat(currentItem.querySelector('input[name="custom_button_opacity[]"]').value),
                    radius: parseInt(currentItem.querySelector('input[name="custom_button_radius[]"]').value),
                    textColor: currentItem.querySelector('input[name="custom_button_text_color[]"]').value,
                    bold: currentItem.querySelector('input[name="custom_button_text_bold[]"]').value === 'true',
                    italic: currentItem.querySelector('input[name="custom_button_text_italic[]"]').value === 'true',
                    fontSize: parseInt(currentItem.querySelector('input[name="custom_button_font_size[]"]').value),
                    hasBorder: currentItem.querySelector('input[name="custom_button_has_border[]"]').value === 'true',
                    borderColor: currentItem.querySelector('input[name="custom_button_border_color[]"]').value,
                    borderWidth: parseInt(currentItem.querySelector('input[name="custom_button_border_width[]"]').value),
                    hasHoverEffect: currentItem.querySelector('input[name="custom_button_has_hover[]"]').value === 'true',
                    shadowType: currentItem.querySelector('input[name="custom_button_shadow_type[]"]').value
                };
                openButtonModal(dataToEdit, itemIndex);
            });
        }
    });


    // Lógica para o tipo de fundo do CARTÃO (já existente)
    const cardBgTypeRadios = document.querySelectorAll('input[name="card_background_type"]');
    const cardBgColorPicker = document.getElementById('card_background_color_picker');
    const cardBgImageUploadSection = document.getElementById('card_background_image_upload_section');

    function updateCardBackgroundVisibility() {
        if (!cardBgColorPicker || !cardBgImageUploadSection) return;
        const selectedTypeRadio = document.querySelector('input[name="card_background_type"]:checked');
        if (!selectedTypeRadio) return;

        const selectedType = selectedTypeRadio.value;
        // A visibilidade do color picker em si (o input type color) é controlada pelo display do seu label pai
        // que é ajustado aqui.
        const colorPickerLabel = cardBgColorPicker.closest('label');

        if (selectedType === 'color') {
            if (colorPickerLabel) colorPickerLabel.style.display = 'flex'; // Ou 'inline-flex' dependendo do seu layout
            cardBgColorPicker.style.display = 'inline-block'; // Garante que o input color esteja visível
            cardBgImageUploadSection.style.display = 'none';
        } else if (selectedType === 'image') {
            if (colorPickerLabel) colorPickerLabel.style.display = 'flex'; // Mantém o label do radio visível
            cardBgColorPicker.style.display = 'none'; // Esconde o input color
            cardBgImageUploadSection.style.display = 'block';
        }
    }
    if (cardBgTypeRadios.length > 0) {
        cardBgTypeRadios.forEach(radio => radio.addEventListener('change', updateCardBackgroundVisibility));
        updateCardBackgroundVisibility(); // Estado inicial
    }


    // Aplicar opacidade aos previews de botões existentes ao carregar a página
    document.querySelectorAll('#custom-buttons-container .custom-button-item').forEach(buttonItem => {
        const previewDiv = buttonItem.querySelector('.button-preview');
        // Os valores de cor e opacidade agora vêm das variáveis CSS --btn-bg-color e --btn-opacity
        // definidas no style do elemento .button-preview.
        // A função hexToRgba é usada para aplicar a opacidade.
        const bgColorFromVar = previewDiv.style.getPropertyValue('--btn-bg-color').trim();
        const opacityFromVar = parseFloat(previewDiv.style.getPropertyValue('--btn-opacity').trim());

        if (previewDiv && bgColorFromVar && !isNaN(opacityFromVar)) {
            previewDiv.style.backgroundColor = hexToRgba(bgColorFromVar, opacityFromVar);
        } else if (previewDiv && bgColorFromVar) { // Se opacidade não definida, usa a cor como está (fallback)
            previewDiv.style.backgroundColor = bgColorFromVar;
        }
    });

    // --- NOVA LÓGICA PARA BACKGROUND DA PÁGINA PRINCIPAL ---
    const backgroundTypeRadiosPage = document.querySelectorAll('input[name="background_type_page"]');
    const backgroundPageImageOptions = document.getElementById('background_page_image_options');
    const backgroundPageColorOptions = document.getElementById('background_page_color_options');

    const backgroundPreviewPage = document.getElementById('background_preview_page');
    const backgroundPreviewPageOverlay = document.getElementById('background_preview_page_overlay');
    const darkenEnabledCheckboxPage = document.getElementById('background_image_darken_enabled_page');
    const darkenControlsPage = document.getElementById('background_image_darken_controls_page');
    const darkenSliderPage = document.getElementById('background_image_darken_level_page');
    const darkenValueSpanPage = document.getElementById('darken_level_value_page');

    const colorPickerPage = document.getElementById('background_color_value_page');
    const colorHexSpanPage = document.getElementById('background_color_hex_page');

    function updatePageBackgroundControlsVisibility() {
        const selectedType = document.querySelector('input[name="background_type_page"]:checked');
        if (selectedType && backgroundPageImageOptions && backgroundPageColorOptions) {
            if (selectedType.value === 'image') {
                backgroundPageImageOptions.style.display = 'block';
                backgroundPageColorOptions.style.display = 'none';
            } else if (selectedType.value === 'color') {
                backgroundPageImageOptions.style.display = 'none';
                backgroundPageColorOptions.style.display = 'block';
            }
        }
    }

    if (backgroundTypeRadiosPage.length > 0) {
        backgroundTypeRadiosPage.forEach(radio => {
            radio.addEventListener('change', updatePageBackgroundControlsVisibility);
        });
        updatePageBackgroundControlsVisibility(); // Estado inicial
    }

    window.updatePageBackgroundDarkenPreview = function() { // Tornando global para ser chamada por previewImage
        if (!backgroundPreviewPageOverlay || !darkenEnabledCheckboxPage || !darkenSliderPage || !darkenValueSpanPage) return;

        if (darkenEnabledCheckboxPage.checked) {
            const level = parseFloat(darkenSliderPage.value);
            backgroundPreviewPageOverlay.style.backgroundColor = `rgba(0, 0, 0, ${level})`;
            backgroundPreviewPageOverlay.style.display = 'block';
            darkenValueSpanPage.textContent = level.toFixed(2);
        } else {
            backgroundPreviewPageOverlay.style.display = 'none';
            darkenValueSpanPage.textContent = (0.0).toFixed(2);
        }
    }

    if (darkenEnabledCheckboxPage) {
        darkenEnabledCheckboxPage.addEventListener('change', function () {
            if (darkenControlsPage) {
                darkenControlsPage.style.display = this.checked ? 'block' : 'none';
            }
            if (!this.checked && darkenSliderPage) {
                darkenSliderPage.value = 0; // Reseta o slider se desmarcado
            }
            updatePageBackgroundDarkenPreview();
        });
        // Estado inicial do controle do slider
        if (darkenControlsPage) {
             darkenControlsPage.style.display = darkenEnabledCheckboxPage.checked ? 'block' : 'none';
        }
    }

    if (darkenSliderPage) {
        darkenSliderPage.addEventListener('input', updatePageBackgroundDarkenPreview);
        // Estado inicial do span do valor
        if (darkenValueSpanPage) darkenValueSpanPage.textContent = parseFloat(darkenSliderPage.value).toFixed(2);
    }
    
    // Chamada inicial para a prévia do escurecimento se uma imagem já estiver carregada
    if (backgroundPreviewPage && backgroundPreviewPage.src && backgroundPreviewPage.src !== window.location.href && !backgroundPreviewPage.src.includes('blob:')) {
        updatePageBackgroundDarkenPreview();
    }


    if (colorPickerPage && colorHexSpanPage) {
        colorPickerPage.addEventListener('input', function() {
            colorHexSpanPage.textContent = this.value.toUpperCase();
        });
        if (colorPickerPage.value) { // Estado inicial
            colorHexSpanPage.textContent = colorPickerPage.value.toUpperCase();
        }
    }
    // --- FIM DA NOVA LÓGICA PARA BACKGROUND DA PÁGINA PRINCIPAL ---

}); // Fim do DOMContentLoaded