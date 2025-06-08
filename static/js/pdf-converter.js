// PDF.js와 jsPDF는 전역 변수로 사용
const pdfjsLib = window['pdfjs-dist/build/pdf'];
const { jsPDF } = window.jspdf;
const { PDFDocument } = PDFLib;

// PDF.js 워커 및 CMap 설정
pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
const CMAP_URL = 'https://cdn.jsdelivr.net/npm/pdfjs-dist@3.11.174/cmaps/';
const CMAP_PACKED = true;

class PDFConverter {
    // PDF를 이미지로 변환
    static async pdfToImage(pdfFile, format) {
        try {
            const arrayBuffer = await pdfFile.arrayBuffer();
            const pdf = await pdfjsLib.getDocument({ data: arrayBuffer }).promise;
            const page = await pdf.getPage(1);
            
            const scale = 2;
            const viewport = page.getViewport({ scale });
            
            const canvas = document.createElement('canvas');
            canvas.width = viewport.width;
            canvas.height = viewport.height;
            
            const context = canvas.getContext('2d');
            const renderContext = {
                canvasContext: context,
                viewport: viewport
            };
            
            await page.render(renderContext).promise;
            
            return new Promise((resolve, reject) => {
                canvas.toBlob((blob) => {
                    if (blob) {
                        resolve(blob);
                    } else {
                        reject(new Error('Failed to convert PDF to image'));
                    }
                }, `image/${format}`, 0.95);
            });
        } catch (error) {
            console.error('PDF to Image conversion failed:', error);
            throw error;
        }
    }

    // PDF를 텍스트로 변환 (txt 변환용)
    static async pdfToText(pdfFile) {
        try {
            const arrayBuffer = await pdfFile.arrayBuffer();
            const pdf = await pdfjsLib.getDocument({
                data: arrayBuffer,
                cMapUrl: CMAP_URL,
                cMapPacked: CMAP_PACKED
            }).promise;
            
            let fullText = '';
            for (let i = 1; i <= pdf.numPages; i++) {
                const page = await pdf.getPage(i);
                const textContent = await page.getTextContent();
                const pageText = textContent.items.map(item => item.str).join(' ');
                fullText += pageText + '\n\n';
            }
            return fullText;
        } catch (error) {
            console.error('PDF to Text conversion failed:', error);
            throw error;
        }
    }

    // PDF를 Word로 변환
    static async pdfToWord(pdfFile) {
        try {
            const formData = new FormData();
            formData.append('file', pdfFile);
            
            const response = await fetch('/convert/pdf-to-docx', {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Server conversion failed');
            }
            
            return await response.blob();
        } catch (error) {
            console.error('PDF to Word conversion failed:', error);
            throw error;
        }
    }

    // PDF를 HWP로 변환
    static async pdfToHwp(pdfFile) {
        try {
            const formData = new FormData();
            formData.append('file', pdfFile);
            
            const response = await fetch('/convert/pdf-to-hwp', {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Server conversion failed');
            }
            
            return await response.blob();
        } catch (error) {
            console.error('PDF to HWP conversion failed:', error);
            throw error;
        }
    }

    // HWP를 PDF로 변환
    static async hwpToPdf(hwpFile) {
        try {
            const formData = new FormData();
            formData.append('file', hwpFile);
            
            const response = await fetch('/convert/hwp-to-pdf', {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Server conversion failed');
            }
            
            return await response.blob();
        } catch (error) {
            console.error('HWP to PDF conversion failed:', error);
            throw error;
        }
    }

    // 이미지를 PDF로 변환
    static async imageToPDF(imageFile) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = function(event) {
                const img = new Image();
                img.onload = function() {
                    try {
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
                        const blob = doc.output('blob');
                        resolve(blob);
                    } catch (error) {
                        console.error('PDF generation error:', error);
                        reject(error);
                    }
                };
                img.onerror = function(error) {
                    console.error('Image loading error:', error);
                    reject(error);
                };
                img.src = event.target.result;
            };
            reader.onerror = function(error) {
                console.error('File reading error:', error);
                reject(error);
            };
            reader.readAsDataURL(imageFile);
        });
    }

    // 텍스트를 PDF로 변환
    static async textToPDF(textContent) {
        try {
            const doc = new jsPDF();
            const pageWidth = doc.internal.pageSize.getWidth();
            const margin = 10;
            const fontSize = 12;
            
            doc.setFontSize(fontSize);
            const lines = doc.splitTextToSize(textContent, pageWidth - 2 * margin);
            
            let y = margin;
            lines.forEach(line => {
                if (y > doc.internal.pageSize.getHeight() - margin) {
                    doc.addPage();
                    y = margin;
                }
                doc.text(line, margin, y);
                y += fontSize;
            });

            return doc.output('blob');
        } catch (error) {
            console.error('Text to PDF conversion failed:', error);
            throw error;
        }
    }

