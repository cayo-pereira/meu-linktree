// Função para obter valor de um elemento
function getValue(elementId) {
    const el = document.getElementById(elementId);
    return el ? el.value : '';
}

// Função para atualizar preview de texto
function updateTextPreview(previewElementId, text, font, color) {
    const previewEl = document.getElementById(previewElementId);
    if (previewEl) {
        previewEl.textContent = text || 'Prévia...';
        previewEl.style.fontFamily = font || 'Inter, sans-serif';

        if (previewElementId.includes('card_')) {
            previewEl.style.backgroundColor = '#444'; // Cor de fundo específica para preview do cartão
            previewEl.style.color = color || '#FFFFFF'; // Cor do texto específica para preview do cartão
        } else {
            // Para outros previews, usa as variáveis CSS para consistência com o tema
            previewEl.style.backgroundColor = getComputedStyle(document.documentElement).getPropertyValue('--input-bg-light').trim();
            previewEl.style.color = color || getComputedStyle(document.documentElement).getPropertyValue('--text-color-light').trim();
        }
    }
}

function previewImage(input, previewId, fileInfoId) {
    const previewContainer = document.getElementById(previewId + '_container');
    const previewImageEl = document.getElementById(previewId);
    const fileInfoEl = document.getElementById(fileInfoId);
    const fileWrapper = input.closest('.file-upload-wrapper');
    const removeBtn = document.getElementById('remove_card_background_image_btn'); // Para o caso específico do bg do cartão

    if (input.files && input.files[0]) {
        const reader = new FileReader();
        reader.onload = function (e) {
            previewImageEl.src = e.target.result;
            previewImageEl.style.display = 'block';
            if (previewContainer) previewContainer.style.display = 'block'; // Garante que o container fique visível
            if (previewContainer) previewContainer.classList.add('preview-active');
            if (fileInfoEl) fileInfoEl.textContent = input.files[0].name;
            if (fileWrapper) fileWrapper.classList.add('has-file');
            if (previewId === 'card_background_image_preview' && removeBtn) {
                removeBtn.style.display = 'inline-flex'; // Mostra o botão de remover
                document.getElementById('remove_card_background_image').value = 'false'; // Reseta o campo hidden
            }
        };
        reader.readAsDataURL(input.files[0]);
    }
}


