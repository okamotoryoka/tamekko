from flask import (

    Flask,

    render_template,

    request,

    redirect,

    url_for,

    flash,

    session,

    Response,

)

from datetime import date, datetime

import csv

import io



app = Flask(__name__)

app.secret_key = "tamekko-secret-key"





# =========================================================

# 簡易データ

# ※あとでDBに置き換える

# =========================================================



account = {

    "id": "child01",

    "password": "1234",

    "name": "りょうか",

    "pin": "1234",

    # お小遣い設定

    "allowance": 3000,

    "pay_day": 25,

    # 貯金

    "balance": 3500,

    # コイン

    "coin": 1260,

    # 貯金目標

    "goal_name": "ゲーム機",

    "goal_amount": 10000,

    # ペット

    "pet": "みどりん",

    "level": 3,

    "exp": 180,

    "energy": 80,

    # デイリーログイン

    "last_login": None,

    # 遠征

    "last_expedition": None,

}





# =========================================================

# 入出金データ

# =========================================================



transactions_data = [

    {

        "id": 1,

        "type": "入金",

        "category": "おこづかい",

        "amount": 1000,

        "status": "承認済み",

        "date": "2026-09-20",

    },

    {

        "id": 2,

        "type": "出金",

        "category": "おかし",

        "amount": 150,

        "status": "登録済み",

        "date": "2026-09-21",

    },

]





# 仮入金

pending_deposits = [

    {"id": 1, "amount": 500, "status": "承認待ち", "date": "2026-09-28"}

]





# =========================================================

# ショップ

# =========================================================



shop_items = [

    {"id": 1, "name": "りんご", "price": 100, "icon": "🍎", "effect": 10},

    {"id": 2, "name": "ケーキ", "price": 200, "icon": "🍰", "effect": 20},

    {"id": 3, "name": "ボール", "price": 300, "icon": "⚽", "effect": 15},

    {"id": 4, "name": "リボン", "price": 500, "icon": "🎀", "effect": 25},

]





owned_items = {1: 2, 2: 1, 3: 1, 4: 0}





purchase_history_data = []





# =========================================================

# ミッション

# =========================================================



missions_data = [

    {

        "id": 1,

        "name": "アプリを開こう",

        "description": "今日アプリを開く",

        "reward": 10,

        "status": "未クリア",

    },

    {

        "id": 2,

        "name": "100円貯金しよう",

        "description": "100円以上貯金する",

        "reward": 10,

        "status": "受取可能",

    },

    {

        "id": 3,

        "name": "支出を記録しよう",

        "description": "出金を1回記録する",

        "reward": 20,

        "status": "受取済み",

    },

]





# =========================================================

# 共通処理

# =========================================================





def daily_login_check():



    today = date.today().isoformat()



    # 今日まだログインしていない

    if account["last_login"] != today:



        account["last_login"] = today



        # デイリーミッションをクリア

        for mission in missions_data:



            if mission["id"] == 1:



                if mission["status"] == "未クリア":

                    mission["status"] = "受取可能"





def pet_image():



    energy = account["energy"]



    if energy >= 70:

        return "みどりん.png"



    elif energy >= 30:

        return "みどりん普通.png"



    else:

        return "みどりん疲れ.png"





# =========================================================

# ホーム

# =========================================================





@app.route("/")

def home():

    daily_login_check()



    goal_amount = account.get("goal_amount") or 0

    goal_percent = (

        min(100, int(account["balance"] * 100 / goal_amount)) if goal_amount else 0

    )



    # ホームのポップアップで使うデータ

    owned = []

    for item in shop_items:

        count = owned_items.get(item["id"], 0)

        if count > 0:

            data = item.copy()

            data["count"] = count

            owned.append(data)



    all_received = all(mission["status"] == "受取済み" for mission in missions_data)



    return render_template(

        "home.html",

        account=account,

        pet_image=pet_image(),

        goal_percent=goal_percent,

        shop_items=shop_items,

        owned_items_list=owned,

        missions=missions_data,

        all_received=all_received,

        purchase_history=purchase_history_data,

        open_popup=request.args.get("popup", ""),

    )





# =========================================================

# ログイン

# =========================================================





@app.route("/login", methods=["GET", "POST"])

