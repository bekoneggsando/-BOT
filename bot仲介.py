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
    "friend":   1485178465643790569  # フレンド募集募集一覧ch
}

# 募集ボタンを置くチャンネル（パネル設置用）
CH_VALORANT = 1484074198392639559
CH_APEX     = 1484385439530876928
CH_ZATSUDAN = 1484385781241090128
CH_SOUDAN   = 1484386174394040431
CH_FRIEND   = 1484117154910699530

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
    def __init__(self, host_id, target_count, vc_ch_id, text_ch_id=None):
        super().__init__(timeout=None)
        self.host_id, self.target_count = host_id, target_count
        self.vc_ch_id, self.text_ch_id = vc_ch_id, text_ch_id
        self.joined_users = []

    @ui.button(label="参加して専用部屋に入る", style=discord.ButtonStyle.success, emoji="🚪", custom_id="join_room_v2")
    async def join_btn(self, it: discord.Interaction, btn: ui.Button):
        if it.user.id == self.host_id or it.user.id in self.joined_users:
            return await it.response.send_message("既に参加しているか募集主です。", ephemeral=True)
        
        vc_ch = it.guild.get_channel(self.vc_ch_id)
        if vc_ch is None:
            btn.label, btn.disabled = "部屋が削除されています", True
            await it.message.edit(view=self)
            return await it.response.send_message("この募集の専用部屋は既に削除されています。", ephemeral=True)

        await it.response.defer(ephemeral=True)
        overwrite = discord.PermissionOverwrite(view_channel=True, connect=True, send_messages=True)
        
        try:
            await vc_ch.set_permissions(it.user, overwrite=overwrite)
            if self.text_ch_id:
                text_ch = it.guild.get_channel(self.text_ch_id)
                if text_ch: await text_ch.set_permissions(it.user, overwrite=overwrite)
        except:
            pass

        self.joined_users.append(it.user.id)
        rem = self.target_count - len(self.joined_users)
        
        if rem <= 0:
            btn.label, btn.disabled, btn.style = "満員御礼", True, discord.ButtonStyle.secondary
            embed = it.message.embeds[0]
            embed.color = discord.Color.dark_gray()
            embed.title = f"【締切】{embed.title}"
            await it.message.edit(embed=embed, view=self)
            await it.channel.send(f"🎊 {it.user.mention}さんが参加して**満員**になりました！")
        else:
            await it.channel.send(f"✅ {it.user.mention}さんが参加！ (あと **{rem}** 人)")
        await it.followup.send(f"参加完了！{vc_ch.mention} に入れます。", ephemeral=True)

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

        view = JoinView(host_id=it.user.id, target_count=target_count, vc_ch_id=vc_ch.id, text_ch_id=text_ch.id if text_ch else None)
        
        # 募集メッセージ送信
        list_ch_msg = await list_ch.send(
            content=f"{mention_text}📢 {it.user.mention}さんが新しい募集を開始しました！",
            embed=embed,
            view=view
        )
        await it.followup.send(f"募集を【 {list_ch.name} 】に投稿しました！\n{limit_minutes}分間、誰も参加しなければ自動で削除されます。", ephemeral=True)

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
        placeholder="通知を受け取りたい時間を選んでください（複数選択可）",
        min_values=1,
        max_values=24, # 最大24個まで一気に選べる
        options=[discord.SelectOption(label=f"{i}時OK", value=str(i)) for i in range(24)],
        custom_id="time_role_select"
    )
    async def select_time(self, it: discord.Interaction, select: ui.Select):
        await it.response.defer(ephemeral=True)
        
        # 選択された時間のロールIDをリスト化
        selected_hours = [int(v) for v in select.values]
        add_roles = []
        remove_roles = []

        for hour, r_id in TIME_ROLES.items():
            role = it.guild.get_role(r_id)
            if not role: continue
            
            if hour in selected_hours:
                add_roles.append(role)
            else:
                # 選択しなかった時間は外す（更新処理）
                remove_roles.append(role)

        # ロールの付け外しを一気に実行
        if remove_roles: await it.user.remove_roles(*remove_roles)
        if add_roles: await it.user.add_roles(*add_roles)

        await it.followup.send(f"✅ 通知を受け取る時間を更新しました！", ephemeral=True)

bot = MyBot()

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