document.addEventListener('DOMContentLoaded', function () {
    // Chama as funções de preview para inicializar os campos de texto com os valores existentes
    updateTextPreview('nome_preview', getValue('nome'), getValue('nome_font'), getValue('nome_color'));
    updateTextPreview('bio_preview', getValue('bio'), getValue('bio_font'), getValue('bio_color'));
    updateTextPreview('card_nome_preview', getValue('card_nome'), getValue('card_nome_font'), getValue('card_nome_color'));
    updateTextPreview('card_titulo_preview', getValue('card_titulo'), getValue('card_titulo_font'), getValue('card_titulo_color'));
    updateTextPreview('card_registro_preview', getValue('card_registro_profissional'), getValue('card_registro_font'), getValue('card_registro_color'));

    const fotosParaPreview = [
        { id: 'foto_preview', infoId: 'foto_info', uploadId: 'foto_upload' },
        { id: 'background_preview', infoId: 'background_info', uploadId: 'background_upload' },
        { id: 'card_background_image_preview', infoId: 'card_background_info', uploadId: 'card_background_upload' }
    ];

    fotosParaPreview.forEach(item => {
        const previewElement = document.getElementById(item.id);
        const infoElement = document.getElementById(item.infoId);
        const containerElement = document.getElementById(item.id + '_container');
        const uploadInput = document.getElementById(item.uploadId); // Pega o input de upload
        const fileWrapper = uploadInput ? uploadInput.closest('.file-upload-wrapper') : null;


        if (previewElement && previewElement.src && previewElement.src !== window.location.href && !previewElement.src.includes('blob:') && previewElement.src.trim() !== '') {
            // Se existe uma imagem carregada (vinda do servidor)
            if(containerElement) containerElement.style.display = 'block'; // Mostra o container
            if(containerElement) containerElement.classList.add('preview-active');
            if (infoElement) {
                 // Tenta extrair e mostrar o nome do arquivo da URL
                 try {
                    const urlParts = previewElement.src.split('/');
                    const fileNameWithQuery = urlParts[urlParts.length - 1]; // Pega a última parte: nome.jpg?timestamp=123
                    const fileName = fileNameWithQuery.split('?')[0]; // Remove parâmetros query: nome.jpg
                    infoElement.textContent = `Atual: ${decodeURIComponent(fileName)}`;
                } catch (e) {
                    infoElement.textContent = 'Imagem atual'; // Fallback
                }
            }
            if (fileWrapper) fileWrapper.classList.add('has-file');
            // Se for o preview da imagem de fundo do cartão, mostra o botão de remover
            if (item.id === 'card_background_image_preview') {
                const removeBtn = document.getElementById('remove_card_background_image_btn');
                if (removeBtn) removeBtn.style.display = 'inline-flex';
            }
        } else {
            // Se não há imagem ou é a imagem padrão/placeholder
            if (infoElement) infoElement.textContent = 'Nenhum arquivo selecionado';
            if (containerElement) containerElement.style.display = 'none'; // Esconde o container se não há imagem válida
            // Se for o preview da imagem de fundo do cartão e não há imagem, esconde o botão de remover
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
    const cardBgInfo = document.getElementById('card_background_info'); // Para atualizar o texto de info
    
    if (removeCardBgBtn) {
        removeCardBgBtn.addEventListener('click', () => {
            if(cardBgUploadInput) cardBgUploadInput.value = ''; // Limpa o input file
            if(cardBgImagePreview) cardBgImagePreview.src = ''; // Limpa o src da imagem de preview
            if(cardBgImagePreview) cardBgImagePreview.style.display = 'none'; // Esconde a imagem
            if(cardBgImagePreviewContainer) cardBgImagePreviewContainer.classList.remove('preview-active');
            if(cardBgImagePreviewContainer) cardBgImagePreviewContainer.style.display = 'none'; // Esconde o container
            if(cardBgInfo) cardBgInfo.textContent = 'Nenhum arquivo selecionado'; // Reseta a info
            const cardBgUploadWrapper = cardBgUploadInput ? cardBgUploadInput.closest('.file-upload-wrapper') : null;
            if(cardBgUploadWrapper) cardBgUploadWrapper.classList.remove('has-file');
            if(removeCardBgHiddenInput) removeCardBgHiddenInput.value = 'true'; // Marca para remoção no backend
            removeCardBgBtn.style.display = 'none'; // Esconde o próprio botão de remover
        });
    }


    // Função para escapar HTML e prevenir XSS ao inserir dados do usuário no DOM
    function escapeHtml(text) {
        if (typeof text !== 'string') {
            return ''; // Retorna string vazia se não for uma string
        }
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return text.replace(/[&<>"']/g, function (m) { return map[m]; });
    }

    // Função para renderizar um botão personalizado na lista
    function renderCustomButton(buttonData) {
        const customButtonsContainer = document.getElementById('custom-buttons-container');
        
        const buttonField = document.createElement('div');
        buttonField.className = 'custom-button-item';

        // Define valores padrão se não existirem em buttonData (importante para botões novos)
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
        let buttonPreviewClasses = ['button-preview']; // Base class
        if (hasBorder) {
            borderStyle = `border: ${borderWidth}px solid ${borderColor};`;
            buttonPreviewClasses.push('has-border-preview');
        }
        if (hasHoverEffect) {
            buttonPreviewClasses.push('hover-effect-preview');
        }
        if (shadowType && shadowType !== 'none') { // Adiciona classe de sombra se não for 'none'
            buttonPreviewClasses.push(`shadow-${shadowType}`);
        }


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

        // Adiciona listener para o botão de remover
        buttonField.querySelector('.remove-item').addEventListener('click', function () {
            this.closest('.custom-button-item').remove();
        });
    }

    // Se você precisar carregar os dados via JS (por exemplo, de um JSON),
    // você chamaria renderExistingSocialIcons, renderExistingCardLinks e renderCustomButton aqui.
    // A forma como estava no seu HTML original com blocos Jinja {% for ... %} é para renderização no servidor.
    // Se esses dados vêm do 'dados' do Flask, eles já são renderizados no HTML diretamente.
    // As funções abaixo seriam úteis se você estivesse, por exemplo, carregando esses dados via uma API fetch
    // e precisasse renderizá-los dinamicamente no lado do cliente após o carregamento da página.

    /*
    // Exemplo de como seria se os dados fossem passados para o JS para renderização cliente:
    // Supondo que `window.APP_DATA.socialLinks` existisse (definido no HTML via Jinja)
    if (window.APP_DATA && window.APP_DATA.socialLinks) {
        renderExistingSocialIcons(window.APP_DATA.socialLinks);
    }
    if (window.APP_DATA && window.APP_DATA.cardLinks) {
        renderExistingCardLinks(window.APP_DATA.cardLinks);
    }
    if (window.APP_DATA && window.APP_DATA.customButtons) {
        window.APP_DATA.customButtons.forEach(button => renderCustomButton(button));
    }
    */
    
    // Adiciona listener para impedir que o clique dentro do conteúdo do modal feche o modal
    // (útil se o listener de fechar modal estiver no window ou no overlay do modal)
    const iconModalContent = document.querySelector('#icon-modal .modal-content');
    if (iconModalContent) {
        iconModalContent.addEventListener('click', (e) => {
            e.stopPropagation();
        });
    }
    const buttonModalContent = document.querySelector('#button-modal .modal-content');
    if (buttonModalContent) {
        buttonModalContent.addEventListener('click', (e) => {
            e.stopPropagation();
        });
    }

    // Inicializa SortableJS para os containers
    const socialIconsContainer = document.getElementById('social-icons-container');
    const customButtonsContainer = document.getElementById('custom-buttons-container');
    const cardLinksContainer = document.getElementById('card-links-container'); // Adicionado

    if (socialIconsContainer) new Sortable(socialIconsContainer, { animation: 150, ghostClass: 'sortable-ghost', chosenClass: 'sortable-chosen', handle: '.drag-handle', });
    if (customButtonsContainer) new Sortable(customButtonsContainer, { animation: 150, ghostClass: 'sortable-ghost', chosenClass: 'sortable-chosen', handle: '.drag-handle', });
    if (cardLinksContainer) new Sortable(cardLinksContainer, { animation: 150, ghostClass: 'sortable-ghost', chosenClass: 'sortable-chosen', handle: '.drag-handle', }); // Adicionado
    
    // Elementos do DOM para os modais
    const iconModal = document.getElementById('icon-modal');
    const buttonModal = document.getElementById('button-modal');
    const addIconBtn = document.getElementById('add-icon-btn');
    const addButtonBtn = document.getElementById('add-button-btn');
    const addCardLinkBtn = document.getElementById('add-card-link-btn'); // Adicionado

    const iconModalCloseBtn = document.querySelector('.icon-modal-close');
    const buttonModalCloseBtn = document.querySelector('.button-modal-close');

    const iconsGrid = document.querySelector('#icon-modal .icons-grid');
    const iconSearchInput = document.getElementById('icon-search');
    const prevIconPageBtn = document.getElementById('prev-icon-page');
    const nextIconPageBtn = document.getElementById('next-icon-page');
    const currentPageSpan = document.getElementById('current-page');

    let currentModalPurpose = ''; // 'social' ou 'card_link'

    // Lista de todos os ícones disponíveis (pode ser expandida)
    const allSocialIcons = [ { name: 'instagram', path: '/static/icons/instagram.png' }, { name: 'linkedin', path: '/static/icons/linkedin.png' }, { name: 'github', path: '/static/icons/github.png' }, { name: 'email', path: '/static/icons/email.png' }, { name: 'whatsapp', path: '/static/icons/whatsapp.png' }, { name: 'twitter', path: '/static/icons/twitter.png' }, { name: 'facebook', path: '/static/icons/facebook.png' }, { name: 'youtube', path: '/static/icons/youtube.png' }, { name: 'telegram', path: '/static/icons/telegram.png' }, { name: 'tiktok', path: '/static/icons/tiktok.png' }, { name: 'pinterest', path: '/static/icons/pinterest.png' }, { name: 'twitch', path: '/static/icons/twitch.png' }, { name: 'discord', path: '/static/icons/discord.png' }, { name: 'snapchat', path: '/static/icons/snapchat.png' }, { name: 'reddit', path: '/static/icons/reddit.png' }, { name: 'vimeo', path: '/static/icons/vimeo.png' }, { name: 'medium', path: '/static/icons/medium.png' }, { name: 'spotify', path: '/static/icons/spotify.png' }, { name: 'soundcloud', path: '/static/icons/soundcloud.png' }, { name: 'behance', path: '/static/icons/behance.png' }, { name: 'dribbble', path: '/static/icons/dribbble.png' }, { name: 'flickr', path: '/static/icons/flickr.png' }, { name: 'etsy', path: '/static/icons/etsy.png' }, { name: 'paypal', path: '/static/icons/paypal.png' }, { name: 'google-drive', path: '/static/icons/google-drive.png' }, { name: 'dropbox', path: '/static/icons/dropbox.png' }, { name: 'link', path: '/static/icons/link.png' }, { name: 'phone', path: '/static/icons/phone.png' }, { name: 'website', path: '/static/icons/website.png' }, { name: 'xing', path: '/static/icons/xing.png' }, { name: 'mastodon', path: '/static/icons/mastodon.png' }, { name: 'stack-overflow', path: '/static/icons/stack-overflow.png' }, { name: 'gitlab', path: '/static/icons/gitlab.png' }, { name: 'bitbucket', path: '/static/icons/bitbucket.png' }, { name: 'codepen', path: '/static/icons/codepen.png' }, { name: 'dev-to', path: '/static/icons/dev-to.png' }, { name: 'freecodecamp', path: '/static/icons/freecodecamp.png' }, { name: 'hashnode', path: '/static/icons/hashnode.png' }, { name: 'product-hunt', path: '/static/icons/product-hunt.png' }, { name: 'unsplash', path: '/static/icons/unsplash.png' }, { name: 'patreon', path: '/static/icons/patreon.png' }, { name: 'buymeacoffee', path: '/static/icons/buymeacoffee.png' }, { name: 'ko-fi', path: '/static/icons/ko-fi.png' }, { name: 'slack', path: '/static/icons/slack.png' }, { name: 'teams', path: '/static/icons/teams.png' }, { name: 'skype', path: '/static/icons/skype.png' }, { name: 'google-scholar', path: '/static/icons/google-scholar.png' }, { name: 'researchgate', path: '/static/icons/researchgate.png' }, { name: 'academia-edu', path: '/static/icons/academia-edu.png' } ];
    let filteredIcons = [];
    let currentPage = 1;
    const iconsPerPage = 8; // Número de ícones por página na modal

    function renderIcons() {
        if (!iconsGrid) return;
        iconsGrid.innerHTML = '';
        const start = (currentPage - 1) * iconsPerPage;
        const end = start + iconsPerPage;
        const iconsToRender = filteredIcons.slice(start, end);

        // Se a página atual ficou vazia após uma filtragem e não é a primeira página, volte uma página.
        if (iconsToRender.length === 0 && filteredIcons.length > 0 && currentPage > 1) {
            currentPage--;
            renderIcons(); // Chama recursivamente para renderizar a página anterior
            return;
        }

        iconsToRender.forEach(icon => {
            const iconElement = document.createElement('div');
            iconElement.className = 'icon-option';
            iconElement.innerHTML = `
                <img src="${icon.path}" alt="${icon.name}">
                <p>${icon.name.replace(/-/g, ' ')}</p>`; // Exibe nome amigável
            iconElement.addEventListener('click', function () {
                // Remove a seleção de qualquer outro ícone e seleciona o clicado
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
        nextIconPageBtn.disabled = currentPage >= totalPages || filteredIcons.length === 0; // Desabilita se não houver ícones ou estiver na última página
    }

    // Filtra e renderiza os ícones baseados na busca
    function filterAndRenderIcons() {
        if (!iconSearchInput) return;
        const searchTerm = iconSearchInput.value.toLowerCase().trim();
        if (searchTerm === '') {
            filteredIcons = [...allSocialIcons]; // Se busca vazia, mostra todos
        } else {
            filteredIcons = allSocialIcons.filter(icon =>
                icon.name.toLowerCase().includes(searchTerm)
            );
        }
        currentPage = 1; // Reseta para a primeira página ao filtrar
        renderIcons();
    }

    // Função para fechar todos os modais
    function closeModals() {
        if(iconModal) iconModal.classList.remove('active', 'show');
        if(buttonModal) buttonModal.classList.remove('active', 'show');
        document.body.classList.remove('modal-open');
        currentModalPurpose = ''; // Limpa o propósito do modal de ícones
    }

    // Event listeners para busca e paginação de ícones
    if(iconSearchInput) iconSearchInput.addEventListener('input', filterAndRenderIcons);
    if(prevIconPageBtn) prevIconPageBtn.addEventListener('click', () => { if (currentPage > 1) { currentPage--; renderIcons(); } });
    if(nextIconPageBtn) nextIconPageBtn.addEventListener('click', () => { const totalPages = Math.ceil(filteredIcons.length / iconsPerPage); if (currentPage < totalPages) { currentPage++; renderIcons(); } });

    // Abrir modal de ícones para Ícones Sociais
    if(addIconBtn) addIconBtn.addEventListener('click', () => {
        currentModalPurpose = 'social'; // Define o propósito
        filterAndRenderIcons(); // Inicializa/reseta a lista de ícones
        iconModal.classList.add('show');
        document.body.classList.add('modal-open');
        setTimeout(() => iconModal.classList.add('active'), 50); // Para animação
    });

    // Abrir modal de ícones para Links do Cartão
    if(addCardLinkBtn) addCardLinkBtn.addEventListener('click', () => {
        const currentCardLinksCount = document.querySelectorAll('#card-links-container .card-link-item').length;
        if (currentCardLinksCount >= 3) {
            alert('Você pode adicionar no máximo 3 links ao cartão de visitas.');
            return;
        }
        currentModalPurpose = 'card_link'; // Define o propósito
        filterAndRenderIcons(); // Inicializa/reseta a lista de ícones
        iconModal.classList.add('show');
        document.body.classList.add('modal-open');
        setTimeout(() => iconModal.classList.add('active'), 50); // Para animação
    });


    // Salvar ícone selecionado
    const saveIconBtn = document.getElementById('save-icon');
    if(saveIconBtn) saveIconBtn.addEventListener('click', function (event) {
        event.preventDefault(); // Previne submit se estiver dentro de um form
        const selectedIcon = document.querySelector('.icon-option.selected');
        if (selectedIcon) {
            const iconName = selectedIcon.querySelector('p').textContent.toLowerCase().replace(/ /g, '-');
            const iconPath = `/static/icons/${iconName}.png`; // Caminho do ícone

            let targetContainer, itemClass, inputNameForCheck, itemHTML;

            if (currentModalPurpose === 'social') {
                targetContainer = socialIconsContainer;
                itemClass = 'social-item';
                inputNameForCheck = 'social_icon_name[]';
                itemHTML = `
                    <i class="fas fa-grip-vertical drag-handle"></i> <img src="${iconPath}" alt="${iconName}" width="24">
                    <input type="hidden" name="social_icon_name[]" value="${escapeHtml(iconName)}">
                    <input type="text" name="social_icon_url[]"
                                placeholder="Insira o link para ${iconName.replace(/-/g, ' ')}"
                                class="form-input" required>
                    <span class="remove-item"><i class="fas fa-times"></i></span>`;
            } else if (currentModalPurpose === 'card_link') {
                targetContainer = cardLinksContainer;
                itemClass = 'card-link-item';
                inputNameForCheck = 'card_icon_name[]';
                itemHTML = `
                    <i class="fas fa-grip-vertical drag-handle"></i> <img src="${iconPath}" alt="${iconName}" width="24">
                    <input type="hidden" name="card_icon_name[]" value="${escapeHtml(iconName)}">
                    <div class="input-group">
                        <input type="text" name="card_icon_url[]"
                                    placeholder="URL (Opcional)"
                                    class="form-input">
                        <input type="text" name="card_icon_at_text[]"
                                    placeholder="@texto"
                                    class="form-input">
                    </div>
                    <span class="remove-item"><i class="fas fa-times"></i></span>`;
            } else { return; } // Propósito desconhecido

            // Verifica se o ícone já foi adicionado ao container específico
            let iconExists = false;
            if(targetContainer) {
                targetContainer.querySelectorAll(`input[name="${inputNameForCheck}"]`).forEach(input => {
                    if (input.value === iconName) iconExists = true;
                });
            }


            if (iconExists) { alert('Este ícone já foi adicionado!'); closeModals(); return; }

            const newItemField = document.createElement('div');
            newItemField.className = itemClass;
            newItemField.innerHTML = itemHTML;
            if(targetContainer) targetContainer.appendChild(newItemField);
            
            // Foca no primeiro input de texto do item adicionado, se houver
            const firstInput = newItemField.querySelector('input[type="text"]');
            if (firstInput) firstInput.focus();

            // Adiciona listener para o novo botão de remover
            newItemField.querySelector('.remove-item').addEventListener('click', function () {
                this.closest(`.${itemClass}`).remove();
            });
            closeModals();
        } else {
            alert('Por favor, selecione um ícone primeiro!');
        }
    });

    // Lógica para o modal de criação de botão
    const buttonHasBorderCheckbox = document.getElementById('button-has-border');
    const borderOptionsGroup = document.getElementById('border-options-group');

    // Mostra/esconde opções de borda baseado no checkbox
    if(buttonHasBorderCheckbox) buttonHasBorderCheckbox.addEventListener('change', function() {
        if(borderOptionsGroup) borderOptionsGroup.style.display = this.checked ? 'flex' : 'none';
        updateButtonPreview(); // Atualiza o preview quando a borda é alterada
    });

    // Elementos do DOM para o preview do botão
    const liveButtonPreview = document.getElementById('live-button-preview');
    const buttonTextInput = document.getElementById('button-text'); // Corrigido para pegar o elemento
    const buttonColorInput = document.getElementById('button-color');
    const buttonRadiusInput = document.getElementById('button-radius');
    const radiusValueSpan = document.getElementById('radius-value');
    const buttonTextColorInput = document.getElementById('button-text-color');
    const buttonTextBoldCheckbox = document.getElementById('button-text-bold');
    const buttonTextItalicCheckbox = document.getElementById('button-text-italic');
    const buttonFontSizeInput = document.getElementById('button-font-size');
    // Elementos da borda já definidos: buttonHasBorderCheckbox, borderOptionsGroup
    const buttonBorderColorInput = document.getElementById('button-border-color');
    const buttonBorderWidthInput = document.getElementById('button-border-width');
    const buttonHasHoverCheckbox = document.getElementById('button-has-hover');
    const buttonShadowTypeSelect = document.getElementById('button-shadow-type'); // Adicionado

    // Função para atualizar o preview do botão em tempo real
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

        // Aplica ou remove a borda
        if (buttonHasBorderCheckbox.checked) {
            liveButtonPreview.style.border = `${buttonBorderWidthInput.value}px solid ${buttonBorderColorInput.value}`;
        } else {
            liveButtonPreview.style.border = 'none';
        }

        // Gerencia classes de sombra
        ['shadow-soft', 'shadow-medium', 'shadow-hard', 'shadow-inset'].forEach(cls => liveButtonPreview.classList.remove(cls));
        if (buttonShadowTypeSelect.value !== 'none') {
            liveButtonPreview.classList.add(`shadow-${buttonShadowTypeSelect.value}`);
        }

        // Adiciona/remove classe de efeito hover para CSS (se houver estilos CSS para .hover-effect-preview:hover)
        liveButtonPreview.classList.toggle('hover-effect-preview', buttonHasHoverCheckbox.checked);
    }
    
    // Adiciona listeners para atualizar o preview do botão
    [buttonTextInput, buttonColorInput, buttonRadiusInput, buttonTextColorInput, buttonTextBoldCheckbox, buttonTextItalicCheckbox, buttonFontSizeInput, buttonBorderColorInput, buttonBorderWidthInput, buttonHasHoverCheckbox, buttonShadowTypeSelect].forEach(el => {
        if (el) el.addEventListener(el.type === 'checkbox' || el.type === 'select-one' ? 'change' : 'input', updateButtonPreview);
    });


    // Abrir modal de criação de botão
    if(addButtonBtn) addButtonBtn.addEventListener('click', () => {
        // Reseta os campos do modal para valores padrão
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
        if(borderOptionsGroup) borderOptionsGroup.style.display = 'none'; // Esconde opções de borda
        if(buttonBorderColorInput) buttonBorderColorInput.value = '#000000';
        if(buttonBorderWidthInput) buttonBorderWidthInput.value = '2';
        if(buttonHasHoverCheckbox) buttonHasHoverCheckbox.checked = false;
        if(buttonShadowTypeSelect) buttonShadowTypeSelect.value = 'none'; // Reseta sombra
        updateButtonPreview(); // Atualiza o preview com os valores resetados

        if(buttonModal) {
            buttonModal.classList.add('show');
            document.body.classList.add('modal-open');
            setTimeout(() => buttonModal.classList.add('active'), 50); // Para animação
        }
    });
    
    // Salvar botão personalizado
    const saveButtonBtn = document.getElementById('save-button');
    if(saveButtonBtn) saveButtonBtn.addEventListener('click', function (event) {
        event.preventDefault(); // Previne submit se estiver dentro de um form
        const btnText = buttonTextInput.value; // Usar a variável já definida
        const btnLink = document.getElementById('button-link').value; // Pega o valor do link
        
        if (btnText && btnLink) { // Verifica se texto e link foram preenchidos
            const newButtonData = {
                text: btnText,
                link: btnLink,
                color: buttonColorInput.value,
                radius: buttonRadiusInput.value,
                textColor: buttonTextColorInput.value,
                bold: buttonTextBoldCheckbox.checked,
                italic: buttonTextItalicCheckbox.checked,
                fontSize: buttonFontSizeInput.value,
                hasBorder: buttonHasBorderCheckbox.checked,
                borderColor: buttonBorderColorInput.value,
                borderWidth: buttonBorderWidthInput.value,
                hasHoverEffect: buttonHasHoverCheckbox.checked,
                shadowType: buttonShadowTypeSelect.value // Adicionado
            };
            
            renderCustomButton(newButtonData); // Usa a função para adicionar o botão à lista
            closeModals();
        } else {
            alert('Por favor, preencha o texto e o link do botão!');
        }
    });

    // Fechar modais
    if(iconModalCloseBtn) iconModalCloseBtn.addEventListener('click', closeModals);
    if(buttonModalCloseBtn) buttonModalCloseBtn.addEventListener('click', closeModals);

    // Fechar modal clicando fora do conteúdo
    window.addEventListener('click', function (event) {
        if (event.target === iconModal || event.target === buttonModal) {
            closeModals();
        }
    });

    // Adiciona funcionalidade de remover para itens já existentes na página (carregados pelo servidor)
    document.querySelectorAll('.social-item .remove-item, .custom-button-item .remove-item, .card-link-item .remove-item').forEach(item => {
        item.addEventListener('click', function() {
            // Encontra o ancestral 'social-item', 'custom-button-item' ou 'card-link-item' e o remove
            this.closest('.social-item, .custom-button-item, .card-link-item').remove();
        });
    });

    // Lógica para o tipo de background do cartão (Cor Sólida vs Imagem)
    const cardBgTypeRadios = document.querySelectorAll('input[name="card_background_type"]');
    const cardBgColorPicker = document.getElementById('card_background_color_picker');
    const cardBgImageUploadSection = document.getElementById('card_background_image_upload_section');

    function updateCardBackgroundVisibility() {
        if (!cardBgColorPicker || !cardBgImageUploadSection) return;
        const selectedTypeRadio = document.querySelector('input[name="card_background_type"]:checked');
        if (!selectedTypeRadio) return; // Sai se nenhum estiver selecionado (improvável com default)
        const selectedType = selectedTypeRadio.value;

        cardBgColorPicker.style.display = selectedType === 'color' ? 'inline-block' : 'none';
        cardBgImageUploadSection.style.display = selectedType === 'image' ? 'block' : 'none';
    }

    cardBgTypeRadios.forEach(radio => {
        radio.addEventListener('change', updateCardBackgroundVisibility);
    });
    updateCardBackgroundVisibility(); // Chama na inicialização para configurar corretamente

}); // Fim do DOMContentLoaded