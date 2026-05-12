# SEIF GitHub Pages 部署指南

## 文件说明

本目录包含用于部署 SEIF 项目 GitHub Pages 的文件。

### 部署步骤

1. **克隆仓库**
   ```bash
   git clone https://github.com/Rainier-rq1/SEIF.git
   cd SEIF
   ```

2. **创建 docs 文件夹**（如果不存在）
   ```bash
   mkdir docs
   ```

3. **将文件复制到 docs 文件夹**
   - 将 `index.html` 复制到 `docs/`
   - 将 `styles.css` 复制到 `docs/`

4. **推送到 GitHub**
   ```bash
   git add .
   git commit -m "Add GitHub Pages site"
   git push origin main
   ```

5. **启用 GitHub Pages**
   - 进入 GitHub 仓库页面
   - 点击 Settings > Pages
   - Source 选择 "Deploy from a branch"
   - Branch 选择 "main" 和 "/ (root)"
   - 点击 Save

6. **等待部署**
   - 等待几分钟后，你的页面将出现在: `https://Rainier-rq1.github.io/SEIF/`

## 本地预览

如果你想本地预览，可以使用 Python 的 HTTP 服务器：

```bash
cd docs
python -m http.server 8000
```

然后在浏览器中打开 `http://localhost:8000`

## 自定义

你可以通过编辑 `index.html` 和 `styles.css` 来自定义页面样式和内容。
