import discord
from discord import ui, app_commands
from discord.ext import commands
import random
import os

# ================= 設定エリア =================
# RailwayのVariables設定で TOKEN という名前で保存してください
# 直接書きたい場合は os.getenv("TOKEN") を "あなたのトークン" に書き換えてください
TOKEN = os.getenv("TOKEN")

CH_VALORANT = 1484074198392639559
CH_APEX     = 1484385439530876928
CH_ZATSUDAN = 1484385781241090128
CH_SOUDAN   = 1484386174394040431
CH_FRIEND   = 1484117154910699530

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
    @ui.button(label="話題を振る（ガチャ）", style=discord.ButtonStyle.secondary, emoji="🎲", custom_id="neta_gacha_v100")
    async def neta_button(self, it: discord.Interaction, btn: ui.Button):
        topic = random.choice(NATIVE_TOPICS)
        await it.response.send_message(content=f"🎲 {it.user.display_name}さんが話題を引きました！\n### {topic}")

class JoinView(ui.View):
    def __init__(self, host_id, target_count, vc_ch_id, text_ch_id=None):
        super().__init__(timeout=None)
        self.host_id = host_id
        self.target_count = target_count
        self.vc_ch_id = vc_ch_id
        self.text_ch_id = text_ch_id
        self.joined_users = []

    @ui.button(label="参加して専用部屋に入る", style=discord.ButtonStyle.success, emoji="🚪", custom_id="join_room_v100")
    async def join_btn(self, it: discord.Interaction, btn: ui.Button):
        if it.user.id == self.host_id or it.user.id in self.joined_users:
            return await it.response.send_message("既に参加しているか募集主です。", ephemeral=True)
        
        # チャンネルの取得（再起動後も動くようにIDから取得）
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
            btn.label, btn.disabled, btn.style = "満員", True, discord.ButtonStyle.secondary
            await it.message.edit(view=self)
            await it.channel.send(f"🎊 {it.user.mention}さんが参加して**満員**になりました！")
        else:
            await it.channel.send(f"✅ {it.user.mention}さんが参加！ (あと **{rem}** 人)")
        await it.followup.send(f"参加完了！{vc_ch.mention} に入れます。", ephemeral=True)

