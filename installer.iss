; Inno Setup 配置文件
; 错题管理系统 Windows 安装包
;
; 使用方法:
;   1. 先运行 build.bat 构建发布包
;   2. 安装 Inno Setup: https://jrsoftware.org/isinfo.php
;   3. 用 Inno Setup 打开此文件，点击"编译"
;   4. 生成的安装包在 installer_output 目录

#define MyAppName "错题管理系统"
#define MyAppNameEn "CuotiSystem"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "CuotiSystem"
#define MyAppExeName "cuoti_frontend.exe"

[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppNameEn}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=installer_output
OutputBaseFilename=错题管理系统_Setup_{#MyAppVersion}
Compression=lzma2/fast
SolidCompression=no
WizardStyle=modern
PrivilegesRequired=admin
; SetupIconFile=  ; 如有 .ico 图标文件可在此设置
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create desktop shortcut"; GroupDescription: "Additional options:"
Name: "startmenuicon"; Description: "Create start menu shortcut"; GroupDescription: "Additional options:"

[Files]
; 后端
Source: "dist\CuotiSystem\backend\*"; DestDir: "{app}\backend"; Flags: ignoreversion recursesubdirs createallsubdirs

; 前端
Source: "dist\CuotiSystem\frontend\*"; DestDir: "{app}\frontend"; Flags: ignoreversion recursesubdirs createallsubdirs

; 模型文件（PP-StructureV3 + VL GGUF 模型）
Source: "dist\CuotiSystem\models\*"; DestDir: "{app}\models"; Flags: ignoreversion recursesubdirs createallsubdirs

; llama.cpp 工具（VL 增强模式推理引擎）
Source: "dist\CuotiSystem\tools\*"; DestDir: "{app}\tools"; Flags: ignoreversion recursesubdirs createallsubdirs; Check: VLFilesExist

; 启动脚本
Source: "dist\CuotiSystem\start.bat"; DestDir: "{app}"; Flags: ignoreversion

[Dirs]
Name: "{app}\uploads"
Name: "{app}\processed"
Name: "{app}\logs"

[Icons]
; 桌面快捷方式（指向前端）
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\frontend\{#MyAppExeName}"; Tasks: desktopicon

; 开始菜单
Name: "{group}\{#MyAppName}"; Filename: "{app}\frontend\{#MyAppExeName}"; Tasks: startmenuicon
Name: "{group}\卸载 {#MyAppName}"; Filename: "{uninstallexe}"; Tasks: startmenuicon

[Run]
; 安装完成后可选启动程序
Filename: "{app}\frontend\{#MyAppExeName}"; Description: "启动 {#MyAppName}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; 卸载时清理运行时生成的文件
Type: filesandordirs; Name: "{app}\processed"
Type: filesandordirs; Name: "{app}\logs"
Type: filesandordirs; Name: "{app}\uploads"

[Code]
// 检查 tools 目录是否存在（VL 增强模式文件）
function VLFilesExist: Boolean;
begin
  Result := DirExists(ExpandConstant('{src}\dist\CuotiSystem\tools'));
end;

// 设置环境变量
procedure CurStepChanged(CurStep: TSetupStep);
var
  EnvPath: String;
begin
  if CurStep = ssPostInstall then
  begin
    // 设置 PADDLE_PDX_CACHE_HOME 指向安装目录下的模型
    EnvPath := ExpandConstant('{app}\models');
    RegWriteStringValue(HKEY_CURRENT_USER, 'Environment', 'PADDLE_PDX_CACHE_HOME', EnvPath);
    
    // 设置 PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK
    RegWriteStringValue(HKEY_CURRENT_USER, 'Environment', 'PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK', 'True');
    RegWriteStringValue(HKEY_CURRENT_USER, 'Environment', 'PADDLE_PDX_ENABLE_MKLDNN_BYDEFAULT', 'False');
    
    // VL 增强模式环境变量
    RegWriteStringValue(HKEY_CURRENT_USER, 'Environment', 'VL_ENABLED', 'True');
    RegWriteStringValue(HKEY_CURRENT_USER, 'Environment', 'VL_LLAMA_CPP_DIR', ExpandConstant('{app}\tools\llama-cpp'));
  end;
end;

// 卸载时清理环境变量
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usPostUninstall then
  begin
    RegDeleteValue(HKEY_CURRENT_USER, 'Environment', 'PADDLE_PDX_CACHE_HOME');
    RegDeleteValue(HKEY_CURRENT_USER, 'Environment', 'PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK');
    RegDeleteValue(HKEY_CURRENT_USER, 'Environment', 'PADDLE_PDX_ENABLE_MKLDNN_BYDEFAULT');
    RegDeleteValue(HKEY_CURRENT_USER, 'Environment', 'VL_ENABLED');
    RegDeleteValue(HKEY_CURRENT_USER, 'Environment', 'VL_LLAMA_CPP_DIR');
  end;
end;