def login():



    if request.method == "POST":



        login_id = request.form.get("login_id", "").strip()

        password = request.form.get("password", "").strip()



        if login_id != account["id"] or password != account["password"]:



            flash("IDまたはパスワードが正しくありません")



            return render_template("login.html")



        session["logged_in"] = True



        daily_login_check()



        return redirect(url_for("home"))



    return render_template("login.html")





# =========================================================

# ログアウト

# =========================================================





@app.route("/logout")

def logout():



    session.clear()



    return redirect(url_for("login"))





# =========================================================

# キャラ

# =========================================================





@app.route("/character")

def character():



    return redirect(url_for("home"))





# =========================================================

# ペット変更

# =========================================================





@app.route("/character/select", methods=["GET", "POST"])

def character_select():



    pets = ["みどりん", "キンケツル", "さんざ犬"]



    if request.method == "POST":



        selected = request.form.get("pet")



        if not selected:



            flash("ペットをえらんでね")



            return render_template("character_select.html", pets=pets, account=account)



        account["pet"] = selected



        flash("ペットを変更したよ！")



        return redirect(url_for("home"))



    return render_template("character_select.html", pets=pets, account=account)





# =========================================================

# 入出金トップ

# =========================================================





# =========================================================

# 入出金

# =========================================================





@app.route("/transactions", methods=["GET", "POST"])

def transactions():



    # 出金で使用する3分類

    categories = [

        "必要",

        "ほしい",

        "無駄づかい",

    ]



    # =====================================================

    # POST

    # =====================================================

    if request.method == "POST":



        transaction_type = request.form.get("type", "").strip()



        # =================================================

        # 入金

        # =================================================

        if transaction_type == "deposit":



            amount = request.form.get("amount", type=int)



            memo = request.form.get("memo", "").strip()



            # 金額チェック

            if amount is None or amount <= 0:



                flash("金額を入力してね")



                return redirect(url_for("transactions"))



            # 新しい申請ID

            new_id = max([item["id"] for item in pending_deposits], default=0) + 1



            # 承認待ちとして登録

            pending_deposits.append(

                {

                    "id": new_id,

                    "amount": amount,

                    "status": "承認待ち",

                    "date": date.today().isoformat(),

                    "memo": memo,

                }

            )



            # この時点では残高は増やさない

            # 親が承認したときに加算する



            flash("おうちの人に入金を申請したよ！")



            return redirect(url_for("transactions"))



        # =================================================

        # 出金

        # =================================================

        elif transaction_type == "withdrawal":



            # -------------------------------------------------

            # transactions.html から

            # 3項目の金額をそれぞれ受け取る

            # -------------------------------------------------



            amount_necessary = request.form.get("amount_necessary", type=int) or 0



            amount_want = request.form.get("amount_want", type=int) or 0



            amount_waste = request.form.get("amount_waste", type=int) or 0



            # -------------------------------------------------

            # カテゴリと金額

            # -------------------------------------------------



            amounts = {

                "必要": amount_necessary,

                "ほしい": amount_want,

                "無駄づかい": amount_waste,

            }



            # -------------------------------------------------

            # マイナス値は禁止

            # -------------------------------------------------



            for category, amount in amounts.items():



                if amount < 0:



                    flash("正しい金額を入力してね")



                    return redirect(url_for("transactions"))



            # -------------------------------------------------

            # 0円の項目を除外

            #

            # 例

            #

            # 必要      3000

            # ほしい    1000

            # 無駄       0

            #

            # ↓

            #

            # 必要 3000

            # ほしい 1000

            #

            # の2件だけ登録

            # -------------------------------------------------



            entered_items = {

                category: amount for category, amount in amounts.items() if amount > 0

            }



            # -------------------------------------------------

            # 何も入力されていない

            # -------------------------------------------------



            if not entered_items:



                flash("使った金額を入力してね")



                return redirect(url_for("transactions"))



            # -------------------------------------------------

            # 合計金額

            # -------------------------------------------------



            total_amount = sum(entered_items.values())



            # -------------------------------------------------

            # 残高チェック

            # -------------------------------------------------



            if total_amount > account["balance"]:



                flash("貯金額が足りないよ")



                return redirect(url_for("transactions"))



            # -------------------------------------------------

            # 次の履歴ID

            # -------------------------------------------------



            next_id = max([item["id"] for item in transactions_data], default=0) + 1



            # -------------------------------------------------

            # 1カテゴリにつき1件の履歴として保存

            # -------------------------------------------------



            for category, amount in entered_items.items():



                transactions_data.append(

                    {

                        "id": next_id,

                        "type": "出金",

                        "category": category,

                        "amount": amount,

                        "status": "登録済み",

                        "date": date.today().isoformat(),

                        "memo": "",

                    }

                )



                next_id += 1



            # -------------------------------------------------

            # 残高は「合計額」を1回だけ減らす

            # -------------------------------------------------



            account["balance"] -= total_amount



            # -------------------------------------------------

            # 支出ミッション

            # -------------------------------------------------



            for mission in missions_data:



                if mission["id"] == 3:



                    if mission["status"] == "未クリア":



                        mission["status"] = "受取可能"



            # -------------------------------------------------

            # 完了

            # -------------------------------------------------



            flash(f"{total_amount:,}円の支出を記録したよ！")



            return redirect(url_for("history"))



        # =================================================

        # typeがおかしい場合

        # =================================================



        else:



            flash("入金か出金を選んでね")



            return redirect(url_for("transactions"))



    # =====================================================

    # GET

    # =====================================================



    return render_template(
        "transactions.html",
        account=account,
        categories=categories,
        pet_image=pet_image(),
        mode=request.args.get("mode", "withdrawal"),
    )





