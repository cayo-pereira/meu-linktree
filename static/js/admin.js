// Função para obter valor de um elemento
function getValue(elementId) {
    const el = document.getElementById(elementId);
    return el ? el.value : '';
}

// Função para atualizar preview de texto genérico
function updateTextPreview(previewElementId, text, font, color) {
    const previewEl = document.getElementById(previewElementId);
    if (previewEl) {
        previewEl.textContent = text || 'Prévia...';
        previewEl.style.fontFamily = font || 'Inter, sans-serif';

        // Ajuste para diferenciar previews de página e previews de cartão
        if (previewElementId.includes('card_')) { 
            previewEl.style.backgroundColor = '#444'; 
            previewEl.style.color = color || '#FFFFFF'; 
        } else { 
            previewEl.style.backgroundColor = getComputedStyle(document.documentElement).getPropertyValue('--input-bg-light').trim();
            previewEl.style.color = color || getComputedStyle(document.documentElement).getPropertyValue('--text-color-light').trim();
        }
    }
}

// Função específica para atualizar o preview do texto de um item de link do cartão
function updateCardLinkItemPreview(itemElement) {
    const atTextInput = itemElement.querySelector('.card-link-item-at-text');
    const fontSelect = itemElement.querySelector('.card-link-item-font'); // O select visível
    const colorInput = itemElement.querySelector('.card-link-item-color'); // O input color visível
    const previewDiv = itemElement.querySelector('.card-link-item-preview');

    if (!atTextInput || !fontSelect || !colorInput || !previewDiv) {
        return;
    }

    const text = atTextInput.value.trim() || '@texto';
    const font = fontSelect.value || DEFAULT_FONT_JS; // DEFAULT_FONT_JS vindo do HTML
    const color = colorInput.value || DEFAULT_TEXT_COLOR_CARD_JS; // DEFAULT_TEXT_COLOR_CARD_JS vindo do HTML

    previewDiv.textContent = text;
    previewDiv.style.fontFamily = font;
    previewDiv.style.color = color;
    previewDiv.style.backgroundColor = '#555'; // Fundo escuro para contraste com texto claro
    previewDiv.style.borderColor = color; // Borda com a cor do texto
}


function previewImage(input, previewId, fileInfoId) {
    const previewContainer = document.getElementById(previewId + '_container');
    const previewImageEl = document.getElementById(previewId);
    const fileInfoEl = document.getElementById(fileInfoId);
    const fileWrapper = input.closest('.file-upload-wrapper');
    const removeBtn = document.getElementById('remove_card_background_image_btn');

    if (input.files && input.files[0]) {
        const reader = new FileReader();
        reader.onload = function (e) {
            previewImageEl.src = e.target.result;
            previewImageEl.style.display = 'block';
            if (previewContainer) previewContainer.style.display = 'block';
            if (previewContainer) previewContainer.classList.add('preview-active');
            if (fileInfoEl) fileInfoEl.textContent = input.files[0].name;
            if (fileWrapper) fileWrapper.classList.add('has-file');
            if (previewId === 'card_background_image_preview' && removeBtn) {
                removeBtn.style.display = 'inline-flex';
                document.getElementById('remove_card_background_image').value = 'false';
            }
        };
        reader.readAsDataURL(input.files[0]);
    }
}


