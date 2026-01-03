# GitHub Actions 部署指南

这个目录包含了在 GitHub Actions 上运行航班价格监控所需的所有文件。

## 1. 文件说明

- `flight_alert_action.py`: 专门为 GitHub Actions 优化的脚本。它从环境变量读取配置，并将价格历史保存到 `price_history.json` 文件中。
- `requirements.txt`: Python 依赖库列表。
- `../.github/workflows/flight_check.yml`: GitHub Actions 的工作流配置文件，定义了定时任务（每小时运行一次）。

## 2. 部署步骤

### 第一步：上传代码到 GitHub
将整个项目（包括 `.github` 文件夹和 `GitHub` 文件夹）推送到你的 GitHub 仓库。

### 第二步：配置 Secrets (环境变量)
为了保护你的隐私（如邮箱密码），我们需要在 GitHub 仓库中设置 Secrets。

1. 进入你的 GitHub 仓库页面。
2. 点击 **Settings** (设置) -> **Secrets and variables** -> **Actions**。
3. 点击 **New repository secret** (新建仓库密钥)。
4. 依次添加以下密钥（Name 和 Secret）：

| Name             | Value (示例)           | 说明                              |
|------------------|------------------------|-----------------------------------|
| `DATE_TO_GO`     | `20260117,20260118`    | 监控日期，多个日期用逗号分隔      |
| `PLACE_FROM`     | `SHA`                  | 出发地代码 (上海虹桥)             |
| `PLACE_TO`       | `JIQ`                  | 目的地代码 (黔江)                 |
| `FLIGHT_WAY`     | `Oneway`               | 单程 (Oneway) 或 往返 (Roundtrip) |
| `PRICE_STEP`     | `50`                   | 价格变化多少才通知                |
| `EMAIL_SENDER`   | `your_email@qq.com`    | 发件人邮箱                        |
| `EMAIL_PASSWORD` | `your_auth_code`       | 邮箱授权码 (不是登录密码)         |
| `EMAIL_RECEIVER` | `receiver@example.com` | 收件人邮箱                        |
| `SMTP_SERVER`    | `smtp.qq.com`          | SMTP 服务器地址                   |
| `SMTP_PORT`      | `465`                  | SMTP 端口                         |

### 第三步：配置 Workflow 权限
为了让脚本能够将 `price_history.json` (价格历史记录) 保存回仓库，你需要赋予 Workflow 写权限。

1. 进入 **Settings** -> **Actions** -> **General**。
2. 滚动到 **Workflow permissions** 部分。
3. 选中 **Read and write permissions**。
4. 点击 **Save**。

### 第四步：启用并测试
1. 配置完成后，Action 会根据 `flight_check.yml` 中的设置每小时自动运行。
2. 你也可以手动触发一次来测试：
   - 点击仓库上方的 **Actions** 标签。
   - 点击左侧的 **Flight Price Monitor**。
   - 点击右侧的 **Run workflow** 按钮。

## 3. 注意事项
- **首次运行**：第一次运行时，脚本会记录当前价格并保存到 `price_history.json`。你会收到一封"首次记录"的邮件（如果配置了发送首次通知）。
- **价格历史**：`price_history.json` 文件会被自动提交到仓库的 `GitHub` 目录下。请不要手动修改它，除非你想重置历史价格。