# =========================================================

# 出金編集

# =========================================================





@app.route("/withdraw/edit/<int:transaction_id>", methods=["GET", "POST"])

def edit_withdraw(transaction_id):



    target = next(

        (

            x

            for x in transactions_data

            if x["id"] == transaction_id and x["type"] == "出金"

        ),

        None,

    )



    if target is None:



        flash("出金データが見つかりません")



        return redirect(url_for("history"))



    categories = ["必要", "ほしい", "無駄づかい"]



    if request.method == "POST":



        category = request.form.get("category")



        amount = request.form.get("amount", type=int)



        if not category:



            flash("何に使ったか選んでね")



            return redirect(request.url)



        if not amount:



            flash("使ったお金を入力してね")



            return redirect(request.url)



        old_amount = target["amount"]



        difference = amount - old_amount



        if difference > 0 and difference > account["balance"]:



            flash("貯金額が足りないよ")



            return redirect(request.url)



        account["balance"] -= difference



        target["category"] = category

        target["amount"] = amount



        flash("出金内容を更新したよ！")



        return redirect(url_for("history"))



    return render_template(

        "withdraw_edit.html", transaction=target, categories=categories

    )





# =========================================================

# 入出金履歴

# =========================================================





@app.route("/history")

def history():



    return render_template(

        "history.html", transactions=transactions_data, account=account

    )





# =========================================================

# CSV出力

# =========================================================





@app.route("/history/csv")

def history_csv():



    output = io.StringIO()



    writer = csv.writer(output)



    writer.writerow(["日付", "種類", "種目", "金額", "状態"])



    for item in transactions_data:



        writer.writerow(

            [

                item["date"],

                item["type"],

                item["category"],

                item["amount"],

                item["status"],

            ]

        )



    csv_data = "\ufeff" + output.getvalue()



    return Response(

        csv_data,

        mimetype="text/csv",

        headers={"Content-Disposition": "attachment; filename=history.csv"},

    )





# =========================================================

# ショップ

# =========================================================





@app.route("/shop")

def shop():



    return render_template("shop.html", items=shop_items, account=account)





# =========================================================

# 購入

# =========================================================





@app.route("/shop/buy/<int:item_id>", methods=["POST"])

def buy_item(item_id):



    item = next((x for x in shop_items if x["id"] == item_id), None)



    if item is None:



        flash("アイテムが見つからないよ")



        return redirect(url_for("home", popup="shop"))



    if account["coin"] < item["price"]:



        flash("コインが足りないよ！")



        return redirect(url_for("home", popup="shop"))



    account["coin"] -= item["price"]



    owned_items[item_id] = owned_items.get(item_id, 0) + 1



    purchase_history_data.append(

        {

            "name": item["name"],

            "price": item["price"],

            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),

        }

    )



    flash(f'{item["name"]}を購入したよ！')



    return redirect(url_for("home", popup="shop"))





# =========================================================

# 所持アイテム

# =========================================================





@app.route("/items")

def items():



    items = []



    for item in shop_items:



        count = owned_items.get(item["id"], 0)



        if count > 0:



            data = item.copy()

            data["count"] = count



            items.append(data)



    return render_template("items.html", items=items)