document.addEventListener('DOMContentLoaded', function () {
    // Inicializar previews de texto genéricos
    updateTextPreview('nome_preview', getValue('nome'), getValue('nome_font'), getValue('nome_color'));
    updateTextPreview('bio_preview', getValue('bio'), getValue('bio_font'), getValue('bio_color'));
    updateTextPreview('card_nome_preview', getValue('card_nome'), getValue('card_nome_font'), getValue('card_nome_color'));
    updateTextPreview('card_titulo_preview', getValue('card_titulo'), getValue('card_titulo_font'), getValue('card_titulo_color'));
    updateTextPreview('card_registro_preview', getValue('card_registro_profissional'), getValue('card_registro_font'), getValue('card_registro_color'));
    // NOVO: Inicializar preview do endereço do cartão
    updateTextPreview('card_endereco_preview', getValue('card_endereco'), getValue('card_endereco_font'), getValue('card_endereco_color'));


    // Inicializar previews de imagem
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
            if(containerElement) containerElement.style.display = 'block';
            if(containerElement) containerElement.classList.add('preview-active');
            if (infoElement) {
                 try {
                    const urlParts = previewElement.src.split('/');
                    const fileNameWithQuery = urlParts[urlParts.length - 1];
                    const fileName = fileNameWithQuery.split('?')[0];
                    infoElement.textContent = `Atual: ${decodeURIComponent(fileName)}`;
                } catch (e) {
                    infoElement.textContent = 'Imagem atual';
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

    // Lógica para o botão de remover imagem de fundo do cartão
    const removeCardBgBtn = document.getElementById('remove_card_background_image_btn');
    const cardBgUploadInput = document.getElementById('card_background_upload');
    const cardBgImagePreview = document.getElementById('card_background_image_preview');
    const cardBgImagePreviewContainer = document.getElementById('card_background_image_preview_container');
    const removeCardBgHiddenInput = document.getElementById('remove_card_background_image');
    const cardBgInfo = document.getElementById('card_background_info'); 
    
    if (removeCardBgBtn) {
        removeCardBgBtn.addEventListener('click', () => {
            if(cardBgUploadInput) cardBgUploadInput.value = ''; 
            if(cardBgImagePreview) cardBgImagePreview.src = ''; 
            if(cardBgImagePreview) cardBgImagePreview.style.display = 'none'; 
            if(cardBgImagePreviewContainer) cardBgImagePreviewContainer.classList.remove('preview-active');
            if(cardBgImagePreviewContainer) cardBgImagePreviewContainer.style.display = 'none'; 
            if(cardBgInfo) cardBgInfo.textContent = 'Nenhum arquivo selecionado'; 
            const cardBgUploadWrapper = cardBgUploadInput ? cardBgUploadInput.closest('.file-upload-wrapper') : null;
            if(cardBgUploadWrapper) cardBgUploadWrapper.classList.remove('has-file');
            if(removeCardBgHiddenInput) removeCardBgHiddenInput.value = 'true'; 
            removeCardBgBtn.style.display = 'none'; 
        });
    }

    function escapeHtml(text) {
        if (typeof text !== 'string') {
            return '';
        }
        const map = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' };
        return text.replace(/[&<>"']/g, function (m) { return map[m]; });
    }

    function renderCustomButton(buttonData) {
        const customButtonsContainer = document.getElementById('custom-buttons-container');
        const buttonField = document.createElement('div');
        buttonField.className = 'custom-button-item';

        const textColor = buttonData.textColor || '#FFFFFF';
        const bold = buttonData.bold || false;
        const italic = buttonData.italic || false;
        const fontSize = buttonData.fontSize || 16;
        const hasBorder = buttonData.hasBorder || false;
        const borderColor = buttonData.borderColor || '#000000';
        const borderWidth = buttonData.borderWidth || 2;
        const hasHoverEffect = buttonData.hasHoverEffect || false;
        const shadowType = buttonData.shadowType || 'none';
        let borderStyle = '';
        let buttonPreviewClasses = ['button-preview'];
        if (hasBorder) {
            borderStyle = `border: ${borderWidth}px solid ${borderColor};`;
            buttonPreviewClasses.push('has-border-preview');
        }
        if (hasHoverEffect) buttonPreviewClasses.push('hover-effect-preview');
        if (shadowType && shadowType !== 'none') buttonPreviewClasses.push(`shadow-${shadowType}`);

        buttonField.innerHTML = `
            <i class="fas fa-grip-vertical drag-handle"></i> <div style="flex-grow: 1;">
                <div class="${buttonPreviewClasses.join(' ')}" 
                    style="background: ${buttonData.color}; border-radius: ${buttonData.radius}px; padding: 8px; margin-bottom: 8px; color: ${textColor}; font-weight: ${bold ? 'bold' : 'normal'}; font-style: ${italic ? 'italic' : 'normal'}; font-size: ${fontSize}px; ${borderStyle}">
                    ${escapeHtml(buttonData.text)}
                </div>
                <input type="hidden" name="custom_button_text[]" value="${escapeHtml(buttonData.text)}">
                <input type="hidden" name="custom_button_link[]" value="${escapeHtml(buttonData.link)}">
                <input type="hidden" name="custom_button_color[]" value="${escapeHtml(buttonData.color)}">
                <input type="hidden" name="custom_button_radius[]" value="${escapeHtml(String(buttonData.radius))}">
                <input type="hidden" name="custom_button_text_color[]" value="${escapeHtml(textColor)}">
                <input type="hidden" name="custom_button_text_bold[]" value="${bold}">
                <input type="hidden" name="custom_button_text_italic[]" value="${italic}">
                <input type="hidden" name="custom_button_font_size[]" value="${fontSize}">
                <input type="hidden" name="custom_button_has_border[]" value="${hasBorder}">
                <input type="hidden" name="custom_button_border_color[]" value="${escapeHtml(borderColor)}">
                <input type="hidden" name="custom_button_border_width[]" value="${escapeHtml(String(borderWidth))}">
                <input type="hidden" name="custom_button_has_hover[]" value="${hasHoverEffect}">
                <input type="hidden" name="custom_button_shadow_type[]" value="${escapeHtml(shadowType)}">
            </div>
            <span class="remove-item"><i class="fas fa-times"></i></span>
        `;
        if (customButtonsContainer) customButtonsContainer.appendChild(buttonField);
        buttonField.querySelector('.remove-item').addEventListener('click', function () {
            this.closest('.custom-button-item').remove();
        });
    }
    
    const iconModalContent = document.querySelector('#icon-modal .modal-content');
    if (iconModalContent) iconModalContent.addEventListener('click', (e) => e.stopPropagation());
    const buttonModalContent = document.querySelector('#button-modal .modal-content');
    if (buttonModalContent) buttonModalContent.addEventListener('click', (e) => e.stopPropagation());

    const socialIconsContainer = document.getElementById('social-icons-container');
    const customButtonsContainer = document.getElementById('custom-buttons-container');
    const cardLinksContainer = document.getElementById('card-links-container'); 

    if (socialIconsContainer) new Sortable(socialIconsContainer, { animation: 150, ghostClass: 'sortable-ghost', chosenClass: 'sortable-chosen', handle: '.drag-handle', });
    if (customButtonsContainer) new Sortable(customButtonsContainer, { animation: 150, ghostClass: 'sortable-ghost', chosenClass: 'sortable-chosen', handle: '.drag-handle', });
    if (cardLinksContainer) new Sortable(cardLinksContainer, { animation: 150, ghostClass: 'sortable-ghost', chosenClass: 'sortable-chosen', handle: '.drag-handle', }); 
    
    const iconModal = document.getElementById('icon-modal');
    const buttonModal = document.getElementById('button-modal');
    const addIconBtn = document.getElementById('add-icon-btn');
    const addButtonBtn = document.getElementById('add-button-btn');
    const addCardLinkBtn = document.getElementById('add-card-link-btn');
    const iconModalCloseBtn = document.querySelector('.icon-modal-close');
    const buttonModalCloseBtn = document.querySelector('.button-modal-close');
    const iconsGrid = document.querySelector('#icon-modal .icons-grid');
    const iconSearchInput = document.getElementById('icon-search');
    const prevIconPageBtn = document.getElementById('prev-icon-page');
    const nextIconPageBtn = document.getElementById('next-icon-page');
    const currentPageSpan = document.getElementById('current-page');
    let currentModalPurpose = '';

    const allSocialIcons = [ { name: 'instagram', path: '/static/icons/instagram.png' }, { name: 'linkedin', path: '/static/icons/linkedin.png' }, { name: 'github', path: '/static/icons/github.png' }, { name: 'email', path: '/static/icons/email.png' }, { name: 'whatsapp', path: '/static/icons/whatsapp.png' }, { name: 'twitter', path: '/static/icons/twitter.png' }, { name: 'facebook', path: '/static/icons/facebook.png' }, { name: 'youtube', path: '/static/icons/youtube.png' }, { name: 'telegram', path: '/static/icons/telegram.png' }, { name: 'tiktok', path: '/static/icons/tiktok.png' }, { name: 'pinterest', path: '/static/icons/pinterest.png' }, { name: 'twitch', path: '/static/icons/twitch.png' }, { name: 'discord', path: '/static/icons/discord.png' }, { name: 'snapchat', path: '/static/icons/snapchat.png' }, { name: 'reddit', path: '/static/icons/reddit.png' }, { name: 'vimeo', path: '/static/icons/vimeo.png' }, { name: 'medium', path: '/static/icons/medium.png' }, { name: 'spotify', path: '/static/icons/spotify.png' }, { name: 'soundcloud', path: '/static/icons/soundcloud.png' }, { name: 'behance', path: '/static/icons/behance.png' }, { name: 'dribbble', path: '/static/icons/dribbble.png' }, { name: 'flickr', path: '/static/icons/flickr.png' }, { name: 'etsy', path: '/static/icons/etsy.png' }, { name: 'paypal', path: '/static/icons/paypal.png' }, { name: 'google-drive', path: '/static/icons/google-drive.png' }, { name: 'dropbox', path: '/static/icons/dropbox.png' }, { name: 'link', path: '/static/icons/link.png' }, { name: 'phone', path: '/static/icons/phone.png' }, { name: 'website', path: '/static/icons/website.png' }, { name: 'xing', path: '/static/icons/xing.png' }, { name: 'mastodon', path: '/static/icons/mastodon.png' }, { name: 'stack-overflow', path: '/static/icons/stack-overflow.png' }, { name: 'gitlab', path: '/static/icons/gitlab.png' }, { name: 'bitbucket', path: '/static/icons/bitbucket.png' }, { name: 'codepen', path: '/static/icons/codepen.png' }, { name: 'dev-to', path: '/static/icons/dev-to.png' }, { name: 'freecodecamp', path: '/static/icons/freecodecamp.png' }, { name: 'hashnode', path: '/static/icons/hashnode.png' }, { name: 'product-hunt', path: '/static/icons/product-hunt.png' }, { name: 'unsplash', path: '/static/icons/unsplash.png' }, { name: 'patreon', path: '/static/icons/patreon.png' }, { name: 'buymeacoffee', path: '/static/icons/buymeacoffee.png' }, { name: 'ko-fi', path: '/static/icons/ko-fi.png' }, { name: 'slack', path: '/static/icons/slack.png' }, { name: 'teams', path: '/static/icons/teams.png' }, { name: 'skype', path: '/static/icons/skype.png' }, { name: 'google-scholar', path: '/static/icons/google-scholar.png' }, { name: 'researchgate', path: '/static/icons/researchgate.png' }, { name: 'academia-edu', path: '/static/icons/academia-edu.png' } ];
    let filteredIcons = [];
    let currentPage = 1;
    const iconsPerPage = 8;

    function renderIcons() {
        if (!iconsGrid) return;
        iconsGrid.innerHTML = '';
        const start = (currentPage - 1) * iconsPerPage;
        const end = start + iconsPerPage;
        const iconsToRender = filteredIcons.slice(start, end);
        if (iconsToRender.length === 0 && filteredIcons.length > 0 && currentPage > 1) {
            currentPage--;
            renderIcons();
            return;
        }
        iconsToRender.forEach(icon => {
            const iconElement = document.createElement('div');
            iconElement.className = 'icon-option';
            iconElement.innerHTML = `<img src="${icon.path}" alt="${icon.name}"><p>${icon.name.replace(/-/g, ' ')}</p>`;
            iconElement.addEventListener('click', function () {
                document.querySelectorAll('.icon-option').forEach(el => el.classList.remove('selected'));
                this.classList.add('selected');
            });
            iconsGrid.appendChild(iconElement);
        });
        updatePaginationControls();
    }

    function updatePaginationControls() {
        if (!currentPageSpan || !prevIconPageBtn || !nextIconPageBtn) return;
        const totalPages = Math.ceil(filteredIcons.length / iconsPerPage);
        currentPageSpan.textContent = currentPage;
        prevIconPageBtn.disabled = currentPage === 1;
        nextIconPageBtn.disabled = currentPage >= totalPages || filteredIcons.length === 0;
    }

    function filterAndRenderIcons() {
        if (!iconSearchInput) return;
        const searchTerm = iconSearchInput.value.toLowerCase().trim();
        filteredIcons = searchTerm === '' ? [...allSocialIcons] : allSocialIcons.filter(icon => icon.name.toLowerCase().includes(searchTerm));
        currentPage = 1;
        renderIcons();
    }

    function closeModals() {
        if(iconModal) iconModal.classList.remove('active', 'show');
        if(buttonModal) buttonModal.classList.remove('active', 'show');
        document.body.classList.remove('modal-open');
        currentModalPurpose = '';
    }

    if(iconSearchInput) iconSearchInput.addEventListener('input', filterAndRenderIcons);
    if(prevIconPageBtn) prevIconPageBtn.addEventListener('click', () => { if (currentPage > 1) { currentPage--; renderIcons(); } });
    if(nextIconPageBtn) nextIconPageBtn.addEventListener('click', () => { const totalPages = Math.ceil(filteredIcons.length / iconsPerPage); if (currentPage < totalPages) { currentPage++; renderIcons(); } });

    if(addIconBtn) addIconBtn.addEventListener('click', () => {
        currentModalPurpose = 'social';
        filterAndRenderIcons();
        iconModal.classList.add('show');
        document.body.classList.add('modal-open');
        setTimeout(() => iconModal.classList.add('active'), 50);
    });

    if(addCardLinkBtn) addCardLinkBtn.addEventListener('click', () => {
        const currentCardLinksCount = document.querySelectorAll('#card-links-container .card-link-item').length;
        if (currentCardLinksCount >= 3) {
            alert('Você pode adicionar no máximo 3 links ao cartão de visitas.');
            return;
        }
        currentModalPurpose = 'card_link';
        filterAndRenderIcons();
        iconModal.classList.add('show');
        document.body.classList.add('modal-open');
        setTimeout(() => iconModal.classList.add('active'), 50);
    });


    const saveIconBtn = document.getElementById('save-icon');
    if(saveIconBtn) saveIconBtn.addEventListener('click', function (event) {
        event.preventDefault();
        const selectedIcon = document.querySelector('.icon-option.selected');
        if (selectedIcon) {
            const iconName = selectedIcon.querySelector('p').textContent.toLowerCase().replace(/ /g, '-');
            const iconPath = `/static/icons/${iconName}.png`;
            let targetContainer, itemClass, inputNameForCheck;

            const newItemField = document.createElement('div'); 

            if (currentModalPurpose === 'social') {
                targetContainer = socialIconsContainer;
                itemClass = 'social-item';
                inputNameForCheck = 'social_icon_name[]';
                // Guardar o HTML do item social para evitar redefinição acidental
                const socialItemHTML = `
                    <i class="fas fa-grip-vertical drag-handle"></i> <img src="${iconPath}" alt="${iconName}" width="24">
                    <input type="hidden" name="social_icon_name[]" value="${escapeHtml(iconName)}">
                    <input type="text" name="social_icon_url[]"
                                placeholder="Insira o link para ${iconName.replace(/-/g, ' ')}"
                                class="form-input" required>
                    <span class="remove-item"><i class="fas fa-times"></i></span>`;
                newItemField.innerHTML = socialItemHTML; // Definir o HTML aqui para o social_item
            } else if (currentModalPurpose === 'card_link') {
                targetContainer = cardLinksContainer;
                itemClass = 'card-link-item';
                inputNameForCheck = 'card_icon_name[]';
                
                newItemField.className = itemClass;

                const dragHandle = document.createElement('i');
                dragHandle.className = 'fas fa-grip-vertical drag-handle';
                newItemField.appendChild(dragHandle);

                const imgIcon = document.createElement('img');
                imgIcon.src = iconPath; imgIcon.alt = iconName; imgIcon.width = 24;
                newItemField.appendChild(imgIcon);

                const hiddenIconNameInput = document.createElement('input');
                hiddenIconNameInput.type = 'hidden'; hiddenIconNameInput.name = 'card_icon_name[]'; hiddenIconNameInput.value = escapeHtml(iconName);
                newItemField.appendChild(hiddenIconNameInput);

                const inputGroupDiv = document.createElement('div');
                inputGroupDiv.className = 'input-group';
                const urlInput = document.createElement('input');
                urlInput.type = 'text'; urlInput.name = 'card_icon_url[]'; urlInput.placeholder = 'URL (Opcional)'; urlInput.className = 'form-input';
                inputGroupDiv.appendChild(urlInput);
                const atTextInput = document.createElement('input');
                atTextInput.type = 'text'; atTextInput.name = 'card_icon_at_text[]'; atTextInput.placeholder = '@texto'; atTextInput.className = 'form-input card-link-item-at-text';
                inputGroupDiv.appendChild(atTextInput);
                newItemField.appendChild(inputGroupDiv);

                const styleControlsDiv = document.createElement('div');
                styleControlsDiv.className = 'card-link-style-controls';
                
                const hiddenFontInput = document.createElement('input');
                hiddenFontInput.type = 'hidden'; hiddenFontInput.name = 'card_icon_font[]'; hiddenFontInput.value = DEFAULT_FONT_JS;
                styleControlsDiv.appendChild(hiddenFontInput);

                const fontSelect = document.createElement('select');
                fontSelect.className = 'form-input card-link-item-font';
                const fonts = [ { name: 'Padrão (Inter)', value: 'Inter, sans-serif' }, { name: 'Arial', value: 'Arial, sans-serif' }, { name: 'Verdana', value: 'Verdana, sans-serif' }, { name: 'Georgia', value: 'Georgia, serif' }, { name: 'Times New Roman', value: "'Times New Roman', Times, serif" }, { name: 'Courier New', value: "'Courier New', Courier, monospace" }, { name: 'Roboto', value: 'Roboto, sans-serif' }, { name: 'Open Sans', value: "'Open Sans', sans-serif" }, { name: 'Lato', value: 'Lato, sans-serif' }, { name: 'Montserrat', value: 'Montserrat, sans-serif' }];
                fonts.forEach(font => {
                    const option = document.createElement('option');
                    option.value = font.value; option.textContent = font.name;
                    if (font.value === DEFAULT_FONT_JS) option.selected = true;
                    fontSelect.appendChild(option);
                });
                styleControlsDiv.appendChild(fontSelect);

                const hiddenColorInput = document.createElement('input');
                hiddenColorInput.type = 'hidden'; hiddenColorInput.name = 'card_icon_color[]'; hiddenColorInput.value = DEFAULT_TEXT_COLOR_CARD_JS;
                styleControlsDiv.appendChild(hiddenColorInput);

                const colorInput = document.createElement('input');
                colorInput.type = 'color'; colorInput.className = 'card-link-item-color'; colorInput.value = DEFAULT_TEXT_COLOR_CARD_JS;
                styleControlsDiv.appendChild(colorInput);
                newItemField.appendChild(styleControlsDiv);

                const previewDiv = document.createElement('div');
                previewDiv.className = 'card-link-item-preview';
                newItemField.appendChild(previewDiv);
                
                atTextInput.addEventListener('input', () => updateCardLinkItemPreview(newItemField));
                fontSelect.addEventListener('change', () => {
                    hiddenFontInput.value = fontSelect.value;
                    updateCardLinkItemPreview(newItemField);
                });
                colorInput.addEventListener('input', () => {
                    hiddenColorInput.value = colorInput.value;
                    updateCardLinkItemPreview(newItemField);
                });
                 // Adiciona o botão de remover para card_link
                const removeSpanCard = document.createElement('span');
                removeSpanCard.className = 'remove-item';
                removeSpanCard.innerHTML = '<i class="fas fa-times"></i>';
                newItemField.appendChild(removeSpanCard); // Adiciona ao final do newItemField
                
            } else { return; }

            let iconExists = false;
            if(targetContainer) {
                targetContainer.querySelectorAll(`input[name="${inputNameForCheck}"]`).forEach(input => {
                    if (input.value === iconName) iconExists = true;
                });
            }

            if (iconExists) { alert('Este ícone já foi adicionado!'); closeModals(); return; }
            
            // Definir classe aqui se não for card_link (já que socialItemHTML foi definido antes)
            if (currentModalPurpose === 'social') {
                newItemField.className = itemClass;
            }
            
            if(targetContainer) targetContainer.appendChild(newItemField);
            
            // Adicionar listener de remoção após o item ser adicionado ao DOM
            // O listener para card_link já é adicionado acima dinamicamente
            // O listener para social_item precisa ser adicionado aqui, pois o HTML é setado via innerHTML
            const removeButton = newItemField.querySelector('.remove-item');
            if (removeButton) {
                removeButton.addEventListener('click', function () {
                    this.closest(`.${itemClass}`).remove();
                });
            }


            if (currentModalPurpose === 'card_link') { 
                updateCardLinkItemPreview(newItemField);
            }
            
            const firstInput = newItemField.querySelector('input[type="text"]');
            if (firstInput) firstInput.focus();

            closeModals();
        } else {
            alert('Por favor, selecione um ícone primeiro!');
        }
    });

    document.querySelectorAll('#card-links-container .card-link-item').forEach(item => {
        updateCardLinkItemPreview(item); 

        const atTextInput = item.querySelector('.card-link-item-at-text');
        const fontSelect = item.querySelector('.card-link-item-font'); 
        const colorInput = item.querySelector('.card-link-item-color'); 
        const hiddenFontInput = item.querySelector('input[name="card_icon_font[]"]'); 
        const hiddenColorInput = item.querySelector('input[name="card_icon_color[]"]'); 

        if (atTextInput) {
            atTextInput.addEventListener('input', () => updateCardLinkItemPreview(item));
        }
        if (fontSelect && hiddenFontInput) {
            fontSelect.addEventListener('change', () => {
                hiddenFontInput.value = fontSelect.value; 
                updateCardLinkItemPreview(item);
            });
        }
        if (colorInput && hiddenColorInput) {
            colorInput.addEventListener('input', () => {
                hiddenColorInput.value = colorInput.value; 
                updateCardLinkItemPreview(item);
            });
        }
    });


    const buttonHasBorderCheckbox = document.getElementById('button-has-border');
    const borderOptionsGroup = document.getElementById('border-options-group');
    if(buttonHasBorderCheckbox) buttonHasBorderCheckbox.addEventListener('change', function() {
        if(borderOptionsGroup) borderOptionsGroup.style.display = this.checked ? 'flex' : 'none';
        updateButtonPreview();
    });

    const liveButtonPreview = document.getElementById('live-button-preview');
    const buttonTextInput = document.getElementById('button-text');
    const buttonColorInput = document.getElementById('button-color');
    const buttonRadiusInput = document.getElementById('button-radius');
    const radiusValueSpan = document.getElementById('radius-value');
    const buttonTextColorInput = document.getElementById('button-text-color');
    const buttonTextBoldCheckbox = document.getElementById('button-text-bold');
    const buttonTextItalicCheckbox = document.getElementById('button-text-italic');
    const buttonFontSizeInput = document.getElementById('button-font-size');
    const buttonBorderColorInput = document.getElementById('button-border-color');
    const buttonBorderWidthInput = document.getElementById('button-border-width');
    const buttonHasHoverCheckbox = document.getElementById('button-has-hover');
    const buttonShadowTypeSelect = document.getElementById('button-shadow-type');

    function updateButtonPreview() {
        if (!liveButtonPreview || !buttonTextInput || !buttonColorInput || !buttonRadiusInput || !radiusValueSpan || !buttonTextColorInput || !buttonTextBoldCheckbox || !buttonTextItalicCheckbox || !buttonFontSizeInput || !buttonHasBorderCheckbox || !buttonBorderColorInput || !buttonBorderWidthInput || !buttonHasHoverCheckbox || !buttonShadowTypeSelect) return;
        liveButtonPreview.textContent = buttonTextInput.value || 'Texto do Botão';
        liveButtonPreview.style.backgroundColor = buttonColorInput.value;
        liveButtonPreview.style.borderRadius = `${buttonRadiusInput.value}px`;
        radiusValueSpan.textContent = `${buttonRadiusInput.value}px`;
        liveButtonPreview.style.color = buttonTextColorInput.value;
        liveButtonPreview.style.fontWeight = buttonTextBoldCheckbox.checked ? 'bold' : 'normal';
        liveButtonPreview.style.fontStyle = buttonTextItalicCheckbox.checked ? 'italic' : 'normal';
        liveButtonPreview.style.fontSize = `${buttonFontSizeInput.value}px`;
        liveButtonPreview.style.border = buttonHasBorderCheckbox.checked ? `${buttonBorderWidthInput.value}px solid ${buttonBorderColorInput.value}` : 'none';
        ['shadow-soft', 'shadow-medium', 'shadow-hard', 'shadow-inset'].forEach(cls => liveButtonPreview.classList.remove(cls));
        if (buttonShadowTypeSelect.value !== 'none') liveButtonPreview.classList.add(`shadow-${buttonShadowTypeSelect.value}`);
        liveButtonPreview.classList.toggle('hover-effect-preview', buttonHasHoverCheckbox.checked);
    }
    
    [buttonTextInput, buttonColorInput, buttonRadiusInput, buttonTextColorInput, buttonTextBoldCheckbox, buttonTextItalicCheckbox, buttonFontSizeInput, buttonBorderColorInput, buttonBorderWidthInput, buttonHasHoverCheckbox, buttonShadowTypeSelect].forEach(el => {
        if (el) el.addEventListener(el.type === 'checkbox' || el.type === 'select-one' ? 'change' : 'input', updateButtonPreview);
    });

    if(addButtonBtn) addButtonBtn.addEventListener('click', () => {
        if(buttonTextInput) buttonTextInput.value = '';
        const buttonLinkInput = document.getElementById('button-link');
        if(buttonLinkInput) buttonLinkInput.value = '';
        if(buttonColorInput) buttonColorInput.value = '#4CAF50';
        if(buttonRadiusInput) buttonRadiusInput.value = '10';
        if(radiusValueSpan) radiusValueSpan.textContent = '10px';
        if(buttonTextColorInput) buttonTextColorInput.value = '#FFFFFF';
        if(buttonTextBoldCheckbox) buttonTextBoldCheckbox.checked = false;
        if(buttonTextItalicCheckbox) buttonTextItalicCheckbox.checked = false;
        if(buttonFontSizeInput) buttonFontSizeInput.value = '16';
        if(buttonHasBorderCheckbox) buttonHasBorderCheckbox.checked = false;
        if(borderOptionsGroup) borderOptionsGroup.style.display = 'none';
        if(buttonBorderColorInput) buttonBorderColorInput.value = '#000000';
        if(buttonBorderWidthInput) buttonBorderWidthInput.value = '2';
        if(buttonHasHoverCheckbox) buttonHasHoverCheckbox.checked = false;
        if(buttonShadowTypeSelect) buttonShadowTypeSelect.value = 'none';
        updateButtonPreview();
        if(buttonModal) {
            buttonModal.classList.add('show');
            document.body.classList.add('modal-open');
            setTimeout(() => buttonModal.classList.add('active'), 50);
        }
    });
    
    const saveButtonBtn = document.getElementById('save-button');
    if(saveButtonBtn) saveButtonBtn.addEventListener('click', function (event) {
        event.preventDefault();
        const btnText = buttonTextInput.value;
        const btnLink = document.getElementById('button-link').value;
        if (btnText && btnLink) {
            const newButtonData = {
                text: btnText, link: btnLink, color: buttonColorInput.value, radius: buttonRadiusInput.value,
                textColor: buttonTextColorInput.value, bold: buttonTextBoldCheckbox.checked, italic: buttonTextItalicCheckbox.checked,
                fontSize: buttonFontSizeInput.value, hasBorder: buttonHasBorderCheckbox.checked, borderColor: buttonBorderColorInput.value,
                borderWidth: buttonBorderWidthInput.value, hasHoverEffect: buttonHasHoverCheckbox.checked, shadowType: buttonShadowTypeSelect.value
            };
            renderCustomButton(newButtonData);
            closeModals();
        } else {
            alert('Por favor, preencha o texto e o link do botão!');
        }
    });

    if(iconModalCloseBtn) iconModalCloseBtn.addEventListener('click', closeModals);
    if(buttonModalCloseBtn) buttonModalCloseBtn.addEventListener('click', closeModals);
    window.addEventListener('click', function (event) {
        if (event.target === iconModal || event.target === buttonModal) closeModals();
    });

    document.querySelectorAll('.social-item .remove-item, .custom-button-item .remove-item, .card-link-item .remove-item').forEach(item => {
        item.addEventListener('click', function() {
            this.closest('.social-item, .custom-button-item, .card-link-item').remove();
        });
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
        cardBgImageUploadSection.style.display = selectedType === 'image' ? 'block' : 'none';
    }
    cardBgTypeRadios.forEach(radio => radio.addEventListener('change', updateCardBackgroundVisibility));
    updateCardBackgroundVisibility();

}); // Fim do DOMContentLoaded