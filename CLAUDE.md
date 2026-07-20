# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python automation project. The repository is currently empty / newly initialized — update this file as the codebase grows with actual commands (setup, lint, test, run) and architecture notes.

## Git Workflow

- **コードを変更したら、その都度コミットしてGitHubへプッシュすること。** 変更をローカルに溜め込まず、1つの意味のある変更単位ごとにコミット・プッシュを行う。
- コミットメッセージは変更内容が分かるように簡潔に書く。
- プッシュ前に `git status` / `git diff` で差分を確認し、意図しないファイル(認証情報や一時ファイルなど)が含まれていないことを確認する。
- force push など破壊的な操作は行わない。
