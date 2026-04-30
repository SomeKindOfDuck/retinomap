# Retinomap
Retinotopic mapを作成するための刺激提示や解析プログラムです。

## Install

このプロジェクトは Python パッケージマネージャー `uv` で管理されています。  
依存関係のインストールや実行には `uv` を使用してください。

まず、各自の環境に `uv` をインストールしてください。  
インストール方法は[公式ドキュメント](https://docs.astral.sh/uv/)を参照してください。  

もしも`git`が各自の環境になければ、あらかじめインストールしてください。  
インストール方法は[公式ドキュメント](https://git-scm.com/install/linux)を参照してください。

### `uv`と`git`のインストール後

ターミナル上で以下のコマンドを実行します。
```
git clone https://github.com/SomeKindOfDuck/retinomap
cd retinomap
```

ターミナル上で`uv sync`を実行して依存関係をインストールします。
問題なくインストールできたら、`uv run retinomap`を実行すると、GUIが立ち上がります。

またプロジェクト直下で`uv tool install .`を実行することで、`retinomap`や`sanity-check`、などのコマンドがプロジェクト外のディレクトリでも使用できるようになります。  
この方法であれば、`uv run`を明示することなく、使用することができます。

## 使い方
### retinomap
分からなかったら聞いてください。

### sanity-check
刺激提示後に作成されるlogファイルを引数に渡す（`sanity-check ログファイルのパス`）ことで、コマ落ちなどがないかを調べることができます。  
