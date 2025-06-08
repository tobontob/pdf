class HwpConverter {
    constructor() {
        this.form = document.getElementById('upload-form');
        this.fileInput = document.getElementById('file-input');
        this.convertBtn = document.getElementById('convert-btn');
        this.downloadBtn = document.getElementById('download-btn');
        this.progressBar = document.getElementById('progress-bar');
        this.progressContainer = document.getElementById('progress-container');
        this.messageContainer = document.getElementById('message-container');
        
        this.convertedFilePath = null;
        this.setupEventListeners();
    }

    setupEventListeners() {
        this.form.addEventListener('submit', (e) => this.handleSubmit(e));
        this.fileInput.addEventListener('change', () => this.handleFileSelect());
        this.downloadBtn.addEventListener('click', () => this.handleDownload());
    }

    handleFileSelect() {
        const file = this.fileInput.files[0];
        if (file) {
            // 파일이 선택되면 변환 버튼 활성화
            this.convertBtn.disabled = false;
            // 이전 변환 결과 초기화
            this.resetConversion();
        } else {
            this.convertBtn.disabled = true;
        }
    }

    async handleSubmit(e) {
        e.preventDefault();
        const file = this.fileInput.files[0];
        if (!file) return;

        try {
            this.showProgress();
            this.convertBtn.disabled = true;
            
            const result = await this.convertFile(file);
            this.convertedFilePath = result.path;
            
            this.showMessage('변환이 완료되었습니다!', 'success');
            this.downloadBtn.style.display = 'block';
        } catch (error) {
            console.error('Conversion failed:', error);
            this.showMessage('변환 중 오류가 발생했습니다: ' + error.message, 'error');
        } finally {
            this.hideProgress();
            this.convertBtn.disabled = false;
        }
    }

    async convertFile(file) {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch('/api/convert/hwp-to-pdf', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const error = await response.text();
            throw new Error(error);
        }

        return await response.json();
    }

    async handleDownload() {
        if (!this.convertedFilePath) return;

        try {
            const response = await fetch(`/api/download?path=${encodeURIComponent(this.convertedFilePath)}`);
            if (!response.ok) throw new Error('다운로드 실패');

            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'converted.pdf';
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        } catch (error) {
            console.error('Download failed:', error);
            this.showMessage('다운로드 중 오류가 발생했습니다.', 'error');
        }
    }

    showProgress() {
        this.progressContainer.style.display = 'block';
        this.progressBar.style.width = '100%';
    }

    hideProgress() {
        this.progressContainer.style.display = 'none';
        this.progressBar.style.width = '0%';
    }

    showMessage(message, type) {
        this.messageContainer.textContent = message;
        this.messageContainer.className = `message ${type}`;
        this.messageContainer.style.display = 'block';
    }

    resetConversion() {
        this.convertedFilePath = null;
        this.downloadBtn.style.display = 'none';
        this.messageContainer.style.display = 'none';
        this.hideProgress();
    }
}

// Initialize the converter when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new HwpConverter();
}); 