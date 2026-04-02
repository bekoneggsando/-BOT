import discord
from discord import ui, app_commands
from discord.ext import commands
import random
import os
import asyncio
import pytz
from datetime import datetime
# ================= 設定エリア =================
TOKEN = os.getenv("TOKEN")

# 📢 各カテゴリーの「募集カード」を投稿するチャンネルID
# 右側の数字を、あなたが作成したそれぞれの専用チャンネルIDに書き換えてください
LIST_CHANNELS = {
    "valorant": 1485178392419500122, # VALORANT募集一覧ch
    "apex":     1485178436673736734, # Apex募集一覧ch
    "zatsudan": 1485178502125850634, # 雑談募集一覧ch
    "soudan":   1485178544052240514, # 悩み相談募集一覧ch
    "friend":   1485178465643790569, # フレンド募集募集一覧ch
    "partner":  1489135172191256688  #パートナー募集
}

# 募集ボタンを置くチャンネル（パネル設置用）
CH_VALORANT = 1484074198392639559
CH_APEX     = 1484385439530876928
CH_ZATSUDAN = 1484385781241090128
CH_SOUDAN   = 1484386174394040431
CH_FRIEND   = 1484117154910699530
CH_PARTNER = 1489120434703306792
# 時間ごとのロールID {時間(int): ロールID(int)}
TIME_ROLES = {
    0: 1488523839397953706, 1: 1488522397505028288, 2: 1488522658986459289, 3: 1488522716716994682, 4: 1488522760480096407, 5: 1488522805745156246,
    6: 1488522891669667941, 7: 1488522917221236777, 8: 1488522921268875314, 9: 1488522923970138132, 10: 1488522926897762354, 11: 1488522929393242202,
    12: 1488522929766535319, 13: 1488522930546671778, 14: 1488523194934493236, 15: 1488523196536721499, 16: 1488523197069660160, 17: 1488523197769846966,
    18: 1488523207936839680, 19: 1488523210139111444, 20: 1488523212211093504, 21: 1488523217973936218, 22: 1488523220067029162, 23: 1488523221845409803
}

    # ================= 設定エリア =================
# ...既存の設定...


ROLE_IDS = {
    "valorant": 1484070601546268732, # VALORANT通知用ロールID
    "apex":     1484070672547450931, # Apex通知用ロールID
    "zatsudan": 1484070570328064040, # 雑談通知用ロールID
    "soudan":   1484070539990405201, # 悩み相談通知用ロールID
    "friend":   1488462522532102164  # フレンド募集通知用ロールID
}
# =============================================

NATIVE_TOPICS = [
    "最近ハマっている食べ物や飲み物は？ 🍕",
    "一番好きなゲームのタイトルとその魅力を教えて！ 🎮",
    "最近見たアニメや映画でおすすめはある？ 🎬",
    "もし100万円あったら何に使う？ 💰",
    "自分の性格を一言で表すと？ 😊",
    "休みの日はインドア派？アウトドア派？ 🏠🌳",
    "最近買って良かったアイテムは？ 🛒",
    "今一番行きたい場所はどこ？ 🗺️",
    "好きなアーティストや曲を教えて！ 🎧",
    "学生時代の部活は何をしていた？ 🏆"
]
# =============================================

class NetaView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    @ui.button(label="話題を振る（ガチャ）", style=discord.ButtonStyle.secondary, emoji="🎲", custom_id="neta_gacha_v2")
    async def neta_button(self, it: discord.Interaction, btn: ui.Button):
        topic = random.choice(NATIVE_TOPICS)
        await it.response.send_message(content=f"🎲 {it.user.display_name}さんが話題を引きました！\n### {topic}")

