#!/usr/bin/env bash
set -euo pipefail

REPO_URL_HTTPS="https://github.com/Tanglumy/Finance-Bro.git"

step() { echo; echo "==> $*"; }

# 0) 确认在 Git 仓库
step "检查是否在 Git 仓库目录"
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "❌ 当前目录不是 Git 仓库。请先 cd 到 Finance-Bro 仓库根目录再运行。"
  exit 1
fi
git status -sb || true

# 1) 远端配置：确保 origin 存在且指向 HTTPS
step "配置/修复远端 origin"
if git remote | grep -qx origin; then
  git remote set-url origin "$REPO_URL_HTTPS"
else
  git remote add origin "$REPO_URL_HTTPS"
fi
git remote -v

# 2) 认证：HTTPS 需要 PAT。先设置凭证助手（macOS）
step "设置凭证助手（macOS）"
if [[ "$(uname -s)" == "Darwin" ]]; then
  git config --global credential.helper osxkeychain || true
fi

# 3) 测试连通性（这里会触发登录框；用户名=GitHub用户名，密码=PAT）
step "测试与 origin 的连通性（可能会要求输入用户名/PAT）"
git ls-remote origin >/dev/null

# 4) 确保当前在一个分支而非游离 HEAD，并把分支名对齐 main
step "对齐分支为 main（若当前不是分支，创建/切换到 main）"
current_branch="$(git symbolic-ref --quiet --short HEAD || true)"
if [[ -z "${current_branch}" ]]; then
  # 游离 HEAD，强制建一个 main 指向当前提交
  git checkout -B main
elif [[ "${current_branch}" != "main" ]]; then
  # 你的工作分支不是 main，也允许直接推到远端 main
  echo "当前分支是 ${current_branch}，将以当前 HEAD 推送到远端 main"
fi

# 5) 强推（带保护）
step "强推到远端 main（--force-with-lease）"
git push origin HEAD:main --force-with-lease -u

echo
echo "✅ 完成：已推送到 $REPO_URL_HTTPS 的 main"
echo "如遇 push protection 再次拦截，复制最新报错的 commit 哈希给我，我来进一步清理。"