// 디버그 로깅 함수
function debug(message, data = null) {
    console.log(`[Debug] ${message}`, data || '');
}

// DOM이 로드된 후 실행
document.addEventListener('DOMContentLoaded', function() {
    debug('main.js 로드됨');
    
    // 파일 업로드 초기화
    initializeFileUploads();
    
    // Bootstrap 컴포넌트 초기화
    initializeBootstrapComponents();
    
    // AJAX 폼 초기화
    initializeAjaxForms();
});

// 파일 업로드 초기화
function initializeFileUploads() {
    debug('파일 업로드 초기화 시작');
    
    // 파일 업로드 영역 선택
    const fileUploads = document.querySelectorAll('.file-upload');
    const count = fileUploads.length;
    debug(`파일 업로드 요소 찾음: ${count}개`);
    
    if (!count) {
        debug('파일 업로드 요소를 찾을 수 없음');
        return;
    }
    
    fileUploads.forEach((upload, index) => {
        debug(`파일 업로드 요소 ${index + 1} 초기화 시작`);
        setupDropZone(upload);
        debug(`파일 업로드 요소 ${index + 1} 초기화 완료`);
    });
}

// 드롭존 설정
function setupDropZone(dropZone) {
    const input = dropZone.querySelector('input[type="file"]');
    const display = dropZone.querySelector('.file-name-display');
    
    if (!input || !display) {
        debug('드롭존 필수 요소 누락', { input, display });
        return;
    }
    
    debug('드롭존 설정', dropZone.id || '익명');
    
    // 파일 선택 이벤트
    input.addEventListener('change', function(e) {
        e.stopPropagation();
        debug('파일 선택됨', this.files);
        if (this.files.length > 0) {
            const totalSize = Array.from(this.files).reduce((sum, file) => sum + file.size, 0);
            const maxSize = 16 * 1024 * 1024; // 16MB
            
            if (totalSize > maxSize) {
                display.textContent = '파일 크기가 너무 큽니다 (최대 16MB)';
                display.style.color = 'red';
                this.value = ''; // 파일 선택 초기화
                return;
            }
        }
        handleFiles(this.files, display);
    });
    
    // 드래그 앤 드롭 이벤트
    dropZone.addEventListener('dragenter', function(e) {
        e.preventDefault();
        e.stopPropagation();
        this.classList.add('dragover');
        debug('드래그 진입');
    });
    
    dropZone.addEventListener('dragover', function(e) {
        e.preventDefault();
        e.stopPropagation();
        if (!this.classList.contains('dragover')) {
            this.classList.add('dragover');
        }
    });
    
    dropZone.addEventListener('dragleave', function(e) {
        e.preventDefault();
        e.stopPropagation();
        
        // 실제로 드롭존을 벗어났는지 확인
        const rect = this.getBoundingClientRect();
        const x = e.clientX;
        const y = e.clientY;
        
        if (x <= rect.left || x >= rect.right || y <= rect.top || y >= rect.bottom) {
            this.classList.remove('dragover');
            debug('드래그 떠남');
        }
    });
    
    dropZone.addEventListener('drop', function(e) {
        e.preventDefault();
        e.stopPropagation();
        this.classList.remove('dragover');
        
        const files = e.dataTransfer.files;
        debug('파일 드롭됨', files);
        
        if (files.length > 0) {
            const totalSize = Array.from(files).reduce((sum, file) => sum + file.size, 0);
            const maxSize = 16 * 1024 * 1024; // 16MB
            
            if (totalSize > maxSize) {
                display.textContent = '파일 크기가 너무 큽니다 (최대 16MB)';
                display.style.color = 'red';
                return;
            }
            
            input.files = files;
            handleFiles(files, display);
        }
    });
    
    // 클릭 이벤트
    dropZone.addEventListener('click', function(e) {
        // input 요소나 버튼을 클릭한 경우 무시
        if (e.target !== this && !e.target.matches('i, p')) {
            return;
        }
        
        debug('드롭존 클릭됨');
        input.click();
        e.preventDefault();
    });
}

// 파일 처리
function handleFiles(files, display) {
    if (files.length > 0) {
        const fileNames = Array.from(files).map(file => file.name).join(', ');
        display.textContent = fileNames;
        display.style.display = 'block';
        display.style.color = ''; // 색상 초기화
        debug('파일 이름 표시됨', fileNames);
    } else {
        display.textContent = '';
        display.style.display = 'none';
        debug('파일 이름 지워짐');
    }
}

// Bootstrap 컴포넌트 초기화
function initializeBootstrapComponents() {
    debug('Bootstrap 컴포넌트 초기화 시작');
    
    try {
        // Alert 자동 닫기
        const alerts = document.querySelectorAll('.alert');
        alerts.forEach(alert => {
            new bootstrap.Alert(alert);
        });
        
        // Tooltip 초기화
        const tooltips = document.querySelectorAll('[data-bs-toggle="tooltip"]');
        tooltips.forEach(tooltip => {
            new bootstrap.Tooltip(tooltip);
        });
        
        debug('Bootstrap 컴포넌트 초기화 완료');
    } catch (error) {
        debug('Bootstrap 컴포넌트 초기화 오류', error);
    }
}

// AJAX 폼 초기화
function initializeAjaxForms() {
    const forms = document.querySelectorAll('form[data-ajax="true"]');
    debug('AJAX 폼 초기화', forms);
    
    forms.forEach(form => {
        form.addEventListener('submit', handleFormSubmit);
    });
}

// 폼 제출 처리
async function handleFormSubmit(e) {
    e.preventDefault();
    const form = e.target;
    debug('폼 제출 시작', form);
    
    const formData = new FormData(form);
    const submitButton = form.querySelector('button[type="submit"]');
    const progressBar = document.querySelector('.progress');
    const progressBarInner = progressBar.querySelector('.progress-bar');
    const statusDiv = document.getElementById('conversionStatus');
    
    if (!progressBar || !progressBarInner || !statusDiv) {
        debug('진행 상태 표시 요소 누락');
        return;
    }

    // 파일 크기 검증
    const fileInput = form.querySelector('input[type="file"]');
    if (fileInput && fileInput.files.length > 0) {
        const file = fileInput.files[0];
        const maxSize = 16 * 1024 * 1024; // 16MB
        if (file.size > maxSize) {
            statusDiv.textContent = '파일 크기가 16MB를 초과합니다. 더 작은 파일을 선택해 주세요.';
            statusDiv.className = 'error';
            return;
        }
    }
    
    try {
        // UI 업데이트
        submitButton.disabled = true;
        progressBar.style.display = 'block';
        progressBarInner.style.width = '50%';
        statusDiv.textContent = '변환 중...';
        statusDiv.className = '';
        
        // 서버 요청
        const response = await fetch(form.action, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.message || '서버 오류가 발생했습니다.');
        }
        
        const result = await response.json();
        
        // 성공 처리
        progressBarInner.style.width = '100%';
        statusDiv.textContent = '변환이 완료되었습니다!';
        statusDiv.className = 'success';
        
        if (result.download_url) {
            window.location.href = result.download_url;
        }
    } catch (error) {
        // 오류 처리
        debug('폼 제출 오류', error);
        statusDiv.textContent = '오류가 발생했습니다: ' + error.message;
        statusDiv.className = 'error';
        progressBarInner.style.width = '0%';
    } finally {
        // 정리
        submitButton.disabled = false;
        setTimeout(() => {
            progressBar.style.display = 'none';
            progressBarInner.style.width = '0%';
        }, 3000);
    }
}

 