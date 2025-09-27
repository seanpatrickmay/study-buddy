class StudyBotApp {
    constructor() {
        this.files = new Map();
        this.ankiFile = null;
        this.studyMaterials = null;

        this.initializeElements();
        this.bindEvents();
    }

    initializeElements() {
        // File upload elements
        this.fileInput = document.getElementById('file-input');
        this.fileUploadArea = document.getElementById('file-upload-area');
        this.fileList = document.getElementById('file-list');
        this.processBtn = document.getElementById('process-btn');
        this.clearBtn = document.getElementById('clear-btn');

        // Anki upload elements
        this.ankiInput = document.getElementById('anki-input');
        this.ankiUploadArea = document.getElementById('anki-upload-area');
        this.ankiFileDisplay = document.getElementById('anki-file');

        // Section elements
        this.uploadSection = document.getElementById('upload-section');
        this.progressSection = document.getElementById('progress-section');
        this.resultsSection = document.getElementById('results-section');
        this.errorSection = document.getElementById('error-section');

        // Progress elements
        this.progressFill = document.getElementById('progress-fill');
        this.progressText = document.getElementById('progress-text');

        // Results elements
        this.mainResultHeader = document.getElementById('main-result-header');
        this.mainResultContent = document.getElementById('main-result-content');

        // Download elements
        this.ankiDownloadBtn = document.getElementById('anki-download-btn');
        this.studyGuideBtn = document.getElementById('study-guide-btn');

        // Control buttons
        this.newUploadBtn = document.getElementById('new-upload-btn');
        this.retryBtn = document.getElementById('retry-btn');
        this.errorMessage = document.getElementById('error-message');

        // Toast container
        this.toastContainer = document.getElementById('toast-container');
    }

    bindEvents() {
        // File input events
        this.fileInput.addEventListener('change', (e) => this.handleFileSelect(e));
        this.ankiInput.addEventListener('change', (e) => this.handleAnkiFileSelect(e));

        // Drag and drop events for PDFs
        this.fileUploadArea.addEventListener('dragover', (e) => this.handleDragOver(e));
        this.fileUploadArea.addEventListener('dragleave', (e) => this.handleDragLeave(e));
        this.fileUploadArea.addEventListener('drop', (e) => this.handleDrop(e));

        // Drag and drop events for Anki files
        this.ankiUploadArea.addEventListener('dragover', (e) => this.handleAnkiDragOver(e));
        this.ankiUploadArea.addEventListener('dragleave', (e) => this.handleAnkiDragLeave(e));
        this.ankiUploadArea.addEventListener('drop', (e) => this.handleAnkiDrop(e));

        // Button events
        this.processBtn.addEventListener('click', () => this.processFiles());
        this.clearBtn.addEventListener('click', () => this.clearFiles());
        this.newUploadBtn.addEventListener('click', () => this.resetToUpload());
        this.retryBtn.addEventListener('click', () => this.processFiles());

        // Download events
        this.ankiDownloadBtn.addEventListener('click', () => this.downloadAnkiPackage());
        this.studyGuideBtn.addEventListener('click', () => this.downloadStudyGuide());

        // Copy button events
        document.querySelectorAll('.copy-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.copyToClipboard(e));
        });
    }

    // File handling methods
    handleFileSelect(event) {
        const files = Array.from(event.target.files);
        this.addFiles(files);
    }

    handleDragOver(event) {
        event.preventDefault();
        this.fileUploadArea.classList.add('dragover');
    }

    handleDragLeave(event) {
        event.preventDefault();
        this.fileUploadArea.classList.remove('dragover');
    }

    handleDrop(event) {
        event.preventDefault();
        this.fileUploadArea.classList.remove('dragover');
        const files = Array.from(event.dataTransfer.files).filter(file =>
            file.type === 'application/pdf'
        );
        this.addFiles(files);
    }

    addFiles(files) {
        files.forEach(file => {
            if (file.type === 'application/pdf' && file.size <= 50 * 1024 * 1024) { // 50MB limit
                const fileId = Date.now() + '-' + Math.random();
                this.files.set(fileId, file);
                this.renderFile(fileId, file);
            } else if (file.type !== 'application/pdf') {
                this.showToast('Only PDF files are supported', 'error');
            } else {
                this.showToast('File size must be less than 50MB', 'error');
            }
        });
        this.updateProcessButton();
        this.fileInput.value = ''; // Reset file input
    }

    renderFile(fileId, file) {
        const fileItem = document.createElement('div');
        fileItem.className = 'file-item';
        fileItem.innerHTML = `
            <div class="file-info">
                <i class="fas fa-file-pdf"></i>
                <div>
                    <div class="file-name">${file.name}</div>
                    <div class="file-size">${this.formatFileSize(file.size)}</div>
                </div>
            </div>
            <button class="remove-file" onclick="app.removeFile('${fileId}')">
                <i class="fas fa-times"></i>
            </button>
        `;
        this.fileList.appendChild(fileItem);
    }

    removeFile(fileId) {
        this.files.delete(fileId);
        this.renderFileList();
        this.updateProcessButton();
    }

    renderFileList() {
        this.fileList.innerHTML = '';
        this.files.forEach((file, fileId) => {
            this.renderFile(fileId, file);
        });
    }

    clearFiles() {
        this.files.clear();
        this.ankiFile = null;
        this.fileList.innerHTML = '';
        this.ankiFileDisplay.innerHTML = '';
        this.updateProcessButton();
        this.showToast('Files cleared', 'info');
    }

    // Anki file handling methods
    handleAnkiFileSelect(event) {
        const file = event.target.files[0];
        if (file) {
            this.setAnkiFile(file);
        }
    }

    handleAnkiDragOver(event) {
        event.preventDefault();
        this.ankiUploadArea.classList.add('dragover');
    }

    handleAnkiDragLeave(event) {
        event.preventDefault();
        this.ankiUploadArea.classList.remove('dragover');
    }

    handleAnkiDrop(event) {
        event.preventDefault();
        this.ankiUploadArea.classList.remove('dragover');
        const file = event.dataTransfer.files[0];
        if (file && file.name.endsWith('.apkg')) {
            this.setAnkiFile(file);
        } else if (file) {
            this.showToast('Only .apkg files are supported', 'error');
        }
    }

    setAnkiFile(file) {
        if (!file.name.endsWith('.apkg')) {
            this.showToast('Only .apkg files are supported', 'error');
            return;
        }

        this.ankiFile = file;
        this.renderAnkiFile(file);
        this.updateProcessButton();
        this.showToast('Anki export added - will prioritize difficult terms!', 'success');
    }

    renderAnkiFile(file) {
        this.ankiFileDisplay.innerHTML = `
            <div class="file-item">
                <div class="file-info">
                    <i class="fas fa-brain"></i>
                    <div>
                        <div class="file-name">${file.name}</div>
                        <div class="file-size">${this.formatFileSize(file.size)}</div>
                    </div>
                </div>
                <button class="remove-file" onclick="app.clearAnkiFile()">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;
    }

    clearAnkiFile() {
        this.ankiFile = null;
        this.ankiFileDisplay.innerHTML = '';
        this.ankiInput.value = '';
        this.updateProcessButton();
        this.showToast('Anki export removed', 'info');
    }

    updateProcessButton() {
        // Enable process button if either PDFs are uploaded OR Anki file is uploaded
        this.processBtn.disabled = this.files.size === 0 && !this.ankiFile;
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    // Processing methods
    async processFiles() {
        if (this.files.size === 0 && !this.ankiFile) {
            this.showToast('Please upload PDFs or an Anki export file to process', 'error');
            return;
        }

        this.showSection('progress');
        this.updateProgress(0, 'Preparing files...');

        const formData = new FormData();
        this.files.forEach((file) => {
            formData.append('files', file);
        });

        // Add Anki file if provided
        if (this.ankiFile) {
            formData.append('anki_export', this.ankiFile);
        }

        try {
            this.updateProgress(25, 'Uploading files...');

            const response = await fetch('/process', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            this.updateProgress(50, 'Processing documents...');

            const result = await response.json();

            this.updateProgress(75, 'Generating study materials...');

            if (result.status === 'success') {
                this.updateProgress(100, 'Complete!');
                setTimeout(() => {
                    this.displayResults(result);
                }, 1000);
            } else {
                throw new Error(result.message || 'Processing failed');
            }

        } catch (error) {
            console.error('Processing error:', error);
            this.showError(error.message);
        }
    }

    updateProgress(percentage, text) {
        this.progressFill.style.width = `${percentage}%`;
        this.progressText.textContent = text;
    }

    // Results display methods
    displayResults(result) {
        const { materials, metadata } = result;
        this.studyMaterials = result;

        // Check processing type
        const processingType = metadata?.processing_type;

        if (processingType === 'pdf_to_anki') {
            // PDF to Anki processing - show instructions only
            this.mainResultHeader.innerHTML = `<h3><i class="fas fa-info-circle"></i> Next Steps</h3>`;

            this.mainResultContent.innerHTML = `<div class="message-box">
                <p>${materials.message || 'Anki package created successfully!'}</p>
                <p><strong>What to do next:</strong></p>
                <ol>
                    <li>Download the Anki package below</li>
                    <li>Import it into Anki and study the cards</li>
                    <li>Export your deck from Anki (with scheduling information)</li>
                    <li>Upload the export here to get your personalized cheat sheet</li>
                </ol>
            </div>`;

        } else if (processingType === 'anki_only') {
            // Anki-only processing - show cheat sheet
            this.mainResultHeader.innerHTML = `
                <h3><i class="fas fa-chart-line"></i> Your Personalized Cheat Sheet</h3>
                <button class="copy-btn" data-target="main-result-content">
                    <i class="fas fa-copy"></i>
                </button>
            `;

            if (materials.cheat_sheet) {
                this.mainResultContent.innerHTML = `<pre>${materials.cheat_sheet}</pre>`;
            } else {
                this.mainResultContent.innerHTML = `<p>No cheat sheet generated. Please try uploading your Anki export again.</p>`;
            }
        }

        // Setup download functionality
        this.setupDownloads(result.files, processingType);

        this.showSection('results');
        this.showToast('Processing completed successfully!', 'success');
    }


    setupDownloads(files, processingType) {
        // Reset both buttons to disabled
        this.ankiDownloadBtn.disabled = true;
        this.studyGuideBtn.disabled = true;

        if (processingType === 'pdf_to_anki') {
            // PDF to Anki processing - only show Anki download
            if (files && files.anki_package) {
                this.ankiDownloadBtn.disabled = false;
                this.ankiDownloadBtn.setAttribute('data-file', files.anki_package);
            }
            // Ensure study guide button stays disabled
            this.studyGuideBtn.disabled = true;

        } else if (processingType === 'anki_only') {
            // Anki-only processing - only show cheat sheet download
            if (files && files.cheat_sheet) {
                this.studyGuideBtn.disabled = false;
                this.studyGuideBtn.setAttribute('data-file', files.cheat_sheet);
                // Update button text for cheat sheet
                const studyGuideText = this.studyGuideBtn.querySelector('.download-btn') || this.studyGuideBtn;
                if (studyGuideText.innerHTML) {
                    studyGuideText.innerHTML = '<i class="fas fa-download"></i> Download Cheat Sheet';
                }
            }
            // Ensure Anki download button stays disabled
            this.ankiDownloadBtn.disabled = true;
        }
    }

    downloadAnkiPackage() {
        const filePath = this.ankiDownloadBtn.getAttribute('data-file');
        if (filePath) {
            this.downloadFile(filePath, 'study_materials.apkg');
        } else {
            this.showToast('Anki package not available', 'error');
        }
    }

    downloadStudyGuide() {
        const filePath = this.studyGuideBtn.getAttribute('data-file');
        if (filePath) {
            const fileName = filePath.includes('cheat_sheet') ? 'cheat_sheet.md' : 'study_guide.md';
            this.downloadFile(filePath, fileName);
        } else {
            this.showToast('Study guide not available', 'error');
        }
    }

    downloadFile(filePath, fileName) {
        // Create download link
        const link = document.createElement('a');
        link.href = `/download/${encodeURIComponent(filePath.replace(/^.*[\\\/]/, ''))}`;
        link.download = fileName;
        link.style.display = 'none';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);

        this.showToast(`Downloading ${fileName}...`, 'success');
    }


    // Utility methods
    showSection(sectionName) {
        // Hide all sections
        this.uploadSection.style.display = 'none';
        this.progressSection.style.display = 'none';
        this.resultsSection.style.display = 'none';
        this.errorSection.style.display = 'none';

        // Show target section
        switch (sectionName) {
            case 'upload':
                this.uploadSection.style.display = 'block';
                break;
            case 'progress':
                this.progressSection.style.display = 'block';
                break;
            case 'results':
                this.resultsSection.style.display = 'block';
                break;
            case 'error':
                this.errorSection.style.display = 'block';
                break;
        }
    }

    showError(message) {
        this.errorMessage.textContent = message;
        this.showSection('error');
        this.showToast('Processing failed', 'error');
    }

    resetToUpload() {
        this.clearFiles();
        this.showSection('upload');
        this.showToast('Ready for new files', 'info');
    }

    copyToClipboard(event) {
        const targetId = event.target.closest('.copy-btn').dataset.target;
        const targetElement = document.getElementById(targetId);
        const text = targetElement.textContent;

        navigator.clipboard.writeText(text).then(() => {
            this.showToast('Copied to clipboard!', 'success');
        }).catch(() => {
            this.showToast('Failed to copy to clipboard', 'error');
        });
    }

    showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;

        const icon = type === 'success' ? 'check-circle' :
                    type === 'error' ? 'exclamation-circle' :
                    'info-circle';

        toast.innerHTML = `
            <i class="fas fa-${icon}"></i>
            <span>${message}</span>
        `;

        this.toastContainer.appendChild(toast);

        // Remove toast after 3 seconds
        setTimeout(() => {
            toast.style.animation = 'slideOut 0.3s ease forwards';
            setTimeout(() => {
                if (toast.parentNode) {
                    toast.parentNode.removeChild(toast);
                }
            }, 300);
        }, 3000);
    }
}

// Initialize the app when the page loads
let app;
document.addEventListener('DOMContentLoaded', () => {
    app = new StudyBotApp();
});