class JoinView(ui.View):
    def __init__(self, host_id, target_count, vc_ch_id, limit_minutes, text_ch_id=None):
        super().__init__(timeout=None)
        self.host_id = host_id
        self.target_count = target_count
        self.vc_ch_id = vc_ch_id
        self.text_ch_id = text_ch_id
        self.joined_users = []
        # --- 👇 ここを追加：残り時間を秒で管理 ---
        self.remaining_seconds = limit_minutes * 60
    # --- 2. 参加・キャンセルボタン ---
    @ui.button(label="参加する / キャンセル", style=discord.ButtonStyle.success, emoji="✋", custom_id="join_or_cancel")
    # 参加ボタンの中身（Embed更新部分）を少しだけ賢くしました
    async def join_button(self, it: discord.Interaction, btn: ui.Button):
        user_id = it.user.id
        if user_id == self.host_id:
            return await it.response.send_message("募集主はすでに追加されています！", ephemeral=True)

        if user_id in self.joined_users:
            self.joined_users.remove(user_id)
            msg = "参加をキャンセルしました。"
        else:
            if len(self.joined_users) >= self.target_count:
                return await it.response.send_message("すでに満員です！", ephemeral=True)
            self.joined_users.append(user_id)
            msg = "参加を確定しました！"

        # --- Embedの更新ロジック ---
        embed = it.message.embeds[0]
        remaining = self.target_count - len(self.joined_users)
        
        # 1番目のフィールド（人数）を更新
        embed.set_field_at(0, name="👥 人数", value=f"あと **{remaining}** 人", inline=True)
        
        # 参加者リストの文字列作成
        mentions = [f"<@{uid}>" for uid in self.joined_users]
        user_list_str = "、".join(mentions) if mentions else "なし"

        # 「現在の参加者」フィールドを探して更新、なければ作る
        target_field_index = None
        for i, field in enumerate(embed.fields):
            if field.name == "📝 現在の参加者":
                target_field_index = i
                break
        
        if target_field_index is not None:
            embed.set_field_at(target_field_index, name="📝 現在の参加者", value=user_list_str, inline=False)
        else:
            embed.add_field(name="📝 現在の参加者", value=user_list_str, inline=False)

        await it.message.edit(embed=embed, view=self)
        await it.response.send_message(msg, ephemeral=True)

        if remaining == 1:
            await it.channel.send(f"🔥 **あと1人**で開始です！ (募集主: <@{self.host_id}>)", delete_after=60)

    # --- 4. 延長ボタン ---
    @ui.button(label="10分延長", style=discord.ButtonStyle.secondary, emoji="➕", custom_id="extend_time")
    async def extend(self, it: discord.Interaction, btn: ui.Button):
        if it.user.id != self.host_id:
            return await it.response.send_message("募集主しか延長できません。", ephemeral=True)
        
        # 実際に内部の秒数を増やす！
        self.remaining_seconds += 600
        
        # Embedの表示も更新して安心させる
        embed = it.message.embeds[0]
        # 3番目のフィールド「⌛ 締切」を更新（indexは作成順に合わせて調整してください）
        # もし「10分後に消去」という表示なら、そこを書き換えます
        embed.set_field_at(2, name="⌛ 締切", value="延長されました！", inline=True)
        
        await it.message.edit(embed=embed)
        await it.response.send_message("⏳ 締切を10分延長しました！", ephemeral=True)

    # --- 1. 手動終了ボタン ---
    @ui.button(label="募集を終了", style=discord.ButtonStyle.danger, emoji="✖️", custom_id="stop_recruit")
    async def stop(self, it: discord.Interaction, btn: ui.Button):
        if it.user.id != self.host_id:
            return await it.response.send_message("募集主しか終了できません。", ephemeral=True)
        
        # Embedを締切済みに書き換える
        embed = it.message.embeds[0]
        embed.title = f"【終了】{embed.title}"
        embed.color = discord.Color.default()
        
        await it.message.edit(content="❌ この募集は終了しました。", embed=embed, view=None)
        await it.response.send_message("募集を締め切りました。", ephemeral=True)

