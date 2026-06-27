use serde::{Deserialize, Serialize};
use std::sync::Mutex;
use std::time::Duration;
use tokio::io::AsyncReadExt;

/// 共享 HTTP 客户端（复用连接池）
fn shared_client() -> reqwest::Client {
    static CLIENT: std::sync::OnceLock<reqwest::Client> = std::sync::OnceLock::new();
    CLIENT
        .get_or_init(|| {
            reqwest::Client::builder()
                .timeout(Duration::from_secs(120))
                .connect_timeout(Duration::from_secs(10))
                .build()
                .unwrap_or_default()
        })
        .clone()
}

/// 验证 server_url 的格式（协议 + 有效主机）
/// 客户端模式下用户显式配置服务器地址，不做 host 白名单限制
fn validate_server_url(url_str: &str) -> Result<url::Url, String> {
    let parsed = url::Url::parse(url_str).map_err(|e| format!("无效的 URL: {}", e))?;

    // 仅允许 http/https
    match parsed.scheme() {
        "http" | "https" => {}
        _ => return Err("仅允许 http/https 协议".to_string()),
    }

    // 确保有主机名
    parsed
        .host_str()
        .ok_or_else(|| "URL 缺少主机名".to_string())?;

    Ok(parsed)
}

/// 验证上传文件路径安全性（C4）：拒绝指向敏感目录或用户主目录直接子项的路径
fn validate_upload_path(file_path: &str) -> Result<(), String> {
    let path_lower = file_path.to_lowercase();

    // 拒绝包含敏感目录名的路径
    let sensitive_dirs = [
        ".ssh",
        ".gnupg",
        ".aws",
        ".azure",
        "appdata",
        ".config",
        ".kube",
        "credentials",
        ".env",
    ];
    for dir in &sensitive_dirs {
        if path_lower.contains(dir) {
            return Err(format!("文件路径包含敏感目录: {}", dir));
        }
    }

    // 拒绝用户主目录的直接子文件（防止读取 ~/.bashrc, ~/.profile 等）
    if let Some(home) = dirs::home_dir() {
        let home_str = home.to_string_lossy();
        let home_trimmed = home_str.trim_end_matches(['/', '\\']);
        if let Some(relative) = path_lower.strip_prefix(&home_trimmed.to_lowercase()) {
            let relative_trimmed = relative.trim_start_matches(['/', '\\']);
            // 如果剩余部分不含分隔符，说明是主目录的直接子文件
            if !relative_trimmed.is_empty()
                && !relative_trimmed.contains('/')
                && !relative_trimmed.contains('\\')
            {
                return Err("不允许上传用户主目录下的直接文件".to_string());
            }
        }
    }

    Ok(())
}

/// 验证下载 endpoint 参数（H7）：仅允许指定的 API 路径前缀
fn validate_endpoint(endpoint: &str) -> Result<(), String> {
    // 必须以允许的 API 路径前缀开头
    let allowed_prefixes = ["/api/v1/", "/uploads/", "/processed/", "/storage/"];
    let has_valid_prefix = allowed_prefixes.iter().any(|p| endpoint.starts_with(p));
    if !has_valid_prefix {
        return Err(format!(
            "endpoint 必须以以下路径之一开头: {}",
            allowed_prefixes.join(", ")
        ));
    }

    // 禁止路径穿越和可疑字符
    if endpoint.contains("..") {
        return Err("endpoint 不允许包含 '..'".to_string());
    }
    if endpoint.contains('@') {
        return Err("endpoint 不允许包含 '@'".to_string());
    }
    if endpoint.contains('\0') {
        return Err("endpoint 不允许包含空字节".to_string());
    }

    Ok(())
}

/// 应用状态
struct AppState {
    server_url: Mutex<String>,
    api_key: Mutex<String>,
}

/// 健康检查结果
#[derive(Debug, Serialize, Deserialize)]
struct HealthResult {
    status: String,
    timestamp: f64,
    version: String,
}

/// 检查服务器连接状态
#[tauri::command]
async fn check_server(server_url: String, api_key: String) -> Result<bool, String> {
    validate_server_url(&server_url)?;
    let url = format!("{}/health", server_url);
    match shared_client()
        .get(&url)
        .header("Authorization", format!("Bearer {}", api_key))
        .send()
        .await
    {
        Ok(resp) => Ok(resp.status().is_success()),
        Err(_) => Ok(false),
    }
}

/// 获取服务器 URL
#[tauri::command]
fn get_server_url(state: tauri::State<AppState>) -> String {
    state
        .server_url
        .lock()
        .unwrap_or_else(|e| e.into_inner())
        .clone()
}

/// 设置服务器 URL
#[tauri::command]
fn set_server_url(state: tauri::State<AppState>, url: String) -> Result<(), String> {
    // 验证 URL 格式（协议 + 主机名）
    validate_server_url(&url)?;
    *state.server_url.lock().unwrap_or_else(|e| e.into_inner()) = url;
    Ok(())
}

