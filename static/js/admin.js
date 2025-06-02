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
            previewEl.style.backgroundColor = '#444';
            previewEl.style.color = color || '#FFFFFF';
        } else {
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
        return;
    }

    const text = atTextInput.value.trim() || '@texto';
    const font = fontSelect.value || DEFAULT_FONT_JS;
    const color = colorInput.value || DEFAULT_TEXT_COLOR_CARD_JS;

    previewDiv.textContent = text;
    previewDiv.style.fontFamily = font;
    previewDiv.style.color = color;
    previewDiv.style.backgroundColor = '#555';
    previewDiv.style.borderColor = color;
}


function previewImage(input, previewId, fileInfoId) {
    const previewContainer = document.getElementById(previewId + '_container');
    const previewImageEl = document.getElementById(previewId);
    const fileInfoEl = document.getElementById(fileInfoId);
    const fileWrapper = input.closest('.file-upload-wrapper');
    const removeCardBgImageBtn = document.getElementById('remove_card_background_image_btn');

    if (input.files && input.files[0]) {
        const reader = new FileReader();
        reader.onload = function (e) {
            if (previewImageEl) {
                previewImageEl.src = e.target.result;
                previewImageEl.style.display = 'block';
            }
            if (previewContainer) {
                previewContainer.style.display = 'block';
                previewContainer.classList.add('preview-active');
            }
            if (fileInfoEl) fileInfoEl.textContent = input.files[0].name;
            if (fileWrapper) fileWrapper.classList.add('has-file');

            if (previewId === 'card_background_image_preview' && removeCardBgImageBtn) {
                removeCardBgImageBtn.style.display = 'inline-flex';
                const hiddenRemoveInput = document.getElementById('remove_card_background_image');
                if (hiddenRemoveInput) hiddenRemoveInput.value = 'false';
            }
        };
        reader.readAsDataURL(input.files[0]);
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

    const fotosParaPreview = [
        { id: 'foto_preview', infoId: 'foto_info', uploadId: 'foto_upload' },
        { id: 'background_preview', infoId: 'background_info', uploadId: 'background_upload' },
        { id: 'card_background_image_preview', infoId: 'card_background_info', uploadId: 'card_background_upload' }
    ];

    fotosParaPreview.forEach(item => {
        const previewElement = document.getElementById(item.id);
        const infoElement = document.getElementById(item.infoId);
        const containerElement = document.getElementById(item.id + '_container');
        const uploadInput = document.getElementById(item.uploadId);
        const fileWrapper = uploadInput ? uploadInput.closest('.file-upload-wrapper') : null;

        if (previewElement && previewElement.src && previewElement.src !== window.location.href && !previewElement.src.includes('blob:') && previewElement.src.trim() !== '') {
            if (containerElement) {
                containerElement.style.display = 'block';
                containerElement.classList.add('preview-active');
            }
            if (infoElement) {
                try {
                    const urlParts = previewElement.src.split('/');
                    const fileNameWithQuery = urlParts[urlParts.length - 1];
                    const fileName = fileNameWithQuery.split('?')[0];
                    infoElement.textContent = `Atual: ${decodeURIComponent(fileName)}`;
                } catch (e) {
                    infoElement.textContent = 'Imagem atual carregada';
                }
            }
            if (fileWrapper) fileWrapper.classList.add('has-file');
            if (item.id === 'card_background_image_preview') {
                const removeBtn = document.getElementById('remove_card_background_image_btn');
                if (removeBtn) removeBtn.style.display = 'inline-flex';
            }
        } else {
            if (infoElement) infoElement.textContent = 'Nenhum arquivo selecionado';
            if (containerElement) containerElement.style.display = 'none';
            if (item.id === 'card_background_image_preview') {
                const removeBtn = document.getElementById('remove_card_background_image_btn');
                if (removeBtn) removeBtn.style.display = 'none';
            }
        }
    });

    const removeCardBgBtn = document.getElementById('remove_card_background_image_btn');
    const cardBgUploadInput = document.getElementById('card_background_upload');
    const cardBgImagePreview = document.getElementById('card_background_image_preview');
    const cardBgImagePreviewContainer = document.getElementById('card_background_image_preview_container');
    const removeCardBgHiddenInput = document.getElementById('remove_card_background_image');
    const cardBgInfo = document.getElementById('card_background_info');

    if (removeCardBgBtn) {
        removeCardBgBtn.addEventListener('click', () => {
            if (cardBgUploadInput) cardBgUploadInput.value = '';
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

            if (removeCardBgHiddenInput) removeCardBgHiddenInput.value = 'true';
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
    let currentIconModalPurpose = ''; 
    let selectedIconNameForButtonModal = ''; 

    const allSocialIcons = [
        { name: '500px', path: '500px.png' }, { name: 'behance', path: 'behance.png' },
        { name: 'blogger', path: 'blogger.png' }, { name: 'codepen', path: 'codepen.png' },
        { name: 'discord', path: 'discord.png' }, { name: 'dribbble', path: 'dribbble.png' },
        { name: 'email', path: 'email.png' }, { name: 'email-preto', path: 'email-preto.png' },
        { name: 'facebook', path: 'facebook.png' }, { name: 'figma', path: 'figma.png' },
        { name: 'github', path: 'github.png' }, { name: 'github-redondo', path: 'github-redondo.png' },
        { name: 'gitlab', path: 'gitlab.png' }, { name: 'gmail', path: 'gmail.png' },
        { name: 'gmail-redondo', path: 'gmail-redondo.png' }, { name: 'google-play', path: 'google-play.png' },
        { name: 'instagram', path: 'instagram.png' }, { name: 'instagram-redondo', path: 'instagram-redondo.png' },
        { name: 'linkedin', path: 'linkedin.png' }, { name: 'linkedin-redondo', path: 'linkedin-redondo.png' },
        { name: 'linkedin-p', path: 'linkedin-p.png' }, { name: 'medium', path: 'medium.png' },
        { name: 'messenger', path: 'messenger.png' }, { name: 'paypal', path: 'paypal.png' },
        { name: 'pinterest', path: 'pinterest.png' }, { name: 'presente', path: 'presente.png' },
        { name: 'presente-p', path: 'presente-p.png' }, { name: 'quora', path: 'quora.png' },
        { name: 'reddit', path: 'reddit.png' }, { name: 'skype', path: 'skype.png' },
        { name: 'snapchat', path: 'snapchat.png' }, { name: 'soundcloud', path: 'soundcloud.png' },
        { name: 'spotify', path: 'spotify.png' }, { name: 'stackoverflow', path: 'stackoverflow.png' },
        { name: 'telegram', path: 'telegram.png' }, { name: 'tiktok', path: 'tiktok.png' },
        { name: 'tumblr', path: 'tumblr.png' }, { name: 'twitch', path: 'twitch.png' },
        { name: 'twitter', path: 'twitter.png' }, { name: 'twitter-x', path: 'twitter-x.png' },
        { name: 'vimeo', path: 'vimeo.png' }, { name: 'whatsapp', path: 'whatsapp.png' },
        { name: 'whatsapp-preto', path: 'whatsapp-preto.png' }, { name: 'whatsapp-v-p', path: 'whatsapp-v-p.png' },
        { name: 'wordpress', path: 'wordpress.png' }, { name: 'youtube', path: 'youtube.png' },
        { name: 'zoom', path: 'zoom.png' }
    ].sort((a, b) => a.name.localeCompare(b.name)); 

    let filteredIcons = [...allSocialIcons];
    let currentPage = 1;
    const iconsPerPage = 9;

    function renderIcons() {
        if (!iconsGrid || !currentPageSpan) return;
        iconsGrid.innerHTML = '';
        const start = (currentPage - 1) * iconsPerPage;
        const end = start + iconsPerPage;
        const paginatedIcons = filteredIcons.slice(start, end);

        paginatedIcons.forEach(icon => {
            const iconDiv = document.createElement('div');
            iconDiv.className = 'icon-option';
            iconDiv.dataset.iconName = icon.name; 
            iconDiv.innerHTML = `
                <img src="${STATIC_ICONS_PATH}${icon.path}" alt="${icon.name.replace(/-/g, ' ')}">
                <p>${icon.name.replace(/-/g, ' ')}</p>
            `;
            iconDiv.addEventListener('click', function () {
                document.querySelectorAll('.icon-option.selected').forEach(sel => sel.classList.remove('selected'));
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
        selectedIconNameForButtonModal = '';
    }

    if (iconSearchInput) iconSearchInput.addEventListener('input', filterAndRenderIcons);
    if (prevIconPageBtn) prevIconPageBtn.addEventListener('click', () => { if (currentPage > 1) { currentPage--; renderIcons(); } });
    if (nextIconPageBtn) nextIconPageBtn.addEventListener('click', () => { const totalPages = Math.ceil(filteredIcons.length / iconsPerPage); if (currentPage < totalPages) { currentPage++; renderIcons(); } });

    function openIconModal(purpose) {
        currentIconModalPurpose = purpose;
        if (iconSearchInput) iconSearchInput.value = '';
        filterAndRenderIcons(); 
        if (iconModal) {
            if (purpose === 'button_icon_selector') {
                iconModal.classList.add('modal-on-top');
            }
            iconModal.classList.add('show');
            document.body.classList.add('modal-open');
            setTimeout(() => iconModal.classList.add('active'), 50);
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
            const selectedIconDiv = iconModal.querySelector('.icon-option.selected');
            if (!selectedIconDiv) {
                alert('Por favor, selecione um ícone.');
                return;
            }
            const iconNameFromDataset = selectedIconDiv.dataset.iconName; // Ex: 'instagram' (nome amigável/chave)

            let iconFileName = ''; // Irá armazenar o nome do arquivo, ex: 'instagram.png'
            const iconData = allSocialIcons.find(iconObj => iconObj.name === iconNameFromDataset);
            if (iconData && iconData.path) {
                iconFileName = iconData.path;
            } else {
                console.warn(`Dados do ícone não encontrados para: ${iconNameFromDataset}. Usando fallback para nome do arquivo.`);
                iconFileName = `${iconNameFromDataset}.png`; // Fallback, caso o ícone não esteja no array allSocialIcons (improvável)
            }

            if (currentIconModalPurpose === 'social') {
                const socialItem = document.createElement('div');
                socialItem.className = 'social-item';
                socialItem.innerHTML = `
                    <i class="fas fa-grip-vertical drag-handle" title="Arrastar para reordenar"></i>
                    <img src="${STATIC_ICONS_PATH}${iconFileName}" alt="${iconNameFromDataset}" width="24" height="24">
                    <input type="hidden" name="social_icon_name[]" value="${iconFileName}"> {/* Salva o NOME DO ARQUIVO */}
                    <input type="text" name="social_icon_url[]" placeholder="Insira o link para ${iconNameFromDataset.replace(/-/g, ' ')}" class="form-input" required>
                    <span class="remove-item" title="Remover este ícone"><i class="fas fa-times"></i></span>
                `;
                socialIconsContainer.appendChild(socialItem);
                socialItem.querySelector('.remove-item').addEventListener('click', function () { this.closest('.social-item').remove(); });
                closeModals(); 
            } else if (currentIconModalPurpose === 'card_link') {
                const cardLinkItem = document.createElement('div');
                cardLinkItem.className = 'card-link-item';
                cardLinkItem.innerHTML = `
                    <i class="fas fa-grip-vertical drag-handle" title="Arrastar para reordenar"></i>
                    <img src="${STATIC_ICONS_PATH}${iconFileName}" alt="${iconNameFromDataset}" width="24" height="24">
                    <input type="hidden" name="card_icon_name[]" value="${iconFileName}"> {/* Salva o NOME DO ARQUIVO */}
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
                cardLinksContainer.appendChild(cardLinkItem);
                updateCardLinkItemPreview(cardLinkItem);
                cardLinkItem.querySelector('.remove-item').addEventListener('click', function () { this.closest('.card-link-item').remove(); });
                
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
                selectedIconNameForButtonModal = iconFileName; // Salva o NOME DO ARQUIVO (ex: 'instagram.png')
                
                const buttonModalActualIconType = document.getElementById('button-modal-actual-icon-type');
                const buttonModalActualIconValue = document.getElementById('button-modal-actual-icon-value');
                const libraryIconNamePreview = document.getElementById('button-library-icon-name-preview');

                if (buttonModalActualIconType) buttonModalActualIconType.value = 'library_icon';
                if (buttonModalActualIconValue) buttonModalActualIconValue.value = selectedIconNameForButtonModal; // Salva o NOME DO ARQUIVO
                if (libraryIconNamePreview) libraryIconNamePreview.textContent = `Ícone selecionado: ${iconNameFromDataset.replace(/-/g, ' ')}`; // Exibe o nome amigável

                updateButtonPreview(); 
                
                // MODIFICAÇÃO: Fechar APENAS o iconModal
                if (iconModal) {
                    iconModal.classList.remove('active', 'show', 'modal-on-top');
                }
                // Manter a classe 'modal-open' no body se o buttonModal ainda estiver visível.
                // A função closeModals() cuidaria de remover 'modal-open' do body,
                // mas como não a chamamos aqui, o body continua com overflow:hidden,
                // o que é bom enquanto o buttonModal estiver aberto.
                currentIconModalPurpose = ''; // Resetar o propósito para o próximo uso
            } else {
                closeModals(); 
            }
        });
    }

    document.querySelectorAll('#card-links-container .card-link-item').forEach(item => {
        updateCardLinkItemPreview(item);
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

    const buttonModalActualIconType = document.getElementById('button-modal-actual-icon-type');
    const buttonModalActualIconValue = document.getElementById('button-modal-actual-icon-value');


    function manageButtonIconFieldsVisibility() {
        const selectedType = buttonIconTypeSelect.value;

        buttonIconUrlExternalGroup.style.display = selectedType === 'image_url_external' ? 'block' : 'none';
        buttonNewImageFileGroup.style.display = selectedType === 'image_upload_new' ? 'block' : 'none';
        buttonSelectLibraryIconGroup.style.display = selectedType === 'library_icon' ? 'block' : 'none';
        buttonIconRoundedGroup.style.display = (selectedType === 'image_url_external' || selectedType === 'image_upload_new') ? 'flex' : 'none';

        if (selectedType !== 'image_url_external') buttonIconUrlExternalInput.value = '';
        if (selectedType !== 'image_upload_new') {
            buttonNewImageFileInput.value = ''; 
            if (buttonNewImageFileInfo) buttonNewImageFileInfo.textContent = 'Nenhum arquivo selecionado';
        }
        if (selectedType !== 'library_icon') {
            if (libraryIconNamePreview) libraryIconNamePreview.textContent = '';
            selectedIconNameForButtonModal = ''; 
        }
        if (selectedType === 'none') {
            if (buttonModalActualIconType) buttonModalActualIconType.value = 'none';
            if (buttonModalActualIconValue) buttonModalActualIconValue.value = '';
        }
        
        if (selectedType !== 'image_url_external' && selectedType !== 'image_upload_new') {
            buttonIconRoundedCheckbox.checked = false;
        }
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
        formData.append('button_image', file);

        if (liveButtonIconPreview) liveButtonIconPreview.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';


        try {
            const response = await fetch(UPLOAD_BUTTON_IMAGE_URL, {
                method: 'POST',
                body: formData,
            });
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ error: 'Erro desconhecido no upload.' }));
                throw new Error(errorData.error || `Erro ${response.status}`);
            }
            const data = await response.json();
            if (data.url) {
                return data.url;
            } else {
                throw new Error(data.error || 'URL da imagem não retornada.');
            }
        } catch (error) {
            console.error('Erro no upload da imagem do botão:', error);
            alert(`Erro ao enviar imagem: ${error.message}`);
            if (liveButtonIconPreview) liveButtonIconPreview.innerHTML = ''; 
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
                    if (buttonModalActualIconType) buttonModalActualIconType.value = 'image_uploaded'; 
                    if (buttonModalActualIconValue) buttonModalActualIconValue.value = uploadedUrl;
                    updateButtonPreview();
                } else {
                    this.value = '';
                    if (buttonNewImageFileInfo) buttonNewImageFileInfo.textContent = 'Falha no envio. Nenhum arquivo selecionado.';
                    if (buttonModalActualIconType) buttonModalActualIconType.value = 'none'; 
                    if (buttonModalActualIconValue) buttonModalActualIconValue.value = '';
                    updateButtonPreview();
                }
            } else {
                if (buttonNewImageFileInfo) buttonNewImageFileInfo.textContent = 'Nenhum arquivo selecionado';
                if (buttonModalActualIconType && buttonModalActualIconType.value === 'image_uploaded') { 
                    buttonModalActualIconType.value = 'none';
                    buttonModalActualIconValue.value = '';
                }
                updateButtonPreview();
            }
        });
    }
    if (buttonIconUrlExternalInput) {
        buttonIconUrlExternalInput.addEventListener('input', function () {
            if (buttonIconTypeSelect.value === 'image_url_external') {
                if (buttonModalActualIconType) buttonModalActualIconType.value = 'image_url_external';
                if (buttonModalActualIconValue) buttonModalActualIconValue.value = this.value;
                updateButtonPreview();
            }
        });
    }


    function updateButtonPreview() {
        if (!liveButtonPreview || !liveButtonTextPreview || !liveButtonIconPreview || !buttonTextInput || !buttonColorInput || !buttonRadiusInput || !radiusValueSpan || !buttonTextColorInput || !buttonTextBoldCheckbox || !buttonTextItalicCheckbox || !buttonFontSizeInput || !buttonHasBorderCheckbox || !buttonBorderColorInput || !buttonBorderWidthInput || !buttonHasHoverCheckbox || !buttonShadowTypeSelect || !buttonOpacitySlider || !opacityValueSpan || !buttonIconTypeSelect || !buttonIconUrlExternalInput || !buttonStyleSelect || !buttonIconRoundedCheckbox || !borderOptionsGroup || !buttonModalActualIconType || !buttonModalActualIconValue) {
            return;
        }

        liveButtonTextPreview.textContent = buttonTextInput.value.trim() || 'Texto do Botão';

        const bgColor = buttonColorInput.value;
        const bgOpacity = parseFloat(buttonOpacitySlider.value);
        opacityValueSpan.textContent = bgOpacity.toFixed(2);
        liveButtonPreview.style.backgroundColor = hexToRgba(bgColor, bgOpacity);

        liveButtonPreview.style.borderRadius = `${buttonRadiusInput.value}px`;
        if (radiusValueSpan) radiusValueSpan.textContent = `${buttonRadiusInput.value}px`;

        liveButtonPreview.style.color = buttonTextColorInput.value;
        liveButtonPreview.style.fontWeight = buttonTextBoldCheckbox.checked ? 'bold' : 'normal';
        liveButtonPreview.style.fontStyle = buttonTextItalicCheckbox.checked ? 'italic' : 'normal';
        liveButtonPreview.style.fontSize = `${buttonFontSizeInput.value}px`;

        if (buttonHasBorderCheckbox.checked) {
            liveButtonPreview.style.border = `${buttonBorderWidthInput.value}px solid ${buttonBorderColorInput.value}`;
        } else {
            liveButtonPreview.style.border = 'none';
        }

        liveButtonPreview.classList.remove('shadow-soft', 'shadow-medium', 'shadow-hard', 'shadow-inset',
            'button-style-default', 'button-style-solid_shadow',
            'hover-effect-preview');

        const selectedButtonStyle = buttonStyleSelect.value;
        liveButtonPreview.classList.add(`button-style-${selectedButtonStyle}`);

        const defaultStyleControls = [
            buttonShadowTypeSelect.closest('.form-group'),
            buttonHasHoverCheckbox.closest('.form-group-inline')
        ];

        if (selectedButtonStyle === 'default') {
            if (buttonShadowTypeSelect.value !== 'none') {
                liveButtonPreview.classList.add(`shadow-${buttonShadowTypeSelect.value}`);
            }
            if (buttonHasHoverCheckbox.checked) {
                liveButtonPreview.classList.add('hover-effect-preview');
            }
            defaultStyleControls.forEach(el => el.style.display = el.tagName === 'DIV' && el.classList.contains('form-group-inline') ? 'flex' : 'block');
        } else {
            defaultStyleControls.forEach(el => el.style.display = 'none');
        }

        const actualIconType = buttonModalActualIconType.value;
        const actualIconValue = buttonModalActualIconValue.value.trim();
        const iconRounded = buttonIconRoundedCheckbox.checked;

        liveButtonIconPreview.innerHTML = ''; 

        if (actualIconType === 'image_url_external' && actualIconValue) {
            const img = document.createElement('img');
            img.src = actualIconValue;
            img.alt = 'Ícone';
            if (iconRounded) img.classList.add('rounded');
            liveButtonIconPreview.appendChild(img);
        } else if (actualIconType === 'image_uploaded' && actualIconValue) {
            const img = document.createElement('img');
            img.src = actualIconValue; 
            img.alt = 'Ícone Enviado';
            if (iconRounded) img.classList.add('rounded');
            liveButtonIconPreview.appendChild(img);
        } else if (actualIconType === 'library_icon' && actualIconValue) {
            const img = document.createElement('img');
            img.src = `${STATIC_ICONS_PATH}${actualIconValue}`; 
            img.alt = actualIconValue.split('.')[0];
            if (iconRounded) img.classList.add('rounded');
            liveButtonIconPreview.appendChild(img);
        }
    }


    if (buttonHasBorderCheckbox) {
        buttonHasBorderCheckbox.addEventListener('change', function () {
            if (borderOptionsGroup) borderOptionsGroup.style.display = this.checked ? 'flex' : 'none';
            updateButtonPreview();
        });
    }

    const elementsForButtonPreviewUpdate = [
        buttonTextInput, buttonColorInput, buttonRadiusInput, buttonTextColorInput,
        buttonTextBoldCheckbox, buttonTextItalicCheckbox, buttonFontSizeInput,
        buttonHasBorderCheckbox, buttonBorderColorInput, buttonBorderWidthInput,
        buttonHasHoverCheckbox, buttonShadowTypeSelect,
        buttonOpacitySlider, buttonIconTypeSelect, buttonIconUrlExternalInput, 
        buttonIconRoundedCheckbox, buttonStyleSelect
    ];

    elementsForButtonPreviewUpdate.forEach(el => {
        if (el) {
            const eventType = (el.type === 'checkbox' || el.tagName === 'SELECT' || el.type === 'range') ? 'change' : 'input';
            el.addEventListener(eventType, updateButtonPreview);
        }
    });

    function openButtonModal(data = null, index = -1) {
        currentButtonModalPurpose = data ? 'edit' : 'add';
        editingButtonData = data; 
        document.getElementById('button-modal-editing-index').value = index;


        buttonTextInput.value = data ? data.text : '';
        buttonLinkInput.value = data ? data.link : '';
        buttonStyleSelect.value = data ? data.buttonStyle : DEFAULT_BUTTON_STYLE_JS;

        const currentIconType = data ? data.iconType : DEFAULT_BUTTON_ICON_TYPE_JS;
        const currentIconUrl = data ? data.iconUrl : DEFAULT_BUTTON_ICON_URL_JS; 
        buttonModalActualIconType.value = currentIconType;
        buttonModalActualIconValue.value = currentIconUrl;


        if (currentIconType === 'image_url_external') {
            buttonIconTypeSelect.value = 'image_url_external';
            buttonIconUrlExternalInput.value = currentIconUrl;
        } else if (currentIconType === 'image_uploaded') { 
            buttonIconTypeSelect.value = 'image_upload_new'; 
            if (buttonNewImageFileInfo) buttonNewImageFileInfo.textContent = currentIconUrl.split('/').pop();
        } else if (currentIconType === 'library_icon') {
            buttonIconTypeSelect.value = 'library_icon';
            selectedIconNameForButtonModal = currentIconUrl; 
            if (libraryIconNamePreview) libraryIconNamePreview.textContent = `Ícone atual: ${currentIconUrl.split('.')[0].replace(/-/g, ' ')}`;
        } else { 
            buttonIconTypeSelect.value = 'none';
        }
        
        manageButtonIconFieldsVisibility();

        buttonIconRoundedCheckbox.checked = data ? data.iconRounded : DEFAULT_BUTTON_ICON_ROUNDED_JS;
        buttonColorInput.value = data ? data.color : '#4CAF50';
        buttonOpacitySlider.value = data ? data.opacity : DEFAULT_BUTTON_OPACITY_JS;
        buttonRadiusInput.value = data ? data.radius : '10';
        buttonTextColorInput.value = data ? data.textColor : '#FFFFFF';
        buttonTextBoldCheckbox.checked = data ? data.bold : false;
        buttonTextItalicCheckbox.checked = data ? data.italic : false;
        buttonFontSizeInput.value = data ? data.fontSize : '16';
        buttonHasBorderCheckbox.checked = data ? data.hasBorder : false;
        borderOptionsGroup.style.display = buttonHasBorderCheckbox.checked ? 'flex' : 'none';
        buttonBorderColorInput.value = data ? data.borderColor : '#000000';
        buttonBorderWidthInput.value = data ? data.borderWidth : '2';
        buttonHasHoverCheckbox.checked = data ? data.hasHoverEffect : false;
        buttonShadowTypeSelect.value = data ? data.shadowType : 'none';

        updateButtonPreview();
        if (buttonModal) {
            buttonModal.classList.add('show');
            document.body.classList.add('modal-open');
            setTimeout(() => buttonModal.classList.add('active'), 50);
        }
    }


    if (addButtonBtn) {
        addButtonBtn.addEventListener('click', () => openButtonModal());
    }

    const saveButtonModalBtn = document.getElementById('save-button'); 
    if (saveButtonModalBtn) {
        saveButtonModalBtn.addEventListener('click', function (event) {
            event.preventDefault(); 

            const btnText = buttonTextInput.value.trim();
            const btnLinkValue = buttonLinkInput.value.trim(); 

            if (!btnText) {
                alert('Por favor, preencha o texto do botão!');
                if (buttonTextInput) { 
                    buttonTextInput.focus();
                }
                return; 
            }

            if (buttonLinkInput && !buttonLinkInput.checkValidity()) {
                buttonLinkInput.reportValidity();
                return; 
            }
            
            const btnLink = btnLinkValue;

            const newButtonData = {
                text: btnText,
                link: btnLink,
                buttonStyle: buttonStyleSelect.value,
                iconType: buttonModalActualIconType.value,
                iconUrl: buttonModalActualIconValue.value,
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
                hasHoverEffect: buttonHasHoverCheckbox.checked,
                shadowType: buttonShadowTypeSelect.value,
            };

            const editingIndex = parseInt(document.getElementById('button-modal-editing-index').value);
            if (editingIndex > -1) { 
                const items = customButtonsContainer.querySelectorAll('.custom-button-item');
                if (items[editingIndex]) {
                    items[editingIndex].remove();
                    renderCustomButton(newButtonData, editingIndex);
                } else {
                    renderCustomButton(newButtonData);
                }
            } else { 
                renderCustomButton(newButtonData);
            }
            closeModals();
        });
    }

    function renderCustomButton(buttonData, index = -1) {
        const customButtonsContainer = document.getElementById('custom-buttons-container');
        if (!customButtonsContainer) return;

        const buttonField = document.createElement('div');
        buttonField.className = 'custom-button-item';

        const text = escapeHtml(buttonData.text || 'Botão');
        const link = escapeHtml(buttonData.link || '#');
        const buttonStyle = escapeHtml(buttonData.buttonStyle || DEFAULT_BUTTON_STYLE_JS);
        const iconType = escapeHtml(buttonData.iconType || DEFAULT_BUTTON_ICON_TYPE_JS);
        const iconUrl = escapeHtml(buttonData.iconUrl || DEFAULT_BUTTON_ICON_URL_JS); 
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
        const hasHoverEffect = buttonData.hasHoverEffect || false; 
        const shadowType = escapeHtml(buttonData.shadowType || 'none'); 


        let borderStyleCSS = '';
        let buttonPreviewClasses = ['button-preview', `button-style-${buttonStyle}`];
        if (hasBorder) {
            borderStyleCSS = `border: ${borderWidth}px solid ${borderColor};`;
            buttonPreviewClasses.push('has-border-preview');
        }
        if (buttonStyle === 'default') {
            if (hasHoverEffect) buttonPreviewClasses.push('hover-effect-preview');
            if (shadowType !== 'none') buttonPreviewClasses.push(`shadow-${shadowType}`);
        }

        let iconHtmlInList = '';
        if (iconType === 'image_url_external' && iconUrl) {
            iconHtmlInList = `<img src="${iconUrl}" alt="Ícone" class="button-embedded-icon ${iconRounded ? 'rounded' : ''}">`;
        } else if (iconType === 'image_uploaded' && iconUrl) { 
            iconHtmlInList = `<img src="${iconUrl}" alt="Ícone Enviado" class="button-embedded-icon ${iconRounded ? 'rounded' : ''}">`;
        } else if (iconType === 'library_icon' && iconUrl) { 
            iconHtmlInList = `<img src="${STATIC_ICONS_PATH}${iconUrl}" alt="${iconUrl.split('.')[0]}" class="button-embedded-icon ${iconRounded ? 'rounded' : ''}">`;
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

        if (index > -1 && customButtonsContainer.childNodes[index]) {
            customButtonsContainer.insertBefore(buttonField, customButtonsContainer.childNodes[index]);
        } else {
            customButtonsContainer.appendChild(buttonField);
        }

        buttonField.querySelector('.remove-item').addEventListener('click', function () {
            this.closest('.custom-button-item').remove();
        });
        buttonField.querySelector('.edit-item-btn').addEventListener('click', function () {
            const currentItem = this.closest('.custom-button-item');
            const parent = currentItem.parentNode;
            const itemIndex = Array.prototype.indexOf.call(parent.children, currentItem);

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

    document.querySelectorAll('.social-item .remove-item, .custom-button-item .remove-item, .card-link-item .remove-item').forEach(item => {
        item.addEventListener('click', function () {
            this.closest('.social-item, .custom-button-item, .card-link-item').remove();
        });
    });

    document.querySelectorAll('#custom-buttons-container .custom-button-item').forEach((buttonItem, itemIndex) => {
        const editBtn = buttonItem.querySelector('.edit-item-btn'); 
        if (!editBtn) { 
            const newEditBtn = document.createElement('button');
            newEditBtn.type = 'button';
            newEditBtn.className = 'edit-item-btn';
            newEditBtn.title = 'Editar este botão';
            newEditBtn.innerHTML = '<i class="fas fa-edit"></i>';
            
            const removeBtnSpan = buttonItem.querySelector('.remove-item');
            if (removeBtnSpan) {
                buttonItem.insertBefore(newEditBtn, removeBtnSpan);
            } else {
                buttonItem.appendChild(newEditBtn); 
            }


            newEditBtn.addEventListener('click', function () {
                const currentItem = this.closest('.custom-button-item');
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
        } else {
            editBtn.addEventListener('click', function () {
                const currentItem = this.closest('.custom-button-item');
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
    });


    const cardBgTypeRadios = document.querySelectorAll('input[name="card_background_type"]');
    const cardBgColorPicker = document.getElementById('card_background_color_picker');
    const cardBgImageUploadSection = document.getElementById('card_background_image_upload_section');

    function updateCardBackgroundVisibility() {
        if (!cardBgColorPicker || !cardBgImageUploadSection) return;
        const selectedTypeRadio = document.querySelector('input[name="card_background_type"]:checked');
        if (!selectedTypeRadio) return;

        const selectedType = selectedTypeRadio.value;
        cardBgColorPicker.style.display = selectedType === 'color' ? 'inline-block' : 'none';
        if (cardBgColorPicker.parentElement.tagName === 'LABEL' && selectedType === 'color') {
            cardBgColorPicker.parentElement.style.display = 'flex';
        } else if (cardBgColorPicker.parentElement.tagName === 'LABEL') {
            cardBgColorPicker.parentElement.style.display = 'flex';
        }
        cardBgImageUploadSection.style.display = selectedType === 'image' ? 'block' : 'none';
    }
    if (cardBgTypeRadios.length > 0) {
        cardBgTypeRadios.forEach(radio => radio.addEventListener('change', updateCardBackgroundVisibility));
        updateCardBackgroundVisibility();
    }
    document.querySelectorAll('#custom-buttons-container .custom-button-item').forEach(buttonItem => {
        const previewDiv = buttonItem.querySelector('.button-preview');
        const bgColor = buttonItem.querySelector('input[name="custom_button_color[]"]').value;
        const opacity = parseFloat(buttonItem.querySelector('input[name="custom_button_opacity[]"]').value);
        if (previewDiv && bgColor && !isNaN(opacity)) {
            previewDiv.style.backgroundColor = hexToRgba(bgColor, opacity);
        }
    });
});