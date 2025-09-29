class StudyBuddy {
    constructor() {
        // Cache DOM elements
        this.pdfInput = document.getElementById('pdf-input');
        this.pdfList = document.getElementById('pdf-list');
        this.pdfClear = document.getElementById('pdf-clear');
        this.deckRun = document.getElementById('deck-run');
        this.deckLoader = document.getElementById('deck-loader');
        this.deckFeedback = document.getElementById('deck-feedback');
        this.deckDownload = document.getElementById('deck-download');
        this.flashcardsDownload = document.getElementById('flashcards-download');
        this.deckProgress = document.getElementById('deck-progress');
        this.deckCheatSheetTex = document.getElementById('deck-cheatsheet-tex');
        this.deckCheatSheetPdf = document.getElementById('deck-cheatsheet-pdf');

        this.ankiInput = document.getElementById('anki-input');
        this.ankiClear = document.getElementById('anki-clear');
        this.ankiFileChip = document.getElementById('anki-file');
        this.ankiRun = document.getElementById('anki-run');
        this.ankiLoader = document.getElementById('anki-loader');
        this.ankiFeedback = document.getElementById('anki-feedback');
        this.ankiProgress = document.getElementById('anki-progress');
        this.ankiCheatSheetTex = document.getElementById('anki-cheatsheet-tex');
        this.ankiCheatSheetPdf = document.getElementById('anki-cheatsheet-pdf');

        if (!this._elementsReady()) {
            console.error('Study Buddy initialisation aborted: missing required elements.');
            return;
        }

        this.pdfFiles = [];
        this.ankiFile = null;

        this.wireEvents();
    }

    _elementsReady() {
        return [
            this.pdfInput,
            this.pdfList,
            this.pdfClear,
            this.deckRun,
            this.deckLoader,
            this.deckFeedback,
            this.deckDownload,
            this.flashcardsDownload,
            this.deckProgress,
            this.deckCheatSheetTex,
            this.deckCheatSheetPdf,
            this.ankiInput,
            this.ankiClear,
            this.ankiFileChip,
            this.ankiRun,
            this.ankiLoader,
            this.ankiFeedback,
            this.ankiProgress,
            this.ankiCheatSheetTex,
            this.ankiCheatSheetPdf,
        ].every(Boolean);
    }

    wireEvents() {
        this.pdfInput.addEventListener('change', (event) => this.handlePdfChange(event));
        this.pdfList.addEventListener('click', (event) => this.handlePdfRemoval(event));
        this.pdfClear.addEventListener('click', () => this.clearPdfs());
        this.deckRun.addEventListener('click', () => this.generateDeck());

        this.ankiInput.addEventListener('change', (event) => this.handleAnkiChange(event));
        this.ankiClear.addEventListener('click', () => this.clearAnki());
        this.ankiRun.addEventListener('click', () => this.generateCheatSheet());
    }

    /* ---------- Step 1: PDFs to deck ---------- */
    handlePdfChange(event) {
        const incoming = Array.from(event.target.files || []);
        if (!incoming.length) {
            return;
        }
        const filtered = incoming.filter((file) => this._isAllowedStudyFile(file));
        if (filtered.length !== incoming.length) {
            this.showToast('Only PDF, PPT, and PPTX files are supported', 'error');
        }
        if (!filtered.length) {
            return;
        }
        this.pdfFiles = this._mergeFiles(this.pdfFiles, filtered);
        this.renderPdfList();
        this.syncPdfInput();
        this.updateDeckControls();
    }

    handlePdfRemoval(event) {
        const button = event.target.closest('[data-remove-index]');
        if (!button) {
            return;
        }
        const index = Number(button.dataset.removeIndex);
        if (!Number.isNaN(index)) {
            this.pdfFiles.splice(index, 1);
            this.renderPdfList();
            this.syncPdfInput();
            this.updateDeckControls();
        }
    }

    clearPdfs() {
        this.pdfFiles = [];
        this.pdfInput.value = '';
        this.renderPdfList();
        this.updateDeckControls();
        if (this.deckCheatSheetTex) this.deckCheatSheetTex.hidden = true;
        if (this.deckCheatSheetPdf) this.deckCheatSheetPdf.hidden = true;
    }

    renderPdfList() {
        if (this.pdfFiles.length === 0) {
            this.pdfList.innerHTML = '';
            this.pdfClear.hidden = true;
            return;
        }

        const items = this.pdfFiles
            .map((file, index) => `
                <li>
                    <div class="file-meta">
                        <span>${file.name}</span>
                        <span>${this.formatFileSize(file.size)}</span>
                    </div>
                    <button type="button" class="file-remove" data-remove-index="${index}">Remove</button>
                </li>
            `)
            .join('');
        this.pdfList.innerHTML = items;
        this.pdfClear.hidden = false;
    }

    syncPdfInput() {
        if (typeof DataTransfer === 'undefined') {
            return;
        }
        try {
            const dataTransfer = new DataTransfer();
            this.pdfFiles.forEach((file) => dataTransfer.items.add(file));
            this.pdfInput.files = dataTransfer.files;
        } catch (_) {
            /* Ignore - some browsers disallow programmatic assignment */
        }
    }

    updateDeckControls() {
        const hasFiles = this.pdfFiles.length > 0;
        this.deckRun.disabled = !hasFiles;
    }

    async generateDeck() {
        if (this.deckRun.disabled || this.pdfFiles.length === 0) {
            return;
        }

        this.setDeckProcessing(true);
        this.showProgress(this.deckProgress, true);
        this.updateProgress(this.deckProgress, 10);
        this.setDeckFeedback('Preparing upload…');

        try {
            const payload = await this.submitRequest(
                { pdfs: this.pdfFiles },
                (percent, message) => {
                    this.updateProgress(this.deckProgress, percent);
                    if (message) {
                        this.setDeckFeedback(message);
                    }
                }
            );
            this.updateProgress(this.deckProgress, 100);
            this.handleDeckResponse(payload);
        } catch (error) {
            const message = error instanceof Error ? error.message : 'Failed to process documents.';
            this.setDeckFeedback(message, 'error');
        } finally {
            this.setDeckProcessing(false);
        }
    }

    setDeckProcessing(isProcessing) {
        this.deckRun.disabled = isProcessing || this.pdfFiles.length === 0;
        this.deckLoader.hidden = !isProcessing;
        if (!isProcessing) {
            this.hideProgress(this.deckProgress);
        }
    }

    setDeckFeedback(message, tone = '') {
        this.deckFeedback.textContent = message;
        this.deckFeedback.className = `status${tone ? ` ${tone}` : ''}`;
    }

    handleDeckResponse(data) {
        const { files = {}, metadata = {}, message } = data;
        const cardCount = metadata.flashcards_created;
        const summaryParts = [];
        if (typeof cardCount === 'number') {
            summaryParts.push(`${cardCount} flashcards ready.`);
        }
        summaryParts.push('Download the deck, study, then upload your Anki export in Step 2.');
        this.setDeckFeedback(`${message || 'Deck generated successfully.'} ${summaryParts.join(' ')}`.trim(), 'success');

        this.configureDownload(this.deckDownload, files.anki_package, 'Download Anki deck (.apkg)');
        this.configureDownload(this.flashcardsDownload, files.flashcards, 'Download flashcards (.json)');
        this.configureDownload(this.deckCheatSheetTex, files.cheat_sheet, 'Download cheat sheet (.tex)');
        this.configureDownload(this.deckCheatSheetPdf, files.cheat_sheet_pdf, 'Download cheat sheet (.pdf)');
    }

    /* ---------- Step 2: Anki export to cheat sheet ---------- */
    handleAnkiChange(event) {
        const [file] = event.target.files || [];
        this.ankiFile = file || null;
        this.renderAnkiFile();
        this.updateAnkiControls();
    }

    clearAnki() {
        this.ankiFile = null;
        this.ankiInput.value = '';
        this.renderAnkiFile();
        this.updateAnkiControls();
        if (this.ankiCheatSheetTex) this.ankiCheatSheetTex.hidden = true;
        if (this.ankiCheatSheetPdf) this.ankiCheatSheetPdf.hidden = true;
    }

    renderAnkiFile() {
        if (this.ankiFile) {
            this.ankiFileChip.textContent = `${this.ankiFile.name} · ${this.formatFileSize(this.ankiFile.size)}`;
            this.ankiFileChip.hidden = false;
            this.ankiClear.hidden = false;
        } else {
            this.ankiFileChip.hidden = true;
            this.ankiClear.hidden = true;
        }
    }

    updateAnkiControls() {
        this.ankiRun.disabled = !this.ankiFile;
    }

    async generateCheatSheet() {
        if (!this.ankiFile || this.ankiRun.disabled) {
            return;
        }

        this.setAnkiProcessing(true);
        this.showProgress(this.ankiProgress, true);
        this.updateProgress(this.ankiProgress, 10);
        this.setAnkiFeedback('Preparing upload…');

        try {
            const payload = await this.submitRequest(
                { anki: this.ankiFile },
                (percent, message) => {
                    this.updateProgress(this.ankiProgress, percent);
                    if (message) {
                        this.setAnkiFeedback(message);
                    }
                }
            );
            this.updateProgress(this.ankiProgress, 100);
            this.handleAnkiResponse(payload);
        } catch (error) {
            const message = error instanceof Error ? error.message : 'Failed to process Anki export.';
            this.setAnkiFeedback(message, 'error');
        } finally {
            this.setAnkiProcessing(false);
        }
    }

    setAnkiProcessing(isProcessing) {
        this.ankiRun.disabled = isProcessing || !this.ankiFile;
        this.ankiLoader.hidden = !isProcessing;
        if (!isProcessing) {
            this.hideProgress(this.ankiProgress);
        }
    }

    setAnkiFeedback(message, tone = '') {
        this.ankiFeedback.textContent = message;
        this.ankiFeedback.className = `status${tone ? ` ${tone}` : ''}`;
    }

    handleAnkiResponse(data) {
        const { files = {}, metadata = {}, message } = data;
        const analysed = metadata.cards_analyzed;
        const hardest = metadata.hardest_card;

        const details = [];
        if (typeof analysed === 'number') {
            details.push(`${analysed} cards analysed.`);
        }
        if (hardest) {
            details.push(`Top challenge: ${hardest}.`);
        }

        const composed = [message || 'Cheat sheet ready.', ...details].join(' ');
        this.setAnkiFeedback(composed.trim(), 'success');

        this.configureDownload(this.ankiCheatSheetTex, files.cheat_sheet, 'Download cheat sheet (.tex)');
        this.configureDownload(this.ankiCheatSheetPdf, files.cheat_sheet_pdf, 'Download cheat sheet (.pdf)');
    }

    /* ---------- Networking helpers ---------- */
    async submitRequest({ pdfs = [], anki = null }, onProgress) {
        const formData = new FormData();
        pdfs.forEach((file) => formData.append('files', file));
        if (anki) {
            formData.append('anki_export', anki);
        }

        if (typeof onProgress === 'function') {
            onProgress(20, 'Uploading files…');
        }

        const response = await fetch('/process', {
            method: 'POST',
            body: formData,
        });

        if (!response.ok) {
            let detail = 'Request failed.';
            try {
                const errorData = await response.json();
                detail = errorData.detail || errorData.message || detail;
            } catch (_) {
                /* ignore */
            }
            throw new Error(detail);
        }

        if (typeof onProgress === 'function') {
            onProgress(55, 'Processing documents…');
        }

        const payload = await response.json();
        if (payload.status !== 'success') {
            throw new Error(payload.message || 'Processing failed.');
        }

        if (typeof onProgress === 'function') {
            onProgress(85, 'Finalising results…');
        }
        return payload;
    }

    configureDownload(anchor, path, label) {
        if (!anchor) {
            return;
        }
        if (!path) {
            anchor.hidden = true;
            anchor.removeAttribute('href');
            return;
        }
        anchor.textContent = label;
        anchor.href = this.buildDownloadUrl(path);
        anchor.hidden = false;
    }

    buildDownloadUrl(path) {
        const safeSegments = path.split(/[\\/]+/).map(encodeURIComponent).join('/');
        return `/download/${safeSegments}`;
    }

    showProgress(progressEl, show) {
        if (!progressEl) {
            return;
        }
        progressEl.hidden = !show;
        if (show) {
            progressEl.value = 0;
        }
    }

    updateProgress(progressEl, value) {
        if (!progressEl) {
            return;
        }
        progressEl.value = Math.min(100, Math.max(0, value));
    }

    hideProgress(progressEl) {
        if (!progressEl) {
            return;
        }
        setTimeout(() => {
            progressEl.hidden = true;
            progressEl.value = 0;
        }, 300);
    }

    formatFileSize(bytes) {
        if (!Number.isFinite(bytes) || bytes <= 0) {
            return '0 B';
        }
        const units = ['B', 'KB', 'MB', 'GB'];
        const index = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1);
        const value = bytes / Math.pow(1024, index);
        return `${value.toFixed(value >= 10 || index === 0 ? 0 : 1)} ${units[index]}`;
    }

    _mergeFiles(existing, incoming) {
        const map = new Map(existing.map((file) => [`${file.name}-${file.size}-${file.lastModified}`, file]));
        incoming.forEach((file) => {
            const key = `${file.name}-${file.size}-${file.lastModified}`;
            if (!map.has(key)) {
                map.set(key, file);
            }
        });
        return Array.from(map.values());
    }

    _isAllowedStudyFile(file) {
        const ext = file.name.split('.').pop()?.toLowerCase() || '';
        return ['pdf', 'ppt', 'pptx'].includes(ext);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new StudyBuddy();
});
