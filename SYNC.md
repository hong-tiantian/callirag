# 两机器同步规范

## 角色
- **远程 D:\htt\callirag**：真相之源，跑数据生成 + 训练，写 outputs/
- **本地 D:\00_project\callirag**：clone 自 GitHub，看代码 + 小数据，不跑训练

## 唯一允许的工作流

### 本地（改代码）
```bash
git pull
# 改代码
git add -A
git commit -m "..."
git push
```

### 远程（拉改动 + 跑实验）
```bash
git pull
# 跑实验、写 outputs
git add retrieval_data_prepare/outputs/*.json retrieval_data_prepare/outputs/*.jsonl
git commit -m "..."
git push
```

## 铁律
1. 只用 `main` 一个分支
2. 永远不 `git push --force`
3. push 前先 `git pull`
4. 图像永远不 git add（.gitignore 兜底；style/gt 例外已配白名单）
5. 不用 submodule（已废弃）
6. 大文件（图像、ckpt、生成结果数千张）走 scp/rclone

## 大文件传输
远程 → 本地：
```bash
scp -r user@<remote>:/d/htt/callirag/retrieval_data_prepare/outputs/baseline ./local/path
```

## baseline_clean/ 不入 git
`baseline_clean/FontDiffuser` 和 `baseline_clean/VQ-Font` 是 pristine 参考拷贝，不修改、不上 git。需要 diff 时各机器自行 clone：

```bash
mkdir -p baseline_clean
git clone git@github.com:hong-tiantian/FontDiffuser.git baseline_clean/FontDiffuser
git clone git@github.com:hong-tiantian/VQ-Font.git baseline_clean/VQ-Font
```

## 紧急回滚
```bash
git log --oneline -10
git reset --hard <commit>   # 破坏性，用前确认
```

## 历史负担说明
之前约 38 张生成图像曾入 git 历史（约 78MB）。本次清理通过 `git rm --cached` 让它们退出当前索引，但历史里仍存在。不做 `git filter-repo`（风险高），接受这点历史体积。
