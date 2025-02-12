from fastapi import FastAPI, Request, Query
import httpx
import xml.etree.ElementTree as ET
import re, os
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta
from starlette.responses import Response


load_dotenv()

app = FastAPI()

DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1338991514860257361/MEVHuHDMACFKZ7wb9qrq2Q5Hfbha8aLIrrxn3tOF90hR1tGihxQ05DBWuR_lMEQj--bB"
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

published_videos = set()

def parse_iso_duration(duration):
    pattern = re.compile(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?')
    match = pattern.match(duration)

    if not match:
        return None

    hours = int(match.group(1)) if match.group(1) else 0
    minutes = int(match.group(2)) if match.group(2) else 0
    seconds = int(match.group(3)) if match.group(3) else 0

    return hours * 3600 + minutes * 60 + seconds

def format_duration(seconds):
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    if hours > 0:
        return f"{hours}:{minutes:02}:{seconds:02}"
    return f"{minutes}:{seconds:02}"

def format_publish_date(published_at):
    published_time = datetime.strptime(published_at, "%Y-%m-%dT%H:%M:%SZ")
    moscow_tz = timezone(timedelta(hours=3))  # UTC+3
    published_time = published_time.replace(tzinfo=timezone.utc).astimezone(moscow_tz)

    now = datetime.now(timezone.utc).astimezone(moscow_tz)
    delta = now - published_time

    if delta.days == 0:
        return f"Сегодня, в {published_time.strftime('%H:%M')}"
    elif delta.days == 1:
        return f"Вчера, в {published_time.strftime('%H:%M')}"
    else:
        return published_time.strftime("%d.%m.%Y, в %H:%M")

async def get_video_details(video_id):
    url = f"https://www.googleapis.com/youtube/v3/videos?part=contentDetails,snippet&id={video_id}&key={YOUTUBE_API_KEY}"

    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        data = response.json()

    if "items" in data and len(data["items"]) > 0:
        details = data["items"][0]["contentDetails"]
        snippet = data["items"][0]["snippet"]

        duration = parse_iso_duration(details["duration"])
        title = snippet["title"]
        channel_name = snippet["channelTitle"]
        thumbnail_url = snippet["thumbnails"]["high"]["url"]
        published_at = snippet["publishedAt"]

        return duration, title, channel_name, thumbnail_url, published_at

    return None, None, None, None, None

@app.get("/youtube")
async def verify_hub(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_topic: str = Query(None, alias="hub.topic"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
    hub_lease_seconds: int = Query(None, alias="hub.lease_seconds")
):
    """ YouTube требует подтверждения вебхука """
    if hub_mode == "subscribe" and hub_challenge:
        print(f"✅ YouTube отправил challenge: {hub_challenge}")
        return Response(content=hub_challenge, media_type="text/plain")  # Вернуть challenge в raw-формате
    
    return Response(content="❌ Ошибка: неверный запрос", status_code=400, media_type="text/plain")

@app.post("/youtube")
async def youtube_webhook(request: Request):
    try:
        data = await request.body()
        root = ET.fromstring(data)

        entry = root.find(".//{http://www.w3.org/2005/Atom}entry")
        if entry is None:
            return {"status": "error", "reason": "Entry not found"}

        video_id = entry.find("{http://www.w3.org/2005/Atom}id").text.split(":")[-1]
        video_url = f"https://www.youtube.com/watch?v={video_id}"

        # Проверяем длительность видео
        duration, title, channel_name, thumbnail_url, published_at = await get_video_details(video_id)
        if duration is None:
#            print(f"❌ Видео {video_id} не найдено через API!")
            return {"status": "error", "reason": "Video not found"}

        if duration <= 60:  # Исключаем шортсы
#            print(f"❌ Пропущено: {video_url} (Shorts, {duration} сек)")
            return {"status": "ignored"}

        if video_id in published_videos:
#            print(f"❌ Пропущено: {video_url} (дубликат)")
            return {"status": "ignored"}

        published_videos.add(video_id)

        formatted_duration = format_duration(duration)
        formatted_publish_date = format_publish_date(published_at)

        embed = {
            "title": title,
            "url": video_url,
            "image": {"url": thumbnail_url},
            "description": f"Длительность: {formatted_duration}\n{formatted_publish_date}",
            "color": 0xff0000  # Красный цвет (YouTube)
        }

        button = {
            "type": 1,
            "components": [
                {
                    "type": 2,
                    "label": "СМОТРЕТЬ",
                    "style": 5,
                    "url": video_url
                }
            ]
        }

        # Отправляем видео в Discord
        async with httpx.AsyncClient() as client:
            response = await client.post(DISCORD_WEBHOOK_URL, json={
                "embeds": [embed],
                "components": [button]
            })
#            print(f"✅ Видео опубликовано: {video_url} | Status: {response.status_code}")

        return {"status": "ok"}

    except Exception as e:
#        print(f"❌ Ошибка обработки вебхука: {e}")
        return {"status": "error", "reason": str(e)}