/// 获取 API Key
#[tauri::command]
fn get_api_key(state: tauri::State<AppState>) -> String {
    state
        .api_key
        .lock()
        .unwrap_or_else(|e| e.into_inner())
        .clone()
}

/// 设置 API Key
#[tauri::command]
fn set_api_key(state: tauri::State<AppState>, key: String) -> Result<(), String> {
    if key.is_empty() {
        return Err("API Key 不能为空".to_string());
    }
    *state.api_key.lock().unwrap_or_else(|e| e.into_inner()) = key;
    Ok(())
}

/// 通过 Tauri 代理上传图片文件（避免浏览器 CORS 对 multipart 的限制）
/// 修复 M9：先打开文件句柄，再从同一句柄获取元数据和读取内容，消除 TOCTOU 竞态
/// 修复 C4：增加路径合法性校验
#[tauri::command]
async fn upload_file(
    server_url: String,
    api_key: String,
    file_path: String,
) -> Result<serde_json::Value, String> {
    validate_server_url(&server_url)?;
    validate_upload_path(&file_path)?;

    let path = std::path::Path::new(&file_path);
    let file_name = path
        .file_name()
        .and_then(|n| n.to_str())
        .unwrap_or("upload.jpg")
        .to_string();

    // 限制可上传文件的大小（50MB）
    const MAX_UPLOAD_SIZE: u64 = 50 * 1024 * 1024;

    // M9 fix: 打开文件后从同一句柄读取元数据和内容，消除 TOCTOU 竞态
    let mut file = tokio::fs::File::open(&file_path)
        .await
        .map_err(|e| format!("打开文件失败: {}", e))?;

    let metadata = file
        .metadata()
        .await
        .map_err(|e| format!("读取文件信息失败: {}", e))?;
    if metadata.len() > MAX_UPLOAD_SIZE {
        return Err(format!(
            "文件过大: {:.1}MB (上限 50MB)",
            metadata.len() as f64 / 1024.0 / 1024.0
        ));
    }

    let mut file_bytes = Vec::with_capacity(metadata.len() as usize);
    file.read_to_end(&mut file_bytes)
        .await
        .map_err(|e| format!("读取文件失败: {}", e))?;

    let mime = match file_name.rsplit('.').next() {
        Some("png") => "image/png",
        Some("bmp") => "image/bmp",
        Some("webp") => "image/webp",
        Some("tiff") | Some("tif") => "image/tiff",
        _ => "image/jpeg",
    };

    let part = reqwest::multipart::Part::bytes(file_bytes)
        .file_name(file_name)
        .mime_str(mime)
        .map_err(|e| format!("构建上传数据失败: {}", e))?;

    let form = reqwest::multipart::Form::new().part("file", part);

    let url = format!("{}/api/v1/upload/image", server_url);
    let client = shared_client();
    let resp = client
        .post(&url)
        .header("Authorization", format!("Bearer {}", api_key))
        .multipart(form)
        .send()
        .await
        .map_err(|e| format!("上传请求失败: {}", e))?;

    if !resp.status().is_success() {
        let body = resp.text().await.unwrap_or_default();
        return Err(format!("上传失败: {}", body));
    }

    let json: serde_json::Value = resp
        .json()
        .await
        .map_err(|e| format!("解析响应失败: {}", e))?;

    Ok(json)
}

/// 验证文件名安全性：拒绝包含路径分隔符或穿越序列的输入
fn sanitize_filename(filename: &str) -> Result<String, String> {
    // 拒绝路径穿越
    if filename.contains("..") || filename.contains('/') || filename.contains('\\') {
        return Err("文件名包含不允许的字符".to_string());
    }
    // 仅取最终的文件名部分（防止意外传入路径）
    let name = std::path::Path::new(filename)
        .file_name()
        .and_then(|n| n.to_str())
        .ok_or_else(|| "无效的文件名".to_string())?;

    if name.is_empty() {
        return Err("文件名不能为空".to_string());
    }

    Ok(name.to_string())
}

