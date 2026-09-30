# ためっこ 修正版

## 今回の変更
- 下部ナビ（ホーム / 入出金 / 記録 / メニュー）を全画面から削除
- ショップ・ミッション・図鑑・アイテムをホーム上のポップアップ表示に変更
- ポップアップ右上の「×」で閉じられる
- ショップ購入・ミッション報酬受取・アイテム使用後も該当ポップアップへ戻る
- 目標・遠征・設定・親管理・入出金などは専用画面へ遷移
- 専用画面は「‹」戻るボタンで前の画面へ戻る
- ホームの各メニューは static/images/*.png のPNGアイコンを使用

## PNG名
shop_icon.png / mission_icon.png / book_icon.png / goal_icon.png / expedition_icon.png / item_icon.png / settings_icon.png / parent_icon.png / money_icon.png / room_bg.png

画像を変更したい場合は、同じファイル名で `static/images/` のPNGを差し替えてください。

## 起動
```powershell
python app.py
```
ブラウザで http://127.0.0.1:5000 を開きます。
