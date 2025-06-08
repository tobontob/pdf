// PDF.js와 jsPDF는 전역 변수로 사용
const pdfjsLib = window['pdfjs-dist/build/pdf'];
const { jsPDF } = window.jspdf;

// PDF.js 워커 및 CMap 설정
pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
const CMAP_URL = 'https://cdn.jsdelivr.net/npm/pdfjs-dist@3.11.174/cmaps/';
const CMAP_PACKED = true;

class PDFConverter {
    // PDF를 이미지로 변환
    static async pdfToImage(pdfFile, format = 'jpeg') {
        try {
            const arrayBuffer = await pdfFile.arrayBuffer();
            const pdf = await pdfjsLib.getDocument({
                data: arrayBuffer,
                cMapUrl: CMAP_URL,
                cMapPacked: CMAP_PACKED
            }).promise;
            const page = await pdf.getPage(1);
            const viewport = page.getViewport({ scale: 1.5 });

            const canvas = document.createElement('canvas');
            const context = canvas.getContext('2d');
            canvas.height = viewport.height;
            canvas.width = viewport.width;

            await page.render({
                canvasContext: context,
                viewport: viewport
            }).promise;

            return canvas.toDataURL(`image/${format}`, 1.0);
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

    // PDF를 Word로 변환 (docx 변환용)
    static async pdfToWord(pdfFile) {
        try {
            const text = await this.pdfToText(pdfFile);
            
            // docxtemplater 사용하여 Word 문서 생성
            const zip = new PizZip();
            
            // 기본 Word 문서 템플릿 생성
            zip.file("word/document.xml", 
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>' +
                '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">' +
                '<w:body><w:p><w:r><w:t>' + text.replace(/[<>&]/g, function(c) {
                    return c === '<' ? '&lt;' : c === '>' ? '&gt;' : '&amp;';
                }) + '</w:t></w:r></w:p></w:body></w:document>'
            );
            
            // 필수 Word 문서 구조 파일들 추가
            zip.file("[Content_Types].xml",
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>' +
                '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">' +
                '<Default Extension="xml" ContentType="application/xml"/>' +
                '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>' +
                '</Types>'
            );
            
            zip.file("_rels/.rels",
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>' +
                '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">' +
                '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>' +
                '</Relationships>'
            );
            
            // Word 문서를 Blob으로 생성
            const blob = zip.generate({
                type: "blob",
                mimeType: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                compression: "DEFLATE"
            });

            return blob;
        } catch (error) {
            console.error('PDF to Word conversion failed:', error);
            throw error;
        }
    }

    // 이미지를 PDF로 변환
    static async imageToPDF(imageFile) {
        try {
            return new Promise((resolve, reject) => {
                const reader = new FileReader();
                reader.onload = function(event) {
                    const img = new Image();
                    img.src = event.target.result;
                    
                    img.onload = function() {
                        try {
                            const doc = new jsPDF({
                                orientation: img.width > img.height ? 'landscape' : 'portrait',
                                unit: 'px'
                            });

                            const pdfWidth = doc.internal.pageSize.getWidth();
                            const pdfHeight = doc.internal.pageSize.getHeight();

                            const ratio = Math.min(pdfWidth / img.width, pdfHeight / img.height);
                            const width = img.width * ratio;
                            const height = img.height * ratio;
                            const x = (pdfWidth - width) / 2;
                            const y = (pdfHeight - height) / 2;

                            doc.addImage(img, 'JPEG', x, y, width, height);
                            resolve(doc.output('blob'));
                        } catch (error) {
                            reject(error);
                        }
                    };
                    
                    img.onerror = reject;
                };
                reader.onerror = reject;
                reader.readAsDataURL(imageFile);
            });
        } catch (error) {
            console.error('Image to PDF conversion failed:', error);
            throw error;
        }
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
    static async wordToPDF(wordFile) {
        try {
            const arrayBuffer = await wordFile.arrayBuffer();
            const result = await window.mammoth.extractRawText({ arrayBuffer });
            return await this.textToPDF(result.value);
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

    // 파일 형식에 따라 변환 옵션 업데이트
    fileInput.addEventListener('change', function() {
        const file = this.files[0];
        formatSelect.innerHTML = ''; // 기존 옵션 초기화
        
        if (file) {
            if (file.type === 'application/pdf') {
                // PDF 파일이 선택된 경우
                addOption('jpg', 'JPG 이미지');
                addOption('png', 'PNG 이미지');
                addOption('webp', 'WebP 이미지');
                addOption('docx', 'Word 문서');
                addOption('txt', '텍스트 문서');
            } else if (file.type.startsWith('image/')) {
                // 이미지 파일이 선택된 경우
                addOption('pdf', 'PDF 문서');
            } else if (file.type.includes('word') || file.type === 'text/plain') {
                // 문서 파일이 선택된 경우
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
    convertForm.onsubmit = async function(e) {
        e.preventDefault();
        const file = fileInput.files[0];
        const format = formatSelect.value;

        if (!file || !format) {
            alert('파일과 변환 형식을 선택해주세요.');
            return;
        }

        try {
            progressBar.style.display = 'block';
            downloadLink.style.display = 'none';
            let result;

            if (file.type === 'application/pdf') {
                // PDF 변환
                if (['jpg', 'png', 'webp'].includes(format)) {
                    result = await PDFConverter.pdfToImage(file, format);
                    const response = await fetch(result);
                    result = await response.blob();
                } else if (format === 'docx') {
                    result = await PDFConverter.pdfToWord(file);
                } else if (format === 'txt') {
                    const text = await PDFConverter.pdfToText(file);
                    result = new Blob([text], { type: 'text/plain' });
                }
            } else if (file.type.startsWith('image/')) {
                // 이미지 변환
                result = await PDFConverter.imageToPDF(file);
            } else if (file.type.includes('word')) {
                // Word 문서 변환
                result = await PDFConverter.wordToPDF(file);
            } else if (file.type === 'text/plain') {
                // 텍스트 문서 변환
                const text = await file.text();
                result = await PDFConverter.textToPDF(text);
            }

            const url = URL.createObjectURL(result);
            downloadLink.href = url;
            downloadLink.download = `converted.${format}`;
            downloadLink.style.display = 'block';
            downloadLink.click();

        } catch (error) {
            console.error('Conversion failed:', error);
            alert('변환 중 오류가 발생했습니다: ' + error.message);
        } finally {
            progressBar.style.display = 'none';
        }
    };
}); 