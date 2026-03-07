import discord
from discord.ext import commands
from discord import app_commands
import os
from flask import Flask
import threading

# ----------------- 環境変数 -----------------
TOKEN = os.getenv("DISCORD_TOKEN")
REVIEW_CHANNEL_ID = int(os.getenv("REVIEW_CHANNEL_ID"))

# ----------------- Discord BOT -----------------
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ----------------- Flask サーバ -----------------
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is alive!"

def run_flask():
    app.run(host="0.0.0.0", port=8080)

# Flaskを別スレッドで起動
threading.Thread(target=run_flask).start()

# ----------------- レビューモーダル -----------------
class ReviewModal(discord.ui.Modal, title="レビューを書く"):
    rating = discord.ui.TextInput(
        label="評価 (1〜5)", placeholder="例: 5", required=True
    )
    comment = discord.ui.TextInput(
        label="レビュー内容",
        style=discord.TextStyle.paragraph,
        placeholder="取引の感想を書いてください",
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            rating_value = int(self.rating.value)
            if rating_value < 1 or rating_value > 5:
                raise ValueError
        except:
            await interaction.response.send_message(
                "評価は1〜5の数字で入力してください", ephemeral=True
            )
            return

        channel = bot.get_channel(REVIEW_CHANNEL_ID)
        if channel is None:
            await interaction.response.send_message(
                "レビュー投稿チャンネルが見つかりません。", ephemeral=True
            )
            return

        embed = discord.Embed(title="新しいレビュー", color=discord.Color.green())
        embed.add_field(name="評価", value="⭐" * rating_value)
        embed.add_field(name="コメント", value=self.comment.value)
        embed.set_footer(text=f"投稿者: {interaction.user}")

        try:
            await channel.send(embed=embed)
            await interaction.response.send_message("レビューを投稿しました！", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message(
                "BOTにチャンネル送信権限がありません。", ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                f"レビュー投稿中にエラーが発生しました: {e}", ephemeral=True
            )

# ----------------- ボタン -----------------
class ReviewButton(discord.ui.View):
    @discord.ui.button(label="レビューを書く", style=discord.ButtonStyle.green)
    async def review(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ReviewModal())

# ----------------- /finish -----------------
@bot.tree.command(name="finish", description="取引を終了してレビューを書く")
async def finish(interaction: discord.Interaction):
    await interaction.response.send_message(
        "取引が終了しました。レビューを書いてください👇",
        view=ReviewButton()
    )

# ----------------- /server-rate -----------------
@bot.tree.command(name="server-rate", description="サーバーの平均評価を表示")
async def server_rate(interaction: discord.Interaction):
    channel = bot.get_channel(REVIEW_CHANNEL_ID)
    if channel is None:
        await interaction.response.send_message(
            "レビュー投稿チャンネルが見つかりません。", ephemeral=True
        )
        return

    messages = [msg async for msg in channel.history(limit=None)]
    total, count = 0, 0

    for msg in messages:
        if not msg.embeds:
            continue
        embed = msg.embeds[0]
        rating_field = embed.fields[0].value
        total += rating_field.count("⭐")
        count += 1

    if count == 0:
        await interaction.response.send_message("レビューはまだありません。", ephemeral=True)
        return

    avg = total / count
    await interaction.response.send_message(f"⭐ サーバー平均評価\n平均: {avg:.2f} ⭐\nレビュー数: {count} 件")

# ----------------- /review-star -----------------
@bot.tree.command(name="review-star", description="指定の星評価のレビュー一覧を表示")
@app_commands.describe(star="1〜5の評価を入力")
async def review_star(interaction: discord.Interaction, star: int):
    if star < 1 or star > 5:
        await interaction.response.send_message("1〜5の評価を指定してください。", ephemeral=True)
        return

    channel = bot.get_channel(REVIEW_CHANNEL_ID)
    if channel is None:
        await interaction.response.send_message(
            "レビュー投稿チャンネルが見つかりません。", ephemeral=True
        )
        return

    messages = [msg async for msg in channel.history(limit=None)]
    reviews = []

    for msg in messages:
        if not msg.embeds:
            continue
        embed = msg.embeds[0]
        rating = embed.fields[0].value.count("⭐")
        if rating == star:
            comment = embed.fields[1].value
            footer = embed.footer.text
            reviews.append(f"・コメント: {comment}\n  {footer}")

    if not reviews:
        await interaction.response.send_message(f"⭐{star} のレビューはまだありません。", ephemeral=True)
        return

    await interaction.response.send_message(f"⭐{star} レビュー一覧\n" + "\n\n".join(reviews))

# ----------------- on_ready -----------------
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"ログインしました: {bot.user}")

# ----------------- BOT起動 -----------------
bot.run(TOKEN)
