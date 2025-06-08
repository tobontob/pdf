// PDF.js와 jsPDF 라이브러리 import
import * as pdfjsLib from 'pdfjs-dist';
import { jsPDF } from 'jspdf';

// PDF.js 워커 설정
pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';

class PDFConverter {
    // PDF를 이미지로 변환
    static async pdfToImage(pdfFile, format = 'jpeg') {
        try {
            const arrayBuffer = await pdfFile.arrayBuffer();
            const pdf = await pdfjsLib.getDocument(arrayBuffer).promise;
            const page = await pdf.getPage(1);
            const viewport = page.getViewport({ scale: 1.5 });

            // Canvas 생성
            const canvas = document.createElement('canvas');
            const context = canvas.getContext('2d');
            canvas.height = viewport.height;
            canvas.width = viewport.width;

            // PDF 페이지를 Canvas에 렌더링
            await page.render({
                canvasContext: context,
                viewport: viewport
            }).promise;

            // Canvas를 이미지로 변환
            return canvas.toDataURL(`image/${format}`, 1.0);
        } catch (error) {
            console.error('PDF to Image conversion failed:', error);
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

                            // 이미지 크기를 PDF 페이지에 맞게 조정
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

// 이벤트 핸들러 설정
document.addEventListener('DOMContentLoaded', function() {
    const convertForm = document.getElementById('convertForm');
    const fileInput = document.getElementById('fileInput');
    const formatSelect = document.getElementById('formatSelect');
    const convertButton = document.getElementById('convertButton');
    const progressBar = document.getElementById('progressBar');
    const downloadLink = document.getElementById('downloadLink');

    if (convertForm) {
        convertForm.onsubmit = async function(e) {
            e.preventDefault();
            const file = fileInput.files[0];
            const format = formatSelect.value;

            if (!file) {
                alert('파일을 선택해주세요.');
                return;
            }

            try {
                progressBar.style.display = 'block';
                let result;

                if (file.type === 'application/pdf') {
                    // PDF를 이미지로 변환
                    if (format === 'jpg' || format === 'png') {
                        result = await PDFConverter.pdfToImage(file, format);
                        // 데이터 URL을 Blob으로 변환
                        const response = await fetch(result);
                        const blob = await response.blob();
                        // 다운로드 링크 생성
                        const url = URL.createObjectURL(blob);
                        downloadLink.href = url;
                        downloadLink.download = `converted.${format}`;
                    }
                } else if (file.type.startsWith('image/')) {
                    // 이미지를 PDF로 변환
                    result = await PDFConverter.imageToPDF(file);
                    const url = URL.createObjectURL(result);
                    downloadLink.href = url;
                    downloadLink.download = 'converted.pdf';
                }

                progressBar.style.display = 'none';
                downloadLink.style.display = 'block';
                downloadLink.click(); // 자동 다운로드 시작

            } catch (error) {
                console.error('Conversion failed:', error);
                alert('변환 중 오류가 발생했습니다: ' + error.message);
                progressBar.style.display = 'none';
            }
        };
    }
}); 