class MultiRecruitModal(ui.Modal):
    def __init__(self, mode, title):
        super().__init__(title=title)
        self.mode = mode
        self.count_input = ui.TextInput(label="1. 募集人数 (数字)", placeholder="例: 2", min_length=1, max_length=1)
        self.add_item(self.count_input)

        # カテゴリー別項目
        if mode == "valorant":
            self.add_item(ui.TextInput(label="2. 自分のランク", placeholder="例：ゴールド2", max_length=20))
            self.add_item(ui.TextInput(label="3. モード / サーバー", placeholder="例：コンペ / 東京", max_length=30))
            self.add_item(ui.TextInput(label="4. 相手への条件", placeholder="例：シルバー〜プラチナ", max_length=100))
            self.add_item(ui.TextInput(label="5. 雰囲気・一言", style=discord.TextStyle.paragraph))
        elif mode == "apex":
            self.add_item(ui.TextInput(label="2. 自分のランク / Lv", placeholder="例：プラチナ", max_length=50))
            self.add_item(ui.TextInput(label="3. 目的 / モード", placeholder="例：カジュアル", max_length=30))
            self.add_item(ui.TextInput(label="4. 相手への希望条件", max_length=100))
            self.add_item(ui.TextInput(label="5. VC・スタイル", style=discord.TextStyle.paragraph))
        elif mode == "zatsudan":
            self.add_item(ui.TextInput(label="2. 今の話題", max_length=50))
            self.add_item(ui.TextInput(label="3. 活動期限", max_length=30))
            self.add_item(ui.TextInput(label="4. 相手の雰囲気", max_length=100))
            self.add_item(ui.TextInput(label="5. 備考・スタイル", style=discord.TextStyle.paragraph))
        elif mode == "soudan":
            self.add_item(ui.TextInput(label="2. 相談のジャンル", max_length=50))
            self.add_item(ui.TextInput(label="3. 相談の重さ", max_length=30))
            self.add_item(ui.TextInput(label="4. 相手への希望", required=False))
            self.add_item(ui.TextInput(label="5. 接し方の希望", style=discord.TextStyle.paragraph))
        elif mode == "friend":
            self.add_item(ui.TextInput(label="2. メインの趣味", max_length=50))
            self.add_item(ui.TextInput(label="3. 活動時間帯", max_length=30))
            self.add_item(ui.TextInput(label="4. 自分の雰囲気", max_length=100))
            self.add_item(ui.TextInput(label="5. どんな友達になりたいか", style=discord.TextStyle.paragraph))

    async def on_submit(self, it: discord.Interaction):
        if not self.count_input.value.isdigit():
            return await it.response.send_message("人数は数字で入力してください。", ephemeral=True)
        
        target_count = int(self.count_input.value)
        await it.response.defer(ephemeral=True)
        guild = it.guild
        over = {guild.default_role: discord.PermissionOverwrite(view_channel=False),
                it.user: discord.PermissionOverwrite(view_channel=True, connect=True, send_messages=True),
                guild.me: discord.PermissionOverwrite(view_channel=True, manage_channels=True)}

        vc_ch = await guild.create_voice_channel(name=f"🔊-{it.user.display_name}の部屋", overwrites=over)
        text_ch = await guild.create_text_channel(name=f"💬-{it.user.display_name}専用ch", overwrites=over) if self.mode == "friend" else None

        # 作成された部屋に話題ボタンを投稿
        target_post = text_ch if text_ch else vc_ch
        if self.mode in ["zatsudan", "friend"]:
            await target_post.send(embed=discord.Embed(title="🚀 会話サポート", description="話題に困ったらボタンを押してね！"), view=NetaView())

        colors = {"valorant": 0xFF4654, "apex": 0xFF0000, "zatsudan": 0x5865F2, "soudan": 0x9B59B6, "friend": 0xE91E63}
        embed = discord.Embed(title=f"【{self.title}】詳細募集", color=colors.get(self.mode, 0x95a5a6))
        embed.set_author(name=it.user.display_name, icon_url=it.user.display_avatar.url)
        embed.add_field(name="👥 人数", value=f"あと **{target_count}** 人", inline=True)
        embed.add_field(name="🔗 専用部屋", value=vc_ch.mention, inline=True)
        if text_ch: embed.add_field(name="💬 専用チャット", value=text_ch.mention, inline=True)

        for item in self.children:
            if item != self.count_input and item.value:
                embed.add_field(name=f"🔘 {item.label[3:]}", value=item.value, inline=False)
        
        # IDを渡すように変更（再起動対策）
        view = JoinView(host_id=it.user.id, target_count=target_count, vc_ch_id=vc_ch.id, text_ch_id=text_ch.id if text_ch else None)
        await it.channel.send(content=f"📢 {it.user.mention}さんが募集中！", embed=embed, view=view)
        await it.followup.send("募集を開始しました！", ephemeral=True)

class UniversalPanelView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    @ui.button(label="📝 条件を指定して募集", style=discord.ButtonStyle.primary, custom_id="panel_start_v100")
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
        intents.members = intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)
    async def setup_hook(self):
        self.add_view(UniversalPanelView())
        self.add_view(NetaView())
        # 注意：JoinViewは動的に作成されるため、ここでの登録は不要ですが
        # 永続化したい場合は別途処理が必要です。通常はこれで動きます。
        await self.tree.sync()

bot = MyBot()

@bot.tree.command(name="setup")
@app_commands.checks.has_permissions(administrator=True)
async def setup(it: discord.Interaction):
    await it.response.send_message("募集パネルを設置しました！", view=UniversalPanelView())

if __name__ == "__main__":
    if TOKEN:
        bot.run(TOKEN)
    else:
        print("エラー: TOKENが設定されていません。")