    // Word를 PDF로 변환
    static async wordToPdf(wordFile) {
        try {
            const arrayBuffer = await wordFile.arrayBuffer();
            const result = await mammoth.convertToHtml({ arrayBuffer });
            const html = result.value;

            const doc = new jsPDF();
            const pageHeight = doc.internal.pageSize.height;
            const lines = doc.splitTextToSize(html.replace(/<[^>]+>/g, ' '), doc.internal.pageSize.width - 20);
            let y = 10;

            for (let i = 0; i < lines.length; i++) {
                if (y > pageHeight - 10) {
                    doc.addPage();
                    y = 10;
                }
                doc.text(10, y, lines[i]);
                y += 7;
            }

            return doc.output('blob');
        } catch (error) {
            console.error('Word to PDF conversion failed:', error);
            throw error;
        }
    }

    // 여러 페이지 PDF 처리
    static async convertMultiPagePDF(pdfFile, format = 'jpeg') {
        try {
            const arrayBuffer = await pdfFile.arrayBuffer();
            const pdf = await pdfjsLib.getDocument(arrayBuffer).promise;
            const totalPages = pdf.numPages;
            const images = [];

            for (let pageNum = 1; pageNum <= totalPages; pageNum++) {
                const page = await pdf.getPage(pageNum);
                const viewport = page.getViewport({ scale: 1.5 });

                const canvas = document.createElement('canvas');
                const context = canvas.getContext('2d');
                canvas.height = viewport.height;
                canvas.width = viewport.width;

                await page.render({
                    canvasContext: context,
                    viewport: viewport
                }).promise;

                images.push(canvas.toDataURL(`image/${format}`, 1.0));
            }

            return images;
        } catch (error) {
            console.error('Multi-page PDF conversion failed:', error);
            throw error;
        }
    }
}

// 이벤트 핸들러
document.addEventListener('DOMContentLoaded', function() {
    const convertForm = document.getElementById('convertForm');
    const fileInput = document.getElementById('fileInput');
    const formatSelect = document.getElementById('formatSelect');
    const progressBar = document.getElementById('progressBar');
    const downloadLink = document.getElementById('downloadLink');
    const statusMessage = document.getElementById('statusMessage');

    // 파일 형식에 따라 변환 옵션 업데이트
    fileInput.addEventListener('change', function() {
        const file = this.files[0];
        formatSelect.innerHTML = '<option value="">변환 형식 선택</option>';
        
        if (file) {
            if (file.type === 'application/pdf') {
                // PDF 파일이 선택된 경우
                addOption('docx', 'Word 문서 (DOCX)');
                addOption('hwp', '한글 문서 (HWP)');
                addOption('jpg', 'JPG 이미지');
                addOption('png', 'PNG 이미지');
                addOption('txt', '텍스트 문서');
            } else if (file.type.startsWith('image/')) {
                // 이미지 파일이 선택된 경우
                addOption('pdf', 'PDF 문서');
            } else if (file.name.endsWith('.hwp')) {
                // HWP 파일이 선택된 경우
                addOption('pdf', 'PDF 문서');
            } else if (file.type.includes('word') || file.name.match(/\.docx?$/i)) {
                // Word 파일이 선택된 경우
                addOption('pdf', 'PDF 문서');
            }
        }
    });

    function addOption(value, text) {
        const option = document.createElement('option');
        option.value = value;
        option.textContent = text;
        formatSelect.appendChild(option);
    }

    // 변환 처리
    convertForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        const file = fileInput.files[0];
        const format = formatSelect.value;

        if (!file || !format) {
            showStatus('파일과 변환 형식을 선택해주세요.', 'error');
            return;
        }

        try {
            progressBar.style.display = 'block';
            downloadLink.style.display = 'none';
            statusMessage.style.display = 'none';
            let result;

            if (file.type === 'application/pdf') {
                // PDF 변환
                if (format === 'docx') {
                    result = await PDFConverter.pdfToWord(file);
                } else if (format === 'hwp') {
                    result = await PDFConverter.pdfToHwp(file);
                } else if (['jpg', 'png'].includes(format)) {
                    result = await PDFConverter.pdfToImage(file, format);
                }
            } else if (file.type.startsWith('image/')) {
                // 이미지 변환
                result = await PDFConverter.imageToPDF(file);
            } else if (file.name.endsWith('.hwp')) {
                // HWP 변환
                result = await PDFConverter.hwpToPdf(file);
            }

            if (result instanceof Blob) {
                const url = URL.createObjectURL(result);
                downloadLink.href = url;
                downloadLink.download = `${file.name.split('.')[0]}.${format}`;
                downloadLink.style.display = 'block';
                showStatus('변환이 완료되었습니다!', 'success');
            } else {
                throw new Error('변환 결과가 올바르지 않습니다.');
            }
        } catch (error) {
            console.error('Conversion failed:', error);
            showStatus('변환 중 오류가 발생했습니다: ' + error.message, 'error');
        } finally {
            progressBar.style.display = 'none';
        }
    });

    function showStatus(message, type) {
        statusMessage.textContent = message;
        statusMessage.className = `alert ${type === 'error' ? 'alert-danger' : 'alert-success'} mt-3`;
        statusMessage.style.display = 'block';
    }
}); 