# =========================================================

# アイテム使用

# =========================================================





@app.route("/items/use/<int:item_id>", methods=["POST"])

def use_item(item_id):



    count = owned_items.get(item_id, 0)



    if count <= 0:



        flash("アイテムを持ってないよ")



        return redirect(url_for("home", popup="items"))



    item = next((x for x in shop_items if x["id"] == item_id), None)



    owned_items[item_id] -= 1



    account["energy"] = min(100, account["energy"] + item["effect"])



    flash(f'{item["name"]}を使ったよ！')



    return redirect(url_for("home", popup="items"))





# =========================================================

# 購入履歴

# =========================================================





@app.route("/purchase-history")

def purchase_history():



    return render_template("purchase_history.html", history=purchase_history_data)





# =========================================================

# ミッション

# =========================================================





@app.route("/missions")

def missions():



    all_received = all(x["status"] == "受取済み" for x in missions_data)



    return render_template(

        "missions.html", missions=missions_data, all_received=all_received

    )





# =========================================================

# ミッション報酬

# =========================================================





@app.route("/missions/receive/<int:mission_id>", methods=["POST"])

def receive_mission(mission_id):



    mission = next((x for x in missions_data if x["id"] == mission_id), None)



    if mission is None or mission["status"] != "受取可能":



        flash("報酬の受取に失敗しました。")



        return redirect(url_for("home", popup="missions"))



    account["coin"] += mission["reward"]



    mission["status"] = "受取済み"



    flash(f'{mission["reward"]}コインGET！')



    return redirect(url_for("home", popup="missions"))





# =========================================================

# 遠征

# =========================================================





@app.route("/expedition", methods=["GET", "POST"])

def expedition():



    today = date.today().isoformat()



    already_done = account["last_expedition"] == today



    if request.method == "POST":



        if already_done:



            flash("きょうはもうつかれたよ")



            return redirect(url_for("expedition"))



        # 即時完了

        reward = 30



        account["coin"] += reward



        account["last_expedition"] = today



        return render_template("expedition_result.html", reward=reward, account=account)



    return render_template("expedition.html", already_done=already_done)





# =========================================================

# 貯金目標

# =========================================================





@app.route("/goal", methods=["GET", "POST"])

def goal():



    if request.method == "POST":



        goal_name = request.form.get("goal_name", "").strip()



        goal_amount = request.form.get("goal_amount", type=int)



        if not goal_name or not goal_amount:



            flash("このフィールドを入力してください")



            return redirect(url_for("goal"))



        account["goal_name"] = goal_name



        account["goal_amount"] = goal_amount



        flash("貯金目標を保存したよ！")



        return redirect(url_for("goal"))



    return render_template("goal.html", account=account)





# =========================================================

# AIサポート

# =========================================================





@app.route("/ai")