/// 通过 Rust 侧直接下载文件到用户 Downloads 目录
/// 作为 WebView2 中 JS blob 下载的保底方案
/// 修复 H7：增加 endpoint 参数校验
/// 修复 M11：Content-Length 缺失时打印警告
/// 修复 M12：canonicalize 失败时返回错误而非静默回退
/// 修复 L9：使用 tokio::fs::write 避免阻塞异步执行器
#[tauri::command]
async fn download_file(
    server_url: String,
    api_key: String,
    endpoint: String,
    filename: String,
) -> Result<String, String> {
    validate_server_url(&server_url)?;
    validate_endpoint(&endpoint)?;

    // 验证并清理文件名
    let safe_filename = sanitize_filename(&filename)?;

    let url = format!("{}{}", server_url, endpoint);
    let client = shared_client();
    let resp = client
        .get(&url)
        .header("Authorization", format!("Bearer {}", api_key))
        .send()
        .await
        .map_err(|e| format!("下载请求失败: {}", e))?;

    if !resp.status().is_success() {
        return Err(format!("下载失败: HTTP {}", resp.status()));
    }

    // 限制下载文件大小（200MB）
    const MAX_DOWNLOAD_SIZE: u64 = 200 * 1024 * 1024;
    let content_length = resp.content_length();

    // M11 fix: 如果服务器未返回 Content-Length，打印警告；post-download 检查会捕获实际超限
    match content_length {
        Some(len) if len > MAX_DOWNLOAD_SIZE => {
            return Err(format!(
                "文件过大: {:.1}MB (上限 200MB)",
                len as f64 / 1024.0 / 1024.0
            ));
        }
        None => {
            eprintln!(
                "[download_file] 警告: 服务器未返回 Content-Length 头，将依赖下载后大小检查"
            );
        }
        _ => {}
    }

    let bytes = resp
        .bytes()
        .await
        .map_err(|e| format!("读取数据失败: {}", e))?;

    // 二次检查实际字节大小
    if bytes.len() as u64 > MAX_DOWNLOAD_SIZE {
        return Err("下载数据超过大小限制".to_string());
    }

    // 获取用户 Downloads 目录
    let downloads_dir = dirs::download_dir()
        .unwrap_or_else(|| dirs::home_dir().unwrap_or_default().join("Downloads"));

    // 确保目录存在
    tokio::fs::create_dir_all(&downloads_dir)
        .await
        .map_err(|e| format!("创建目录失败: {}", e))?;

    let file_path = downloads_dir.join(&safe_filename);

    // M12 fix: 最终验证——确保路径仍在 downloads_dir 内；canonicalize 失败时返回错误
    let real_downloads = tokio::fs::canonicalize(&downloads_dir)
        .await
        .map_err(|e| format!("无法解析下载目录: {}", e))?;
    let real_target = file_path
        .parent()
        .map(|p| tokio::fs::canonicalize(p))
        .ok_or_else(|| "无法解析保存路径".to_string())?
        .await
        .map_err(|e| format!("无法解析保存路径: {}", e))?;
    if !real_target.starts_with(&real_downloads) {
        return Err("保存路径验证失败".to_string());
    }

    // L9 fix: 使用 tokio::fs::write 替代 std::fs::write 以避免阻塞异步执行器
    tokio::fs::write(&file_path, &bytes)
        .await
        .map_err(|e| format!("保存文件失败: {}", e))?;

    Ok(file_path.to_string_lossy().to_string())
}

/// 启动 OCR 处理
#[tauri::command]
async fn start_ocr(
    server_url: String,
    api_key: String,
    file_id: String,
    use_vl: bool,
) -> Result<serde_json::Value, String> {
    validate_server_url(&server_url)?;

    let url = format!("{}/api/v1/ocr/process", server_url);
    let client = shared_client();

    let body = serde_json::json!({
        "file_id": file_id,
        "use_vl": use_vl
    });

    let resp = client
        .post(&url)
        .header("Authorization", format!("Bearer {}", api_key))
        .json(&body)
        .send()
        .await
        .map_err(|e| format!("OCR请求失败: {}", e))?;

    if !resp.status().is_success() {
        let body = resp.text().await.unwrap_or_default();
        return Err(format!("OCR启动失败: {}", body));
    }

    let json: serde_json::Value = resp
        .json()
        .await
        .map_err(|e| format!("解析响应失败: {}", e))?;

    Ok(json)
}

/// 查询任务状态
#[tauri::command]
async fn get_task_status(
    server_url: String,
    api_key: String,
    task_id: String,
) -> Result<serde_json::Value, String> {
    validate_server_url(&server_url)?;

    // 验证 task_id 格式（应为 UUID）
    if task_id.contains('/') || task_id.contains('\\') || task_id.contains("..") {
        return Err("无效的任务 ID".to_string());
    }

    let url = format!("{}/api/v1/ocr/status/{}", server_url, task_id);
    let client = shared_client();

    let resp = client
        .get(&url)
        .header("Authorization", format!("Bearer {}", api_key))
        .send()
        .await
        .map_err(|e| format!("查询失败: {}", e))?;

    let json: serde_json::Value = resp
        .json()
        .await
        .map_err(|e| format!("解析响应失败: {}", e))?;

    Ok(json)
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .manage(AppState {
            server_url: Mutex::new("http://localhost:8100".to_string()),
            api_key: Mutex::new(String::new()),
        })
        .invoke_handler(tauri::generate_handler![
            check_server,
            get_server_url,
            set_server_url,
            get_api_key,
            set_api_key,
            upload_file,
            start_ocr,
            get_task_status,
            download_file,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