class MultiRecruitModal(ui.Modal):
    def __init__(self, mode, title):
        super().__init__(title=title)
        self.mode = mode
        
        # 全カテゴリー共通の「人数」と「時間設定」
        self.count_input = ui.TextInput(label="1. 募集人数 (数字のみ)", placeholder="2", min_length=1, max_length=1)
        self.limit_input = ui.TextInput(label="2. 何分待つ？ (数字のみ・自動締切用)", placeholder="15", min_length=1, max_length=2)
        self.play_time = ui.TextInput(label="3. プレイ終了時間 (目安)", placeholder="23時まで / 2時間 / 未定", max_length=20)
        
        self.add_item(self.count_input)
        self.add_item(self.limit_input)
        self.add_item(self.play_time)

        # 残り2枠をカテゴリーごとに最適化
        if mode == "valorant":
            self.add_item(ui.TextInput(label="4. 自分のランク", placeholder="ゴールド2", max_length=20))
            self.add_item(ui.TextInput(label="5. その他 (モード・条件・一言)", style=discord.TextStyle.paragraph))
        elif mode == "apex":
            self.add_item(ui.TextInput(label="4. ランク / Lv", placeholder="プラチナ", max_length=20))
            self.add_item(ui.TextInput(label="5. その他 (モード・条件・スタイル)", style=discord.TextStyle.paragraph))
        elif mode == "zatsudan":
            self.add_item(ui.TextInput(label="4. 今の話題", placeholder="アニメの話 / 雑談", max_length=50))
            self.add_item(ui.TextInput(label="5. 雰囲気・備考", style=discord.TextStyle.paragraph))
        elif mode == "soudan":
            self.add_item(ui.TextInput(label="4. 相談内容のジャンル", placeholder="仕事 / 人間関係", max_length=50))
            self.add_item(ui.TextInput(label="5. 接し方の希望 (聞き専 / アドバイス等)", style=discord.TextStyle.paragraph))
        elif mode == "friend":
            self.add_item(ui.TextInput(label="4. 趣味・活動時間帯", placeholder="ゲーム / 夜メイン", max_length=50))
            self.add_item(ui.TextInput(label="5. 自己紹介・どんな友達になりたいか", style=discord.TextStyle.paragraph))

    async def on_submit(self, it: discord.Interaction):
        # 入力チェック
        if not self.count_input.value.isdigit() or not self.limit_input.value.isdigit():
            return await it.response.send_message("「人数」と「待機時間」は半角数字で入力してください。", ephemeral=True)
        
        target_count = int(self.count_input.value)
        limit_minutes = int(self.limit_input.value) # 自動締切までの分数
        
        await it.response.defer(ephemeral=True)
        guild = it.guild
        over = {guild.default_role: discord.PermissionOverwrite(view_channel=False),
                it.user: discord.PermissionOverwrite(view_channel=True, connect=True, send_messages=True),
                guild.me: discord.PermissionOverwrite(view_channel=True, manage_channels=True)}

        # チャンネル作成
        vc_ch = await guild.create_voice_channel(name=f"🔊-{it.user.display_name}の部屋", overwrites=over)
        text_ch = await guild.create_text_channel(name=f"💬-{it.user.display_name}専用ch", overwrites=over) if self.mode == "friend" else None

        # 部屋に話題ガチャを投稿
        target_post = text_ch if text_ch else vc_ch
        if self.mode in ["zatsudan", "friend"]:
            await target_post.send(embed=discord.Embed(title="🚀 会話サポート", description="話題に困ったらボタンを押してね！"), view=NetaView())

        # 投稿先
        target_list_id = LIST_CHANNELS.get(self.mode)
        list_ch = guild.get_channel(target_list_id) if target_list_id else it.channel

        # Embed作成
        colors = {"valorant": 0xFF4654, "apex": 0xFF0000, "zatsudan": 0x5865F2, "soudan": 0x9B59B6, "friend": 0xE91E63}
        embed = discord.Embed(title=f"【{self.title}】詳細募集", color=colors.get(self.mode, 0x95a5a6))
        embed.set_author(name=it.user.display_name, icon_url=it.user.display_avatar.url)
        embed.add_field(name="👥 人数", value=f"あと **{target_count}** 人", inline=True)
        embed.add_field(name="⏰ 終了予定", value=self.play_time.value, inline=True)
        embed.add_field(name="⌛ 締切", value=f"{limit_minutes}分後に自動消去", inline=True)
        embed.add_field(name="🔗 専用部屋", value=vc_ch.mention, inline=True)

        for item in self.children:
            if item not in [self.count_input, self.limit_input, self.play_time] and item.value:
                embed.add_field(name=f"🔘 {item.label[3:]}", value=item.value, inline=False)

        # --- 👇 ここから差し替え 👇 ---
        # --- 👇 24時間ロール対応版：ここから差し替え 👇 ---
        role_id = ROLE_IDS.get(self.mode)  # ゲームロール（VALORANTなど）
        mention_text = ""
        
        if role_id:
            import pytz
            from datetime import datetime
            jst = pytz.timezone('Asia/Tokyo')
            now_hour = datetime.now(jst).hour

            # 現在の時間に対応するロールIDを取得 (TIME_ROLES辞書から)
            time_role_id = TIME_ROLES.get(now_hour)
            time_role = guild.get_role(time_role_id)
            game_role = guild.get_role(role_id)

            if time_role and game_role:
                # 「今の時間ロール」を持っていて、かつ「ゲームロール」も持っている人を抽出
                target_mentions = [m.mention for m in time_role.members if game_role in m.roles]
                
                if target_mentions:
                    # 最大50人までメンション（人数が増えても大丈夫なように少し増やしました）
                    mention_text = " ".join(target_mentions[:50]) + " "
                else:
                    # もし該当者が一人もいなければ、募集主が寂しいので
                    # 最低限ゲームロールへのメンションを入れる、などの調整も可能です
                    mention_text = "" 
        # --- 👆 ここまで 👆 ---

        # --- 👇 修正：limit_minutes を View に渡すように変更 ---
        view = JoinView(
            host_id=it.user.id, 
            target_count=target_count, 
            vc_ch_id=vc_ch.id, 
            limit_minutes=limit_minutes, # これを追加
            text_ch_id=text_ch.id if text_ch else None
        )
        
        # 募集メッセージ送信
        list_ch_msg = await list_ch.send(
            content=f"{mention_text}📢 {it.user.mention}さんが新しい募集を開始しました！",
            embed=embed,
            view=view
        )
        
        await it.followup.send(f"募集を【 {list_ch.name} 】に投稿しました！\n設定した時間が経過するか、手動で終了すると部屋は消去されます。", ephemeral=True)

        # --- 🕒 本気の延長対応・自動消去ループ ---
        # view.remaining_seconds が 0 になるまで 10秒おきに監視し続ける
        import asyncio
        while view.remaining_seconds > 0:
            await asyncio.sleep(10)
            view.remaining_seconds -= 10
            
            # 手動終了ボタンなどでメッセージが消えていた場合はループ終了
            try:
                # メッセージがまだ存在するかチェック
                await list_ch_msg.edit() 
            except:
                break

        # --- 🧹 自動消去の実行 ---
        try:
            # 募集メッセージの削除
            await list_ch_msg.delete()
        except:
            pass
            
        try:
            # VCの削除
            await vc_ch.delete()
            # テキストチャンネルがあれば削除
            if text_ch:
                await text_ch.delete()
        except:
            # すでに削除されている場合は何もしない
            pass

        # --- 🕒 自動締切タイマー（バックグラウンドで実行） ---
        async def auto_close_timer():
            await asyncio.sleep(limit_minutes * 60) # 分を秒に変換
            # 誰も参加していない（joined_usersが空）場合のみ実行
            if len(view.joined_users) == 0:
                try:
                    # チャンネル削除
                    await vc_ch.delete()
                    if text_ch: await text_ch.delete()
                    
                    # メッセージの更新（ボタンを消してタイトルを「期限切れ」に）
                    embed.title = f"【期限切れ】{embed.title}"
                    embed.color = discord.Color.dark_gray()
                    await list_ch_msg.edit(content="⏰ 指定時間内に参加者がいなかったため、募集を終了しました。", embed=embed, view=None)
                except Exception as e:
                    print(f"自動消去エラー: {e}")

        # タイマーを開始
        bot.loop.create_task(auto_close_timer())

