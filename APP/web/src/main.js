// ============================================================
// 错题管理系统 - Tauri 客户端
// ============================================================

const App = {
  // 配置
  serverUrl: 'http://localhost:8100',
  apiKey: '',
  selectedFiles: [],
  currentTaskId: null,
  currentQuestionId: null,
  pollingTimer: null,
  currentPage: 1,
  pageSize: 20,
  selectedQuestions: new Set(),
  _blobUrls: [],  // 跟踪已创建的 blob URL 以便释放

  // 释放所有已跟踪的 blob URL
  revokeBlobUrls() {
    this._blobUrls.forEach(url => URL.revokeObjectURL(url));
    this._blobUrls = [];
  },

  // 初始化
  init() {
    this.loadSettings();
    this.bindEvents();
    this.createServerToast();
    this.checkConnection();
    this.startAutoCheck();
  },

  // ========================
  // 工具函数
  // ========================

  api(path) {
    return `${this.serverUrl}${path}`;
  },

  async fetchApi(path, options = {}) {
    const url = this.api(path);
    const headers = options.headers || {};
    if (this.apiKey) {
      headers['Authorization'] = `Bearer ${this.apiKey}`;
    }
    const resp = await fetch(url, { ...options, headers, signal: AbortSignal.timeout(30000) });
    if (!resp.ok) {
      const body = await resp.json().catch(() => ({}));
      throw new Error(body.error || body.detail || `HTTP ${resp.status}`);
    }
    return resp;
  },

  formatSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  },

  formatDate(dateStr) {
    if (!dateStr) return '-';
    const d = new Date(dateStr);
    return d.toLocaleString('zh-CN', {
      month: '2-digit', day: '2-digit',
      hour: '2-digit', minute: '2-digit'
    });
  },

  formatUptime(seconds) {
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    if (h > 0) return `${h}小时${m}分钟`;
    return `${m}分钟`;
  },

  escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  },

  // 将后端返回的图片路径转换为可访问的 URL
  imageUrl(path) {
    if (!path) return '';
    // 已经是完整 URL 或 data URI
    if (path.startsWith('http') || path.startsWith('data:') || path.startsWith('blob:')) return path;
    // 处理 processed 路径: "./processed\\layout\\xxx.jpeg" → "/processed/layout/xxx.jpeg"
    let normalized = path.replace(/^\.\/processed[\\\/]/, '/processed/').replace(/\\/g, '/');
    // 如果只是文件名（没有路径前缀），加上 /uploads/
    if (!normalized.startsWith('/')) {
      normalized = '/uploads/' + normalized;
    }
    return this.serverUrl + normalized;
  },

  // 简单 Markdown 渲染（含 XSS 防护）
  renderMarkdown(md) {
    if (!md) return '<p style="color:#9ca3af">暂无识别结果</p>';
    let html = this.escapeHtml(md);
    // Headers
    html = html.replace(/^### (.+)$/gm, '<h4>$1</h4>');
    html = html.replace(/^## (.+)$/gm, '<h3>$1</h3>');
    html = html.replace(/^# (.+)$/gm, '<h2>$1</h2>');
    // Bold & italic
    html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');
    // Images — 仅允许 http/https/data 协议
    html = html.replace(/!\[([^\]]*)\]\(([^)]+)\)/g, (match, alt, url) => {
      const trimmed = url.trim();
      if (/^(https?:|data:image\/)/i.test(trimmed) && !/["'<>]/.test(trimmed)) {
        return `<img src="${trimmed}" alt="${this.escapeHtml(alt)}" style="max-width:100%">`;
      }
      return match; // 不安全的协议或含危险字符，保留原始文本
    });
    // Links — 仅允许 http/https 协议，添加 noopener
    html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, (match, text, url) => {
      const trimmed = url.trim();
      if (/^https?:\/\//i.test(trimmed)) {
        return `<a href="${trimmed}" target="_blank" rel="noopener noreferrer">${text}</a>`;
      }
      return match; // 不安全的协议，保留原始文本
    });
    // Lists
    html = html.replace(/^- (.+)$/gm, '<li>$1</li>');
    html = html.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');
    // Horizontal rules
    html = html.replace(/^---$/gm, '<hr>');
    // Line breaks handled by CSS white-space: pre-wrap
    return html;
  },

  // ========================
  // Toast 通知
  // ========================

  createServerToast() {
    if (!document.querySelector('.toast-container')) {
      const container = document.createElement('div');
      container.className = 'toast-container';
      document.body.appendChild(container);
    }
  },

  toast(message, type = 'info') {
    const container = document.querySelector('.toast-container');
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transition = 'opacity 0.3s';
      setTimeout(() => toast.remove(), 300);
    }, 3000);
  },

  // ========================
  // 设置
  // ========================

  loadSettings() {
    try {
      const saved = localStorage.getItem('cuoti-settings');
      if (saved) {
        const s = JSON.parse(saved);
        if (s.serverUrl) {
          try {
            const parsed = new URL(s.serverUrl);
            if (['http:', 'https:'].includes(parsed.protocol)) {
              this.serverUrl = s.serverUrl;
            }
          } catch { /* ignore invalid saved URL */ }
        }
        if (s.apiKey) {
          this.apiKey = s.apiKey;
        }
        if (s.defaultVl !== undefined) {
          document.getElementById('input-default-vl').checked = s.defaultVl;
        }
      }
    } catch (e) { /* ignore */ }
    this.updateServerDisplay();
  },

  updateServerDisplay() {
    const el = document.getElementById('server-url-display');
    if (el) {
      // 仅当不是默认 localhost 时才显示服务器地址
      const display = this.serverUrl !== 'http://localhost:8100' ? this.serverUrl : '';
      el.textContent = display;
      el.title = display ? `当前服务器: ${display}` : '';
    }
  },

  saveSettingsData() {
    const data = {
      serverUrl: this.serverUrl,
      apiKey: this.apiKey,
      defaultVl: document.getElementById('input-default-vl').checked
    };
    localStorage.setItem('cuoti-settings', JSON.stringify(data));
  },

  // ========================
  // 连接检测
  // ========================

  async checkConnection() {
    const badge = document.getElementById('server-status');
    try {
      const resp = await fetch(this.api('/health'), {
        signal: AbortSignal.timeout(5000)
      });
      if (resp.ok) {
        badge.textContent = '已连接';
        badge.className = 'status-badge status-connected';
        this.updateServerDisplay();
        return true;
      }
    } catch (e) { /* ignore */ }
    badge.textContent = '未连接';
    badge.className = 'status-badge status-disconnected';
    this.updateServerDisplay();
    return false;
  },

  startAutoCheck() {
    setInterval(() => this.checkConnection(), 30000);
  },

  // ========================
  // 事件绑定
  // ========================

  bindEvents() {
    // 导航
    document.querySelectorAll('.nav-item').forEach(item => {
      item.addEventListener('click', () => this.switchPage(item.dataset.page));
    });

    // 上传区域
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');

    dropZone.addEventListener('click', () => fileInput.click());
    dropZone.addEventListener('dragover', (e) => {
      e.preventDefault();
      dropZone.classList.add('dragover');
    });
    dropZone.addEventListener('dragleave', () => {
      dropZone.classList.remove('dragover');
    });
    dropZone.addEventListener('drop', (e) => {
      e.preventDefault();
      dropZone.classList.remove('dragover');
      this.handleFiles(e.dataTransfer.files);
    });
    fileInput.addEventListener('change', (e) => {
      this.handleFiles(e.target.files);
      fileInput.value = '';
    });

    // 上传操作
    document.getElementById('btn-start-ocr').addEventListener('click', () => this.startOcr());
    document.getElementById('btn-clear-files').addEventListener('click', () => this.clearFiles());
    document.getElementById('btn-save-question').addEventListener('click', () => this.saveQuestion());
    document.getElementById('btn-download-md').addEventListener('click', () => this.downloadMarkdown());
    document.getElementById('btn-download-zip').addEventListener('click', () => this.downloadZip());
    document.getElementById('btn-new-upload').addEventListener('click', () => this.resetUpload());

    // 错题本
    document.getElementById('filter-status').addEventListener('change', () => {
      this.currentPage = 1;
      this.loadQuestions();
    });
    document.getElementById('btn-batch-export').addEventListener('click', () => this.batchExport());

    // 统计
    document.getElementById('btn-refresh-stats').addEventListener('click', () => this.loadStats());

    // 设置弹窗
    document.getElementById('btn-settings').addEventListener('click', () => this.openSettings());
    document.getElementById('btn-close-settings').addEventListener('click', () => this.closeSettings());
    document.getElementById('btn-save-settings').addEventListener('click', () => this.applySettings());
    document.getElementById('btn-cancel-settings').addEventListener('click', () => this.closeSettings());
    document.querySelector('#settings-modal .modal-overlay').addEventListener('click', () => this.closeSettings());

    // 详情弹窗
    document.getElementById('btn-close-detail').addEventListener('click', () => this.closeDetail());
    document.getElementById('btn-detail-download-zip').addEventListener('click', () => this.downloadDetailZip());
    document.getElementById('btn-detail-export-md').addEventListener('click', () => this.exportDetailMarkdown());
    document.getElementById('btn-detail-export-pdf').addEventListener('click', () => this.exportDetailPdf());
    document.getElementById('btn-detail-delete').addEventListener('click', () => this.deleteCurrentQuestion());
    document.querySelector('#detail-modal .modal-overlay').addEventListener('click', () => this.closeDetail());

    // Escape 关闭弹窗
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        this.closeSettings();
        this.closeDetail();
      }
    });

    // 设置输入框回车提交
    document.getElementById('input-server-url').addEventListener('keydown', (e) => {
      if (e.key === 'Enter') this.applySettings();
    });
  },

  // ========================
  // 页面切换
  // ========================

  switchPage(pageName) {
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));

    document.querySelector(`[data-page="${pageName}"]`).classList.add('active');
    document.getElementById(`page-${pageName}`).classList.add('active');

    if (pageName === 'questions') this.loadQuestions();
    if (pageName === 'stats') this.loadStats();
  },

  // ========================
  // 文件上传
  // ========================

  handleFiles(fileList) {
    const allowed = ['image/jpeg', 'image/png', 'image/bmp', 'image/tiff', 'image/webp'];
    for (const file of fileList) {
      if (!allowed.includes(file.type)) {
        this.toast(`不支持的文件格式: ${file.name}`, 'error');
        continue;
      }
      if (file.size > 10 * 1024 * 1024) {
        this.toast(`文件过大: ${file.name}`, 'error');
        continue;
      }
      this.selectedFiles.push(file);
    }
    this.renderFileList();
  },

  renderFileList() {
    const preview = document.getElementById('upload-preview');
    const fileList = document.getElementById('file-list');

    // 释放旧的 blob URL
    this.revokeBlobUrls();

    if (this.selectedFiles.length === 0) {
      preview.style.display = 'none';
      return;
    }

    preview.style.display = 'block';
    fileList.innerHTML = '';

    this.selectedFiles.forEach((file, index) => {
      const item = document.createElement('div');
      item.className = 'file-item';

      const thumbUrl = URL.createObjectURL(file);
      this._blobUrls.push(thumbUrl);  // 跟踪以便释放
      item.innerHTML = `
        <div class="file-info">
          <img class="file-thumb" src="${thumbUrl}" alt="">
          <div>
            <div class="file-name">${this.escapeHtml(file.name)}</div>
            <div class="file-size">${this.formatSize(file.size)}</div>
          </div>
        </div>
        <button class="file-remove" data-index="${index}">&times;</button>
      `;
      fileList.appendChild(item);
    });

    fileList.querySelectorAll('.file-remove').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const idx = parseInt(e.target.dataset.index);
        this.selectedFiles.splice(idx, 1);
        this.renderFileList();
      });
    });
  },

  clearFiles() {
    this.selectedFiles = [];
    this.renderFileList();
  },

  resetUpload() {
    this.revokeBlobUrls();
    this.selectedFiles = [];
    this.currentTaskId = null;
    this.currentQuestionId = null;
    document.getElementById('result-area').style.display = 'none';
    document.getElementById('processing-area').style.display = 'none';
    document.getElementById('upload-preview').style.display = 'none';
    document.getElementById('drop-zone').style.display = 'block';
  },

  // ========================
  // OCR 处理
  // ========================

  async startOcr() {
    if (this.selectedFiles.length === 0) return;

    const useVl = document.getElementById('chk-use-vl').checked;

    // 隐藏上传区域，显示处理中
    document.getElementById('drop-zone').style.display = 'none';
    document.getElementById('upload-preview').style.display = 'none';
    document.getElementById('result-area').style.display = 'none';
    document.getElementById('processing-area').style.display = 'block';

    const progressFill = document.getElementById('progress-fill');
    const processingText = document.getElementById('processing-text');
    progressFill.style.width = '0%';
    processingText.textContent = '正在上传图片...';

    try {
      // 上传第一个文件（简化为单文件处理）
      const file = this.selectedFiles[0];
      const formData = new FormData();
      formData.append('file', file);

      processingText.textContent = '正在上传图片...';
      progressFill.style.width = '10%';

      const uploadResp = await this.fetchApi('/api/v1/upload/image', {
        method: 'POST',
        body: formData
      });
      const uploadData = await uploadResp.json();
      const fileId = uploadData.file_id;

      // 启动 OCR
      processingText.textContent = '正在识别中，请稍候...';
      progressFill.style.width = '30%';

      const ocrResp = await this.fetchApi('/api/v1/ocr/process', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          file_id: fileId,
          use_vl: useVl
        })
      });
      const ocrData = await ocrResp.json();
      this.currentTaskId = ocrData.task_id;

      // 轮询状态
      this.pollTaskStatus(file);

    } catch (error) {
      this.toast(`处理失败: ${error.message}`, 'error');
      this.resetUpload();
    }
  },

  pollTaskStatus(originalFile) {
    if (this.pollingTimer) clearInterval(this.pollingTimer);

    const progressFill = document.getElementById('progress-fill');
    const processingText = document.getElementById('processing-text');
    let pollCount = 0;
    let transientErrors = 0;
    const maxPolls = 150; // 最多轮询 150 次 (2秒 × 150 = 5 分钟)
    const maxTransientErrors = 3;

    this.pollingTimer = setInterval(async () => {
      pollCount++;
      if (pollCount > maxPolls) {
        clearInterval(this.pollingTimer);
        this.pollingTimer = null;
        this.toast('处理超时，请检查后端状态', 'error');
        this.resetUpload();
        return;
      }

      try {
        const resp = await this.fetchApi(`/api/v1/ocr/status/${this.currentTaskId}`);
        const data = await resp.json();
        transientErrors = 0; // Reset on success

        if (data.status === 'completed') {
          clearInterval(this.pollingTimer);
          this.pollingTimer = null;
          progressFill.style.width = '100%';
          processingText.textContent = '识别完成!';

          // 获取详情
          if (data.question_id) {
            this.currentQuestionId = data.question_id;
            await this.showResult(data.question_id, originalFile);
          }
        } else if (data.status === 'failed') {
          clearInterval(this.pollingTimer);
          this.pollingTimer = null;
          this.toast(`识别失败: ${data.error || data.message}`, 'error');
          this.resetUpload();
        } else {
          // 处理中 - 渐进进度
          const progress = data.progress >= 0 ? data.progress : 50;
          progressFill.style.width = `${30 + progress * 0.6}%`;
          processingText.textContent = `正在识别中... ${progress >= 0 ? progress + '%' : ''}`;
        }
      } catch (error) {
        transientErrors++;
        const isServerError = error.message && error.message.startsWith('HTTP');
        if (isServerError || transientErrors >= maxTransientErrors) {
          clearInterval(this.pollingTimer);
          this.pollingTimer = null;
          this.toast(`查询状态失败: ${error.message}`, 'error');
          this.resetUpload();
        } else {
          console.warn(`[pollTaskStatus] 网络错误 (${transientErrors}/${maxTransientErrors}): ${error.message}`);
        }
      }
    }, 2000);
  },

  async showResult(questionId, originalFile) {
    try {
      const resp = await this.fetchApi(`/api/v1/questions/${questionId}`);
      const question = await resp.json();

      document.getElementById('processing-area').style.display = 'none';
      document.getElementById('result-area').style.display = 'block';

      // 显示原图
      const resultImg = document.getElementById('result-image');
      if (originalFile) {
        const blobUrl = URL.createObjectURL(originalFile);
        this._blobUrls.push(blobUrl);
        resultImg.src = blobUrl;
      } else if (question.original_image_path) {
        resultImg.src = this.imageUrl(question.original_image_path);
      }

      // 显示 Markdown
      const mdContent = document.getElementById('result-md-content');
      mdContent.innerHTML = this.renderMarkdown(question.ocr_result_md);

      // 显示版面分析图
      this.renderLayoutImages(question.layout_images || [], 'result-layout-images', 'result-layout-area');

      this.toast('识别完成!', 'success');
    } catch (error) {
      this.toast(`获取结果失败: ${error.message}`, 'error');
    }
  },

  async saveQuestion() {
    if (this.currentQuestionId) {
      this.switchPage('questions');
      this.toast('已添加到错题本', 'success');
    }
  },

  // 通用下载方法 — 兼容 Tauri WebView2
  async downloadFile(url, filename) {
    // 优先通过 Tauri Rust 侧下载（最可靠）
    if (window.__TAURI__) {
      try {
        const endpoint = url.replace(this.serverUrl, '');
        const savedPath = await window.__TAURI__.core.invoke('download_file', {
          serverUrl: this.serverUrl,
          apiKey: this.apiKey,
          endpoint: endpoint,
          filename: filename,
        });
        this.toast(`已保存到: ${savedPath}`, 'success');
        return;
      } catch (e) {
        console.warn('Rust download failed, trying JS fallback:', e);
      }
    }

    // 降级方案: JS fetch + blob + <a download>
    try {
      const headers = {};
      if (this.apiKey) headers['Authorization'] = `Bearer ${this.apiKey}`;
      const resp = await fetch(url, { headers });
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const blob = await resp.blob();
      const blobUrl = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = blobUrl;
      a.download = filename || '';
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(blobUrl);
      this.toast('下载已开始', 'success');
    } catch (err) {
      this.toast(`下载失败: ${err.message}`, 'error');
    }
  },

  downloadMarkdown() {
    if (!this.currentQuestionId) return;
    this.downloadFile(
      this.api(`/api/v1/reports/${this.currentQuestionId}/markdown`),
      `cuoti_${this.currentQuestionId}.md`
    );
  },

  // 下载归档 ZIP（上传结果页）
  downloadZip() {
    if (!this.currentQuestionId) return;
    this.downloadFile(
      this.api(`/api/v1/reports/${this.currentQuestionId}/download`),
      `cuoti_question_${this.currentQuestionId}.zip`
    );
  },

  // 下载归档 ZIP（详情弹窗）
  downloadDetailZip() {
    if (!this.currentQuestionId) return;
    this.downloadFile(
      this.api(`/api/v1/reports/${this.currentQuestionId}/download`),
      `cuoti_question_${this.currentQuestionId}.zip`
    );
  },

  // 渲染版面分析图片列表
  renderLayoutImages(layoutPaths, containerId, areaId) {
    const container = document.getElementById(containerId);
    const area = document.getElementById(areaId);

    if (!layoutPaths || layoutPaths.length === 0) {
      if (area) area.style.display = 'none';
      return;
    }

    container.innerHTML = '';
    layoutPaths.forEach(path => {
      const url = this.imageUrl(path);
      const figure = document.createElement('figure');
      figure.className = 'layout-item';
      const img = document.createElement('img');
      img.src = url;
      img.alt = '版面分析';
      img.loading = 'lazy';
      const caption = document.createElement('figcaption');
      caption.textContent = path.split(/[\\/]/).pop();
      figure.appendChild(img);
      figure.appendChild(caption);
      figure.addEventListener('click', () => window.open(url, '_blank', 'noopener,noreferrer'));
      container.appendChild(figure);
    });

    if (area) area.style.display = 'block';
  },

  // ========================
  // 错题本
  // ========================

  async loadQuestions() {
    const status = document.getElementById('filter-status').value;
    const container = document.getElementById('questions-list');

    let url = `/api/v1/questions/?page=${this.currentPage}&page_size=${this.pageSize}`;
    if (status) url += `&status=${status}`;

    try {
      const resp = await this.fetchApi(url);
      const data = await resp.json();

      if (!data.items || data.items.length === 0) {
        container.innerHTML = '<div class="empty-state"><p>暂无错题记录</p></div>';
        document.getElementById('questions-pagination').innerHTML = '';
        return;
      }

      container.innerHTML = '';
      this.selectedQuestions.clear();

      data.items.forEach(q => {
        const card = document.createElement('div');
        card.className = 'question-card';
        card.dataset.id = q.id;

        const statusClass = `status-${q.status}`;
        const statusText = { completed: '已完成', processing: '处理中', pending: '待处理', failed: '失败' }[q.status] || q.status;
        const tags = (q.tags || []).map(t => `<span class="tag">${this.escapeHtml(t)}</span>`).join('');
        const fileName = q.original_image_path
          ? q.original_image_path.split(/[\\/]/).pop()
          : `题目 #${q.id}`;

        card.innerHTML = `
          <input type="checkbox" class="question-checkbox" data-id="${q.id}">
          <img class="question-thumb" src="${this.imageUrl(q.original_image_path)}" alt="">
          <div class="question-info">
            <div class="question-title">${this.escapeHtml(fileName)}</div>
            <div class="question-meta">
              <span class="status-badge ${statusClass}">${statusText}</span>
              <span>${this.formatDate(q.created_at)}</span>
            </div>
            ${tags ? `<div class="question-tags">${tags}</div>` : ''}
          </div>
        `;

        const thumbImg = card.querySelector('.question-thumb');
        thumbImg.addEventListener('error', function() { this.style.display = 'none'; });

        card.addEventListener('click', (e) => {
          if (e.target.type === 'checkbox') return;
          this.openDetail(q.id);
        });

        const cb = card.querySelector('.question-checkbox');
        cb.addEventListener('change', (e) => {
          if (e.target.checked) {
            this.selectedQuestions.add(q.id);
          } else {
            this.selectedQuestions.delete(q.id);
          }
        });

        container.appendChild(card);
      });

      // 分页
      this.renderPagination(data.total, data.page, data.page_size);

    } catch (error) {
      container.innerHTML = `<div class="empty-state"><p>加载失败: ${this.escapeHtml(error.message)}</p></div>`;
    }
  },

  renderPagination(total, currentPage, pageSize) {
    const container = document.getElementById('questions-pagination');
    const totalPages = Math.ceil(total / pageSize);

    if (totalPages <= 1) {
      container.innerHTML = '';
      return;
    }

    container.innerHTML = '';

    // 上一页
    if (currentPage > 1) {
      const btn = document.createElement('button');
      btn.textContent = '<';
      btn.addEventListener('click', () => { this.currentPage--; this.loadQuestions(); });
      container.appendChild(btn);
    }

    // 页码
    const start = Math.max(1, currentPage - 2);
    const end = Math.min(totalPages, currentPage + 2);

    for (let i = start; i <= end; i++) {
      const btn = document.createElement('button');
      btn.textContent = i;
      if (i === currentPage) btn.className = 'active';
      btn.addEventListener('click', () => { this.currentPage = i; this.loadQuestions(); });
      container.appendChild(btn);
    }

    // 下一页
    if (currentPage < totalPages) {
      const btn = document.createElement('button');
      btn.textContent = '>';
      btn.addEventListener('click', () => { this.currentPage++; this.loadQuestions(); });
      container.appendChild(btn);
    }
  },

  // ========================
  // 题目详情
  // ========================

  async openDetail(questionId) {
    try {
      const resp = await this.fetchApi(`/api/v1/questions/${questionId}`);
      const q = await resp.json();
      this.currentQuestionId = questionId;

      document.getElementById('detail-img').src = this.imageUrl(q.original_image_path);
      document.getElementById('detail-img').onerror = function() { this.style.display = 'none'; };
      document.getElementById('detail-id').textContent = `#${q.id}`;
      document.getElementById('detail-date').textContent = this.formatDate(q.created_at);

      const statusBadge = document.getElementById('detail-status');
      const statusText = { completed: '已完成', processing: '处理中', pending: '待处理', failed: '失败' }[q.status] || q.status;
      statusBadge.textContent = statusText;
      statusBadge.className = `status-badge status-${q.status}`;

      // Tags
      const tagsContainer = document.getElementById('detail-tags');
      tagsContainer.innerHTML = (q.tags || []).map(t =>
        `<span class="tag">${this.escapeHtml(t)}</span>`
      ).join('');

      // Markdown content
      document.getElementById('detail-md').innerHTML = this.renderMarkdown(q.ocr_result_md);

      // Layout images
      this.renderLayoutImages(q.layout_images || [], 'detail-layout-images', 'detail-layout-area');

      document.getElementById('detail-modal').style.display = 'flex';
    } catch (error) {
      this.toast(`获取详情失败: ${error.message}`, 'error');
    }
  },

  closeDetail() {
    document.getElementById('detail-modal').style.display = 'none';
  },

  exportDetailMarkdown() {
    if (!this.currentQuestionId) return;
    this.downloadFile(
      this.api(`/api/v1/reports/${this.currentQuestionId}/markdown`),
      `cuoti_${this.currentQuestionId}.md`
    );
  },

  exportDetailPdf() {
    if (!this.currentQuestionId) return;
    this.downloadFile(
      this.api(`/api/v1/reports/${this.currentQuestionId}/pdf`),
      `cuoti_${this.currentQuestionId}.pdf`
    );
  },

  async deleteCurrentQuestion() {
    if (!this.currentQuestionId) return;
    if (!confirm('确定要删除这道题目吗？')) return;

    try {
      await this.fetchApi(`/api/v1/questions/${this.currentQuestionId}`, {
        method: 'DELETE'
      });
      this.toast('已删除', 'success');
      this.closeDetail();
      this.loadQuestions();
    } catch (error) {
      this.toast(`删除失败: ${error.message}`, 'error');
    }
  },

  // ========================
  // 批量导出
  // ========================

  async batchExport() {
    if (this.selectedQuestions.size === 0) {
      this.toast('请先选择要导出的题目', 'info');
      return;
    }

    try {
      const resp = await this.fetchApi('/api/v1/reports/batch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question_ids: [...this.selectedQuestions],
          formats: ['markdown', 'pdf']
        })
      });

      const blob = await resp.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `cuoti_reports_${this.selectedQuestions.size}questions.zip`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
      this.toast(`已导出 ${this.selectedQuestions.size} 道题目`, 'success');
    } catch (error) {
      this.toast(`导出失败: ${error.message}`, 'error');
    }
  },

  // ========================
  // 统计
  // ========================

  async loadStats() {
    try {
      // 加载统计数据
      const statsResp = await this.fetchApi('/api/v1/system/stats');
      const stats = await statsResp.json();

      document.getElementById('stat-total').textContent = stats.total_questions || 0;
      document.getElementById('stat-today').textContent = stats.today_processed || 0;

      const dist = stats.status_distribution || {};
      document.getElementById('stat-completed').textContent = dist.completed || 0;
      document.getElementById('stat-failed').textContent = dist.failed || 0;

      // 加载系统状态
      const statusResp = await this.fetchApi('/api/v1/system/status');
      const status = await statusResp.json();

      document.getElementById('sys-cpu').textContent = `${(status.cpu_percent || 0).toFixed(1)}%`;
      document.getElementById('sys-memory').textContent = `${(status.memory_percent || 0).toFixed(1)}%`;
      document.getElementById('sys-disk').textContent = `${(status.disk_usage_percent || 0).toFixed(1)}%`;
      document.getElementById('sys-uptime').textContent = this.formatUptime(status.uptime_seconds || 0);

      // VL 状态
      try {
        const vlResp = await this.fetchApi('/api/v1/ocr/vl/status');
        const vlData = await vlResp.json();
        document.getElementById('vl-status').textContent =
          vlData.available ? '运行中' : (vlData.enabled ? '已启用但未就绪' : '未启用');
        document.getElementById('vl-url').textContent = vlData.server_url || '-';
      } catch (e) {
        document.getElementById('vl-status').textContent = '无法获取';
      }

    } catch (error) {
      this.toast(`加载统计失败: ${error.message}`, 'error');
    }
  },

  // ========================
  // 设置弹窗
  // ========================

  openSettings() {
    document.getElementById('input-server-url').value = this.serverUrl;
    document.getElementById('input-api-key').value = this.apiKey;
    document.getElementById('settings-modal').style.display = 'flex';
  },

  closeSettings() {
    document.getElementById('settings-modal').style.display = 'none';
  },

  applySettings() {
    const url = document.getElementById('input-server-url').value.trim().replace(/\/+$/, '');
    const apiKey = document.getElementById('input-api-key').value.trim();
    if (url) {
      // 验证 URL 格式
      try {
        const parsed = new URL(url);
        if (!['http:', 'https:'].includes(parsed.protocol)) {
          this.toast('仅支持 http/https 协议', 'error');
          return;
        }
      } catch {
        this.toast('无效的 URL 格式', 'error');
        return;
      }
      this.serverUrl = url;
      this.apiKey = apiKey;
      this.saveSettingsData();
      this.updateServerDisplay();
      this.checkConnection();
      this.toast('设置已保存，正在连接服务器...', 'info');
    }
    this.closeSettings();
  }
};

// ========================
// 启动应用
// ========================
document.addEventListener('DOMContentLoaded', () => {
  App.init();
});
