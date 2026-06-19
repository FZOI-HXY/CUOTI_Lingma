use serde::{Deserialize, Serialize};
use std::sync::Mutex;

/// 应用状态
struct AppState {
    server_url: Mutex<String>,
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
async fn check_server(server_url: String) -> Result<bool, String> {
    let url = format!("{}/health", server_url);
    match reqwest::get(&url).await {
        Ok(resp) => Ok(resp.status().is_success()),
        Err(_) => Ok(false),
    }
}

/// 获取服务器 URL
#[tauri::command]
fn get_server_url(state: tauri::State<AppState>) -> String {
    state.server_url.lock().unwrap().clone()
}

/// 设置服务器 URL
#[tauri::command]
fn set_server_url(state: tauri::State<AppState>, url: String) {
    *state.server_url.lock().unwrap() = url;
}

/// 通过 Tauri 代理上传图片文件（避免浏览器 CORS 对 multipart 的限制）
#[tauri::command]
async fn upload_file(
    server_url: String,
    file_path: String,
) -> Result<serde_json::Value, String> {
    let path = std::path::Path::new(&file_path);
    let file_name = path
        .file_name()
        .and_then(|n| n.to_str())
        .unwrap_or("upload.jpg")
        .to_string();

    let file_bytes = tokio::fs::read(&file_path)
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
    let client = reqwest::Client::new();
    let resp = client
        .post(&url)
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

/// 启动 OCR 处理
#[tauri::command]
async fn start_ocr(
    server_url: String,
    file_id: String,
    use_vl: bool,
) -> Result<serde_json::Value, String> {
    let url = format!("{}/api/v1/ocr/process", server_url);
    let client = reqwest::Client::new();

    let body = serde_json::json!({
        "file_id": file_id,
        "use_vl": use_vl
    });

    let resp = client
        .post(&url)
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
    task_id: String,
) -> Result<serde_json::Value, String> {
    let url = format!("{}/api/v1/ocr/status/{}", server_url, task_id);

    let resp = reqwest::get(&url)
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
        })
        .invoke_handler(tauri::generate_handler![
            check_server,
            get_server_url,
            set_server_url,
            upload_file,
            start_ocr,
            get_task_status,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