user_sleep_settings = {}

class SleepTimeSelectView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.select(
        placeholder="何時から通知を止めますか？",
        options=[discord.SelectOption(label=f"{i}時から通知オフ", value=str(i)) for i in range(24)],
        custom_id="sleep_start"
    )
    async def select_start(self, it: discord.Interaction, select: ui.Select):
        user_id = it.user.id
        start_time = int(select.values[0])
        # 現在の終了設定を取得（なければ0）
        _, end = user_sleep_settings.get(user_id, (0, 0))
        user_sleep_settings[user_id] = (start_time, end)
        await it.response.send_message(f"✅ **{start_time}時**から通知を止めるようにしました。", ephemeral=True)

    @ui.select(
        placeholder="何時に通知を再開しますか？",
        options=[discord.SelectOption(label=f"{i}時から通知再開", value=str(i)) for i in range(24)],
        custom_id="sleep_end"
    )
    async def select_end(self, it: discord.Interaction, select: ui.Select):
        user_id = it.user.id
        end_time = int(select.values[0])
        # 現在の開始設定を取得（なければ0）
        start, _ = user_sleep_settings.get(user_id, (0, 0))
        user_sleep_settings[user_id] = (start, end_time)
        await it.response.send_message(f"✅ **{end_time}時**に通知を再開するようにしました。", ephemeral=True)

    @ui.button(label="🕒 通知を受け取る時間の設定", style=discord.ButtonStyle.secondary, emoji="⏰", custom_id="open_time_panel")
    async def open_time(self, it: discord.Interaction, btn: ui.Button):
        embed = discord.Embed(
            title="⏰ 活動時間（通知OK時間）の設定",
            description=(
                "自分が募集通知を受け取っても良い時間を選んでください。\n"
                "ここで選んだ時間のロールが自動的に付与されます。\n\n"
                "**※選ばなかった時間のロールは自動で外れます。**"
            ),
            color=0x34495e
        )
        await it.response.send_message(embed=embed, view=TimeRoleSelectView(), ephemeral=True)

