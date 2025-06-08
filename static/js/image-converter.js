// PDF.js 초기화
const pdfjsLib = window['pdfjs-dist/build/pdf'];
pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';

class ImageConverter {
    constructor() {
        this.dropZone = document.getElementById('dropZone');
        this.fileInput = document.getElementById('fileInput');
        this.previewImage = document.getElementById('previewImage');
        this.convertBtn = document.getElementById('convertBtn');
        this.progressBar = document.getElementById('progressBar');
        this.statusMessage = document.getElementById('statusMessage');
        this.downloadBtn = document.getElementById('downloadBtn');
        this.imageFormatSelect = document.getElementById('imageFormatSelect');
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
        const isImage = file.type.startsWith('image/');
        const conversionType = document.querySelector('input[name="conversionType"]:checked').value;

        if ((isPDF && conversionType === 'pdfToImage') || (isImage && conversionType === 'imageToPdf')) {
            this.showPreview(file);
            this.convertBtn.disabled = false;
        } else {
            this.showStatus('지원하지 않는 파일 형식입니다.', 'error');
            this.convertBtn.disabled = true;
        }
    }

    async showPreview(file) {
        if (file.type === 'application/pdf') {
            this.previewImage.classList.add('d-none');
        } else if (file.type.startsWith('image/')) {
            const reader = new FileReader();
            reader.onload = (e) => {
                this.previewImage.src = e.target.result;
                this.previewImage.classList.remove('d-none');
            };
            reader.readAsDataURL(file);
        }
    }

    updateUI() {
        const conversionType = document.querySelector('input[name="conversionType"]:checked').value;
        
        // 파일 입력 초기화
        this.fileInput.value = '';
        this.previewImage.classList.add('d-none');
        this.convertBtn.disabled = true;
        
        // 이미지 형식 선택 표시/숨김
        if (conversionType === 'pdfToImage') {
            this.imageFormatSelect.style.display = 'block';
            this.fileInput.accept = '.pdf';
        } else {
            this.imageFormatSelect.style.display = 'none';
            this.fileInput.accept = 'image/*';
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
        const format = document.querySelector('#imageFormatSelect select').value;

        try {
            this.progressBar.classList.remove('d-none');
            this.convertBtn.disabled = true;
            this.downloadBtn.classList.add('d-none');
            this.statusMessage.classList.add('d-none');

            let result;
            if (conversionType === 'pdfToImage') {
                result = await this.convertPDFToImage(file, format);
            } else {
                result = await this.convertImageToPDF(file);
            }

            const url = URL.createObjectURL(result);
            this.downloadBtn.href = url;
            this.downloadBtn.download = `converted.${conversionType === 'pdfToImage' ? format : 'pdf'}`;
            this.downloadBtn.classList.remove('d-none');
            this.showStatus('변환이 완료되었습니다!', 'success');
        } catch (error) {
            console.error('Conversion failed:', error);
            this.showStatus('변환 중 오류가 발생했습니다: ' + error.message, 'error');
        } finally {
            this.progressBar.classList.add('d-none');
            this.convertBtn.disabled = false;
        }
    }

    async convertPDFToImage(pdfFile, format) {
        const arrayBuffer = await pdfFile.arrayBuffer();
        const pdf = await pdfjsLib.getDocument({ data: arrayBuffer }).promise;
        const page = await pdf.getPage(1);
        
        const scale = 2;
        const viewport = page.getViewport({ scale });
        
        const canvas = document.createElement('canvas');
        canvas.width = viewport.width;
        canvas.height = viewport.height;
        
        const context = canvas.getContext('2d');
        await page.render({
            canvasContext: context,
            viewport: viewport
        }).promise;
        
        return new Promise((resolve, reject) => {
            canvas.toBlob((blob) => {
                if (blob) {
                    resolve(blob);
                } else {
                    reject(new Error('Failed to convert PDF to image'));
                }
            }, `image/${format}`, 0.95);
        });
    }

    async convertImageToPDF(imageFile) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = function(event) {
                const img = new Image();
                img.onload = function() {
                    try {
                        const { jsPDF } = window.jspdf;
                        const doc = new jsPDF({
                            orientation: img.width > img.height ? 'landscape' : 'portrait',
                            unit: 'px',
                            format: [img.width, img.height]
                        });

                        const pdfWidth = doc.internal.pageSize.getWidth();
                        const pdfHeight = doc.internal.pageSize.getHeight();

                        const ratio = Math.min(pdfWidth / img.width, pdfHeight / img.height);
                        const width = img.width * ratio;
                        const height = img.height * ratio;
                        const x = (pdfWidth - width) / 2;
                        const y = (pdfHeight - height) / 2;

                        doc.addImage(img.src, 'JPEG', x, y, width, height);
                        resolve(doc.output('blob'));
                    } catch (error) {
                        reject(error);
                    }
                };
                img.onerror = reject;
                img.src = event.target.result;
            };
            reader.onerror = reject;
            reader.readAsDataURL(imageFile);
        });
    }
}

// 페이지 로드 시 초기화
document.addEventListener('DOMContentLoaded', () => {
    new ImageConverter();
}); 