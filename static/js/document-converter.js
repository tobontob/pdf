class DocumentConverter {
    constructor() {
        this.dropZone = document.getElementById('dropZone');
        this.fileInput = document.getElementById('fileInput');
        this.fileInfo = document.getElementById('fileInfo');
        this.convertBtn = document.getElementById('convertBtn');
        this.progressBar = document.getElementById('progressBar');
        this.statusMessage = document.getElementById('statusMessage');
        this.downloadBtn = document.getElementById('downloadBtn');
        this.conversionTypeRadios = document.getElementsByName('conversionType');

        this.setupEventListeners();
    }

    setupEventListeners() {
        // 드래그 앤 드롭 이벤트
        this.dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            this.dropZone.classList.add('dragover');
        });

        this.dropZone.addEventListener('dragleave', () => {
            this.dropZone.classList.remove('dragover');
        });

        this.dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            this.dropZone.classList.remove('dragover');
            const file = e.dataTransfer.files[0];
            this.handleFileSelect(file);
        });

        // 파일 선택 이벤트
        this.dropZone.addEventListener('click', () => {
            this.fileInput.click();
        });

        this.fileInput.addEventListener('change', () => {
            const file = this.fileInput.files[0];
            this.handleFileSelect(file);
        });

        // 변환 타입 변경 이벤트
        this.conversionTypeRadios.forEach(radio => {
            radio.addEventListener('change', () => {
                this.updateUI();
            });
        });

        // 변환 버튼 클릭 이벤트
        this.convertBtn.addEventListener('click', () => {
            this.convertFile();
        });
    }

    handleFileSelect(file) {
        if (!file) return;

        const isPDF = file.type === 'application/pdf';
        const isDoc = file.type === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document';
        const conversionType = document.querySelector('input[name="conversionType"]:checked').value;

        if ((isPDF && conversionType === 'pdfToDoc') || (isDoc && conversionType === 'docToPdf')) {
            this.fileInfo.textContent = `선택된 파일: ${file.name} (${this.formatFileSize(file.size)})`;
            this.fileInfo.classList.remove('d-none');
            this.convertBtn.disabled = false;
        } else {
            this.showStatus('지원하지 않는 파일 형식입니다.', 'error');
            this.fileInfo.classList.add('d-none');
            this.convertBtn.disabled = true;
        }
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    updateUI() {
        const conversionType = document.querySelector('input[name="conversionType"]:checked').value;
        
        // 파일 입력 초기화
        this.fileInput.value = '';
        this.fileInfo.classList.add('d-none');
        this.convertBtn.disabled = true;
        this.downloadBtn.classList.add('d-none');
        this.statusMessage.classList.add('d-none');
        
        // 파일 형식 제한 설정
        if (conversionType === 'pdfToDoc') {
            this.fileInput.accept = '.pdf';
        } else {
            this.fileInput.accept = '.docx';
        }
    }

    showStatus(message, type) {
        this.statusMessage.textContent = message;
        this.statusMessage.className = `alert mt-3 alert-${type === 'error' ? 'danger' : 'success'}`;
        this.statusMessage.classList.remove('d-none');
    }

    async convertFile() {
        const file = this.fileInput.files[0];
        if (!file) return;

        const conversionType = document.querySelector('input[name="conversionType"]:checked').value;
        const endpoint = conversionType === 'pdfToDoc' ? '/api/convert/pdf-to-docx' : '/api/convert/docx-to-pdf';

        const formData = new FormData();
        formData.append('file', file);

        try {
            this.progressBar.classList.remove('d-none');
            this.convertBtn.disabled = true;
            this.downloadBtn.classList.add('d-none');
            this.statusMessage.classList.add('d-none');

            const response = await fetch(endpoint, {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const errorText = await response.text();
                let errorMessage;
                try {
                    const errorJson = JSON.parse(errorText);
                    errorMessage = errorJson.error || '변환 중 오류가 발생했습니다.';
                } catch (e) {
                    errorMessage = errorText || '변환 중 오류가 발생했습니다.';
                }
                throw new Error(errorMessage);
            }

            const blob = await response.blob();
            const url = URL.createObjectURL(blob);
            
            this.downloadBtn.href = url;
            this.downloadBtn.download = `${file.name.split('.')[0]}.${conversionType === 'pdfToDoc' ? 'docx' : 'pdf'}`;
            this.downloadBtn.classList.remove('d-none');
            this.showStatus('변환이 완료되었습니다!', 'success');
        } catch (error) {
            console.error('Conversion failed:', error);
            this.showStatus(error.message, 'error');
        } finally {
            this.progressBar.classList.add('d-none');
            this.convertBtn.disabled = false;
        }
    }
}

// 페이지 로드 시 초기화
document.addEventListener('DOMContentLoaded', () => {
    new DocumentConverter();
}); 