class NotificationView(ui.View):
    def __init__(self):
        # タイムアウトを None にしないと add_view でエラーになります
        super().__init__(timeout=None)

    async def toggle_role(self, it: discord.Interaction, key: str):
        role_id = ROLE_IDS.get(key)
        role = it.guild.get_role(role_id)
        if not role:
            return await it.response.send_message("ロールが見つかりません。設定を確認してください。", ephemeral=True)

        if role in it.user.roles:
            await it.user.remove_roles(role)
            await it.response.send_message(f"🔕 {role.name} 通知を【オフ】にしました。", ephemeral=True)
        else:
            await it.user.add_roles(role)
            await it.response.send_message(f"🔔 {role.name} 通知を【オン】にしました！", ephemeral=True)

    @ui.button(label="VALORANT通知", style=discord.ButtonStyle.primary, emoji="🎮", custom_id="role_val")
    async def val_role(self, it: discord.Interaction, btn: ui.Button):
        await self.toggle_role(it, "valorant")

    @ui.button(label="Apex通知", style=discord.ButtonStyle.primary, emoji="🔫", custom_id="role_apex")
    async def apex_role(self, it: discord.Interaction, btn: ui.Button):
        await self.toggle_role(it, "apex")

    @ui.button(label="雑談通知", style=discord.ButtonStyle.success, emoji="💬", custom_id="role_zatsudan")
    async def zatsudan_role(self, it: discord.Interaction, btn: ui.Button):
        await self.toggle_role(it, "zatsudan")

    @ui.button(label="悩み相談通知", style=discord.ButtonStyle.success, emoji="🔰", custom_id="role_soudan")
    async def soudan_role(self, it: discord.Interaction, btn: ui.Button):
        await self.toggle_role(it, "soudan")
        
    @ui.button(label="フレンド募集通知", style=discord.ButtonStyle.secondary, emoji="🤝", custom_id="role_friend")
    async def friend_role(self, it: discord.Interaction, btn: ui.Button):
        await self.toggle_role(it, "friend")

    @ui.button(label="⏰ 通知を受け取る時間の設定", style=discord.ButtonStyle.secondary, emoji="🕒", custom_id="open_time_setting")
    async def open_time(self, it: discord.Interaction, btn: ui.Button):
        embed = discord.Embed(
            title="⏰ 通知OK時間の設定",
            description=(
                "自分が**通知を受け取ってもいい時間**をすべて選んでください。\n"
                "（例：21時〜23時に遊びたいなら、21時、22時、23時を選択）\n\n"
                "※ここで選ばなかった時間のロールは自動的に外れます。"
            ),
            color=0x34495e
        )
        # ここで新しく作った TimeRoleSelectView を呼び出す
        await it.response.send_message(embed=embed, view=TimeRoleSelectView(), ephemeral=True)