def ai():



    if not account["goal_name"] or not account["goal_amount"]:



        return render_template(

            "ai.html", message="かいたいものをいれてね", account=account

        )



    if not account["allowance"] or not account["pay_day"]:



        return render_template(

            "ai.html",

            message=("おこづかいの きんがくと " "もらうひを きめてね！"),

            account=account,

        )



    remaining = max(account["goal_amount"] - account["balance"], 0)



    if remaining == 0:



        message = (

            f'{account["pet"]}だよ！'

            f'{account["goal_name"]}のための'

            "ちょきん、もくひょうたっせい！"

            "すごいね！"

        )



    else:



        months = max(1, (remaining + account["allowance"] - 1) // account["allowance"])



        message = (

            f'{account["pet"]}だよ！ '

            f'{account["goal_name"]}まで'

            f"あと{remaining:,}円！ "

            f"おこづかいをためると"

            f"だいたい{months}か月で"

            "とどきそうだよ。"

            "いっしょにがんばろう！"

        )



    return render_template(

        "ai.html", message=message, account=account, remaining=remaining

    )





# =========================================================

# メニュー

# =========================================================





@app.route("/menu")

def menu():



    return render_template("menu.html", account=account)





# =========================================================

# 設定

# =========================================================





@app.route("/settings")

def settings():



    return render_template("settings.html", account=account)





# =========================================================

# 設定変更PIN

# =========================================================





@app.route("/settings/pin/<setting_name>", methods=["GET", "POST"])

def settings_pin(setting_name):



    if not account["pin"]:



        flash("PINコードが登録されていません")



        return redirect(url_for("settings"))



    if request.method == "POST":



        pin = request.form.get("pin", "")



        if not pin:



            flash("このフィールドを入力してください")



            return redirect(request.url)



        if pin != account["pin"]:



            flash("登録されている値と違います")



            return redirect(request.url)



        if setting_name == "allowance":



            return redirect(url_for("allowance"))



        if setting_name == "pin":



            return redirect(url_for("pin_update"))



    return render_template("settings_pin.html", setting_name=setting_name)





# =========================================================

# お小遣い設定

# =========================================================





@app.route("/allowance", methods=["GET", "POST"])

def allowance():



    if request.method == "POST":



        amount = request.form.get("allowance", type=int)



        pay_day = request.form.get("pay_day", type=int)



        if amount is None or pay_day is None:



            flash("このフィールドを入力してください")



            return redirect(url_for("allowance"))



        # 簡易的な規定値

        if amount > 100000:



            flash("値が規定値を超えています")



            return redirect(url_for("allowance"))



        if pay_day < 1 or pay_day > 31:



            flash("支給日は1〜31で入力してください")



            return redirect(url_for("allowance"))



        account["allowance"] = amount

        account["pay_day"] = pay_day



        flash("お小遣い設定を保存しました")



        return redirect(url_for("settings"))



    return render_template("allowance.html", account=account)





# =========================================================

# PIN変更

# =========================================================





@app.route("/pin-update", methods=["GET", "POST"])

def pin_update():



    if request.method == "POST":



        new_pin = request.form.get("new_pin", "")



        if not new_pin:



            flash("PINコードを入力してください")



            return redirect(request.url)



        if not new_pin.isdigit() or len(new_pin) != 4:



            flash("PINコードは4桁の数字にしてください")



            return redirect(request.url)



        account["pin"] = new_pin



        flash("PINコードを変更しました")



        return redirect(url_for("settings"))



    return render_template("pin_update.html")





# =========================================================

# 親管理へのPIN認証

# =========================================================





@app.route("/parent-pin", methods=["GET", "POST"])

def parent_pin():



    if not account["pin"]:



        flash("PINコードが登録されていません")



        return redirect(url_for("menu"))



    if request.method == "POST":



        pin = request.form.get("pin", "")



        if not pin:



            flash("PINコードを入力してください")



            return redirect(request.url)



        if pin != account["pin"]:



            flash("PINコードが正しくありません")



            return redirect(request.url)



        session["parent_verified"] = True



        return redirect(url_for("parent"))



    return render_template("parent_pin.html")





# =========================================================

# 親管理

# =========================================================





@app.route("/parent")

def parent():



    if not session.get("parent_verified"):



        return redirect(url_for("parent_pin"))



    waiting = [x for x in pending_deposits if x["status"] == "承認待ち"]



    return render_template("parent.html", pending=waiting, account=account)





# =========================================================

# 仮入金承認

# =========================================================





@app.route("/parent/approve/<int:deposit_id>", methods=["POST"])

def approve_deposit(deposit_id):



    if not session.get("parent_verified"):



        return redirect(url_for("parent_pin"))



    target = next((x for x in pending_deposits if x["id"] == deposit_id), None)



    if target is None:



        flash("仮入金が見つかりません")



        return redirect(url_for("parent"))



    if target["status"] != "承認待ち":



        return redirect(url_for("parent"))



    target["status"] = "承認済み"



    account["balance"] += target["amount"]



    new_id = max([x["id"] for x in transactions_data], default=0) + 1



    transactions_data.append(

        {

            "id": new_id,

            "type": "入金",

            "category": "貯金",

            "amount": target["amount"],

            "status": "承認済み",

            "date": target["date"],

        }

    )



    flash("入金を承認しました")



    return redirect(url_for("parent"))





# =========================================================

# 仮入金 非承認

# =========================================================





@app.route("/parent/reject/<int:deposit_id>", methods=["POST"])

def reject_deposit(deposit_id):



    if not session.get("parent_verified"):



        return redirect(url_for("parent_pin"))



    target = next((x for x in pending_deposits if x["id"] == deposit_id), None)



    if target:



        target["status"] = "非承認"



    flash("入金を非承認にしました")



    return redirect(url_for("parent"))





# =========================================================

# 起動

# =========================================================



if __name__ == "__main__":



    app.run(host="0.0.0.0", port=5000, debug=True)
