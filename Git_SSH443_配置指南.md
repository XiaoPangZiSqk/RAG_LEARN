# 从零配置 Git 并通过 SSH 443 端口连接远程仓库

本文档描述一套从空白环境到「能推能拉」的完整配置流程，重点解决两类常见问题：

1. 本地 Git 未初始化、身份信息未配置
2. `https://github.com/...` 直连 443 失败，或密码认证被 GitHub 拒绝

核心思路：**放弃 HTTPS 密码认证，改用 SSH 公钥认证，并把 SSH 连接重定向到 443 端口**，以绕过对 22 端口的封锁。

---

## 目录

- [0. 适用场景与示例约定](#0-适用场景与示例约定)
- [1. Git 安装与环境初始化](#1-git-安装与环境初始化)
- [2. 生成 SSH 密钥并添加到 GitHub](#2-生成-ssh-密钥并添加到-github)
- [3. 配置 SSH 通过 443 端口连接](#3-配置-ssh-通过-443-端口连接)
- [4. 配置仓库与 remote origin](#4-配置仓库与-remote-origin)
- [5. 全链路验证](#5-全链路验证)
- [6. 常见问题排查](#6-常见问题排查)
- [7. 日常使用速查](#7-日常使用速查)
- [8. Git 常用命令手册](#8-git-常用命令手册)
- [附录 A. 完整配置文件对照](#附录-a-完整配置文件对照)
- [附录 B. 网络受限环境的代理转发](#附录-b-网络受限环境的代理转发)
- [附录 C. 一键配置脚本](#附录-c-一键配置脚本)

---

## 0. 适用场景与示例约定

### 适用环境

| 环境 | 说明 |
|---|---|
| WSL2 / Ubuntu / Debian | 本文主环境，命令均以 bash 给出 |
| 原生 Linux | 完全适用 |
| macOS | 命令基本一致，`ssh-keygen`、`chmod` 均可用 |
| Windows 原生 | 需在 Git Bash 中执行，路径改为 `C:/Users/用户名/.ssh/` |

### 示例约定

文中统一使用以下占位符，请全部替换为你自己的值：

| 占位符 | 含义 | 示例 |
|---|---|---|
| `your-username` | GitHub 用户名 | `XiaoPangZiSqk` |
| `your_email@example.com` | GitHub 绑定邮箱 | `xxx@qq.com` |
| `your-repo` | 远程仓库名 | `RAG_LEARN` |
| `/path/to/your-project` | 本地项目绝对路径 | `/home/user/project/demo` |

> 注意：GitHub 用户名区分大小写，但**登录名与显示名可能不同**，以仓库 URL 中出现的为准。

---

## 1. Git 安装与环境初始化

### 1.1 确认系统与当前 Git 来源

```bash
uname -a
which git
git --version
```

**关键判断**：

| `which git` 输出 | 含义 | 处理 |
|---|---|---|
| `/usr/bin/git` | 系统安装的 Linux 版 Git | 正确，继续 |
| `/usr/local/bin/git` | 手动编译安装 | 可用，注意版本 |
| `/mnt/c/Program Files/Git/...` | 调用了 Windows 的 git.exe | **错误**，需重新安装 |
| 无输出 | 未安装 | 执行 1.2 |

> 在 WSL 中误用 Windows 版 Git 会导致路径转换错误、文件权限丢失、换行符混乱，务必确认使用的是 Linux 版。

### 1.2 安装 Git

Debian / Ubuntu / WSL：

```bash
sudo apt update
sudo apt install -y git
hash -r
which git
```

CentOS / RHEL / Fedora：

```bash
sudo dnf install -y git
```

macOS：

```bash
brew install git
```

安装后再次确认：

```bash
which git          # 期望：/usr/bin/git
git --version      # 期望：git version 2.30 以上
```

### 1.3 配置全局身份

Git 每次提交都会记录作者信息，未配置会导致 `commit` 直接失败。

```bash
git config --global user.name  "your-username"
git config --global user.email "your_email@example.com"
```

说明：

- `user.name` 建议与 GitHub 用户名一致，便于识别
- `user.email` **建议使用 GitHub 账号绑定的邮箱**，否则提交不会关联到你的贡献图
- 如需隐藏真实邮箱，可在 GitHub 设置中开启 `Keep my email addresses private`，使用 `12345678+your-username@users.noreply.github.com`

### 1.4 配置默认分支名

Git 2.28 起支持指定初始化分支名。GitHub 默认使用 `main`，建议统一：

```bash
git config --global init.defaultBranch main
```

验证：

```bash
cd /tmp && mkdir demo-init && cd demo-init
git init
git branch --show-current    # 期望输出：main
cd /tmp && rm -rf demo-init
```

### 1.5 配置换行符策略

跨平台协作时最容易踩的坑。不同系统的处理方式：

| 环境 | 推荐值 | 效果 |
|---|---|---|
| Linux / WSL / macOS | `input` | 提交时 CRLF 转 LF，检出时不做转换 |
| Windows 原生 | `true` | 提交时转 LF，检出时转 CRLF |

```bash
# Linux / WSL / macOS
git config --global core.autocrlf input
```

```bash
# Windows 原生（Git Bash）
git config --global core.autocrlf true
```

### 1.6 其他建议配置

```bash
# 设置默认编辑器，避免提交时卡在 vim
git config --global core.editor "vim"

# 让 git 输出彩色，便于阅读
git config --global color.ui auto

# 拉取时对分支做 rebase 而非 merge，保持历史线性（可选）
git config --global pull.rebase false

# 记录命令耗时至 reflog，便于排查
git config --global core.logAllRefUpdates true
```

### 1.7 检查全局配置

```bash
git config --global --list
```

期望能看到：

```
user.name=your-username
user.email=your_email@example.com
init.defaultbranch=main
core.autocrlf=input
```

查看配置来源（区分全局与仓库级）：

```bash
git config --list --show-origin
```

### 1.8 关于 HTTPS 代理配置

如果你的网络需要代理才能访问 GitHub，并且坚持使用 HTTPS，可以用：

```bash
git config --global http.proxy  http://127.0.0.1:7890
git config --global https.proxy http://127.0.0.1:7890
```

**但走 SSH 时这两项不生效**，SSH 有自己的代理机制，见 [附录 B](#附录-b-网络受限环境的代理转发)。

如果之前配过且现在改用 SSH，建议清除，避免干扰：

```bash
git config --global --unset http.proxy
git config --global --unset https.proxy
```

---

## 2. 生成 SSH 密钥并添加到 GitHub

SSH 认证使用非对称密钥对：

- **私钥**（`id_ed25519`）：留在本机，**永不外传**
- **公钥**（`id_ed25519.pub`）：上传到 GitHub，用于验证持有私钥的人

### 2.1 检查是否已有密钥

```bash
ls -al ~/.ssh
```

如果已存在 `id_ed25519` 与 `id_ed25519.pub`，可直接跳到 [2.3](#23-查看并复制公钥)。若要复用已有密钥，无需重复生成。

### 2.2 生成密钥

```bash
ssh-keygen -t ed25519 -C "your_email@example.com" -f ~/.ssh/id_ed25519
```

参数说明：

| 参数 | 作用 |
|---|---|
| `-t ed25519` | 使用 Ed25519 算法（比 RSA 更短更安全，GitHub 推荐） |
| `-C "..."` | 注释，通常写邮箱，仅用于标识，不影响认证 |
| `-f ~/.ssh/id_ed25519` | 指定私钥路径，公钥自动生成为同路径加 `.pub` |

交互提示：

```
Enter passphrase (empty for no passphrase):
Enter same passphrase again:
```

- 直接回车两次 = **不设密码**，使用最方便
- 设置 passphrase = 更安全，但每次使用需输入（可配合 `ssh-agent` 缓存）

生成成功会看到：

```
Your identification has been saved in /home/user/.ssh/id_ed25519
Your public key has been saved in /home/user/.ssh/id_ed25519.pub
The key fingerprint is:
SHA256:xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx your_email@example.com
```

### 2.3 查看并复制公钥

```bash
cat ~/.ssh/id_ed25519.pub
```

输出形如：

```
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx your_email@example.com
```

**完整复制这一整行**（从 `ssh-ed25519` 开始到邮箱结尾），不要换行、不要漏字符。

### 2.4 添加到 GitHub

1. 打开 GitHub，点击右上角头像 → `Settings`
2. 左侧菜单找到 `SSH and GPG keys`
3. 点击 `New SSH key`
4. `Title` 填写便于识别的名称，例如 `wsl-ubuntu`
5. `Key type` 选择 `Authentication Key`
6. `Key` 粘贴上一步复制的完整公钥
7. 点击 `Add SSH key`

### 2.5 修正文件权限

SSH 对权限非常敏感，过宽的权限会导致密钥被拒绝使用：

```bash
chmod 700 ~/.ssh
chmod 600 ~/.ssh/id_ed25519
chmod 644 ~/.ssh/id_ed25519.pub
```

检查结果：

```bash
ls -l ~/.ssh
```

期望：

```
drwx------  id_ed25519      # 私钥，仅本人可读写
-rw-r--r--  id_ed25519.pub  # 公钥，可被读取
```

> 若私钥权限是 `644` 或更宽，SSH 会报 `WARNING: UNPROTECTED PRIVATE KEY FILE` 并拒绝使用。

---

## 3. 配置 SSH 通过 443 端口连接

### 3.1 为什么要走 443 端口

GitHub 的 SSH 标准端口是 `22`，但很多网络环境（公司、校园网、部分运营商）会封锁 22 端口。GitHub 官方提供了备用入口：

| 用途 | 主机 | 端口 |
|---|---|---|
| 标准 SSH | `github.com` | 22 |
| 备用 SSH over HTTPS 端口 | `ssh.github.com` | 443 |

通过 SSH 配置文件把 `github.com` 的连接重定向到 `ssh.github.com:443`，即可在不修改 remote 地址的前提下走通。

### 3.2 编辑 SSH 配置文件

```bash
mkdir -p ~/.ssh
touch ~/.ssh/config
chmod 600 ~/.ssh/config
```

写入以下内容：

```bash
cat > ~/.ssh/config <<'EOF'
Host github.com
    HostName ssh.github.com
    Port 443
    User git
    IdentityFile ~/.ssh/id_ed25519
    IdentitiesOnly yes
    ServerAliveInterval 60
    ServerAliveCountMax 3
EOF
```

### 3.3 参数逐项说明

| 参数 | 值 | 作用 |
|---|---|---|
| `Host` | `github.com` | **匹配别名**。`ssh git@github.com` 或 `git@github.com:...` 会命中此段 |
| `HostName` | `ssh.github.com` | **真实连接的主机名**，实际 DNS 解析和 TCP 连接用它 |
| `Port` | `443` | 实际连接端口，绕开对 22 的封锁 |
| `User` | `git` | SSH 登录用户名。GitHub 固定为 `git`，不是你的账号名 |
| `IdentityFile` | `~/.ssh/id_ed25519` | 指定使用的私钥路径 |
| `IdentitiesOnly` | `yes` | 只使用上面指定的密钥，避免 ssh-agent 中其他密钥导致认证失败 |
| `ServerAliveInterval` | `60` | 每 60 秒发送保活包，防止长连接被中断 |
| `ServerAliveCountMax` | `3` | 连续 3 次无响应后断开 |

**最容易混淆的一点**：`Host` 是「别名」，`HostName` 是「真实地址」。配置了上面这段后：

- 命令里写 `git@github.com` → 实际连接 `ssh.github.com:443`
- remote URL 里写 `git@github.com:your-username/your-repo.git` → 同样走 443

**因此 remote 地址不需要写端口号**。

### 3.4 关于 Host 的匹配规则

`Host` 使用的是模式匹配（glob），不是精确相等：

| 写法 | 匹配范围 |
|---|---|
| `Host github.com` | 仅 `github.com` |
| `Host *.github.com` | 所有子域名，如 `ssh.github.com`、`api.github.com` |
| `Host *` | 所有主机，作为兜底配置 |

如果 remote URL 写的是 `git@ssh.github.com:...`，则 `Host github.com` 这段**不会**命中，会走默认的 22 端口。因此建议统一使用 `git@github.com:...` 形式的地址。

### 3.5 首次连接与 known_hosts

首次连接会提示确认主机指纹：

```
The authenticity of host '[ssh.github.com]:443 ([20.205.243.160]:443)' can't be established.
ED25519 key fingerprint is SHA256:+DiY3wvvV6TuJJhbpZisF/zLDA0zPMSvHdkr4UvCOqU.
Are you sure you want to continue connecting (yes/no/[fingerprint])?
```

输入 `yes` 回车，指纹会被写入 `~/.ssh/known_hosts`，之后不再提示。

> 指纹应以 GitHub 官方公布值为准，可在 GitHub 文档 "SSH key fingerprints" 页面核对。若指纹不符，可能是中间人攻击或网络劫持。

### 3.6 测试 SSH 连通性

```bash
ssh -T git@github.com
```

**成功输出**：

```
Hi your-username! You've successfully authenticated, but GitHub does not provide shell access.
```

看到 `Hi 你的用户名!` 就说明密钥认证已通过。

**注意**：`-T` 表示不分配伪终端（因为 GitHub 不提供 shell）。返回 `exit code 1` 是正常的，不代表失败。

**详细调试**（失败时使用）：

```bash
ssh -vT git@github.com
```

关注输出中这几行，可快速定位问题：

```
debug1: Connecting to ssh.github.com [20.205.243.160] port 443.
debug1: Offering public key: /home/user/.ssh/id_ed25519 ED25519 SHA256:...
debug1: Server accepts key: /home/user/.ssh/id_ed25519 ED25519 SHA256:...
```

- 卡在 `Connecting` → 网络/端口问题
- 有 `Offering public key` 但无 `Server accepts key` → 公钥未添加到 GitHub，或添加到了别的账号
- `no such identity` → `IdentityFile` 路径错误

---

## 4. 配置仓库与 remote origin

有两种常见起点，按你的情况选择。

### 4.1 场景一：远程已有仓库，本地为空（推荐）

```bash
cd /path/to
git clone git@github.com:your-username/your-repo.git
cd your-repo
```

`git clone` 会**自动完成**以下工作，无需手动配置：

- 创建 `.git` 目录
- 写入 `[remote "origin"]` 的 `url` 与 `fetch`
- 建立 `[branch "main"]` 的跟踪关系
- 检出默认分支到工作区

查看结果：

```bash
git remote -v
git branch -vv
```

### 4.2 场景二：本地已有代码，需要关联远程

#### 步骤 1：初始化仓库

```bash
cd /path/to/your-project
git init
git branch -M main
```

#### 步骤 2：添加 remote

```bash
git remote add origin git@github.com:your-username/your-repo.git
```

#### 步骤 3：确认地址格式

```bash
git remote -v
```

期望输出（**必须是 `git@` 开头，不能是 `https://`**）：

```
origin  git@github.com:your-username/your-repo.git (fetch)
origin  git@github.com:your-username/your-repo.git (push)
```

#### 步骤 4：如果已存在 HTTPS 地址，改为 SSH

```bash
git remote set-url origin git@github.com:your-username/your-repo.git
git remote -v
```

> 这是最常见的错误来源：SSH 已经配好且测试通过，但 `remote url` 仍是 `https://`，于是 `push` 依然走 HTTPS 认证，继续要求输入账号密码。

### 4.3 `.git/config` 中 `[remote "origin"]` 的正确形态

配置文件位置：`项目根目录/.git/config`

完整内容示例：

```ini
[core]
	repositoryformatversion = 0
	filemode = true
	bare = false
	logallrefupdates = true
[remote "origin"]
	url = git@github.com:your-username/your-repo.git
	fetch = +refs/heads/*:refs/remotes/origin/*
[branch "main"]
	remote = origin
	merge = refs/heads/main
```

#### `url` 字段

```ini
url = git@github.com:your-username/your-repo.git
```

格式拆解：

```
git          @                          github.com  :  your-username/your-repo.git
┬            ┬                          ┬           ┬  ┬
用户名        分隔符                      主机名        路径
（GitHub 固定为 git）                                  （不含开头斜杠）
```

两种等价写法：

| 形式 | 写法 | 说明 |
|---|---|---|
| SCP 风格 | `git@github.com:owner/repo.git` | 推荐，最短 |
| URL 风格 | `ssh://git@github.com:443/owner/repo.git` | 可显式指定端口 |

若使用 SCP 风格，端口由 `~/.ssh/config` 决定（本方案为 443），**URL 中不写端口**。

#### `fetch` 字段

```ini
fetch = +refs/heads/*:refs/remotes/origin/*
```

这是 refspec 语法，含义是「远程分支到本地远程跟踪分支的映射」：

| 部分 | 含义 |
|---|---|
| `+` | 允许强制更新（非快进也覆盖），用于同步远程的重写历史 |
| `refs/heads/*` | **源**：远程仓库中所有分支（`*` 为通配） |
| `:` | 映射分隔符 |
| `refs/remotes/origin/*` | **目标**：本地的 `origin/xxx` 远程跟踪分支 |

举例：远程有 `main` 和 `dev`，执行 `git fetch` 后，本地会生成/更新：

```
refs/remotes/origin/main
refs/remotes/origin/dev
```

> 注意：远程跟踪分支 `origin/main` 是只读的本地副本，不能直接切换过去修改，需要 `git checkout main` 后操作。

#### `[branch "main"]` 字段

```ini
[branch "main"]
	remote = origin
	merge = refs/heads/main
```

- `remote = origin`：本分支的默认远程是 `origin`
- `merge = refs/heads/main`：`git pull` 时合并远程的哪个分支

这一段由 `git push -u origin main` 或 `git branch -u origin/main` 自动生成。有了它，直接 `git push` / `git pull` 即可，不必每次写 `origin main`。

### 4.4 命令行配置 vs 手工编辑

`.git/config` 是纯文本 INI 文件，手工编辑也能生效，但**推荐始终使用命令**，避免语法错误导致 `fatal: bad config line N`。

| 操作 | 命令 | 等价的手工修改 |
|---|---|---|
| 设置远程地址 | `git remote set-url origin <url>` | 改写 `url =` 行 |
| 新增远程 | `git remote add origin <url>` | 追加整个 `[remote "origin"]` 段 |
| 删除远程 | `git remote remove origin` | 删除整个 `[remote "origin"]` 段 |
| 重命名远程 | `git remote rename origin upstream` | 改段名并同步所有引用 |
| 设置上游分支 | `git branch -u origin/main` | 追加 `[branch "main"]` 段 |
| 查看单项配置 | `git config --local remote.origin.url` | 读取对应行 |

> **不要删除 `.git/config` 文件本身**。它保存了仓库格式版本、远程地址、分支跟踪等关键信息，删除后仓库会处于异常状态，需要重新 `git init`。

### 4.5 提交并推送

```bash
# 建议先配置忽略规则，避免提交缓存、虚拟环境等无关文件
cat > .gitignore <<'EOF'
__pycache__/
*.py[cod]
.venv/
venv/
.ipynb_checkpoints/
.idea/
.vscode/
.DS_Store
*.log
EOF

git add .
git status
git commit -m "init: 项目初始化"
git push -u origin main
```

`-u`（即 `--set-upstream`）的作用：把本地 `main` 与 `origin/main` 绑定，**只需第一次执行**，之后直接 `git push`。

成功输出：

```
Enumerating objects: 12, done.
Counting objects: 100% (12/12), done.
Writing objects: 100% (12/12), 1.23 KiB | 1.23 MiB/s, done.
To github.com:your-username/your-repo.git
 * [new branch]      main -> main
branch 'main' set up to track 'origin/main'.
```

---

## 5. 全链路验证

配置完成后，按**由底层到上层**的顺序逐层验证，任一层失败即可定位问题。

### 5.1 验证层次总览

| 层次 | 验证内容 | 命令 | 成功标志 |
|---|---|---|---|
| 1 | DNS 解析 | `getent hosts github.com` | 返回非 `127.0.0.1` 的 IP |
| 2 | TCP 443 可达 | `nc -zv ssh.github.com 443` | `succeeded` |
| 3 | SSH 认证 | `ssh -T git@github.com` | `Hi your-username!` |
| 4 | Git 远程可读 | `git ls-remote origin` | 列出分支哈希 |
| 5 | 推送 | `git push` | `main -> main` |
| 6 | 拉取 | `git pull` | `Already up to date.` |

### 5.2 第一层：DNS 解析

```bash
getent hosts github.com
getent hosts ssh.github.com
```

期望返回公网 IP，例如：

```
20.205.243.166  github.com
20.205.243.160  ssh.github.com
```

**异常情况**：

- 返回 `127.0.0.1` 或 `0.0.0.0` → hosts 文件被篡改或 DNS 被劫持
- 无输出 → DNS 服务器不可用

排查：

```bash
cat /etc/hosts | grep -i github
cat /etc/resolv.conf
```

若 `/etc/hosts` 中有 github 相关条目且 IP 已失效，删除该行即可。

### 5.3 第二层：TCP 端口可达

```bash
# 标准 SSH 端口
nc -zv github.com 22

# 443 备用端口
nc -zv ssh.github.com 443
```

期望：

```
Connection to ssh.github.com 443 port [tcp/https] succeeded!
```

若未安装 `nc`：

```bash
sudo apt install -y netcat-openbsd
```

或者用 bash 内置的 `/dev/tcp`（无需安装）：

```bash
timeout 5 bash -c 'cat < /dev/null > /dev/tcp/ssh.github.com/443' && echo "443 可达" || echo "443 不通"
```

**异常情况**：

- `Connection refused` → 端口被封或代理未开
- `Connection timed out` → 数据包被丢弃，通常是防火墙
- `Network is unreachable` → 本机无路由，检查网络或代理

### 5.4 第三层：SSH 认证

```bash
ssh -T git@github.com
```

期望：

```
Hi your-username! You've successfully authenticated, but GitHub does not provide shell access.
```

验证实际连接的端口（确认 443 配置生效）：

```bash
ssh -vT git@github.com 2>&1 | grep -E "Connecting to|Offering public key|Server accepts key"
```

期望看到：

```
debug1: Connecting to ssh.github.com [20.205.243.160] port 443.
debug1: Offering public key: /home/user/.ssh/id_ed25519 ED25519 SHA256:...
debug1: Server accepts key: /home/user/.ssh/id_ed25519 ED25519 SHA256:...
```

`port 443` 与 `Server accepts key` 两条同时出现，说明端口重定向与密钥认证均正常。

### 5.5 第四层：Git 远程可读

```bash
cd /path/to/your-project
git remote -v
git ls-remote origin
```

`git ls-remote` 会真正走一次网络，返回远程所有引用：

```
a1b2c3d4e5f6...  HEAD
a1b2c3d4e5f6...  refs/heads/main
```

**这一层通过，说明 Git 与 SSH 已完全打通**，后续 push/pull 必然可用。

也可以查看远程详情：

```bash
git remote show origin
```

期望输出包含：

```
* remote origin
  Fetch URL: git@github.com:your-username/your-repo.git
  Push  URL: git@github.com:your-username/your-repo.git
  HEAD branch: main
  Local branch configured for 'git pull':
    main merges with remote main
```

### 5.6 第五层：推送验证

```bash
# 创建一个测试提交（可跳过，直接推已有提交）
echo "# connection test" >> .connection-test
git add .connection-test
git commit -m "test: 验证 SSH 推送"

# 推送
git push origin main
```

成功输出：

```
To github.com:your-username/your-repo.git
   a1b2c3d..e5f6a7b  main -> main
```

到 GitHub 网页确认该提交已出现，然后清理测试文件：

```bash
git rm .connection-test
git commit -m "chore: 移除连接测试文件"
git push
```

### 5.7 第六层：拉取验证

模拟远程有更新，验证 `pull` 链路：

```bash
# 首次使用可先 fetch，观察是否有更新
git fetch origin
git status

# 拉取当前分支
git pull
```

期望（无更新时）：

```
Already up to date.
```

若有更新：

```
Updating a1b2c3d..e5f6a7b
Fast-forward
 file.txt | 2 +-
 1 file changed, 1 insertion(+), 1 deletion(-)
```

完整验证 clone 链路（可选）：

```bash
cd /tmp
git clone git@github.com:your-username/your-repo.git clone-test
cd clone-test && git log --oneline -3
cd /tmp && rm -rf clone-test
```

clone 成功即证明「DNS → TCP 443 → SSH 认证 → Git 协议」全链路无问题。

---

## 6. 常见问题排查

### 6.1 错误对照表

| 报错 | 原因 | 解决 |
|---|---|---|
| `Failed to connect to github.com port 443 after N ms: Couldn't connect to server` | HTTPS 直连被阻断，或代理未生效 | 改用 SSH 443；或检查代理配置 |
| `remote: Invalid username or token. Password authentication is not supported` | 在 HTTPS 认证中填了账号密码 | 生成 PAT 作为密码；或改用 SSH |
| `Permission denied (publickey)` | 公钥未添加到 GitHub；密钥路径错误；权限过宽 | 检查 `ssh -vT`；确认公钥已上传；`chmod 600` |
| `Host key verification failed` | `known_hosts` 中旧指纹与当前不符 | `ssh-keygen -R ssh.github.com` 后重连 |
| `Connection timed out` / `Connection refused` | 22 端口被封；网络不可达 | 改用 `ssh.github.com:443` |
| `Repository not found` | 仓库不存在；地址拼写错误；无权限；SSH 密钥对应了另一个账号 | 核对 URL 大小写；用 `ssh -T` 确认登录的账号 |
| `fatal: not a git repository` | 当前目录不是仓库根目录 | `cd` 到含 `.git` 的目录 |
| `fatal: No configured push destination` | 未配置 `remote origin` | `git remote add origin <url>` |
| `fatal: The current branch main has no upstream branch` | 未建立跟踪关系 | `git push -u origin main` |
| `fatal: bad config line N in file .git/config` | 手工编辑破坏了 INI 语法 | 修正该行；或从备份恢复 |
| `WARNING: UNPROTECTED PRIVATE KEY FILE` | 私钥权限过宽 | `chmod 600 ~/.ssh/id_ed25519` |
| `Please make sure you have the correct access rights` | 与 `Permission denied` 同类 | 同上 |
| `src refspec main does not match any` | 本地没有 `main` 分支（尚无提交或分支名不同） | `git branch -M main`；先 `git commit` |

### 6.2 排查决策树

```
push 失败
├── 报错是 https:// 相关
│   ├── 提示 invalid username or token → 认证方式错误，改用 SSH
│   └── 提示 couldn't connect           → 网络不通，改用 SSH 443 或配代理
└── 报错是 git@ 相关
    ├── Permission denied (publickey)
    │   ├── ssh -T git@github.com 成功 → remote url 写错（用了别的 ssh 主机名）
    │   └── ssh -T git@github.com 失败 → 公钥/权限/网络问题
    ├── Could not read from remote repository
    │   ├── 仓库不存在或名字拼错 → 核对 GitHub 页面 URL
    │   └── 账号无权限             → 确认密钥属于正确账号
    └── Connection timed out
        └── 22 端口被封 → 配置 HostName ssh.github.com + Port 443
```

### 6.3 关键排查命令合集

```bash
# SSH 详细日志
ssh -vT git@github.com
ssh -vvvT git@github.com

# 查看远程地址（确认不是 https）
git remote -v

# 查看所有配置及来源
git config --list --show-origin

# 查看 SSH 最终生效配置（确认 Host 规则命中）
ssh -G github.com | grep -E "hostname|port|identityfile|user"

# 清除已失效的主机指纹
ssh-keygen -R ssh.github.com
ssh-keygen -R github.com

# 列出 ssh-agent 中的密钥
ssh-add -l
```

`ssh -G github.com` 尤其有用，它会打印解析后的实际配置：

```
hostname ssh.github.com
port 443
user git
identityfile ~/.ssh/id_ed25519
```

如果这里显示的仍是 `hostname github.com` / `port 22`，说明 `~/.ssh/config` 未被正确读取（常见原因：文件权限过宽、`Host` 写错、配置写在错误的用户目录下）。

---

## 7. 日常使用速查

本章只覆盖最高频的操作。完整命令参考见 [第 8 章 Git 常用命令手册](#8-git-常用命令手册)，其中包含分支、标签、stash、冲突处理、历史追溯、危险命令警示等内容。

### 7.1 基本工作流

```bash
git status                    # 查看工作区状态
git diff                      # 查看未暂存的改动
git add <file>                # 暂存指定文件
git add .                     # 暂存所有改动
git commit -m "说明"          # 提交
git push                      # 推送到 origin 的同名分支
```

### 7.2 同步远程

```bash
git fetch                     # 只下载，不合并
git pull                      # 下载并合并到当前分支
git pull --rebase             # 变基合并，历史更线性
```

### 7.3 分支操作

```bash
git switch -c feature/x       # 创建并切换分支
git push -u origin feature/x  # 首次推送新分支
git switch main               # 切回主分支
git branch -vv                # 查看本地分支与跟踪关系
git branch -d feature/x       # 删除本地已合并分支
```

### 7.4 撤销与回退

```bash
git restore <file>            # 撤销工作区改动
git restore --staged <file>   # 取消暂存
git reset --soft HEAD~1       # 撤销最近一次提交，保留改动
git log --oneline -10         # 查看最近提交
git reflog                    # 查看所有 HEAD 移动记录（救命命令）
```

### 7.5 修改配置

```bash
git config --global --list                 # 查看全局配置
git config --local --list                  # 查看仓库配置
git config --global --unset http.proxy     # 删除某项配置
git remote set-url origin <new-url>        # 更换远程地址
```

---

## 8. Git 常用命令手册

第 7 章覆盖高频工作流，本章按功能域给出完整参考。所有命令均可在仓库根目录直接执行。

### 8.1 高频命令总表

| 目的 | 命令 |
|---|---|
| 查看状态 | `git status` |
| 查看改动 | `git diff` |
| 暂存全部 | `git add .` |
| 提交 | `git commit -m "说明"` |
| 推送 | `git push` |
| 拉取 | `git pull` |
| 查看历史 | `git log --oneline -10` |
| 切换分支 | `git switch 分支名` |
| 新建分支 | `git switch -c 新分支` |
| 撤销工作区改动 | `git restore 文件` |
| 查看远程地址 | `git remote -v` |

### 8.2 仓库创建与克隆

| 命令 | 说明 |
|---|---|
| `git init` | 在当前目录初始化新仓库 |
| `git init 目录名` | 创建目录并初始化 |
| `git init --bare` | 创建裸仓库（无工作区，用作服务端） |
| `git clone <url>` | 克隆到同名目录 |
| `git clone <url> 目录名` | 克隆到指定目录 |
| `git clone --depth 1 <url>` | 浅克隆，只取最新一次提交，速度快 |
| `git clone -b 分支名 <url>` | 克隆指定分支 |
| `git clone --recurse-submodules <url>` | 同时初始化子模块 |

### 8.3 配置管理

```bash
git config --global 键 值          # 写入用户全局配置（~/.gitconfig）
git config --local  键 值          # 写入当前仓库（.git/config）
git config --system 键 值          # 写入系统配置（需 root）
git config --global --list         # 列出全局配置
git config --list --show-origin    # 列出全部配置及来源文件
git config --global --unset 键     # 删除某项
git config --global --edit         # 用编辑器打开配置文件
```

常用配置项：

| 键 | 作用 | 推荐值 |
|---|---|---|
| `user.name` | 提交作者名 | 你的 GitHub 用户名 |
| `user.email` | 提交作者邮箱 | GitHub 绑定邮箱 |
| `init.defaultBranch` | 默认分支名 | `main` |
| `core.autocrlf` | 换行符策略 | Linux/WSL 用 `input`，Windows 用 `true` |
| `core.editor` | 默认编辑器 | `vim` / `nano` |
| `color.ui` | 彩色输出 | `auto` |
| `pull.rebase` | pull 默认行为 | `false` 合并，`true` 变基 |
| `push.default` | 默认推送策略 | `simple` |
| `core.ignorecase` | 是否忽略大小写 | macOS/Windows 上常为 `true` |

### 8.4 查看状态与差异

| 命令 | 说明 |
|---|---|
| `git status` | 完整状态 |
| `git status -sb` | 精简状态，含分支跟踪信息 |
| `git diff` | 工作区 vs 暂存区 |
| `git diff --staged` | 暂存区 vs 最新提交（同 `--cached`） |
| `git diff HEAD` | 工作区 vs 最新提交 |
| `git diff 分支1 分支2` | 两个分支的差异 |
| `git diff --stat` | 只显示改动的文件与行数统计 |
| `git diff 提交1 提交2 -- 文件` | 指定文件的历史差异 |
| `git diff --name-only` | 只列出有改动的文件名 |

### 8.5 暂存与提交

| 命令 | 说明 |
|---|---|
| `git add 文件` | 暂存指定文件 |
| `git add .` | 暂存当前目录下所有改动（含新增文件） |
| `git add -A` | 暂存全仓库改动（含新增与删除） |
| `git add -u` | 只暂存已跟踪文件的改动，不含新文件 |
| `git add -p` | 交互式逐块确认，适合拆分提交 |
| `git add -i` | 交互式暂存菜单 |
| `git commit -m "说明"` | 提交暂存内容 |
| `git commit -am "说明"` | 跳过 `add`，提交已跟踪文件的改动（新文件无效） |
| `git commit --amend` | 修改最近一次提交（改信息或补充文件） |
| `git commit --amend --no-edit` | 补充文件但不改提交信息 |
| `git commit --allow-empty -m "说明"` | 创建空提交，常用于触发 CI |
| `git commit --fixup=提交` | 生成 fixup 提交，配合 `rebase --autosquash` 使用 |

`--amend` 注意事项：

```bash
# 只修正提交信息
git commit --amend -m "新的说明"

# 补上漏掉的文件
git add 漏掉的文件
git commit --amend --no-edit
```

> 已推送到远程的提交不要随意 `amend`，会改写历史，导致他人拉取冲突。确需修改时用 `git push --force-with-lease`。

### 8.6 分支管理

| 命令 | 说明 |
|---|---|
| `git branch` | 列出本地分支 |
| `git branch -a` | 列出本地与远程分支 |
| `git branch -r` | 只列远程分支 |
| `git branch -vv` | 显示分支、最新提交与跟踪关系 |
| `git branch 新分支` | 创建分支但不切换 |
| `git branch -m 新名` | 重命名当前分支 |
| `git branch -d 分支` | 删除已合并分支（安全） |
| `git branch -D 分支` | 强制删除分支（未合并也删） |
| `git branch --merged` | 列出已合并到当前分支的分支 |
| `git branch --no-merged` | 列出未合并的分支 |
| `git switch 分支` | 切换分支（推荐） |
| `git switch -c 新分支` | 创建并切换 |
| `git switch -c 新分支 origin/远程分支` | 基于远程分支创建本地分支 |
| `git switch -` | 切回上一个分支 |
| `git checkout 提交哈希` | 临时检出某次提交（detached HEAD） |
| `git branch -u origin/分支` | 设置当前分支的上游 |
| `git push origin --delete 分支` | 删除远程分支 |

### 8.7 远程仓库管理

| 命令 | 说明 |
|---|---|
| `git remote -v` | 查看远程地址 |
| `git remote add origin <url>` | 添加远程 |
| `git remote set-url origin <url>` | 修改远程地址 |
| `git remote rename origin upstream` | 重命名远程 |
| `git remote remove origin` | 删除远程 |
| `git remote show origin` | 查看远程详情（会联网） |
| `git remote prune origin` | 清理远程已删除分支的本地引用 |
| `git ls-remote origin` | 列出远程所有引用（不落地） |

### 8.8 同步：fetch / pull / push

| 命令 | 说明 |
|---|---|
| `git fetch` | 下载远程更新，不合并 |
| `git fetch --all --prune` | 拉取所有远程并清理失效分支 |
| `git pull` | 拉取并合并到当前分支 |
| `git pull --rebase` | 拉取后变基，历史更线性 |
| `git pull origin 分支` | 拉取指定远程分支 |
| `git push` | 推送到已跟踪的上游分支 |
| `git push -u origin main` | 首次推送并建立跟踪关系 |
| `git push origin 分支` | 推送指定分支 |
| `git push origin --tags` | 推送所有标签 |
| `git push --follow-tags` | 推送提交附带的注解标签 |
| `git push --force-with-lease` | 安全强推：远程无他人新提交时才覆盖 |
| `git push --force` | 强推，会覆盖他人提交，慎用 |

**`--force-with-lease` 与 `--force` 的区别**：

- `--force`：无条件覆盖远程，若同事刚推送过，其提交会被抹掉
- `--force-with-lease`：先比对远程引用是否与本地记录一致，不一致则拒绝推送

需要改写历史时，**优先使用 `--force-with-lease`**。

### 8.9 查看历史与追溯

| 命令 | 说明 |
|---|---|
| `git log` | 完整历史 |
| `git log --oneline` | 每行一条，简洁 |
| `git log --oneline --graph --all` | 图形化显示所有分支 |
| `git log -10` | 最近 10 条 |
| `git log --stat` | 显示每次提交的文件改动统计 |
| `git log -p` | 显示每次提交的具体 diff |
| `git log --author="名字"` | 按作者筛选 |
| `git log --since="2024-01-01" --until="2024-12-31"` | 按时间筛选 |
| `git log --grep="关键词"` | 按提交信息搜索 |
| `git log -S"代码片段"` | 搜索引入/删除该字符串的提交（pickaxe） |
| `git log -- 文件路径` | 只看某文件的提交历史 |
| `git log --follow 文件` | 跟踪文件重命名历史 |
| `git show 提交` | 查看某次提交详情 |
| `git show 提交:文件` | 查看某次提交时的文件内容 |
| `git blame 文件` | 逐行显示最后修改者与提交 |
| `git blame -L 10,20 文件` | 只看指定行范围 |
| `git shortlog -sn` | 按提交数统计贡献者 |
| `git describe --tags` | 显示当前提交相对最近标签的位置 |

### 8.10 撤销、回退与恢复

按「影响范围」从轻到重排列：

| 命令 | 影响范围 | 说明 |
|---|---|---|
| `git restore 文件` | 工作区 | 丢弃未暂存的修改（**不可恢复**） |
| `git restore --staged 文件` | 暂存区 | 取消暂存，改动仍在工作区 |
| `git restore --source=HEAD~1 文件` | 工作区 | 把文件恢复到上一次提交的版本 |
| `git checkout -- 文件` | 工作区 | 旧语法，同 `git restore` |
| `git reset HEAD~1` | 暂存区+提交 | 撤销提交，改动保留在工作区（mixed） |
| `git reset --soft HEAD~1` | 提交 | 撤销提交，改动留在暂存区 |
| `git reset --hard HEAD~1` | 全部 | 撤销提交并丢弃改动（**危险**） |
| `git revert 提交` | 新增提交 | 生成一个反向提交来抵消指定提交，**不改历史** |
| `git revert -m 1 合并提交` | 新增提交 | 撤销一次合并提交 |
| `git reflog` | 仅查看 | 查看 HEAD 移动记录，找回误删提交的关键 |
| `git reset --hard 提交哈希` | 全部 | 恢复到 reflog 中的某个状态 |

**`reset` 与 `revert` 的选择**：

| 场景 | 用什么 |
|---|---|
| 本地提交，未推送 | `git reset` |
| 已推送到共享分支 | `git revert` |
| 误删了分支或提交 | 先 `git reflog` 找到哈希，再 `git reset --hard` 或 `git switch -c` |

`git reflog` 示例：

```
a1b2c3d (HEAD -> main) HEAD@{0}: commit: 新增文档
e5f6a7b HEAD@{1}: reset: moving to HEAD~1
c8d9e0f HEAD@{2}: commit: 误删的提交
```

恢复 `c8d9e0f`：

```bash
git switch -c rescue c8d9e0f     # 更安全：新分支上恢复
# 或
git reset --hard c8d9e0f         # 直接回到该状态
```

### 8.11 暂存工作区：stash

用于临时保存未提交的改动，切换分支时不必提交半成品。

| 命令 | 说明 |
|---|---|
| `git stash` | 保存当前改动并清理工作区 |
| `git stash push -m "说明"` | 保存并加备注 |
| `git stash -u` | 连未跟踪文件一起保存 |
| `git stash list` | 查看所有 stash |
| `git stash show -p stash@{0}` | 查看某条 stash 的具体内容 |
| `git stash apply` | 恢复但不删除 stash |
| `git stash pop` | 恢复并删除该条 stash |
| `git stash drop stash@{0}` | 删除指定 stash |
| `git stash clear` | 清空全部 stash（**不可恢复**） |
| `git stash branch 新分支` | 基于 stash 创建新分支并恢复 |

### 8.12 标签管理

标签用于标记发布版本，不随提交移动。

| 命令 | 说明 |
|---|---|
| `git tag` | 列出所有标签 |
| `git tag -l "v1.*"` | 按模式筛选 |
| `git tag v1.0.0` | 创建轻量标签 |
| `git tag -a v1.0.0 -m "发布说明"` | 创建附注标签（推荐，含作者与时间） |
| `git tag -a v1.0.0 提交哈希` | 给历史提交打标签 |
| `git show v1.0.0` | 查看标签详情 |
| `git tag -d v1.0.0` | 删除本地标签 |
| `git push origin v1.0.0` | 推送单个标签 |
| `git push origin --tags` | 推送所有标签 |
| `git push origin --delete v1.0.0` | 删除远程标签 |

### 8.13 冲突处理

冲突发生在 `merge`、`rebase`、`cherry-pick`、`pull` 时。

标准流程：

```bash
# 1. 查看冲突文件
git status

# 2. 打开文件，定位冲突标记
#    <<<<<<< HEAD
#    当前分支内容
#    =======
#    对方分支内容
#    >>>>>>> 分支名

# 3. 手工编辑或使用工具
git mergetool

# 4. 标记已解决
git add 冲突文件

# 5. 继续操作
git commit                    # merge 场景
git rebase --continue         # rebase 场景
git cherry-pick --continue    # cherry-pick 场景
```

放弃本次操作：

| 场景 | 放弃命令 |
|---|---|
| 合并 | `git merge --abort` |
| 变基 | `git rebase --abort` |
| 拣选 | `git cherry-pick --abort` |

常用技巧：

```bash
# 全部采用当前分支版本
git checkout --ours 文件

# 全部采用对方版本
git checkout --theirs 文件

# 列出所有冲突文件
git diff --name-only --diff-filter=U
```

### 8.14 清理与维护

| 命令 | 说明 |
|---|---|
| `git clean -n` | 预览将被删除的未跟踪文件（**先预览**） |
| `git clean -f` | 删除未跟踪文件 |
| `git clean -fd` | 删除未跟踪文件和目录 |
| `git clean -fdx` | 连同 `.gitignore` 忽略的文件一起删（**极其危险**） |
| `git gc` | 垃圾回收，压缩对象 |
| `git gc --prune=now` | 立即清理不可达对象 |
| `git fsck --lost-found` | 查找悬空对象，可用于找回数据 |
| `git count-objects -vH` | 查看仓库体积 |
| `git prune` | 删除不可达对象 |

> `git clean -fdx` 会删掉 `.venv`、`node_modules`、本地配置等所有未跟踪内容，执行前务必先 `git clean -ndx` 预览。

### 8.15 忽略规则

`.gitignore` 写在仓库根目录，只对**未跟踪文件**生效。已被跟踪的文件需先 `git rm --cached`。

| 语法 | 含义 |
|---|---|
| `*.log` | 忽略所有 `.log` 文件 |
| `/build/` | 只忽略根目录下的 `build` 目录 |
| `build/` | 忽略任意层级的 `build` 目录 |
| `**/temp` | 忽略任意层级的 `temp` |
| `doc/*.txt` | 只忽略 `doc` 下第一层 txt |
| `!important.log` | 不忽略该文件（排除规则，须写在忽略规则之后） |
| `# 注释` | 注释行 |
| 空行 | 无意义，用于分隔 |

排查「为什么某个文件被忽略了」：

```bash
git check-ignore -v 文件路径
```

输出会指明是哪个 `.gitignore` 文件的哪一行生效。

移除已被跟踪但想忽略的文件：

```bash
git rm --cached 文件
echo "文件" >> .gitignore
git commit -m "chore: 停止跟踪该文件"
```

### 8.16 别名配置

把长命令缩短，全局生效：

```bash
git config --global alias.st  "status -sb"
git config --global alias.co  "checkout"
git config --global alias.br  "branch"
git config --global alias.ci  "commit"
git config --global alias.last "log -1 HEAD --stat"
git config --global alias.lg  "log --oneline --graph --all --decorate"
git config --global alias.unstage "restore --staged"
```

使用：

```bash
git st          # 等价于 git status -sb
git lg          # 图形化历史
git unstage 文件
```

查看已配置的别名：

```bash
git config --global --get-regexp alias
```

### 8.17 危险命令警示

| 命令 | 后果 | 可恢复性 |
|---|---|---|
| `git reset --hard` | 丢弃工作区与暂存区改动 | 未提交部分**无法恢复** |
| `git clean -fdx` | 删除所有未跟踪文件 | **无法恢复** |
| `git push --force` | 覆盖远程历史 | 需他人本地副本或 reflog 挽救 |
| `git branch -D` | 强删未合并分支 | 可用 `reflog` 找到后恢复 |
| `git checkout -- .` | 丢弃全部工作区改动 | **无法恢复** |
| `git stash clear` | 清空所有 stash | 基本无法恢复 |
| `rm -rf .git` | 删除整个仓库元数据 | 只能从远程重新 clone |
| `git reset --hard HEAD~N` | 回退多次提交 | 未推送部分可用 `reflog` 恢复 |
| `git filter-branch` / `git filter-repo` | 重写全部历史 | 必须提前备份 |

执行任何带 `--hard`、`--force`、`-f`、`clean` 的命令前，先做一次：

```bash
git status
git stash push -u -m "操作前备份"
```

---

## 附录 A. 完整配置文件对照

### A.1 `~/.ssh/config`

```ini
Host github.com
    HostName ssh.github.com
    Port 443
    User git
    IdentityFile ~/.ssh/id_ed25519
    IdentitiesOnly yes
    ServerAliveInterval 60
    ServerAliveCountMax 3
```

### A.2 `~/.gitconfig`

```ini
[user]
	name = your-username
	email = your_email@example.com
[init]
	defaultBranch = main
[core]
	autocrlf = input
	editor = vim
[color]
	ui = auto
[pull]
	rebase = false
```

### A.3 项目 `.git/config`

```ini
[core]
	repositoryformatversion = 0
	filemode = true
	bare = false
	logallrefupdates = true
[remote "origin"]
	url = git@github.com:your-username/your-repo.git
	fetch = +refs/heads/*:refs/remotes/origin/*
[branch "main"]
	remote = origin
	merge = refs/heads/main
```

### A.4 文件权限要求

| 路径 | 权限 | 说明 |
|---|---|---|
| `~/.ssh` | `700` | 仅本人可进入 |
| `~/.ssh/id_ed25519` | `600` | 私钥，仅本人可读写 |
| `~/.ssh/id_ed25519.pub` | `644` | 公钥，可公开 |
| `~/.ssh/config` | `600` | 可设为 `644`，但 `600` 更稳妥 |
| `~/.ssh/known_hosts` | `644` | 主机指纹库 |

---

## 附录 B. 网络受限环境的代理转发

当 `ssh.github.com:443` 也无法直连时，需要让 SSH 走 HTTP/SOCKS 代理。

### B.1 前提

`~/.gitconfig` 中的 `http.proxy` **对 SSH 无效**，必须用 `ProxyCommand`。

### B.2 安装 netcat

```bash
sudo apt install -y netcat-openbsd
```

### B.3 配置 ProxyCommand

```ini
Host github.com
    HostName ssh.github.com
    Port 443
    User git
    IdentityFile ~/.ssh/id_ed25519
    IdentitiesOnly yes
    ProxyCommand nc -X connect -x 127.0.0.1:7890 %h %p
```

参数说明：

| 参数 | 含义 |
|---|---|
| `nc` | netcat，这里作为代理客户端 |
| `-X connect` | 使用 HTTP CONNECT 方法（若代理是 SOCKS5，改为 `-X 5`） |
| `-x 127.0.0.1:7890` | 代理地址与端口 |
| `%h` | 目标主机（由 `HostName` 替换） |
| `%p` | 目标端口（由 `Port` 替换） |

### B.4 WSL2 的特殊情况

WSL2 是独立虚拟机，`127.0.0.1` 指向 WSL 自身，**不是 Windows**。要使用 Windows 上的代理软件，需：

1. 在 Windows 代理软件中开启「允许局域网连接」/ `Allow LAN`
2. 在 WSL 中获取 Windows 主机 IP：

```bash
ip route show default | awk '{print $3}'
```

3. 把 `ProxyCommand` 中的地址改为该 IP：

```ini
ProxyCommand nc -X connect -x 172.20.16.1:7890 %h %p
```

4. 先用 curl 验证代理端口可达：

```bash
curl -x http://172.20.16.1:7890 -I https://github.com
```

若 Windows 11 版本支持，可在 `C:\Users\用户名\.wslconfig` 中启用镜像网络，使 `127.0.0.1` 直接指向 Windows：

```ini
[wsl2]
networkingMode=mirrored
```

修改后在 PowerShell 执行 `wsl --shutdown` 并重新打开 WSL。

### B.5 SOCKS5 代理写法

```ini
ProxyCommand nc -X 5 -x 172.20.16.1:7891 %h %p
```

或用 `socat`：

```bash
sudo apt install -y socat
```

```ini
ProxyCommand socat - PROXY:172.20.16.1:%h:%p,proxyport=7890
```

---

## 附录 C. 一键配置脚本

脚本会完成除「GitHub 网页添加公钥」外的全部步骤，执行前请确认占位符已替换。

```bash
#!/usr/bin/env bash
set -euo pipefail

GIT_USER_NAME="your-username"
GIT_USER_EMAIL="your_email@example.com"
PROJECT_DIR="/path/to/your-project"
REPO_NAME="your-repo"
KEY_PATH="$HOME/.ssh/id_ed25519"

echo "==> 1. 检查 Git"
command -v git >/dev/null || { echo "请先安装 git"; exit 1; }
if git --version | grep -q "windows"; then
  echo "检测到 Windows 版 Git，请改用 Linux 版"; exit 1
fi
git --version

echo "==> 2. 配置全局身份"
git config --global user.name  "$GIT_USER_NAME"
git config --global user.email "$GIT_USER_EMAIL"
git config --global init.defaultBranch main
git config --global core.autocrlf input

echo "==> 3. 生成 SSH 密钥"
mkdir -p "$HOME/.ssh"
chmod 700 "$HOME/.ssh"
if [ ! -f "$KEY_PATH" ]; then
  ssh-keygen -t ed25519 -C "$GIT_USER_EMAIL" -f "$KEY_PATH" -N ""
else
  echo "密钥已存在，跳过生成"
fi
chmod 600 "$KEY_PATH"
chmod 644 "$KEY_PATH.pub"

echo "==> 4. 写入 SSH 配置（443 端口）"
cat > "$HOME/.ssh/config" <<EOF
Host github.com
    HostName ssh.github.com
    Port 443
    User git
    IdentityFile $KEY_PATH
    IdentitiesOnly yes
    ServerAliveInterval 60
    ServerAliveCountMax 3
EOF
chmod 600 "$HOME/.ssh/config"

echo "==> 5. 关联远程仓库"
cd "$PROJECT_DIR"
git init -q 2>/dev/null || true
git branch -M main
if git remote | grep -q "^origin$"; then
  git remote set-url origin "git@github.com:${GIT_USER_NAME}/${REPO_NAME}.git"
else
  git remote add origin "git@github.com:${GIT_USER_NAME}/${REPO_NAME}.git"
fi
git remote -v

echo "==> 6. 完成"
echo "请将以下公钥添加到 GitHub → Settings → SSH and GPG keys："
echo "-------------------------------------------------------------"
cat "$KEY_PATH.pub"
echo "-------------------------------------------------------------"
echo "添加后执行：ssh -T git@github.com"
echo "然后推送： git push -u origin main"
```

使用步骤：

```bash
chmod +x setup-git-ssh.sh
./setup-git-ssh.sh
```

---

## 完成标准

全部配置到位后，下列检查应全部通过：

```bash
ssh -T git@github.com
# Hi your-username! You've successfully authenticated...

git remote -v
# origin  git@github.com:your-username/your-repo.git (fetch)
# origin  git@github.com:your-username/your-repo.git (push)

git ls-remote origin
# 列出远程分支哈希

git status
# Your branch is up to date with 'origin/main'.

git push
# Everything up-to-date
```

六项全部符合，说明 DNS 解析、TCP 443 连通、SSH 密钥认证、Git 远程读写、分支跟踪关系均已正确建立。