class UniversalPanelView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    @ui.button(label="📝 条件を指定して募集", style=discord.ButtonStyle.primary, custom_id="panel_start_v2")
    async def start_btn(self, it: discord.Interaction, btn: ui.Button):
        cid = it.channel_id
        conf = {CH_VALORANT: ("valorant", "VALORANT詳細募集"), CH_APEX: ("apex", "Apex詳細募集"),
                CH_ZATSUDAN: ("zatsudan", "雑談・暇つぶし"), CH_SOUDAN: ("soudan", "悩み相談"), CH_FRIEND: ("friend", "フレンド募集")}
        res = conf.get(cid)
        if res: await it.response.send_modal(MultiRecruitModal(res[0], res[1]))
        else: await it.response.send_message("募集対象外のチャンネルです。", ephemeral=True)

class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = intents.message_content = intents.voice_states = True
        super().__init__(command_prefix="!", intents=intents)
    
    async def setup_hook(self):
        self.add_view(UniversalPanelView())
        self.add_view(NetaView())
        self.add_view(NotificationView())
        # TimeRoleSelectView は「その場出し」なので add_view は不要です
        await self.tree.sync()
        
    # VC自動削除（空になってから60秒後に削除）
    async def on_voice_state_update(self, member, before, after):
        if before.channel and len(before.channel.members) == 0:
            if before.channel.name.startswith("🔊-"):
                await asyncio.sleep(60)
                if len(before.channel.members) == 0:
                    txt_name = before.channel.name.replace("🔊-", "💬-")
                    for ch in member.guild.text_channels:
                        if ch.name == txt_name: await ch.delete()
                    try: await before.channel.delete()
                    except: pass

class TimeRoleSelectView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.select(
        placeholder="通知を受け取りたい時間をすべて選んでください（複数選択可）",
        min_values=0, 
        max_values=24, 
        options=[discord.SelectOption(label=f"{i}時OK", value=str(i)) for i in range(24)],
        custom_id="time_role_multi_select"
    )
    async def select_time(self, it: discord.Interaction, select: ui.Select):
        await it.response.defer(ephemeral=True)
        
        selected_hours = [int(v) for v in select.values]
        add_roles = []
        remove_roles = []

        # TIME_ROLES辞書を使って、選ばれた時間は付与、選ばれてない時間は解除
        for hour, r_id in TIME_ROLES.items():
            role = it.guild.get_role(r_id)
            if not role: continue
            
            if hour in selected_hours:
                if role not in it.user.roles:
                    add_roles.append(role)
            else:
                if role in it.user.roles:
                    remove_roles.append(role)

        if remove_roles: await it.user.remove_roles(*remove_roles)
        if add_roles: await it.user.add_roles(*add_roles)

        await it.followup.send(
            f"✅ 設定を更新しました！\n選択した時間以外は通知がこないようロールを整理しました。", 
            ephemeral=True
        )

# ================= 設定エリア（ここを埋めてください） =================
ROLE_ID_MALE   = 1489141133027049572  # 男性ロールのID
ROLE_ID_FEMALE = 1489141199066365963  # 女性ロールのID

# 投稿先のチャンネル（異性が閲覧するチャンネル）
CH_ID_FOR_FEMALE = 1489274994679746640  # 男性の募集が飛んでいく場所（女性が見るch）
CH_ID_FOR_MALE   = 1489135172191256688  # 女性の募集が飛んでいく場所（男性が見るch）
# =================================================================

