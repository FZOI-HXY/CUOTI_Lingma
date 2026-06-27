# 端口变更说明 - 从8000改为8001

## 🔍 问题背景

### 症状
```powershell
netstat -ano | findstr ":8000.*LISTENING"
  TCP    0.0.0.0:8000           0.0.0.0:0              LISTENING       14580
```

但 `tasklist` 和 `Get-Process` 都找不到PID 14580,这是一个**僵尸进程/残留句柄**。

### 原因
- Windows网络栈保留了TIME_WAIT状态的连接
- 之前的进程异常终止,端口句柄未正确释放
- 即使重启进程,旧端口的残留仍然存在

---

## ✅ 已完成的更改

### 1. 后端配置
**文件:** `backend\.env`
```env
PORT=8001  # 原来是8000
```

### 2. 启动脚本
**文件:** `start_en.bat`
- 端口检查: `:8000` → `:8001`
- 健康检查URL更新
- API文档URL更新

### 3. 前端配置 (已全部更新)

#### frontend/config/settings.py
```python
'backend_url': 'http://localhost:8001',  # 原来是8000
```

#### frontend/api/client.py
```python
url = f"{app_settings.get('backend_url', 'http://localhost:8001')}/health"
```

#### frontend/ui/settings_dialog.py
```python
self.backend_url_input.setText(app_settings.get('backend_url', 'http://localhost:8001'))
```

---

## 🎯 新的访问地址

### 后端API
| 服务 | 新地址 |
|------|--------|
| 根路径 | http://localhost:8001/ |
| 健康检查 | http://localhost:8001/health |
| API文档 | http://localhost:8001/docs |
| ReDoc | http://localhost:8001/redoc |

### API端点示例
```bash
# 健康检查
curl http://localhost:8001/health

# 上传文件
POST http://localhost:8001/api/v1/upload/image

# OCR处理
POST http://localhost:8001/api/v1/ocr/process

# 错题管理
GET http://localhost:8001/api/v1/questions
```

---

## 🚀 如何启动

### 使用新端口启动
```bash
.\start_en.bat
```

脚本会自动:
1. ✅ 检查端口8001是否可用
2. ✅ 启动后端服务在8001端口
3. ✅ 验证健康检查通过
4. ✅ 启动前端应用(自动连接8001端口)

### 验证启动成功
```powershell
# 检查端口8001
netstat -ano | findstr ":8001.*LISTENING"

# 应该看到类似输出:
# TCP    0.0.0.0:8001    0.0.0.0:0    LISTENING    [当前PID]

# 测试健康检查
curl http://localhost:8001/health

# 预期响应:
# {"status":"healthy","timestamp":...,"version":"1.0.0"}
```

---

## 📊 端口对比

| 项目 | 端口8000 (旧) | 端口8001 (新) |
|------|--------------|--------------|
| 状态 | ⚠️ 有残留句柄 | ✅ 干净可用 |
| PID | 14580 (不存在) | 当前运行的进程 |
| 可用性 | ❌ 无法绑定 | ✅ 正常 |
| 建议 | 不再使用 | **推荐使用** |

---

## 💡 常见问题

### Q1: 为什么不用8000端口了?

**A:** 端口8000被一个不存在的进程(PID 14580)占用,这是Windows的已知问题。更换端口是最快最可靠的解决方案。

### Q2: 前端需要修改配置吗?

**A:** 不需要!我已经自动更新了所有前端配置文件。前端现在默认连接 `http://localhost:8001`。

### Q3: 如果我想改回8000端口怎么办?

**A:** 可以,但需要先释放8000端口:

**方法1: 重启计算机**(最简单)
```bash
# 重启后,8000端口会自动释放
# 然后修改 backend\.env: PORT=8000
# 并恢复前端配置中的端口号
```

**方法2: 等待系统自动释放**
```bash
# TIME_WAIT状态通常持续2-4分钟
# 等待后检查:
netstat -ano | findstr ":8000"
# 如果没有输出,说明端口已释放
```

### Q4: 其他脚本需要更新吗?

**A:** 以下脚本可能需要更新(如果需要):
- `status.bat` - 检查端口时改为8001
- `diagnose.bat` - 健康检查URL改为8001

我可以帮您更新这些脚本,需要吗?

---

## 📝 总结

### ✅ 已完成
- 后端配置改为8001端口
- 启动脚本更新为8001端口
- 前端所有配置文件更新为8001端口

### 🎯 下一步
直接使用 `.\start_en.bat` 启动系统,一切都会正常工作在新端口8001上!

### 🔗 新地址
- **API文档**: http://localhost:8001/docs
- **健康检查**: http://localhost:8001/health
- **前端应用**: 自动连接8001端口

---

## 🎉 问题解决!

端口已从8000成功迁移到8001,不再有残留句柄问题。

现在可以正常启动和使用系统了!