class PartnerModal(ui.Modal, title="💖 パートナー募集プロフィール"):
    age = ui.TextInput(label="1. 年齢（成人済の方のみ）", placeholder="例：22歳", min_length=1, max_length=10)
    place = ui.TextInput(label="2. お住まい / 職業", placeholder="例：東京 / 会社員", max_length=50)
    hobby = ui.TextInput(label="3. 趣味 / 性格", placeholder="例：ゲーム、旅行 / 穏やかな性格です", max_length=100)
    target = ui.TextInput(label="4. 理想のタイプ", placeholder="例：一緒に笑い合える方", max_length=100)
    message = ui.TextInput(label="5. 自己紹介・一言", style=discord.TextStyle.paragraph, placeholder="自由に書いてください！")

    async def on_submit(self, it: discord.Interaction):
        await it.response.defer(ephemeral=True)
        
        # --- 性別判定ロジック ---
        target_ch_id = None
        user_role_ids = [role.id for role in it.user.roles]

        if ROLE_ID_MALE in user_role_ids:
            # 投稿者が男性なら、女性が見るチャンネルへ
            target_ch_id = CH_ID_FOR_FEMALE
            gender_label = "♂ 男性からの募集"
            embed_color = 0x3498DB # 青系
        elif ROLE_ID_FEMALE in user_role_ids:
            # 投稿者が女性なら、男性が見るチャンネルへ
            target_ch_id = CH_ID_FOR_MALE
            gender_label = "♀ 女性からの募集"
            embed_color = 0xFF69B4 # ピンク系
        else:
            # 性別ロールがない場合
            return await it.followup.send("性別ロール（男性/女性）を持っていないため投稿できません。オンボーディングで選択してください。", ephemeral=True)

        list_ch = it.guild.get_channel(target_ch_id)
        if not list_ch:
            return await it.followup.send("投稿先のチャンネルが見つかりません。", ephemeral=True)

        # --- Embed作成 ---
        embed = discord.Embed(title=f"{gender_label}", color=embed_color)
        embed.set_author(name=it.user.display_name, icon_url=it.user.display_avatar.url)
        
        embed.add_field(name="🎂 年齢", value=self.age.value, inline=True)
        embed.add_field(name="📍 居住 / 職業", value=self.place.value, inline=True)
        embed.add_field(name="🎨 趣味・性格", value=self.hobby.value, inline=False)
        embed.add_field(name="💎 理想のタイプ", value=self.target.value, inline=False)
        embed.add_field(name="📝 自己紹介", value=self.message.value, inline=False)
        
        await list_ch.send(content=f"💖 {it.user.mention}さんが新しく募集しました！", embed=embed)
        await it.followup.send(f"募集を {list_ch.mention} に投稿しました！", ephemeral=True)

class PartnerPanelView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label="💖 プロフィールを書いて募集する", style=discord.ButtonStyle.danger, custom_id="start_partner_recruit")
    async def partner_btn(self, it: discord.Interaction, btn: ui.Button):
        await it.response.send_modal(PartnerModal())

bot = MyBot()

# サーバー管理者がパネルを設置するためのコマンド
@bot.tree.command(name="setup_partner", description="パートナー募集パネルを設置します")
@app_commands.checks.has_permissions(administrator=True) # 管理者のみ実行可能
async def setup_partner(it: discord.Interaction):
    # パネルの見た目（Embed）を設定
    embed = discord.Embed(
        title="💖 パートナー募集（成人限定）",
        description=(
            "素敵な出会いを探してみませんか？\n"
            "下のボタンからプロフィールを記入して投稿してください。\n\n"
            "**⚠️ 注意事項**\n"
            "・男性は「女性用募集一覧」へ、女性は「男性用募集一覧」へ自動で投稿されます。\n"
            "・虚偽の報告や迷惑行為は即追放対象となります。\n"
            "・相手を尊重したやり取りを心がけましょう。"
        ),
        color=0xFF69B4 # ピンク色
    )
    
    # アイコン画像があれば設定（任意）
    # embed.set_thumbnail(url="あなたのサーバーアイコンURL")

    # ボタンを表示してメッセージを送信
    await it.response.send_message(
        embed=embed, 
        view=PartnerPanelView() # 先ほど作ったボタンクラスを呼び出す
    )

@bot.tree.command(name="notification_setup", description="通知設定パネルを設置します（管理者専用）")
@app_commands.checks.has_permissions(administrator=True)
async def notification_setup(it: discord.Interaction):
    embed = discord.Embed(
        title="🔔 募集通知設定センター",
        description=(
            "新しい募集が投稿されたときに通知（メンション）を受け取りたいカテゴリーを選んでください。\n\n"
            "**ボタンを押すとオン/オフを切り替えられます。**\n"
            "現在いるメンバーの方も、ここから設定可能です！"
        ),
        color=0x2ecc71
    )
    await it.response.send_message("通知設定パネルを設置しました！", ephemeral=True) # メッセージ自体は自分だけに
    await it.channel.send(embed=embed, view=NotificationView()) # パネルをチャンネルに送信

@bot.tree.command(name="setup")
@app_commands.checks.has_permissions(administrator=True)
async def setup(it: discord.Interaction):
    await it.response.send_message("募集パネルを設置しました！", view=UniversalPanelView())

if __name__ == "__main__":
    if TOKEN: bot.run(TOKEN)
